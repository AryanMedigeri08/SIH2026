"""Catalogue integrity and catchment/budget sizing regressions."""
import asyncio
import copy
import json
from unittest.mock import AsyncMock

import pytest

from backend.app.core.business_interpreter import interpret_business_idea
from backend.app.core.machinery_matcher import load_machinery_dataset
from backend.app.core.machinery_variants import resolve_machinery_plan, select_machinery_capacity


def paneer():
    return interpret_business_idea("Make paneer from milk")["machinery_plan"]


def model_selection(variant="small", required=180):
    return json.dumps({"variant_id": variant, "required_capacity_quantity": required,
        "demand": {"monthly_output_demand": required * 25 / 6, "output_unit": "kg", "capacity_unit": "litres",
            "capacity_units_per_output_unit": 5, "working_days_per_month": 25, "working_hours_per_day": 8,
            "stock_turnovers_per_month": 1, "expansion_headroom_pct": 20},
        "demand_basis": "100 households × 0.3 kg paneer/day × 5 litres milk/kg, plus 20% headroom = 180 litres milk/day.",
        "rationale": "250 litres/day covers the reachable paneer demand with room to grow."}), None, "test"


def test_every_profile_has_ordered_options_and_preserves_reference_prices():
    for profile in load_machinery_dataset():
        variants = profile["capacity_variants"]
        assert len(variants) == 5
        assert len({v["variant_id"] for v in variants}) == 5
        amounts = [v["capacity"]["quantity"] for v in variants]
        costs = [v["total_machinery_cost_inr"] for v in variants]
        assert amounts == sorted(amounts) and len(set(amounts)) == 5
        assert costs == sorted(costs)
        for v in variants:
            assert v["total_machinery_cost_inr"] == sum(m["quantity"] * m["estimated_cost_inr"] for m in v["machine_costs"])
            assert all(isinstance(m["quantity"], int) and m["quantity"] >= 1 and m["estimated_cost_inr"] > 0 for m in v["machine_costs"])
        reference = next(v for v in variants if v["variant_id"] == "reference")
        assert reference["typical_capacity"] == profile["typical_capacity"]
        for original, ref in zip(profile["machinery_list"], reference["machine_costs"]):
            assert ref["estimated_cost_inr"] == original["estimated_cost_inr"]
            assert ref["quantity"] == original["quantity"]


def test_llm_receives_local_evidence_all_variants_and_selects_small_dairy():
    captured = {}
    context = {"idea": "Make paneer", "households": 100, "population_projection": {"projected_population": 480},
        "amenities": {"power_supply_hours_per_day": 12}, "project_cost": 2000000}
    def llm(**kwargs):
        captured.update(json.loads(kwargs["messages"][1]["content"]))
        return model_selection()
    plan = select_machinery_capacity(paneer(), context, llm)
    assert captured["evidence"] == context
    assert len(captured["capacity_variants"]) == 5
    assert captured["equipment_budget_inr"] == 1400000
    assert plan["selected_capacity_variant_id"] == "small"
    assert plan["capacity"]["quantity"] == 250
    assert plan["capacity"]["material"] == "milk input"
    assert plan["capacity_selection"]["source"] == "llm_capacity_selection"
    assert all("Ghee" not in m["machine_name"] for m in plan["machinery_list"])
    assert plan["total_machinery_cost_inr"] < paneer()["total_machinery_cost_inr"]
    assert all(m["power_hp"] == 0 for m in plan["machinery_list"])


@pytest.mark.parametrize("answer", [model_selection("expanded"), model_selection("invented"), ('{}', None, 'test'), ('[]', None, 'test')])
def test_invalid_or_oversized_recommendations_fall_back_without_blocking(answer):
    plan = select_machinery_capacity(paneer(), {"project_cost": 2000000}, lambda **kwargs: answer)
    assert plan["selected_capacity_variant_id"] == "starter"
    assert plan["capacity_selection"]["source"] == "indicative_capacity_selection"
    assert plan["total_machinery_cost_inr"] > 0


def test_larger_catchment_can_select_expanded_capacity():
    plan = select_machinery_capacity(paneer(), {"project_cost": 10000000, "households": 5000}, lambda **kwargs: model_selection("expanded", 1500))
    assert plan["capacity"]["quantity"] == 2000
    assert plan["capacity_selection"]["source"] == "llm_capacity_selection"


