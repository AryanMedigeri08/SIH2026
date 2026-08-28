"""
test_business_management.py — Automated Unit, Integration, Persistence, Multi-Business,
Authorization (IDOR), and Status Indicator Test Suite.
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
from backend.app.models.schemas import compute_business_status, BusinessStatus

client = TestClient(app)

# Test Tokens for Users
USER_A_TOKEN = "test-token-usr_alpha_101:alpha@enterprise.in"
USER_B_TOKEN = "test-token-usr_beta_202:beta@enterprise.in"

USER_A_HEADERS = {"Authorization": f"Bearer {USER_A_TOKEN}"}
USER_B_HEADERS = {"Authorization": f"Bearer {USER_B_TOKEN}"}

# Sample Business Payloads
BUSINESS_A1_PAYLOAD = {
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
    "additional_business_details": "10 years experience in clay moulding; local artisan cooperative tie-up.",
}

BUSINESS_A2_PAYLOAD = {
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
    "additional_business_details": "Aggregating perishables from 35 farmer produce organizations.",
}

# High-risk / critical business payload (Outlay 48 Lakh with low 2 Lakh turnover -> unsustainable DSCR < 1.0)
BUSINESS_A3_CRITICAL_PAYLOAD = {
    "business_name": "Shree Balaji High-Debt Heavy Forge",
    "business_category": "manufacturing",
    "sector": "heavy_engineering",
    "investment_amount": 4800000.0,
    "annual_turnover_estimate": 240000.0,  # 20k/mo turnover on 48L debt
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
    "additional_business_details": "Heavy machinery procurement without customer advance contracts.",
}

BUSINESS_B1_PAYLOAD = {
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
    "additional_business_details": "Direct export contract for cardamom and black pepper.",
}


def test_business_status_unit_logic():
    """Test unit logic of compute_business_status for all 4 states."""
    print("\n--- TEST: Unit Logic of Business Status Computation ---")
    
    # 1. Draft
    draft_status = compute_business_status(None)
    assert draft_status.code == "draft"
    assert draft_status.color == "slate"
    assert draft_status.severity == "neutral"
    print("  ✓ Draft status correctly computed")

    # 2. Healthy
    healthy_analysis = {
        "report": {
            "financial_analysis": {"dscr": {"dscr": 2.45, "verdict": "VIABLE"}},
            "ml_viability": {"verdict": "SUITABLE", "confidence_pct": 98.2},
            "risk_assessment": {"average_risk_score": 3.1},
        }
    }
    healthy_status = compute_business_status(healthy_analysis)
    assert healthy_status.code == "healthy"
    assert healthy_status.color == "emerald"
    assert healthy_status.severity == "positive"
    assert healthy_status.dscr == 2.45
    print("  ✓ Healthy status correctly computed (DSCR 2.45 >= 1.33, ML SUITABLE)")

    # 3. Reconsideration (1.0 <= DSCR < 1.33)
    reconsider_analysis = {
        "report": {
            "financial_analysis": {"dscr": {"dscr": 1.15, "verdict": "MARGINAL"}},
            "ml_viability": {"verdict": "CAUTION", "confidence_pct": 82.0},
            "risk_assessment": {"average_risk_score": 5.8},
        }
    }
    reconsider_status = compute_business_status(reconsider_analysis)
    assert reconsider_status.code == "reconsideration"
    assert reconsider_status.color == "amber"
    assert reconsider_status.severity == "warning"
    assert "RBI 1.33 benchmark" in reconsider_status.reason or "CAUTION" in reconsider_status.reason
    print("  ✓ Reconsideration status correctly computed (DSCR 1.15, ML CAUTION)")

    # 4. Critical (DSCR < 1.0)
    critical_analysis = {
        "report": {
            "financial_analysis": {"dscr": {"dscr": 0.42, "verdict": "UNVIABLE"}},
            "ml_viability": {"verdict": "RECONSIDER", "confidence_pct": 95.0},
            "risk_assessment": {"average_risk_score": 8.4},
        }
    }
    critical_status = compute_business_status(critical_analysis)
    assert critical_status.code == "critical"
    assert critical_status.color == "rose"
    assert critical_status.severity == "critical"
    assert "below 1.0" in critical_status.reason or "RECONSIDER" in critical_status.reason
    print("  ✓ Critical solvency status correctly computed (DSCR 0.42 < 1.0, ML RECONSIDER)")


def test_business_lifecycle_and_persistence():
    """Test full creation, analysis, persistence, and session restore for User A."""
    print("\n--- TEST: Business Creation, Analysis & Persistence ---")
    
    # 1. Create Business A1 via create-and-analyze
    resp = client.post("/api/v2/projects/create-and-analyze", json=BUSINESS_A1_PAYLOAD, headers=USER_A_HEADERS)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    biz_a1 = resp.json()
    project_id_1 = biz_a1["project_id"]
    assert biz_a1["business_name"] == BUSINESS_A1_PAYLOAD["business_name"]
    assert biz_a1["user_id"] == "usr_alpha_101"
    assert biz_a1["status"] == "analyzed"
    assert biz_a1["analysis_result"] is not None
    assert "report" in biz_a1["analysis_result"]
    assert "dpr" in biz_a1["analysis_result"]
    assert biz_a1["business_status"]["code"] in ["healthy", "reconsideration", "critical"]
    print(f"  ✓ Business A1 created and analyzed: {project_id_1} (Status: {biz_a1['business_status']['label']})")

    # 2. Retrieve Business A1 (simulating session restore)
    resp = client.get(f"/api/v2/projects/{project_id_1}", headers=USER_A_HEADERS)
    assert resp.status_code == 200
    restored = resp.json()
    assert restored["project_id"] == project_id_1
    assert restored["business_name"] == BUSINESS_A1_PAYLOAD["business_name"]
    assert restored["analysis_result"]["report"]["input_parameters"]["enterprise_name"] == BUSINESS_A1_PAYLOAD["business_name"]
    print("  ✓ Business A1 persistent data restored successfully with full analysis payload")

    # 3. Retrieve DPR in all 3 formats (JSON, Markdown, HTML)
    resp_json = client.get(f"/api/v2/projects/{project_id_1}/dpr?format=json", headers=USER_A_HEADERS)
    assert resp_json.status_code == 200
    assert "section_1_header_and_profile" in resp_json.json()
    assert "section_3_financial_projections" in resp_json.json()

    resp_md = client.get(f"/api/v2/projects/{project_id_1}/dpr?format=markdown", headers=USER_A_HEADERS)
    assert resp_md.status_code == 200
    assert "DETAILED PROJECT REPORT" in resp_md.text

    resp_html = client.get(f"/api/v2/projects/{project_id_1}/dpr?format=html", headers=USER_A_HEADERS)
    assert resp_html.status_code == 200
    assert "<html" in resp_html.text.lower()
    print("  ✓ Bank DPR export verified across JSON, Markdown, and HTML formats")

    # 4. Retrieve Status endpoint directly
    resp_status = client.get(f"/api/v2/projects/{project_id_1}/status", headers=USER_A_HEADERS)
    assert resp_status.status_code == 200
    status_obj = resp_status.json()
    assert "code" in status_obj
    assert "label" in status_obj
    assert "color" in status_obj
    print(f"  ✓ Dedicated status endpoint returned: {status_obj['label']} ({status_obj['color']})")

    return project_id_1


def test_multi_business_support_and_isolation(project_id_1: str):
    """Test that one user can own multiple distinct businesses and switch between them."""
    print("\n--- TEST: Multi-Business Support & Data Isolation ---")
    
    # 1. User A creates second business (Business A2 - Agro Logistics)
    resp2 = client.post("/api/v2/projects/create-and-analyze", json=BUSINESS_A2_PAYLOAD, headers=USER_A_HEADERS)
    assert resp2.status_code == 201
    biz_a2 = resp2.json()
    project_id_2 = biz_a2["project_id"]
    assert project_id_2 != project_id_1
    assert biz_a2["business_name"] == BUSINESS_A2_PAYLOAD["business_name"]
    print(f"  ✓ User A created Business A2: {project_id_2} ('{biz_a2['business_name']}')")

    # 2. User A creates third business (Business A3 - High Risk Critical)
    resp3 = client.post("/api/v2/projects/create-and-analyze", json=BUSINESS_A3_CRITICAL_PAYLOAD, headers=USER_A_HEADERS)
    assert resp3.status_code == 201
    biz_a3 = resp3.json()
    project_id_3 = biz_a3["project_id"]
    assert biz_a3["business_status"]["code"] == "critical"
    print(f"  ✓ User A created Business A3: {project_id_3} (Status: {biz_a3['business_status']['label']})")

    # 3. List all businesses for User A
    resp_list = client.get("/api/v2/projects", headers=USER_A_HEADERS)
    assert resp_list.status_code == 200
    user_projects = resp_list.json()
    assert len(user_projects) >= 3
    ids = [p["project_id"] for p in user_projects]
    assert project_id_1 in ids
    assert project_id_2 in ids
    assert project_id_3 in ids
    print(f"  ✓ User A successfully listed all 3 registered enterprises: {len(user_projects)} found")

    # 4. Verify Data Isolation: Switching between Business A1 and A2
    resp_get_1 = client.get(f"/api/v2/projects/{project_id_1}", headers=USER_A_HEADERS).json()
    resp_get_2 = client.get(f"/api/v2/projects/{project_id_2}", headers=USER_A_HEADERS).json()
    
    assert resp_get_1["business_name"] == BUSINESS_A1_PAYLOAD["business_name"]
    assert resp_get_2["business_name"] == BUSINESS_A2_PAYLOAD["business_name"]
    assert resp_get_1["investment_amount"] == 500000.0
    assert resp_get_2["investment_amount"] == 1500000.0
    assert resp_get_1["district_name"] == "Bankura"
    assert resp_get_2["district_name"] == "Dharwad"
    print("  ✓ Data isolation between Business A1 and Business A2 strictly verified")

    # 5. Update Business A2 without affecting Business A1
    update_payload = {"annual_turnover_estimate": 2500000.0, "additional_business_details": "Updated FPO network"}
    patch_resp = client.patch(f"/api/v2/projects/{project_id_2}", json=update_payload, headers=USER_A_HEADERS)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["annual_turnover_estimate"] == 2500000.0

    # Verify Business A1 remains unchanged
    resp_get_1_again = client.get(f"/api/v2/projects/{project_id_1}", headers=USER_A_HEADERS).json()
    assert resp_get_1_again["annual_turnover_estimate"] == 720000.0
    print("  ✓ Mutating Business A2 did not modify Business A1")

    return project_id_2, project_id_3


def test_authorization_and_idor_protection(project_id_a1: str):
    """Test strict ownership validation: User A cannot access or mutate User B's business."""
    print("\n--- TEST: Ownership Validation & IDOR Security Protection ---")
    
    # 1. User B creates Business B1
    resp_b = client.post("/api/v2/projects/create-and-analyze", json=BUSINESS_B1_PAYLOAD, headers=USER_B_HEADERS)
    assert resp_b.status_code == 201
    biz_b1 = resp_b.json()
    project_id_b1 = biz_b1["project_id"]
    assert biz_b1["user_id"] == "usr_beta_202"
    print(f"  ✓ User B created Business B1: {project_id_b1}")

    # 2. User A attempts to GET User B's business -> Must be 403 Forbidden
    resp_idor_get = client.get(f"/api/v2/projects/{project_id_b1}", headers=USER_A_HEADERS)
    assert resp_idor_get.status_code == 403, f"Expected 403 Forbidden, got {resp_idor_get.status_code}"
    print("  ✓ IDOR Protection: User A GET User B's business -> 403 Forbidden (Blocked)")

    # 3. User A attempts to GET User B's status -> Must be 403 Forbidden
    resp_idor_status = client.get(f"/api/v2/projects/{project_id_b1}/status", headers=USER_A_HEADERS)
    assert resp_idor_status.status_code == 403
    print("  ✓ IDOR Protection: User A GET User B's status -> 403 Forbidden (Blocked)")

    # 4. User A attempts to GET User B's DPR -> Must be 403 Forbidden
    resp_idor_dpr = client.get(f"/api/v2/projects/{project_id_b1}/dpr", headers=USER_A_HEADERS)
    assert resp_idor_dpr.status_code == 403
    print("  ✓ IDOR Protection: User A GET User B's DPR -> 403 Forbidden (Blocked)")

    # 5. User A attempts to PATCH User B's business -> Must be 403 Forbidden
    resp_idor_patch = client.patch(f"/api/v2/projects/{project_id_b1}", json={"investment_amount": 10.0}, headers=USER_A_HEADERS)
    assert resp_idor_patch.status_code == 403
    print("  ✓ IDOR Protection: User A PATCH User B's business -> 403 Forbidden (Blocked)")

    # 6. User A attempts to DELETE User B's business -> Must be 403 Forbidden
    resp_idor_del = client.delete(f"/api/v2/projects/{project_id_b1}", headers=USER_A_HEADERS)
    assert resp_idor_del.status_code == 403
    print("  ✓ IDOR Protection: User A DELETE User B's business -> 403 Forbidden (Blocked)")

    # 7. Unauthenticated request without token -> Must be 401 Unauthorized
    resp_no_auth = client.get(f"/api/v2/projects/{project_id_b1}")
    assert resp_no_auth.status_code == 401
    print("  ✓ Unauthenticated access -> 401 Unauthorized (Blocked)")

    # 8. User B deletes their own business -> Must be 200 OK
    resp_b_del = client.delete(f"/api/v2/projects/{project_id_b1}", headers=USER_B_HEADERS)
    assert resp_b_del.status_code == 200
    print("  ✓ Authorized deletion: User B deleted their own business -> 200 OK")


