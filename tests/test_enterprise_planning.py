"""Planning must reuse the final engine and never create a project per trial."""
import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from tests.test_planning_financial_baseline import CASES, frozen_evidence, make_input
from app.core import enterprise_planning as planner
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.models.planning import AcceptPlan, PlanningRequest
from app.routers import feasibility
from app.routers.planning import router


def request(**kw):
    return PlanningRequest(**{
        "path": "idea_only", "business_id": "dairy_aggregation", "state_name": "West Bengal",
        "district_name": "Bankura", "block_name": "Test block", "village_name": "Test village",
        "promoter_name": "Test promoter", **kw,
    })


UNKNOWN_REGION = {
    "recommendation": "INSUFFICIENT_DATA", "composite_score": 0, "confidence": "INSUFFICIENT_DATA",
    "evidence": {"missing_evidence": ["Customer demand is not verified"]},
    "supply_metrics": {}, "demand_features": {}, "data_lineage": [],
}


@pytest.mark.parametrize("case", CASES.values(), ids=CASES.keys())
def test_preview_has_exact_final_pipeline_financial_parity(case):
    with frozen_evidence():
        inputs = make_input(**case)
        original = inputs.model_dump()
        preview = asyncio.run(planner.evaluate_finances(inputs))
        final, _ = asyncio.run(feasibility._run_pipeline(inputs.model_copy(deep=True)))
    assert preview.financial_analysis == final.financial_analysis
    assert preview.scheme_optimization == final.scheme_optimization
    assert inputs.model_dump() == original  # autosizing must not mutate the caller


@pytest.mark.parametrize("cash", [None, 0, 1000, 100000])
def test_fixed_cost_trials_unknown_zero_and_cash_gap(monkeypatch, cash):
    monkeypatch.setattr(planner, "evaluate_region", AsyncMock(return_value=UNKNOWN_REGION))
    with frozen_evidence():
        result = asyncio.run(planner.build_plans(request(own_cash=cash)))
    proposals = result["proposals"]
    assert [p["project_cost"] for p in proposals] == [300000, 600000, 900000]
    for p in proposals:
        assert p["available_own_money"] == cash
        assert p["equity_gap"] == (None if cash is None else max(p["required_own_money"] - cash, 0))
        assert p["status"] == "review_needed"  # missing evidence never becomes a proven fit


def test_budget_only_shortlist_and_no_project_writes(monkeypatch):
    monkeypatch.setattr(planner, "evaluate_region", AsyncMock(return_value=UNKNOWN_REGION))
    save = AsyncMock(side_effect=AssertionError("preview must not save a report"))
    monkeypatch.setattr(feasibility.db_manager, "save_feasibility_report", save)
    create = AsyncMock(side_effect=AssertionError("preview must not create a project"))
    monkeypatch.setattr(feasibility.db_manager, "create_project", create)
    with frozen_evidence():
        result = asyncio.run(planner.build_plans(request(path="budget_only", own_cash=15000, business_id=None)))
    assert result["evaluated_businesses"] == 6
    assert len(result["proposals"]) == 3
    assert len({p["business_id"] for p in result["proposals"]}) == 3
    assert result["proposals"][0]["affordable"] is True
    save.assert_not_called()
    create.assert_not_called()


def test_custom_idea_requires_cost_evidence():
    with pytest.raises(ValidationError):
        request(business_id="custom", idea_description="Something new")
    req = request(business_id="custom", idea_description="A bicycle repair shop", machinery_quote=110000)
    assert planner.configurations({}, req.machinery_quote) == [("Your equipment quote", 200000, "user_equipment_quote")]


@pytest.mark.parametrize("kw", [{"own_cash": -1}, {"own_cash": float("nan")}, {"state_name": " "},
    {"path": "budget_only", "own_cash": None}, {"machinery_quote": 0}, {"project_cost": 1}])
def test_invalid_inputs_rejected(kw):
    with pytest.raises(ValidationError):
        request(**kw)


def test_pipeline_failure_is_retryable(monkeypatch):
    monkeypatch.setattr(planner, "evaluate_region", AsyncMock(return_value=UNKNOWN_REGION))
    monkeypatch.setattr(planner, "evaluate_finances", AsyncMock(side_effect=RuntimeError("unavailable")))
    with pytest.raises(HTTPException) as error:
        asyncio.run(planner.build_plans(request()))
    assert error.value.status_code == 503


def test_owner_scoped_acceptance_expiry_invalidation_and_unknown_cash(monkeypatch):
    monkeypatch.setattr(planner, "evaluate_region", AsyncMock(return_value=UNKNOWN_REGION))
    with frozen_evidence():
        result = asyncio.run(planner.build_plans(request()))
    store = planner.PlanningSessions()
    draft_id = store.save("alice", request(), result)
    proposal = result["proposals"][0]
    accept = AcceptPlan(proposal_id=proposal["proposal_id"], acknowledge_estimates=True, accept_risks=True)
    with pytest.raises(HTTPException) as error:
        store.accept("bob", draft_id, accept)
    assert error.value.status_code == 404
    with pytest.raises(HTTPException) as error:
        store.accept("alice", draft_id, accept.model_copy(update={"accept_risks": False}))
    assert error.value.status_code == 409
    handoff = store.accept("alice", draft_id, accept)
    assert handoff["initial_data"]["margin_capital"] == proposal["required_own_money"]
    assert handoff["initial_data"]["annual_turnover_estimate"] == proposal["input_parameters"]["annual_turnover_estimate"]
    # Replaying the accepted input into the final pipeline keeps all financial output.
    from app.models.schemas import UserInput
    with frozen_evidence():
        final, _ = asyncio.run(feasibility._run_pipeline(UserInput(**handoff["initial_data"])))
    assert final.financial_analysis == proposal["financial_analysis"]
    store.save("alice", request(own_cash=0), result)
    with pytest.raises(HTTPException):
        store.accept("alice", draft_id, accept)
    fresh = store.save("alice", request(own_cash=0), result)
    assert store.accept("alice", fresh, accept)["initial_data"]["margin_capital"] == 0
    store.drafts[fresh].expires = 0
    with pytest.raises(HTTPException) as error:
        store.accept("alice", fresh, accept)
    assert error.value.status_code == 410


def test_endpoints_require_authentication_and_return_planning_contract(monkeypatch):
    app = FastAPI()
    app.include_router(router)
    monkeypatch.setattr(planner, "evaluate_region", AsyncMock(return_value=UNKNOWN_REGION))
    client = TestClient(app)
    assert client.get("/planning/businesses").status_code == 401
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="planning-api-test")
    assert len(client.get("/planning/businesses").json()) == 16
    with frozen_evidence():
        response = client.post("/planning/evaluate", json=request().model_dump())
    assert response.status_code == 200
    result = response.json()
    response = client.post(f"/planning/{result['draft_id']}/accept", json={
        "proposal_id": result["proposals"][0]["proposal_id"], "acknowledge_estimates": True, "accept_risks": True})
    assert response.status_code == 200
    assert response.json()["initial_data"]["sector"] == "dairy"
    assert client.post("/planning/evaluate", json=request().model_dump()).status_code == 429
