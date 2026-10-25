"""End-to-end offline report generation with incomplete or invalid AI estimates."""
import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from backend.app.main import app  # Application import paths.
from app.models.schemas import UserInput
from app.routers import feasibility as pipeline
from app.core.amenities_client import VillageAmenitiesResult
from app.core.inference import _rule_based_fallback
from app.core.executive_synthesizer import ExecutiveSynthesis
from dpr_generator import dpr_to_html, dpr_to_printable_markdown
from tests.planning_fixtures import raw_input_conversion, uniform_price_mix, business_demand_fixture


@pytest.mark.parametrize("reply,own_capital", [(None, 100000), ("[]", 100000), ('{"selling_price_inr":null}', 2000000), ("valid", 100000)])
def test_report_completes_and_dashboard_matches_export(monkeypatch, reply, own_capital):
    monkeypatch.setattr(pipeline.db_manager, "get_census_demographics", AsyncMock(return_value={
        "base_population_2011": 48, "district_population_2011": 1000000,
        "population_source": "census_exact", "data_year": 2011,
    }))
    monkeypatch.setattr(pipeline.db_manager, "get_district_msme_stats", AsyncMock(return_value={"total_msme": 2000}))
    monkeypatch.setattr(pipeline.db_manager, "get_state_cpi_inflation", AsyncMock(return_value=5))
    monkeypatch.setattr(pipeline.db_manager, "get_weather_risk_score", AsyncMock(return_value=.2))
    monkeypatch.setattr(pipeline, "fetch_village_amenities", lambda **kwargs: VillageAmenitiesResult(
        6, 12, True, False, True, False, "regional_baseline"))
    monkeypatch.setattr(pipeline, "predict_viability", _rule_based_fallback)
    synthesis_inputs = []
    def synthesis(payload, **kwargs):
        synthesis_inputs.append(payload)
        return ExecutiveSynthesis("Planning appraisal", ["Review operating assumptions"], "Estimated costs", "en", False, True, 0, "test", "test")
    monkeypatch.setattr(pipeline, "generate_executive_synthesis", synthesis)
    captured = []
    def llm(**kwargs):
        captured.append(kwargs)
        if reply == "valid":
            package = json.loads(kwargs["messages"][1]["content"])
            if "budget_evidence" in package:
                from app.core.project_budget import _fallback
                return _fallback(package["immutable_equipment_total"], package["immutable_owned_credit"], package["accepted_operations"]).model_dump_json(), None, "test"
            if "immutable_financing_facts" in package:
                from app.core.llm_financials import _fallback
                ops = {**package["accepted_operating_calculations"],
                       "assumptions": {"values": package["operating_assumptions"], "project_budget": package.get("itemized_budget")}}
                return _fallback(ops, package["immutable_financing_facts"]).model_dump_json(), None, "test"
            if "output_schema_example" in package:
                from app.core.enterprise_assumptions import estimate_operations, calculate_operations
                seed = estimate_operations(package["evidence"])
                quantity = package["evidence"]["machinery_profile"]["capacity"]["quantity"]
                seed["values"]["rated_monthly_input_units"] = quantity * 25
                return json.dumps({"values": seed["values"], "calculations": calculate_operations(seed),
                    "demand_forecast": business_demand_fixture(seed["values"], calculate_operations(seed)),
                    "conversion": raw_input_conversion(seed["values"]),
                    "pricing": uniform_price_mix(seed["values"]),
                    "capacity": {"quantity": quantity, "unit": "litres", "period": "day", "monthly_quantity": quantity * 25,
                        "capacity_kind": "throughput", "basis": f"{quantity} litres/day * 25 working days"}}), None, "test"
            return json.dumps({"sector": "dairy", "business_category": "manufacturing", "business_type": "manufacturing",
                "profile_name": "Dairy Processing Unit (Milk Pasteurization, Paneer, Curd & Ghee)"}), None, "test"
        if reply is None:
            raise TimeoutError("Provider unavailable")
        return reply, None, "test"
    monkeypatch.setattr(pipeline.chat_service, "_call_llm_chat_completion", llm)
    report, dpr = asyncio.run(pipeline._run_pipeline(UserInput(
        enterprise_name="Village Paneer", business_idea="Make paneer from milk",
        project_cost=500000, promoter_equity=own_capital,
        state_name="Maharashtra", district_name="Pune", village_name="Test village",
        latitude=18.5, longitude=73.8, annual_turnover_source="estimated",
    )))
    fin = report.financial_analysis
    budget, funding = fin["project_budget"], fin["funding_plan"]
    capital = dpr.section_2_capital_outlay_and_finance
    assert capital["means_of_finance"]["reconciliation_balanced"]
    assert capital["means_of_finance"]["bank_term_loan_amount"] == pytest.approx(fin["loan_principal"])
    assert capital["means_of_finance"]["capital_subsidy_amount"] == 0
    assert fin["net_project_cost"] == budget["net_fresh_outlay"]
    assert funding["cash_applied"] <= own_capital
    assert synthesis_inputs[0]["subsidy_amount"] == 0
    assert synthesis_inputs[0]["potential_scheme_subsidy"] == fin["potential_scheme_subsidy"]
    assert synthesis_inputs[0]["effective_loan"] == fin["loan_principal"]
    assert synthesis_inputs[0]["funding_basis"] == funding["basis"]
    assert budget["net_fresh_outlay"] >= budget["equipment_total"]-budget["owned_machinery_credit"]
    assert sum(capital["capital_outlay"][key]["amount_inr"] for key in ("plant_and_machinery", "electrification_and_site_works", "initial_working_capital_reserve", "contingency_and_pre_operative")) == pytest.approx(fin["net_project_cost"])
    assert fin["gross_annual_sales"] > 0
    assert fin["planning_assumptions"]["is_estimate"] is True
    assert fin["annual_net_profit"] < 0
    assert fin["dscr"]["dscr"] < 1
    rows = dpr.section_3_financial_projections.projection_years
    assert rows[0].gross_turnover == fin["gross_annual_sales"]
    assert rows[0].annual_dscr == pytest.approx(fin["dscr"]["dscr"], abs=.01)
    assert [row.model_dump() for row in rows] == fin["five_year_projections"]
    estimate_label = "Provisional base planning scenario" if reply == "valid" else "Optimistic planning estimate"
    assert estimate_label in dpr_to_html(dpr)
    assert estimate_label in dpr_to_printable_markdown(dpr)
    assert "Itemized estimated budget" in dpr_to_html(dpr)
    assert "Itemized estimated budget" in dpr_to_printable_markdown(dpr)
    assert "Unconfirmed scheme subsidy is excluded" in dpr_to_html(dpr)
    if fin["debt_service_required"]:
        assert "Full repayment-year DSCR" in dpr_to_html(dpr)
        assert "Full repayment-year DSCR" in dpr_to_printable_markdown(dpr)
    json.dumps(report.model_dump(mode="json"), allow_nan=False)
    assert any("amenities" in call["messages"][1]["content"] for call in captured)
    assert report.input_parameters.machinery_plan["selected_capacity_variant_id"] == "starter"
    assert fin["planning_assumptions"]["evidence"]["machinery_profile"]["capacity"]["quantity"] == 100
    if reply == "valid":
        assert "Business-specific demand forecast" in dpr_to_html(dpr)
        assert "Business-specific demand forecast" in dpr_to_printable_markdown(dpr)
        assert fin["planning_assumptions"]["demand_forecast"]["scenarios"]["base"]["realized_monthly_units"] == fin["operating_model"]["monthly_sales_units"]
        definition = fin["planning_assumptions"]["conversion"]["saleable_unit_definition"]
        assert definition in dpr_to_html(dpr)
        assert definition in dpr_to_printable_markdown(dpr)
        assert report.pricing_recommendation["saleable_unit_definition"] == definition
        assert report.pricing_recommendation["average_selling_price_inr"] == fin["operating_model"]["average_selling_price_inr"]
        assert "Average realized selling price" in dpr_to_html(dpr)
        assert "Uniform test price" in dpr_to_printable_markdown(dpr)
        assert fin["operating_model"]["calculation_source"] == "llm_calculated"
        assert fin["financial_calculation_source"] == "llm_calculated"
        assert fin["average_dscr"] == dpr.section_3_financial_projections.average_dscr
    if own_capital == 2000000:
        assert fin["debt_service_required"] is False
        assert fin["amortization"]["monthly_emi"] == 0
        assert fin["dscr"]["verdict"] == "NO DEBT"


def test_project_accepts_missing_sales_and_retains_interpreted_idea():
    from app.models.schemas import ProjectCreate
    from app.routers.projects import _project_dict_to_user_input
    project = ProjectCreate(business_name="Candles", business_category="manufacturing", sector="general",
        investment_amount=50000, state_name="Maharashtra", district_name="Pune", business_idea="Make candles",
        business_type="manufacturing", machinery_plan={"has_estimated_equipment": True, "machinery_list": []},
        owned_machines=[{"machine_name": "Wax melter", "quantity": 1}])
    assert project.annual_turnover_estimate is None
    restored = _project_dict_to_user_input(project.model_dump())
    assert restored.business_idea == "Make candles"
    assert restored.business_type == "manufacturing"
    assert restored.machinery_plan == project.machinery_plan
    assert restored.owned_machines == project.owned_machines
    assert restored.annual_turnover_estimate is None