def test_invalid_business_requests():
    """Test error handling for non-existent and malformed business requests."""
    print("\n--- TEST: Error Handling for Non-Existent Records ---")
    
    resp_404 = client.get("/api/v2/projects/non_existent_id_99999", headers=USER_A_HEADERS)
    assert resp_404.status_code == 404
    print("  ✓ Non-existent business ID -> 404 Not Found")

    resp_404_status = client.get("/api/v2/projects/non_existent_id_99999/status", headers=USER_A_HEADERS)
    assert resp_404_status.status_code == 404
    print("  ✓ Non-existent status query -> 404 Not Found")


if __name__ == "__main__":
    print("=" * 80)
    print("RUNNING AUTOMATED PERSISTENCE, MULTI-BUSINESS & AUTHORIZATION TEST SUITE")
    print("=" * 80)
    
    test_business_status_unit_logic()
    p1 = test_business_lifecycle_and_persistence()
    p2, p3 = test_multi_business_support_and_isolation(p1)
    test_authorization_and_idor_protection(p1)
    test_invalid_business_requests()
    
    print("\n" + "=" * 80)
    print("ALL PERSISTENT MULTI-BUSINESS & AUTHORIZATION TESTS PASSED SUCCESSFULLY! (100%)")
    print("=" * 80)
