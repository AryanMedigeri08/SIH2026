"""Opt-in ODOP advice, score boundaries, shared cache and provider budget."""
import asyncio
import json
import sqlite3
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from tests.test_planning_financial_baseline import make_input  # initializes core import paths
from app.core import odop_hybrid as hybrid
from app.core.odop_hybrid_store import HybridStore
from app.models.odop_hybrid import HybridRequest
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.routers.odop_hybrid import router


def request(**overrides):
    return HybridRequest(**{"consent": True, "state_name": "West Bengal", "district_name": "Bankura",
        "enterprise_name": "Village dairy", "business_category": "manufacturing", "sector": "dairy",
        "idea_description": "Collect milk and make curd for local shops.", **overrides})


def reply(score=85):
    return dict(score=score, summary="Packaging may connect the two businesses; check hygiene and costs.",
        hybrid_name="Dairy with locally sourced clay-pot packaging",
        hybrid_description="Make curd using food-safe clay pots sourced from local artisans; test customer demand first.",
        reasons=["A packaging supply-chain link preserves the original dairy business."],
        practical_steps=["Confirm food-safe pots and compare unit costs."], risks=["Food safety and breakage"],
        missing_information=["Verified demand for this packaging"])


@pytest.fixture
def setup(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(hybrid.time, "time", lambda: now[0])
    completion = Mock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(reply())))]))
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completion)))
    monkeypatch.setattr(hybrid, "_get_groq_client", lambda: client)
    store = HybridStore(SimpleNamespace(pool=None, sqlite=None))
    service = hybrid.HybridEvaluator(store)
    return service, store, completion, now


@pytest.mark.parametrize("score,band", [(0,"poor"),(59,"poor"),(60,"possible"),(61,"possible"),(80,"possible"),(81,"recommended"),(100,"recommended")])
def test_score_boundaries(score, band):
    assert hybrid.score_band(score)[0] == band


def test_cached_results_one_provider_call_no_financial_evaluation(setup, monkeypatch):
    service, store, completion, now = setup
    from app.routers import feasibility
    finance = Mock(side_effect=AssertionError("Synergy advice must not calculate finances"))
    monkeypatch.setattr(feasibility, "_run_pipeline", finance)
    result = asyncio.run(service.evaluate("alice", request()))
    assert result["score"] == 85 and result["band"] == "recommended"
    assert result["cached"] is False
    result2 = asyncio.run(service.evaluate("alice", request()))
    assert result2["cached"] is True
    completion.assert_called_once()
    assert completion.call_args.kwargs["max_tokens"] == 1000
    payload = json.loads(completion.call_args.kwargs["messages"][1]["content"])
    assert payload["district_odop"]["odop_product"] == "Terracotta Pottery & Dokra Metal Craft"
    assert payload["enterprise"]["enterprise_name"] == "Village dairy"
    assert "consent" not in payload["enterprise"]
    finance.assert_not_called()
    with pytest.raises(HTTPException) as error:
        asyncio.run(service.evaluate("alice", request(enterprise_name="Another idea")))
    assert error.value.status_code == 429
    assert int(error.value.headers["Retry-After"]) > 0
    now[0] += 31
    asyncio.run(service.evaluate("alice", request(enterprise_name="Another idea")))
    assert completion.call_count == 2


@pytest.mark.parametrize("score", [101,-1,85.5,"85",None,True])
def test_invalid_provider_score_is_unavailable_not_fabricated(setup, score):
    service, store, completion, _ = setup
    completion.return_value.choices[0].message.content = json.dumps(reply(score))
    with pytest.raises(HTTPException) as error:
        asyncio.run(service.evaluate("alice", request()))
    assert error.value.status_code == 503
    assert store.memory["alice"]["payload"] is None
    assert service.active == 0
    completion.assert_called_once()


def test_rate_limit_no_retry_and_backoff_for_other_owner(setup):
    service, _, completion, _ = setup
    class RateLimited(Exception):
        status_code = 429
    completion.side_effect = RateLimited()
    for owner in ("alice", "bob"):
        with pytest.raises(HTTPException) as error:
            asyncio.run(service.evaluate(owner, request()))
        assert error.value.status_code == 429
    completion.assert_called_once()


def test_unknown_or_partially_matched_district_never_calls_llm(setup):
    service, _, completion, _ = setup
    assert not hybrid.district_context("West Bengal", "Bank")["has_odop_record"]
    with pytest.raises(HTTPException) as error:
        asyncio.run(service.evaluate("alice", request(district_name="Missing district")))
    assert error.value.status_code == 422
    completion.assert_not_called()


def test_shared_workers_cache_leases_and_owner_isolation(tmp_path):
    path = tmp_path / "odop-shared.sqlite3"
    first_db = SimpleNamespace(pool=None, sqlite=sqlite3.connect(path))
    second_db = SimpleNamespace(pool=None, sqlite=sqlite3.connect(path))
    first, second = HybridStore(first_db), HybridStore(second_db)
    try:
        lease = asyncio.run(first.reserve("alice", "hash-a", 1000))
        with pytest.raises(HTTPException) as error:
            asyncio.run(second.reserve("alice", "hash-a", 1001))
        assert error.value.status_code == 429
        asyncio.run(first.complete("alice", lease["attempt_id"], reply(), 1002))
        assert asyncio.run(second.reserve("alice", "hash-a", 1003))["cached"]["score"] == 85
        assert "cached" not in asyncio.run(second.reserve("bob", "hash-a", 1003))
        assert "cached" not in asyncio.run(second.reserve("alice", "hash-a", 100000))
        # An expired older lease cannot overwrite a newer evaluation.
        asyncio.run(first.complete("alice", lease["attempt_id"], reply(10), 100001))
        with pytest.raises(HTTPException):
            asyncio.run(first.reserve("alice", "hash-a", 100001))
    finally:
        first_db.sqlite.close()
        second_db.sqlite.close()


def test_api_requires_auth_and_explicit_consent(setup, monkeypatch):
    service, _, completion, _ = setup
    import app.routers.odop_hybrid as routes
    monkeypatch.setattr(routes, "hybrid_evaluator", service)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    assert client.post("/odop-hybrid/evaluate", json=request().model_dump()).status_code == 401
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="alice")
    assert client.get("/odop-hybrid/context", params={"state_name":"West Bengal", "district_name":"Bankura"}).json()["has_odop_record"]
    completion.assert_not_called()
    payload = request().model_dump()
    payload["consent"] = False
    assert client.post("/odop-hybrid/evaluate", json=payload).status_code == 422
    completion.assert_not_called()
    response = client.post("/odop-hybrid/evaluate", json=request().model_dump())
    assert response.status_code == 200
    assert response.json()["advisory_only"] is True
