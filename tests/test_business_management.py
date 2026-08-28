"""
test_business_management.py — Comprehensive Automated Test Harness:
1. Enterprise Persistence Across Logout & Login
2. Returning User Flow (No Re-registration) vs. New User Flow
3. Logout Session Invalidation & State Cleanup
4. Protected API Access Rejection After Logout
5. Multiple Enterprise Restoration & Data Isolation
6. Strict Cross-User IDOR Access Control (403 Forbidden)
7. Direct Resource Access Authorization Enforcement
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

# Setup Python paths
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
CORE_DIR = BACKEND_DIR / "app" / "core"
for p in (str(CORE_DIR), str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import db_manager
from backend.app.models.schemas import compute_business_status, BusinessStatus

client = TestClient(app)

# User Credentials & Tokens
USER_A_UID = "usr_alpha_enterprise_101"
USER_A_EMAIL = "alpha@udyam.gov.in"
USER_A_TOKEN = f"test-token-{USER_A_UID}:{USER_A_EMAIL}"
USER_A_HEADERS = {"Authorization": f"Bearer {USER_A_TOKEN}"}

USER_B_UID = "usr_beta_enterprise_202"
USER_B_EMAIL = "beta@udyam.gov.in"
USER_B_TOKEN = f"test-token-{USER_B_UID}:{USER_B_EMAIL}"
USER_B_HEADERS = {"Authorization": f"Bearer {USER_B_TOKEN}"}

USER_NEW_UID = "usr_newbie_fresh_303"
USER_NEW_EMAIL = "newbie@udyam.gov.in"
USER_NEW_TOKEN = f"test-token-{USER_NEW_UID}:{USER_NEW_EMAIL}"
USER_NEW_HEADERS = {"Authorization": f"Bearer {USER_NEW_TOKEN}"}

# Payloads
ENTERPRISE_A1_PAYLOAD = {
    "business_name": "Ramesh Eco-Pottery Cluster",
    "business_category": "manufacturing",
    "sector": "handicrafts",
    "investment_amount": 500000.0,
    "annual_turnover_estimate": 720000.0,
    "state_name": "West Bengal",
    "district_name": "Bankura",
    "block_name": "Joypur",
    "village_name": "Joypur",
    "promoter_name": "Ramesh Chandra Sharma",
    "promoter_category": "obc",
    "gender": "Male",
    "is_rural": True,
    "tenure_years": 5.0,
    "moratorium_months": 6,
    "language": "en",
    "additional_business_details": "10 years experience in clay moulding; artisan cluster.",
}

ENTERPRISE_A2_PAYLOAD = {
    "business_name": "Kisan Solar Micro-Cold Storage",
    "business_category": "services",
    "sector": "agro_logistics",
    "investment_amount": 1500000.0,
    "annual_turnover_estimate": 2200000.0,
    "state_name": "Karnataka",
    "district_name": "Dharwad",
    "block_name": "Hubli",
    "village_name": "Unkal",
    "promoter_name": "Smt. Shanta Patil",
    "promoter_category": "women",
    "gender": "Female",
    "is_rural": True,
    "tenure_years": 7.0,
    "moratorium_months": 12,
    "language": "kn",
    "additional_business_details": "Perishables aggregation from 35 FPOs.",
}

ENTERPRISE_A3_CRITICAL_PAYLOAD = {
    "business_name": "Shree Balaji High-Debt Heavy Forge",
    "business_category": "manufacturing",
    "sector": "heavy_engineering",
    "investment_amount": 4800000.0,
    "annual_turnover_estimate": 240000.0,
    "state_name": "Uttar Pradesh",
    "district_name": "Varanasi",
    "block_name": "Arajiline",
    "village_name": "Rameshwar",
    "promoter_name": "Vikramaditya Singh",
    "promoter_category": "general",
    "gender": "Male",
    "is_rural": False,
    "tenure_years": 3.0,
    "moratorium_months": 0,
    "language": "hi",
    "additional_business_details": "High leverage machinery loan.",
}

ENTERPRISE_B1_PAYLOAD = {
    "business_name": "Beta Organic Spice Processing",
    "business_category": "manufacturing",
    "sector": "food_processing",
    "investment_amount": 800000.0,
    "annual_turnover_estimate": 1400000.0,
    "state_name": "Kerala",
    "district_name": "Wayanad",
    "block_name": "Kalpetta",
    "village_name": "Meppadi",
    "promoter_name": "George Varghese",
    "promoter_category": "general",
    "gender": "Male",
    "is_rural": True,
    "tenure_years": 5.0,
    "moratorium_months": 6,
    "language": "en",
    "additional_business_details": "Cardamom export facility.",
}


def test_1_enterprise_persistence_across_logout_and_login():
    """REQUIRED TEST 1: Enterprise Persistence After Logout and Login."""
    global USER_A_HEADERS
    print("\n--- TEST 1: Enterprise Persistence Across Logout and Login ---")
    
    # 1. User A creates Enterprise A1 & A2
    resp1 = client.post("/api/v2/projects/create-and-analyze", json=ENTERPRISE_A1_PAYLOAD, headers=USER_A_HEADERS)
    assert resp1.status_code == 201, f"Failed creating A1: {resp1.text}"
    p1 = resp1.json()
    id_1 = p1["project_id"]

    resp2 = client.post("/api/v2/projects/create-and-analyze", json=ENTERPRISE_A2_PAYLOAD, headers=USER_A_HEADERS)
    assert resp2.status_code == 201, f"Failed creating A2: {resp2.text}"
    p2 = resp2.json()
    id_2 = p2["project_id"]

    # Verify both exist
    list_before = client.get("/api/v2/projects", headers=USER_A_HEADERS).json()
    assert len(list_before) >= 2
    print(f"  [PASS] User A created 2 enterprises: '{p1['business_name']}' ({id_1}) & '{p2['business_name']}' ({id_2})")

    # 2. User A logs out
    logout_resp = client.post("/api/v2/auth/logout", headers=USER_A_HEADERS)
    assert logout_resp.status_code == 200
    print("  [PASS] User A successfully logged out (session terminated on backend)")

    # 3. The logged-out token and unauthenticated calls both fail.
    unauth_resp = client.get("/api/v2/projects")
    assert unauth_resp.status_code == 401
    revoked_resp = client.get("/api/v2/projects", headers=USER_A_HEADERS)
    assert revoked_resp.status_code == 401
    print("  [PASS] Unauthenticated access after logout correctly returns 401 Unauthorized")

    # 4. User A logs in again with the same credentials
    # A real Firebase sign-in obtains a fresh ID token.  The test-token suffix
    # models that newly issued session rather than reusing the revoked bearer.
    USER_A_HEADERS = {"Authorization": f"Bearer test-token-{USER_A_UID}:{USER_A_EMAIL}:relogin-1"}
    session_sync = client.post("/api/v2/auth/session", headers=USER_A_HEADERS)
    assert session_sync.status_code == 200

    # 5. Retrieve User A's enterprises after login
    list_after = client.get("/api/v2/projects", headers=USER_A_HEADERS).json()
    assert len(list_after) >= 2
    ids_after = [p["project_id"] for p in list_after]
    assert id_1 in ids_after
    assert id_2 in ids_after

    # Verify enterprise data and generated analysis are fully restored
    restored_1 = client.get(f"/api/v2/projects/{id_1}", headers=USER_A_HEADERS).json()
    assert restored_1["business_name"] == ENTERPRISE_A1_PAYLOAD["business_name"]
    assert restored_1["analysis_result"]["report"]["report_id"] is not None
    assert restored_1["business_status"]["code"] in ["healthy", "reconsideration", "critical"]
    print("  [PASS] Both enterprises and complete generated analytical data restored after re-login")

    return id_1, id_2


def test_2_returning_user_vs_new_user_flow(id_1: str):
    """REQUIRED TEST 2: Returning User (Dashboard) vs. New User (Registration/Wizard)."""
    print("\n--- TEST 2: Returning User Flow vs. New User Flow ---")
    
    # 1. Returning user with existing enterprises
    resp_returning = client.get("/api/v2/projects", headers=USER_A_HEADERS)
    assert resp_returning.status_code == 200
    projects_returning = resp_returning.json()
    assert len(projects_returning) > 0
    # Expected UI action: Load Dashboard with existing enterprises; DO NOT show wizard
    print(f"  [PASS] Returning User identified with {len(projects_returning)} enterprise(s) -> Dashboard Selected (No Wizard)")

    # 2. Brand new user with 0 enterprises
    resp_new = client.get("/api/v2/projects", headers=USER_NEW_HEADERS)
    assert resp_new.status_code == 200
    projects_new = resp_new.json()
    assert len(projects_new) == 0
    # Expected UI action: Guide new user into Wizard creation flow
    print("  [PASS] New User identified with 0 enterprises -> Wizard / Registration Flow Available")


def test_3_logout_clears_authenticated_state():
    """REQUIRED TEST 3: Logout Invalidation and State Clearing."""
    global USER_A_HEADERS
    print("\n--- TEST 3: Logout Invalidation and Session Cleanup ---")
    
    # 1. User A logs out
    logout_resp = client.post("/api/v2/auth/logout", headers=USER_A_HEADERS)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "success"
    print("  [PASS] Logout endpoint executed with success status")

    # 2. Subsequent requests with empty authorization fail
    resp_empty = client.get("/api/v2/projects", headers={"Authorization": ""})
    assert resp_empty.status_code == 401
    revoked = client.get("/api/v2/projects", headers=USER_A_HEADERS)
    assert revoked.status_code == 401
    print("  [PASS] Empty authorization header returns 401 Unauthorized")

    # Restore a new session for the remaining authorized tests.
    USER_A_HEADERS = {"Authorization": f"Bearer test-token-{USER_A_UID}:{USER_A_EMAIL}:relogin-2"}
    assert client.post("/api/v2/auth/session", headers=USER_A_HEADERS).status_code == 200


def test_4_protected_api_access_after_logout(id_1: str):
    """REQUIRED TEST 4: Protected API Access Rejection After Logout."""
    print("\n--- TEST 4: Protected Endpoints Reject Unauthenticated Access ---")
    
    # Unauthenticated requests to protected endpoints
    endpoints_to_test = [
        ("GET", f"/api/v2/projects/{id_1}"),
        ("GET", f"/api/v2/projects/{id_1}/status"),
        ("GET", f"/api/v2/projects/{id_1}/dpr"),
        ("PATCH", f"/api/v2/projects/{id_1}"),
        ("DELETE", f"/api/v2/projects/{id_1}"),
        ("GET", "/api/v2/projects"),
        ("GET", "/api/v2/auth/me"),
    ]

    for method, url in endpoints_to_test:
        if method == "GET":
            resp = client.get(url)
        elif method == "PATCH":
            resp = client.patch(url, json={})
        elif method == "DELETE":
            resp = client.delete(url)
        
        assert resp.status_code == 401, f"Expected 401 for {method} {url}, got {resp.status_code}"
        print(f"  [PASS] {method} {url} without credentials -> 401 Unauthorized (Protected)")


def test_5_multiple_enterprise_restoration_and_switching(id_1: str, id_2: str):
    """REQUIRED TEST 5: Multiple Enterprise Restoration & Switching."""
    print("\n--- TEST 5: Multiple Enterprise Restoration & Switching ---")
    
    # 1. User A creates a 3rd enterprise (Critical Solvency)
    resp3 = client.post("/api/v2/projects/create-and-analyze", json=ENTERPRISE_A3_CRITICAL_PAYLOAD, headers=USER_A_HEADERS)
    assert resp3.status_code == 201
    p3 = resp3.json()
    id_3 = p3["project_id"]

    # 2. User A retrieves all 3 enterprises
    list_resp = client.get("/api/v2/projects", headers=USER_A_HEADERS)
    assert list_resp.status_code == 200
    all_3 = list_resp.json()
    assert len(all_3) >= 3
    print(f"  [PASS] User A successfully retrieved all {len(all_3)} enterprises")

    # 3. Verify switching: Fetch Enterprise 1 vs Enterprise 2 vs Enterprise 3
    e1 = client.get(f"/api/v2/projects/{id_1}", headers=USER_A_HEADERS).json()
    e2 = client.get(f"/api/v2/projects/{id_2}", headers=USER_A_HEADERS).json()
    e3 = client.get(f"/api/v2/projects/{id_3}", headers=USER_A_HEADERS).json()

    assert e1["sector"] == "handicrafts"
    assert e2["sector"] == "agro_logistics"
    assert e3["sector"] == "heavy_engineering"
    assert e3["business_status"]["code"] == "critical"
    print("  [PASS] Switching between enterprises returns isolated, exact enterprise-specific data")

    # 4. Mutate Enterprise 2 and verify Enterprise 1 is untouched
    client.patch(f"/api/v2/projects/{id_2}", json={"annual_turnover_estimate": 3000000.0}, headers=USER_A_HEADERS)
    e1_check = client.get(f"/api/v2/projects/{id_1}", headers=USER_A_HEADERS).json()
    assert e1_check["annual_turnover_estimate"] == 720000.0
    print("  [PASS] Updating Enterprise 2 has zero side-effects on Enterprise 1")

    return id_3


def test_6_cross_user_data_isolation(id_1: str):
    """REQUIRED TEST 6: Cross-User IDOR Data Isolation."""
    print("\n--- TEST 6: Strict Cross-User Data Isolation & IDOR Protection ---")
    
    # 1. User B creates Enterprise B1
    resp_b = client.post("/api/v2/projects/create-and-analyze", json=ENTERPRISE_B1_PAYLOAD, headers=USER_B_HEADERS)
    assert resp_b.status_code == 201
    p_b1 = resp_b.json()
    id_b1 = p_b1["project_id"]
    report_b1 = p_b1["analysis_result"]["report"]["report_id"]
    print(f"  [PASS] User B created Enterprise B1 ({id_b1})")

    # 2. User A cannot view User B's enterprise list
    list_a = client.get("/api/v2/projects", headers=USER_A_HEADERS).json()
    ids_a = [p["project_id"] for p in list_a]
    assert id_b1 not in ids_a
    print("  [PASS] User B's enterprise B1 is not visible in User A's enterprise list")

    # 3. User A cannot GET User B's enterprise directly
    idor_get = client.get(f"/api/v2/projects/{id_b1}", headers=USER_A_HEADERS)
    assert idor_get.status_code == 403
    print("  [PASS] User A GET User B's enterprise -> 403 Forbidden")

    # 4. User A cannot GET User B's status
    idor_status = client.get(f"/api/v2/projects/{id_b1}/status", headers=USER_A_HEADERS)
    assert idor_status.status_code == 403
    print("  [PASS] User A GET User B's status -> 403 Forbidden")

    # 5. User A cannot GET User B's DPR
    idor_dpr = client.get(f"/api/v2/projects/{id_b1}/dpr", headers=USER_A_HEADERS)
    assert idor_dpr.status_code == 403
    print("  [PASS] User A GET User B's DPR -> 403 Forbidden")

    # 6. User A cannot PATCH User B's enterprise
    idor_patch = client.patch(f"/api/v2/projects/{id_b1}", json={"investment_amount": 1.0}, headers=USER_A_HEADERS)
    assert idor_patch.status_code == 403
    print("  [PASS] User A PATCH User B's enterprise -> 403 Forbidden")

    # 7. User A cannot DELETE User B's enterprise
    idor_del = client.delete(f"/api/v2/projects/{id_b1}", headers=USER_A_HEADERS)
    assert idor_del.status_code == 403
    print("  [PASS] User A DELETE User B's enterprise -> 403 Forbidden")

    # Generated report URLs are also protected and owner-scoped; a known ID
    # cannot be used to bypass the project ownership boundary.
    assert client.get(f"/api/v2/feasibility/{report_b1}").status_code == 401
    report_idor = client.get(f"/api/v2/feasibility/{report_b1}", headers=USER_A_HEADERS)
    assert report_idor.status_code == 404
    print("  [PASS] User A cannot retrieve User B's generated report by manipulated report ID")

    # 8. User B CAN delete their own enterprise
    del_b = client.delete(f"/api/v2/projects/{id_b1}", headers=USER_B_HEADERS)
    assert del_b.status_code == 200
    print("  [PASS] User B authorized deletion of enterprise B1 -> 200 OK")


def test_7_direct_resource_access_enforcement():
    """REQUIRED TEST 7: Backend Direct Resource Access Control."""
    print("\n--- TEST 7: Direct Resource Access Enforcement ---")
    
    resp_404 = client.get("/api/v2/projects/non_existent_project_xyz", headers=USER_A_HEADERS)
    assert resp_404.status_code == 404
    print("  [PASS] Non-existent project query returns 404 Not Found")

    resp_404_status = client.get("/api/v2/projects/non_existent_project_xyz/status", headers=USER_A_HEADERS)
    assert resp_404_status.status_code == 404
    print("  [PASS] Non-existent status query returns 404 Not Found")


def test_8_durable_backend_fallback_persistence():
    """Proves offline persistence is durable, not merely an in-process dictionary."""
    print("\n--- TEST 8: Durable Backend Persistence Without PostgreSQL ---")
    uid = "usr_durable_store_404"
    headers = {"Authorization": f"Bearer test-token-{uid}:durable@udyam.gov.in:session-1"}
    payload = {**ENTERPRISE_A1_PAYLOAD, "business_name": "Durable SQLite Enterprise"}

    # Entering TestClient executes FastAPI lifespan, which selects SQLite when
    # DATABASE_URL is absent. Remove the process cache after creation and prove
    # that the API reloads the enterprise from the backend store.
    with TestClient(app) as persistent_client:
        created = persistent_client.post("/api/v2/projects", json=payload, headers=headers)
        assert created.status_code == 201
        project_id = created.json()["project_id"]
        db_manager.in_memory_projects.clear()
        restored = persistent_client.get(f"/api/v2/projects/{project_id}", headers=headers)
        assert restored.status_code == 200
        assert restored.json()["business_name"] == "Durable SQLite Enterprise"
    print("  [PASS] Enterprise reloaded from durable SQLite backend after memory cache removal")


def test_9_user_language_preference_persists():
    """The selected interface/LLM language is persisted in the user profile."""
    print("\n--- TEST 9: User Language Preference Persistence ---")
    uid = "usr_language_preference_505"
    email = "language@udyam.gov.in"
    headers = {"Authorization": f"Bearer test-token-{uid}:{email}:session-1"}

    initial = client.post("/api/v2/auth/session", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["preferred_language"] == "en"

    saved = client.patch("/api/v2/auth/me", json={"preferred_language": "hi"}, headers=headers)
    assert saved.status_code == 200
    assert saved.json()["preferred_language"] == "hi"

    relogin_headers = {"Authorization": f"Bearer test-token-{uid}:{email}:session-2"}
    restored = client.post("/api/v2/auth/session", headers=relogin_headers)
    assert restored.status_code == 200
    assert restored.json()["preferred_language"] == "hi"

    invalid = client.patch("/api/v2/auth/me", json={"preferred_language": "es"}, headers=relogin_headers)
    assert invalid.status_code == 422
    print("  [PASS] Preferred language survives a fresh login and invalid language codes are rejected")


if __name__ == "__main__":
    print("=" * 80)
    print("RUNNING ENTERPRISE PERSISTENCE, AUTHENTICATION & ACCESS CONTROL TEST SUITE")
    print("=" * 80)
    
    id_1, id_2 = test_1_enterprise_persistence_across_logout_and_login()
    test_2_returning_user_vs_new_user_flow(id_1)
    test_3_logout_clears_authenticated_state()
    test_4_protected_api_access_after_logout(id_1)
    id_3 = test_5_multiple_enterprise_restoration_and_switching(id_1, id_2)
    test_6_cross_user_data_isolation(id_1)
    test_7_direct_resource_access_enforcement()
    test_8_durable_backend_fallback_persistence()
    test_9_user_language_preference_persists()
    
    print("\n" + "=" * 80)
    print("ALL 9 REQUIRED TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80)