def test_reference_capacity_cannot_replace_computed_demand_requirement():
    reply, _, model = model_selection("reference", 180)
    parsed = json.loads(reply)
    parsed["required_capacity_quantity"] = 1100
    plan = select_machinery_capacity(paneer(), {"project_cost": 10000000}, lambda **kwargs: (json.dumps(parsed), None, model))
    assert plan["capacity_selection"]["source"] == "indicative_capacity_selection"
    assert plan["selected_capacity_variant_id"] == "starter"


def test_one_bounded_model_repair_can_correct_oversizing():
    calls = []
    def llm(**kwargs):
        calls.append(kwargs)
        return model_selection("expanded" if len(calls) == 1 else "small", 180)
    plan = select_machinery_capacity(paneer(), {"project_cost": 2000000}, llm)
    assert len(calls) == 2
    assert plan["capacity_selection"]["source"] == "llm_capacity_selection"
    assert plan["selected_capacity_variant_id"] == "small"


def test_small_budget_never_silently_becomes_a_large_plant():
    plan = select_machinery_capacity(paneer(), {"project_cost": 10000}, lambda **kwargs: model_selection("expanded", 1500))
    assert plan["selected_capacity_variant_id"] == "starter"
    assert plan["equipment_funding_gap_inr"] > 0
    assert plan["equipment_funding_gap_inr"] == plan["total_machinery_cost_inr"] - 7000


def test_selected_size_and_prices_survive_rehydration_without_trusting_client_prices():
    plan = select_machinery_capacity(paneer(), {"project_cost": 2000000}, lambda **kwargs: model_selection())
    before = copy.deepcopy(plan)
    plan["machinery_list"][0]["estimated_cost_inr"] = 1
    plan["total_machinery_cost_inr"] = 1
    plan["typical_capacity"] = "999999 litres/day"
    restored = resolve_machinery_plan(plan)
    assert restored["typical_capacity"] == before["typical_capacity"]
    assert restored["total_machinery_cost_inr"] == before["total_machinery_cost_inr"]
    assert restored["machinery_list"] == before["machinery_list"]


def test_cold_storage_variants_remain_stock_not_daily_production():
    profile = load_machinery_dataset()[-1]
    for v in profile["capacity_variants"]:
        assert v["capacity"]["period"] == "stock"
        assert v["capacity"]["capacity_kind"] == "storage"
        assert "/day" not in v["typical_capacity"]


def test_onboarding_sizes_after_equity_then_retains_the_choice(monkeypatch):
    from backend.app.main import app
    from app.routers import onboarding
    from app.core.amenities_client import VillageAmenitiesResult
    monkeypatch.setattr(onboarding.db_manager, "get_census_demographics", AsyncMock(return_value={"base_population_2011": 480, "provenance": "census_exact_village"}))
    monkeypatch.setattr(onboarding.db_manager, "get_district_msme_stats", AsyncMock(return_value={"total_msme": 1000}))
    monkeypatch.setattr(onboarding.db_manager, "get_state_cpi_inflation", AsyncMock(return_value=5))
    monkeypatch.setattr(onboarding, "fetch_village_amenities", lambda **kwargs: VillageAmenitiesResult(6, 12, True, False, True, False, "regional_baseline"))
    calls = []
    def llm(**kwargs):
        calls.append(json.loads(kwargs["messages"][1]["content"]))
        return model_selection()
    monkeypatch.setattr(onboarding.chat_service, "_call_llm_chat_completion", llm)
    fields = {"business_idea": "Make paneer", "sector": "dairy", "promoter_equity": 500000,
        "state_name": "Maharashtra", "district_name": "Pune", "village_name": "Test village"}
    selected = asyncio.run(onboarding._size_machinery_for_fields(fields, paneer()))
    fields["machinery_plan"] = selected
    restored = onboarding._machinery_profile_for_fields(fields)
    assert restored["selected_capacity_variant_id"] == "small"
    assert restored["capacity"]["quantity"] == 250
    assert restored["total_machinery_cost_inr"] == selected["total_machinery_cost_inr"]
    assert calls[0]["evidence"]["census"]["provenance"] == "census_exact_village"
    assert calls[0]["evidence"]["households"] > 0
    assert asyncio.run(onboarding._size_machinery_for_fields(fields, restored))["capacity"]["quantity"] == 250
    assert len(calls) == 1
    fields["promoter_equity"] = 600000
    asyncio.run(onboarding._size_machinery_for_fields(fields, restored))
    assert len(calls) == 2
