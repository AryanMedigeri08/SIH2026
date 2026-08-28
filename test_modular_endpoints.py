"""
test_modular_endpoints.py — End-to-End Verification Harness for all Modular REST Endpoints.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

# Add project root, backend, and core directories to sys.path
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
CORE_DIR = BACKEND_DIR / "app" / "core"
for p in (str(CORE_DIR), str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

results = []

def test_ep(name, method, url, req_body=None, headers=None, expected_status=200, check_fn=None):
    try:
        if method == "GET":
            resp = client.get(url, headers=headers)
        elif method == "POST":
            resp = client.post(url, json=req_body, headers=headers)
        elif method == "PATCH":
            resp = client.patch(url, json=req_body, headers=headers)
        elif method == "DELETE":
            resp = client.delete(url, headers=headers)
        
        status_pass = resp.status_code == expected_status
        extra_pass = True
        detail = ""
        if check_fn and status_pass:
            try:
                extra_pass = check_fn(resp)
            except Exception as e:
                extra_pass = False
                detail = str(e)

        passed = status_pass and extra_pass
        results.append({
            "name": name,
            "method": method,
            "url": url,
            "status_code": resp.status_code,
            "expected_status": expected_status,
            "passed": passed,
            "detail": detail or ("OK" if passed else f"Got {resp.status_code}, expected {expected_status}"),
        })
        print(f"[{'PASS' if passed else 'FAIL'}] {method} {url} -> {resp.status_code} ({detail or 'OK'})")
    except Exception as exc:
        results.append({
            "name": name,
            "method": method,
            "url": url,
            "status_code": 0,
            "expected_status": expected_status,
            "passed": False,
            "detail": str(exc),
        })
        print(f"[FAIL] {method} {url} -> Exception: {exc}")

print("=" * 80)
print("RUNNING MODULAR BACKEND ENDPOINT VERIFICATION")
print("=" * 80)

# 1. System Health
test_ep("System Health Check", "GET", "/api/v2/health", expected_status=200,
        check_fn=lambda r: r.json().get("status") == "healthy" and r.json().get("ml_classifier_loaded") is True)

# 2. Data Sources Discovery
test_ep("List Data Sources", "GET", "/api/v2/data-sources", expected_status=200,
        check_fn=lambda r: len(r.json()) == 6 and any(s["id"] == "census_raw" for s in r.json()))

# 3. Data Sources Schemes Catalog
test_ep("Schemes Master Catalog", "GET", "/api/v2/data-sources/schemes", expected_status=200,
        check_fn=lambda r: len(r.json()) >= 5 and any(s["scheme_id"] == "PMEGP" for s in r.json()))

# 4. System Stats
test_ep("System Stats Telemetry", "GET", "/api/v2/data-sources/stats", expected_status=200,
        check_fn=lambda r: r.json().get("status") == "OPERATIONAL" and len(r.json().get("languages_supported")) == 6)

# 5. LGD Location Hierarchy: States
test_ep("LGD States List", "GET", "/api/v2/locations/states", expected_status=200,
        check_fn=lambda r: len(r.json()) >= 6 and any(s["state_name"] == "West Bengal" for s in r.json()))

# 6. LGD Location Hierarchy: Districts
test_ep("LGD Districts Query", "GET", "/api/v2/locations/districts?state_name=West Bengal", expected_status=200,
        check_fn=lambda r: len(r.json()) >= 1 and any(d["district_name"] == "Bankura" for d in r.json()))

# 7. LGD Location Hierarchy: Blocks
test_ep("LGD Development Blocks", "GET", "/api/v2/locations/blocks?district_name=Bankura", expected_status=200,
        check_fn=lambda r: len(r.json()) >= 1)

# 8. Financial Calculator: Sizing & DSCR
test_ep("Financial Sizing & DSCR", "POST", "/api/v2/financial/calculate",
        req_body={
            "project_cost": 900000.0,
            "annual_turnover": 950000.0,
            "business_category": "manufacturing",
            "sector": "dairy",
            "promoter_category": "general",
            "is_rural": True,
            "tenure_years": 7.0,
            "moratorium_months": 6,
            "interest_rate_pct": 9.5,
        },
        expected_status=200,
        check_fn=lambda r: r.json().get("top_scheme_id") == "PMEGP" and r.json().get("dscr") > 1.33)

# 9. Feasibility Pipeline: Full Assessment
test_ep("Generate Feasibility Assessment", "POST", "/api/v2/feasibility/generate",
        req_body={
            "enterprise_name": "Joypur Fresh Dairy Unit",
            "business_category": "manufacturing",
            "sector": "dairy",
            "promoter_name": "Dipankar Ghosh",
            "promoter_category": "general",
            "gender": "Male",
            "state_name": "West Bengal",
            "district_name": "Bankura",
            "block_name": "Joypur",
            "village_name": "Joypur",
            "is_rural": True,
            "project_cost": 900000.0,
            "annual_turnover_estimate": 950000.0,
            "tenure_years": 7.0,
            "moratorium_months": 6,
            "language": "en",
        },
        expected_status=200,
        check_fn=lambda r: r.json().get("ml_viability", {}).get("verdict") == "SUITABLE" and "report_id" in r.json())

# Retrieve last report_id
last_rep_id = client.post("/api/v2/feasibility/generate", json={
    "enterprise_name": "Joypur Fresh Dairy Unit",
    "business_category": "manufacturing",
    "sector": "dairy",
    "promoter_name": "Dipankar Ghosh",
    "promoter_category": "general",
    "gender": "Male",
    "state_name": "West Bengal",
    "district_name": "Bankura",
    "block_name": "Joypur",
    "village_name": "Joypur",
    "is_rural": True,
    "project_cost": 900000.0,
    "annual_turnover_estimate": 950000.0,
    "tenure_years": 7.0,
    "moratorium_months": 6,
    "language": "en",
}).json().get("report_id")

# 10. Feasibility Report Retrieval by ID
test_ep("Get Feasibility Report by ID", "GET", f"/api/v2/feasibility/{last_rep_id}", expected_status=200,
        check_fn=lambda r: r.json().get("report_id") == last_rep_id)

# 11. Feasibility Report DPR Retrieval
test_ep("Get Report DPR Document", "GET", f"/api/v2/feasibility/{last_rep_id}/dpr?format=json", expected_status=200,
        check_fn=lambda r: "section_1_header_and_profile" in r.json() and "section_2_capital_outlay_and_finance" in r.json())

# 12. Authentication & Profile Management Endpoints
auth_header_alice = {"Authorization": "Bearer test-token-alice_01:alice@example.com"}
auth_header_bob = {"Authorization": "Bearer test-token-bob_02:bob@example.com"}

test_ep("Auth: Register User Profile", "POST", "/api/v2/auth/register",
        req_body={"name": "Alice Sharma", "gender": "Female", "phone": "9876500001", "additional_business_details": "Textile unit"},
        headers=auth_header_alice, expected_status=201,
        check_fn=lambda r: r.json().get("name") == "Alice Sharma" and r.json().get("firebase_uid") == "alice_01")

test_ep("Auth: Sync Session", "POST", "/api/v2/auth/session",
        headers=auth_header_alice, expected_status=200,
        check_fn=lambda r: r.json().get("firebase_uid") == "alice_01")

test_ep("Auth: Get Current Profile", "GET", "/api/v2/auth/me",
        headers=auth_header_alice, expected_status=200,
        check_fn=lambda r: r.json().get("name") == "Alice Sharma")

test_ep("Auth: Update Profile", "PATCH", "/api/v2/auth/me",
        req_body={"phone": "9998887776"},
        headers=auth_header_alice, expected_status=200,
        check_fn=lambda r: r.json().get("phone") == "9998887776")

# 13. Projects Lifecycle & IDOR Protection
test_ep("Projects: Unauthorized List (401)", "GET", "/api/v2/projects", expected_status=401)

created_proj = client.post("/api/v2/projects", json={
    "business_name": "Alice Boutique",
    "business_category": "service",
    "sector": "apparel",
    "investment_amount": 400000.0,
    "annual_turnover_estimate": 500000.0,
    "state_name": "Karnataka",
    "district_name": "Bengaluru Urban",
}, headers=auth_header_alice).json()
alice_proj_id = created_proj.get("project_id")

test_ep("Projects: List User Projects", "GET", "/api/v2/projects",
        headers=auth_header_alice, expected_status=200,
        check_fn=lambda r: any(p["project_id"] == alice_proj_id for p in r.json()))

test_ep("Projects: Owner Access (200)", "GET", f"/api/v2/projects/{alice_proj_id}",
        headers=auth_header_alice, expected_status=200,
        check_fn=lambda r: r.json().get("business_name") == "Alice Boutique")

test_ep("Projects: IDOR Prevention Check (403)", "GET", f"/api/v2/projects/{alice_proj_id}",
        headers=auth_header_bob, expected_status=403)

# 14. Invalid Input Validation: Feasibility (Negative project cost)
test_ep("Input Validation: Negative Cost", "POST", "/api/v2/feasibility/generate",
        req_body={
            "enterprise_name": "Invalid Unit",
            "business_category": "manufacturing",
            "sector": "dairy",
            "promoter_name": "Test",
            "state_name": "West Bengal",
            "district_name": "Bankura",
            "project_cost": -50000.0,
            "annual_turnover_estimate": 950000.0,
        },
        expected_status=422)

# 15. Invalid Input Validation: Financial Calculate (Missing required field)
test_ep("Input Validation: Missing Field", "POST", "/api/v2/financial/calculate",
        req_body={"project_cost": 900000.0},
        expected_status=422)

# 16. 404 Not Found: Non-existent Report ID
test_ep("404 Error: Non-existent Report", "GET", "/api/v2/feasibility/NON_EXISTENT_ID_999", expected_status=404)

print("=" * 80)
total_tests = len(results)
passed_tests = sum(1 for r in results if r["passed"])
print(f"ENDPOINT TESTS COMPLETED: {passed_tests} / {total_tests} PASSED")
print("=" * 80)

if passed_tests < total_tests:
    sys.exit(1)
