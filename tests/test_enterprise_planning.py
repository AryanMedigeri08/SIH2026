"""Planning must reuse the final engine and never create a project per trial."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

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


@pytest.fixture(autouse=True)
def no_paid_idea_calls(monkeypatch):
    monkeypatch.setattr(planner, "_get_groq_client", lambda: None)


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
        preview = asyncio.run(planner.evaluate_finances(inputs)).report
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
    assert [p["project_cost"] for p in proposals] == ([300000, 600000, 900000] if cash is None or cash >= 90000 else [])
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
        result = asyncio.run(planner.build_plans(request(path="budget_only", own_cash=60000, business_id=None)))
    assert result["evaluated_businesses"] == 3
    assert len(result["proposals"]) == 3
    assert len({p["business_id"] for p in result["proposals"]}) == 3
    assert result["proposals"][0]["affordable"] is True
    assert all(p["affordable"] for p in result["proposals"])
    save.assert_not_called()
    create.assert_not_called()


def test_planning_reuses_existing_appraisal_verdict_including_marginal_dscr():
    req = request(own_cash=100000)
    with frozen_evidence():
        report = asyncio.run(planner.evaluate_finances(make_input(project_cost=300000))).report
    # 1.25 must not be called healthy by a separate planner threshold.
    report.financial_analysis["dscr"].update(dscr=1.25, verdict="MARGINAL")
    region = {**UNKNOWN_REGION, "recommendation": "HIGH_OPPORTUNITY", "confidence": "HIGH"}
    proposal = planner.describe_trial(req, planner.CATALOGUE["dairy_aggregation"], "Test", planner.REFERENCE_VERSION, report, region)
    assert proposal["appraisal_status"]["code"] == "reconsideration"
    assert proposal["status"] == "review_needed"


def test_region_uses_explicit_business_intent_and_fails_to_provisional(monkeypatch):
    from app.routers import market_intelligence
    from types import SimpleNamespace
    analyze = AsyncMock(side_effect=RuntimeError("provider down"))
    monkeypatch.setattr(market_intelligence, "get_opportunity_engine", lambda: SimpleNamespace(analyze_opportunity=analyze))
    result = asyncio.run(planner.evaluate_region(request(), planner.CATALOGUE["solar_pump_repair"]))
    intent = analyze.call_args.kwargs["business_intent"]
    assert intent.intent_id == "solar_pump_repair"
    assert intent.primary_category == "SERVICES"
    assert result["recommendation"] == "INSUFFICIENT_DATA"
    assert result["evidence"]["missing_evidence"]


def test_custom_idea_requires_description_but_no_quote():
    with pytest.raises(ValidationError):
        request(business_id="custom", idea_description="Short")
    assert request(business_id="custom", idea_description="A bicycle repair shop").machinery_quote is None


@pytest.mark.parametrize("kw", [{"own_cash": -1}, {"own_cash": float("nan")}, {"state_name": " "},
    {"path": "budget_only", "own_cash": None}, {"machinery_quote": -1}, {"project_cost": 1}])
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
    assert handoff["evaluation"]["report"]["financial_analysis"] == proposal["financial_analysis"]
    assert handoff["evaluation"]["dpr"]
    store.save("alice", request(own_cash=0), result)
    with pytest.raises(HTTPException):
        store.accept("alice", draft_id, accept)
    fresh = store.save("alice", request(own_cash=0), result)
    store.drafts[fresh].expires = 0
    with pytest.raises(HTTPException) as error:
        store.accept("alice", fresh, accept)
    assert error.value.status_code == 410


def test_endpoints_require_authentication_and_return_planning_contract(monkeypatch):
    from app.database import DatabaseManager
    from app.core import planning_selection
    database = DatabaseManager()
    monkeypatch.setattr(planning_selection, "db_manager", database)
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
    assert "_evaluations" not in result
    evaluator = AsyncMock(side_effect=AssertionError("Selection must not appraise again"))
    monkeypatch.setattr(planner, "evaluate_finances", evaluator)
    monkeypatch.setattr(feasibility, "_run_pipeline", AsyncMock(side_effect=AssertionError("No repeat pipeline")))
    response = client.post(f"/planning/{result['draft_id']}/accept", json={
        "proposal_id": result["proposals"][0]["proposal_id"], "acknowledge_estimates": True, "accept_risks": True})
    assert response.status_code == 200
    project = response.json()
    assert project["sector"] == "dairy"
    assert project["status"] == "analyzed"
    assert project["analysis_result"]["report"]["financial_analysis"] == result["proposals"][0]["financial_analysis"]
    assert project["analysis_result"]["dpr"]
    replay = client.post(f"/planning/{result['draft_id']}/accept", json={
        "proposal_id": result["proposals"][0]["proposal_id"], "acknowledge_estimates": True, "accept_risks": True})
    assert replay.status_code == 200
    assert replay.json()["project_id"] == project["project_id"]
    assert len(database.in_memory_projects) == len(database.in_memory_reports) == 1
    evaluator.assert_not_called()
    assert client.post("/planning/evaluate", json=request().model_dump()).status_code == 429


@pytest.mark.parametrize("failure", [None, "cash", "model", "region"])
def test_all_candidates_checked_once_and_only_passing_plans_returned(monkeypatch, failure):
    ideas = [{"sector_id": f"test_{i}", "enterprise_name": name, "sector": "dairy",
              "business_category": "manufacturing", "description": "Synthetic business candidate",
              "configuration_label": "Test", "target_cost": cost, "source": "test"}
             for i, (name, cost) in enumerate([
                 ("Good A", 600000), ("Candidate B", 1000000 if failure == "cash" else 480000), ("Good C", 360000)])]
    generate = AsyncMock(return_value=ideas)
    monkeypatch.setattr(planner, "generate_dynamic_business_ideas", generate)
    async def regional(_req, item):
        return {**UNKNOWN_REGION, "recommendation": "CONSTRAINED_MARKET" if failure == "region" and item["enterprise_name"] == "Candidate B" else "HIGH_OPPORTUNITY",
                "confidence": "HIGH", "composite_score": 70}
    monkeypatch.setattr(planner, "evaluate_region", regional)
    evaluate = planner.evaluate_finances
    async def appraise(inputs):
        result = await evaluate(inputs)
        if failure == "model" and inputs.enterprise_name == "Candidate B":
            result.report.ml_viability["verdict"] = "CAUTION"
        return result
    monkeypatch.setattr(planner, "evaluate_finances", appraise)
    with frozen_evidence():
        result = asyncio.run(planner.build_plans(request(path="budget_only", own_cash=60000, business_id=None)))
        assert feasibility.predict_viability.call_count == 3
        assert feasibility.extract_contextual_machinery.call_count == 3
        assert all(not call.kwargs["use_ai"] for call in feasibility.extract_contextual_machinery.call_args_list)
        assert all(call.kwargs["force_fallback"] for call in feasibility.generate_executive_synthesis.call_args_list)
    assert {p["name"] for p in result["proposals"]} == ({"Good A", "Candidate B", "Good C"} if failure is None else {"Good A", "Good C"})
    assert len(result["_evaluations"]) == (3 if failure is None else 2)
    assert result["rejected_trials"] == (0 if failure is None else 1)
    generate.assert_awaited_once()


@pytest.mark.parametrize("provider_error", [False, True])
def test_one_llm_batch_and_local_fallback_without_retry(monkeypatch, provider_error):
    proposals = [{"tier_index": i % 3, "enterprise_name": f"Synthetic idea {i}", "sector": "dairy",
                  "business_category": "manufacturing", "description": "Check this local business", "target_cost": 1} for i in range(6)]
    create = Mock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"proposals": proposals})))]))
    if provider_error:
        create.side_effect = RuntimeError("429 rate limit (synthetic)")
    monkeypatch.setattr(planner, "_get_groq_client", lambda: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    req = request(path="budget_only", own_cash=60000, business_id=None)
    tiers = planner.calculate_budget_tiers(req.own_cash, req.promoter_category)
    ideas = asyncio.run(planner.generate_dynamic_business_ideas(req, tiers))
    create.assert_called_once()
    assert create.call_args.kwargs["max_tokens"] == 2500
    assert len(ideas) == 3
    assert all(idea["target_cost"] in [t["cost"] for t in tiers] for idea in ideas)


def test_failed_appraisal_cannot_be_selected_even_with_risk_acceptance(monkeypatch):
    monkeypatch.setattr(planner, "evaluate_region", AsyncMock(return_value=UNKNOWN_REGION))
    with frozen_evidence():
        result = asyncio.run(planner.build_plans(request()))
    result["proposals"][0]["ml_viability"]["verdict"] = "RECONSIDER"
    store = planner.PlanningSessions()
    draft_id = store.save("alice", request(), result)
    with pytest.raises(HTTPException) as error:
        store.accept("alice", draft_id, AcceptPlan(proposal_id=result["proposals"][0]["proposal_id"], acknowledge_estimates=True, accept_risks=True))
    assert error.value.status_code == 409


def test_old_preview_without_cached_dpr_requires_refresh(monkeypatch):
    monkeypatch.setattr(planner, "evaluate_region", AsyncMock(return_value=UNKNOWN_REGION))
    with frozen_evidence():
        result = asyncio.run(planner.build_plans(request()))
    result.pop("_evaluations")
    store = planner.PlanningSessions()
    draft_id = store.save("alice", request(), result)
    with pytest.raises(HTTPException) as error:
        store.accept("alice", draft_id, AcceptPlan(proposal_id=result["proposals"][0]["proposal_id"], acknowledge_estimates=True, accept_risks=True))
    assert error.value.status_code == 409


def test_drafts_survive_worker_change_and_restart_without_project_rows(tmp_path):
    import sqlite3
    from types import SimpleNamespace
    from app.core.planning_drafts import PlanningDraftStore
    path = tmp_path / "shared-planning.sqlite3"
    db_a = SimpleNamespace(pool=None, sqlite=sqlite3.connect(path))
    db_b = SimpleNamespace(pool=None, sqlite=sqlite3.connect(path))
    first = PlanningDraftStore(db_a, planner.PlanningSessions())
    second = PlanningDraftStore(db_b, planner.PlanningSessions())
    result = {"proposals": [], "reference_version": planner.REFERENCE_VERSION}
    try:
        draft_id = asyncio.run(first.save("alice", request(), result))
        assert asyncio.run(second.get("alice", draft_id)).result == result
        with pytest.raises(HTTPException) as error:
            asyncio.run(second.get("bob", draft_id))
        assert error.value.status_code == 404
        replacement = asyncio.run(second.save("alice", request(own_cash=0), result))
        with pytest.raises(HTTPException):
            asyncio.run(first.get("alice", draft_id))
        assert asyncio.run(first.get("alice", replacement)).request.own_cash == 0
        assert db_a.sqlite.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [("planning_drafts",)]
        db_a.sqlite.close()
        db_a.sqlite = sqlite3.connect(path)
        restarted = PlanningDraftStore(db_a, planner.PlanningSessions())
        assert asyncio.run(restarted.get("alice", replacement)).result == result
        db_a.sqlite.execute("UPDATE planning_drafts SET expires_at=0")
        db_a.sqlite.commit()
        expired = asyncio.run(second.get("alice", replacement))
        with pytest.raises(HTTPException) as error:
            planner.PlanningSessions().accept("alice", replacement, AcceptPlan(proposal_id="missing"), draft=expired)
        assert error.value.status_code == 410
    finally:
        db_a.sqlite.close()
        db_b.sqlite.close()
