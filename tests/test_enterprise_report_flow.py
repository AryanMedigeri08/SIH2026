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


@pytest.mark.parametrize("reply,own_capital", [(None, 100000), ("[]", 100000), ('{"selling_price_inr":null}', 500000), ("valid", 100000)])
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
    monkeypatch.setattr(pipeline, "generate_executive_synthesis", lambda *args, **kwargs: ExecutiveSynthesis(
        "Planning appraisal", ["Review operating assumptions"], "Estimated costs", "en", False, True, 0, "test", "test"))
    captured = []
    def llm(**kwargs):
        captured.append(kwargs)
        if reply == "valid":
            package = json.loads(kwargs["messages"][1]["content"])
            if "output_schema_example" in package:
                return json.dumps(package["output_schema_example"]), None, "test"
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
    assert fin["gross_annual_sales"] > 0
    assert fin["planning_assumptions"]["is_estimate"] is True
    assert fin["annual_net_profit"] < 0
    assert fin["dscr"]["dscr"] < 1
    rows = dpr.section_3_financial_projections.projection_years
    assert rows[0].gross_turnover == fin["gross_annual_sales"]
    assert rows[0].annual_dscr == pytest.approx(fin["dscr"]["dscr"], abs=.01)
    assert [row.model_dump() for row in rows] == fin["five_year_projections"]
    assert "Optimistic planning estimate" in dpr_to_html(dpr)
    assert "Optimistic planning estimate" in dpr_to_printable_markdown(dpr)
    json.dumps(report.model_dump(mode="json"), allow_nan=False)
    assert any("amenities" in call["messages"][1]["content"] for call in captured)
    if own_capital == 500000:
        assert fin["debt_service_required"] is False
        assert fin["amortization"]["monthly_emi"] == 0
        assert fin["dscr"]["verdict"] == "NO DEBT"


def test_project_accepts_missing_sales_and_retains_interpreted_idea():
    from app.models.schemas import ProjectCreate
    from app.routers.projects import _project_dict_to_user_input
    project = ProjectCreate(business_name="Candles", business_category="manufacturing", sector="general",
        investment_amount=50000, state_name="Maharashtra", district_name="Pune", business_idea="Make candles",
        business_type="manufacturing", machinery_plan={"has_estimated_equipment": True, "machinery_list": []})
    assert project.annual_turnover_estimate is None
    restored = _project_dict_to_user_input(project.model_dump())
    assert restored.business_idea == "Make candles"
    assert restored.business_type == "manufacturing"
    assert restored.machinery_plan == project.machinery_plan
    assert restored.annual_turnover_estimate is None
