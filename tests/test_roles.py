"""Role-based DPR handoff and isolation checks using a temporary durable SQLite DB."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "backend" / "app" / "core", ROOT / "backend", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.config import settings
from app.database import db_manager
from app.core import role_store
from app.core.staff_identity import firebase_staff_email
from app.routers import roles
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    old_pool, old_sqlite = db_manager.pool, db_manager.sqlite
    old_users, old_projects = db_manager.in_memory_users, db_manager.in_memory_projects
    monkeypatch.setattr(settings, "SQLITE_DATABASE_PATH", str(tmp_path / "roles.sqlite3"))
    db_manager.pool = None
    db_manager.sqlite = None
    db_manager.in_memory_users = {}
    db_manager.in_memory_projects = {}
    db_manager._initialize_sqlite()
    try:
        yield TestClient(app)
    finally:
        db_manager.sqlite.close()
        db_manager.pool, db_manager.sqlite = old_pool, old_sqlite
        db_manager.in_memory_users, db_manager.in_memory_projects = old_users, old_projects


def headers(uid):
    return {"Authorization": f"Bearer test-token-{uid}:{uid}@example.com"}


def test_staff_aliases_map_to_firebase_compatible_identities():
    assert firebase_staff_email("Gov@udyam") == "gov@udyam.example.com"
    assert firebase_staff_email("SuperAdmin@udyam") == "superadmin@udyam.example.com"
    assert firebase_staff_email("alandi@udyam") == "alandi@udyam.example.com"


@pytest.mark.asyncio
async def test_role_store_defaults_and_village_uniqueness(client):
    for uid in ("alice", "banker1", "banker2"):
        await db_manager.upsert_user(uid, f"{uid}@example.com", uid)
    assert (await role_store.get_role("alice"))["role"] == "entrepreneur"
    await role_store.assign_role("banker1", "banker", "Maharashtra", "Pune", "Alandi")
    assert (await role_store.find_banker("maharashtra", "pune", "alandi"))["user_id"] == "banker1"
    with pytest.raises(Exception):
        await role_store.assign_role("banker2", "banker", "Maharashtra", "Pune", "Alandi")


@pytest.mark.asyncio
async def test_dpr_submission_membership_messages_and_role_rejection(client, monkeypatch):
    for uid in ("alice", "bob", "banker", "government", "admin"):
        await db_manager.upsert_user(uid, f"{uid}@example.com", uid)
    await role_store.assign_role("banker", "banker", "Maharashtra", "Pune", "Alandi")
    await role_store.assign_role("government", "government")
    await role_store.assign_role("admin", "superadmin")
    project = await db_manager.create_project({
        "user_id": "alice", "business_name": "Alandi Dairy", "business_category": "dairy",
        "investment_amount": 100000, "annual_turnover_estimate": 200000,
        "state_name": "Maharashtra", "district_name": "Pune", "village_name": "Alandi",
        "analysis_result": {"dpr": {"sections": []}},
    })
    monkeypatch.setattr(roles, "lookup_village_bank_branch", lambda *_: {
        "available": True, "verified": True, "source": "data_gov_in_live", "village": "Alandi",
    })
    response = client.post("/api/v2/roles/applications", json={"project_id": project["project_id"]}, headers=headers("alice"))
    assert response.status_code == 200, response.text
    application_id = response.json()["application_id"]
    again = client.post("/api/v2/roles/applications", json={"project_id": project["project_id"]}, headers=headers("alice"))
    assert again.json()["application_id"] == application_id
    assert len(client.get("/api/v2/roles/applications", headers=headers("banker")).json()) == 1
    assert client.get(f"/api/v2/roles/applications/{application_id}", headers=headers("bob")).status_code == 403
    assert client.get(f"/api/v2/roles/applications/{application_id}", headers=headers("government")).status_code == 403
    assert client.get("/api/v2/projects", headers=headers("banker")).status_code == 403
    assert client.get("/api/v2/roles/admin/users", headers=headers("alice")).status_code == 403
    message = client.post(f"/api/v2/roles/applications/{application_id}/messages", json={"body": "Please attach the invoice"}, headers=headers("banker"))
    assert message.status_code == 200, message.text
    assert message.json()["recipient_uid"] == "alice"
    assert len(client.get(f"/api/v2/roles/applications/{application_id}/messages", headers=headers("alice")).json()) == 1
    assert client.get(f"/api/v2/roles/applications/{application_id}/messages", headers=headers("bob")).status_code == 403
    assert client.patch(f"/api/v2/roles/applications/{application_id}/status", json={"status": "under_review"}, headers=headers("alice")).status_code == 403
    assert client.patch(f"/api/v2/roles/applications/{application_id}/status", json={"status": "under_review"}, headers=headers("banker")).status_code == 200
    assert client.get("/api/v2/roles/admin/users", headers=headers("admin")).status_code == 200
    projects_for_alice = client.get("/api/v2/roles/admin/users/alice/projects", headers=headers("admin"))
    assert projects_for_alice.status_code == 200
    assert projects_for_alice.json()[0]["project_id"] == project["project_id"]
    assert client.get("/api/v2/roles/admin/users/alice/projects", headers=headers("bob")).status_code == 403
    admin_detail = client.get(f"/api/v2/roles/admin/applications/{application_id}", headers=headers("admin"))
    assert admin_detail.status_code == 200
    assert len(admin_detail.json()["messages"]) == 1
    assert client.get("/api/v2/roles/applications", headers={}).status_code == 401


def test_bank_availability_must_be_verified(client, monkeypatch):
    from app.core import amenities_client
    monkeypatch.setattr(amenities_client, "find_district_resource_id", lambda _: None)
    result = amenities_client.lookup_village_bank_branch("Maharashtra", "Pune", "Alandi")
    assert result["available"] is False
    assert result["verified"] is False


@pytest.mark.asyncio
async def test_report_dpr_requires_authentication_and_owner(client):
    await db_manager.upsert_user("alice", "alice@example.com", "Alice")
    await db_manager.upsert_user("bob", "bob@example.com", "Bob")
    await db_manager.save_feasibility_report("REP-PRIVATE", {"report": {}, "dpr": {}}, "alice")
    path = "/api/v2/feasibility/REP-PRIVATE/dpr"
    assert client.get(path).status_code == 401
    assert client.get(path, headers=headers("bob")).status_code == 404
    # Exact-owner lookup is the backend authority, independent of frontend routes.
    assert (await db_manager.get_feasibility_report("REP-PRIVATE", "alice")) is not None
    assert (await db_manager.get_feasibility_report("REP-PRIVATE", "bob")) is None


@pytest.mark.asyncio
async def test_first_verified_village_submission_creates_one_banker(client, monkeypatch):
    from app.core import staff_identity
    await db_manager.upsert_user("alice", "alice@example.com", "Alice")
    await db_manager.upsert_user("bob", "bob@example.com", "Bob")
    projects = []
    for uid in ("alice", "bob"):
        projects.append(await db_manager.create_project({
            "user_id": uid, "business_name": f"{uid} business", "business_category": "dairy",
            "investment_amount": 100000, "annual_turnover_estimate": 200000,
            "state_name": "Maharashtra", "district_name": "Pune", "village_name": "Alandi",
            "analysis_result": {"dpr": {"sections": []}},
        }))
    monkeypatch.setattr(roles, "lookup_village_bank_branch", lambda *_: {
        "available": True, "verified": True, "source": "data_gov_in_live", "village": "Alandi",
    })
    calls = []

    async def provision(email, role, name, state, district, village):
        calls.append(email)
        assert staff_identity.firebase_staff_email(email) == "alandi@udyam.example.com"
        await db_manager.upsert_user("village-banker", "alandi@udyam.example.com", name)
        await role_store.assign_role("village-banker", role, state, district, village)
        return {"uid": "village-banker", "created": True}

    monkeypatch.setattr(roles, "_create_staff_account", provision)
    first = client.post("/api/v2/roles/applications", json={"project_id": projects[0]["project_id"]}, headers=headers("alice"))
    second = client.post("/api/v2/roles/applications", json={"project_id": projects[1]["project_id"]}, headers=headers("bob"))
    assert first.status_code == second.status_code == 200
    assert calls == ["alandi@udyam"]
    assert first.json()["banker_uid"] == second.json()["banker_uid"] == "village-banker"
    assert len(client.get("/api/v2/roles/applications", headers=headers("village-banker")).json()) == 2
    assert len(client.get("/api/v2/roles/applications", headers=headers("alice")).json()) == 1
    assert len(client.get("/api/v2/roles/applications", headers=headers("bob")).json()) == 1


@pytest.mark.asyncio
async def test_government_scheme_reach_and_actual_reimbursements_are_separate(client):
    await db_manager.upsert_user("alice", "alice@example.com", "Alice")
    await db_manager.upsert_user("government", "government@example.com", "Government")
    await role_store.assign_role("government", "government")
    await db_manager.create_project({
        "user_id": "alice", "business_name": "Dairy", "business_category": "dairy",
        "investment_amount": 100000, "annual_turnover_estimate": 200000,
        "state_name": "Maharashtra", "district_name": "Pune", "village_name": "Alandi",
        "analysis_result": {"report": {"scheme_optimization": [
            {"scheme_id": "PMEGP", "eligible": True}, {"scheme_id": "PMFME", "eligible": False},
        ]}},
    })
    summary = client.get("/api/v2/roles/government/summary", headers=headers("government"))
    assert summary.status_code == 200, summary.text
    assert summary.json()["total_reimbursed"] == 0
    assert summary.json()["scheme_interest"] == [{"scheme_name": "PMEGP", "eligible_projects": 1, "entrepreneurs": 1}]
    assert client.get("/api/v2/roles/government/summary", headers=headers("alice")).status_code == 403
    payment = client.post("/api/v2/roles/government/disbursements", headers=headers("government"),
                          json={"scheme_name": "PMEGP", "beneficiary_uid": "alice", "amount": 2000})
    assert payment.status_code == 200, payment.text
    updated = client.get("/api/v2/roles/government/summary", headers=headers("government")).json()
    assert updated["total_reimbursed"] == 2000
    assert updated["scheme_interest"] == summary.json()["scheme_interest"]
