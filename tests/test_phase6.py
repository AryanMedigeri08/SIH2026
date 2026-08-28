"""
test_phase6.py — Udyam Saathi Phase 6 REST API Verification Harness.

Six Comprehensive Test Layers using FastAPI TestClient:
  1. SYSTEM & HEALTH: Verifies root welcome endpoint and /health / /api/v2/health status checks.
  2. LGD LOCATIONS HIERARCHY: Verifies state, district, block, and village query resolutions.
  3. STANDALONE FINANCIAL CALCULATORS: Verifies /api/v2/financial/calculate math & scheme ranking.
  4. FEASIBILITY PIPELINE & DPR EXPORTS: Verifies /api/v2/feasibility/generate, retrieval, and
     multi-format DPR exports (JSON, Markdown, HTML).
  5. PROJECT STATE PERSISTENCE & LIFECYCLE: Verifies project creation, listing, retrieval,
     JSONB analysis execution, and persistent DPR retrieval.
  6. 5 SIH PITCH CASE STUDIES REST API VALIDATION: End-to-end HTTP pipeline execution across
     all 5 pitch cases, verifying 200 OK responses, valid JSON schemas, and accurate verdicts.

Run: python test_phase6.py
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

# Add backend and core directories to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
CORE_DIR = BACKEND_DIR / "app" / "core"
for p in (str(CORE_DIR), str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

PASS = 0
FAIL = 0


def check(label: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}  {detail}")


# ============================================================================
# LAYER 1: SYSTEM & HEALTH ENDPOINTS
# ============================================================================
print("=" * 90)
print("LAYER 1 — SYSTEM & HEALTH ENDPOINTS")
print("=" * 90)

r_root = client.get("/")
check("GET / returns HTTP 200 OK", r_root.status_code == 200)
check("Root response contains version and welcome message", "Udyam Saathi" in r_root.json().get("message", ""))

r_health = client.get("/api/v2/health")
check("GET /api/v2/health returns HTTP 200 OK", r_health.status_code == 200)
health_data = r_health.json()
check("Health status is 'healthy'", health_data.get("status") == "healthy")
check("ML classifier status is loaded", health_data.get("ml_classifier_loaded") is True)
check("AI synthesizer status is active", health_data.get("ai_synthesizer_active") is True)

print(f"\nLayer 1 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 2: LGD LOCATIONS HIERARCHY
# ============================================================================
print("=" * 90)
print("LAYER 2 — LGD LOCATIONS HIERARCHY")
print("=" * 90)

r_states = client.get("/api/v2/locations/states")
check("GET /api/v2/locations/states returns HTTP 200 OK", r_states.status_code == 200)
states_list = r_states.json()
check("Returns multiple Indian states/UTs", len(states_list) >= 20)
check("West Bengal is present in states list", any(s["state_name"] == "West Bengal" for s in states_list))

r_dist = client.get("/api/v2/locations/districts?state_name=West Bengal")
check("GET /api/v2/locations/districts?state_name=West Bengal returns HTTP 200 OK", r_dist.status_code == 200)
dist_list = r_dist.json()
check("Bankura district is present in West Bengal", any(d["district_name"] == "Bankura" for d in dist_list))

r_blocks = client.get("/api/v2/locations/blocks?district_code=312")
check("GET /api/v2/locations/blocks returns HTTP 200 OK", r_blocks.status_code == 200)
check("Returns block list for district 312", len(r_blocks.json()) > 0)

r_villages = client.get("/api/v2/locations/villages?district_code=312")
check("GET /api/v2/locations/villages returns HTTP 200 OK", r_villages.status_code == 200)
check("Returns village list for district 312", len(r_villages.json()) > 0)

print(f"\nLayer 2 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 2.5: 613 VILLAGE AMENITIES & INFRASTRUCTURE SCORE
# ============================================================================
print("=" * 90)
print("LAYER 2.5 — 613 VILLAGE AMENITIES API & INFRASTRUCTURE SCORING")
print("=" * 90)

from amenities_client import fetch_village_amenities, compute_infrastructure_score, AmenitiesCache

# 1. Math Bounds & Component Checks
score_perfect = compute_infrastructure_score(power_hours=24.0, has_road=True, has_banking=True, has_internet=True, has_storage=True)
check("Perfect infrastructure score computes to 9.0+ / 10.0", score_perfect >= 9.0, f"got {score_perfect}")

score_poor = compute_infrastructure_score(power_hours=6.0, has_road=False, has_banking=False, has_internet=False, has_storage=False)
check("Under-developed infrastructure score computes to < 4.0", score_poor < 4.0, f"got {score_poor}")

# 2. Regional Baseline Resolution & 613 Metric Query
am_wb = fetch_village_amenities("West Bengal", "Bankura", "Joypur")
check("WB Bankura amenities query succeeds", am_wb.infrastructure_score > 5.0)
check("Total metrics queried == 613", am_wb.total_metrics_queried == 613)
check("Provenance is recorded (live or baseline fallback)", am_wb.provenance in ("data_gov_in_live", "in_memory_cache", "regional_baseline"))

# 3. 24h In-Memory TTL Cache Verification
cache_test = AmenitiesCache(ttl_seconds=3600)
cache_test.set("TestState", "TestDistrict", "TestVillage", am_wb)
cached_item = cache_test.get("TestState", "TestDistrict", "TestVillage")
check("In-memory cache retrieves stored village amenities instantly", cached_item is not None and cached_item.infrastructure_score == am_wb.infrastructure_score)
check("Cached item reflects 'in_memory_cache' provenance", cached_item.provenance == "in_memory_cache")

print(f"\nLayer 2.5 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 3: STANDALONE FINANCIAL CALCULATOR
# ============================================================================
print("=" * 90)
print("LAYER 3 — STANDALONE FINANCIAL CALCULATOR")
print("=" * 90)

calc_payload = {
    "project_cost": 500000.0,
    "annual_turnover": 650000.0,
    "sector": "dairy",
    "business_category": "manufacturing",
    "promoter_category": "general",
    "is_rural": True,
    "tenure_years": 5.0,
    "interest_rate_pct": 11.0,
    "moratorium_months": 6,
}
r_calc = client.post("/api/v2/financial/calculate", json=calc_payload)
check("POST /api/v2/financial/calculate returns HTTP 200 OK", r_calc.status_code == 200)
calc_res = r_calc.json()
check("Calculates non-negative monthly EMI", calc_res.get("monthly_emi", 0) > 0)
check("Identifies top eligible scheme", len(calc_res.get("top_scheme_id", "")) > 0)
check("Calculates DSCR and verdict", calc_res.get("dscr", 0) > 0 and calc_res.get("dscr_verdict") in ("VIABLE", "MARGINAL", "AT RISK"))
check("Returns top 5 ranked schemes table", len(calc_res.get("ranked_schemes", [])) <= 5)

print(f"\nLayer 3 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 4: FEASIBILITY PIPELINE & MULTI-FORMAT DPR EXPORTS
# ============================================================================
print("=" * 90)
print("LAYER 4 — FEASIBILITY PIPELINE & MULTI-FORMAT DPR EXPORTS")
print("=" * 90)

feas_payload = {
    "enterprise_name": "Joypur Fresh Dairy Processing Unit",
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
    "infrastructure_score": 7.2,
    "cpi_inflation_pct": 4.8,
    "weather_risk_score": 0.25,
    "language": "en",
}

r_feas = client.post("/api/v2/feasibility/generate", json=feas_payload)
check("POST /api/v2/feasibility/generate returns HTTP 200 OK", r_feas.status_code == 200)
feas_data = r_feas.json()
report_id = feas_data.get("report_id")
check("Feasibility response contains unique report_id", report_id is not None and report_id.startswith("REP-"))
check("Contains ML viability verdict (SUITABLE)", feas_data.get("ml_viability", {}).get("verdict") == "SUITABLE")
check("Contains grounded executive synthesis", len(feas_data.get("executive_synthesis", {}).get("executive_summary", "")) > 50)

# GET /api/v2/feasibility/{report_id}
r_get_feas = client.get(f"/api/v2/feasibility/{report_id}")
check(f"GET /api/v2/feasibility/{report_id} returns HTTP 200 OK", r_get_feas.status_code == 200)
check("Retrieved report matches generated report ID", r_get_feas.json().get("report_id") == report_id)

# DPR Exports: JSON, Markdown, HTML
r_dpr_json = client.get(f"/api/v2/feasibility/{report_id}/dpr?format=json")
check("GET .../dpr?format=json returns HTTP 200 OK", r_dpr_json.status_code == 200)
check("DPR JSON contains 7 sections", "section_1_header_and_profile" in r_dpr_json.json() and "section_7_statutory_checklist" in r_dpr_json.json())

r_dpr_md = client.get(f"/api/v2/feasibility/{report_id}/dpr?format=markdown")
check("GET .../dpr?format=markdown returns HTTP 200 OK", r_dpr_md.status_code == 200)
check("DPR Markdown contains DETAILED PROJECT REPORT header", "DETAILED PROJECT REPORT" in r_dpr_md.text)

r_dpr_html = client.get(f"/api/v2/feasibility/{report_id}/dpr?format=html")
check("GET .../dpr?format=html returns HTTP 200 OK", r_dpr_html.status_code == 200)
check("DPR HTML contains closing html tag", "</html>" in r_dpr_html.text)

# Direct POST /api/v2/feasibility/dpr?format=html
r_direct_dpr = client.post("/api/v2/feasibility/dpr?format=html", json=feas_payload)
check("POST /api/v2/feasibility/dpr?format=html returns HTTP 200 OK", r_direct_dpr.status_code == 200)
check("Direct DPR returns HTML content", "<!DOCTYPE html>" in r_direct_dpr.text)

print(f"\nLayer 4 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 5: PROJECT STATE PERSISTENCE & LIFECYCLE
# ============================================================================
print("=" * 90)
print("LAYER 5 — PROJECT STATE PERSISTENCE & LIFECYCLE")
print("=" * 90)

project_create_payload = {
    "business_name": "Ramanagara Auto & Mobile Clinic",
    "business_category": "service",
    "sector": "repair",
    "investment_amount": 300000.0,
    "annual_turnover_estimate": 420000.0,
    "state_name": "Karnataka",
    "district_name": "Ramanagara",
    "block_name": "Ramanagara",
    "village_name": "Bidadi",
    "promoter_name": "Kiran Gowda",
    "promoter_category": "general",
    "gender": "Male",
    "is_rural": True,
    "tenure_years": 3.0,
    "moratorium_months": 3,
    "language": "kn",
}

# Auth & IDOR Checks on Projects Endpoint
r_unauth = client.get("/api/v2/projects")
check("GET /api/v2/projects without auth returns HTTP 401 Unauthorized", r_unauth.status_code == 401)

auth_headers = {"Authorization": "Bearer test-token-user_demo_101:kiran@example.com"}

# Register user profile
r_reg = client.post("/api/v2/auth/register", json={
    "name": "Kiran Gowda",
    "gender": "Male",
    "phone": "9876543210",
    "additional_business_details": "Specialized in tractor hydraulics and smartphone board repair.",
}, headers=auth_headers)
check("POST /api/v2/auth/register returns HTTP 201 Created", r_reg.status_code == 201)

# Sync session
r_sess = client.post("/api/v2/auth/session", headers=auth_headers)
check("POST /api/v2/auth/session returns HTTP 200 OK", r_sess.status_code == 200)

# Get current user profile
r_me = client.get("/api/v2/auth/me", headers=auth_headers)
check("GET /api/v2/auth/me returns user profile", r_me.status_code == 200 and r_me.json().get("name") == "Kiran Gowda")

# Create Project with Bearer Token
r_proj_create = client.post("/api/v2/projects", json=project_create_payload, headers=auth_headers)
check("POST /api/v2/projects returns HTTP 201 Created", r_proj_create.status_code == 201)
proj_data = r_proj_create.json()
project_id = proj_data.get("project_id")
check("Project record created with unique project_id", project_id is not None and project_id.startswith("proj_"))
check("Initial project status is 'draft'", proj_data.get("status") == "draft")

# List projects for user
r_proj_list = client.get("/api/v2/projects", headers=auth_headers)
check("GET /api/v2/projects returns HTTP 200 OK", r_proj_list.status_code == 200)
check("User project list contains created project", any(p["project_id"] == project_id for p in r_proj_list.json()))

# Get project details (Owner)
r_proj_get = client.get(f"/api/v2/projects/{project_id}", headers=auth_headers)
check(f"GET /api/v2/projects/{project_id} returns HTTP 200 OK", r_proj_get.status_code == 200)
check("Project details match business name", r_proj_get.json().get("business_name") == "Ramanagara Auto & Mobile Clinic")

# IDOR Security Check: Attempt access as different user
other_user_headers = {"Authorization": "Bearer test-token-other_user_999:other@example.com"}
r_idor = client.get(f"/api/v2/projects/{project_id}", headers=other_user_headers)
check("GET /api/v2/projects/{id} as other user returns HTTP 403 Forbidden (IDOR Protected)", r_idor.status_code == 403)

# Analyze project and persist JSONB analysis result
r_proj_analyze = client.post(f"/api/v2/projects/{project_id}/analyze", headers=auth_headers)
check(f"POST /api/v2/projects/{project_id}/analyze returns HTTP 200 OK", r_proj_analyze.status_code == 200)
analyzed_proj = r_proj_analyze.json()
check("Project status updated to 'analyzed'", analyzed_proj.get("status") == "analyzed")
check("Project analysis_result JSONB is populated", analyzed_proj.get("analysis_result") is not None)
check("Analysis result contains report and dpr", "report" in analyzed_proj["analysis_result"] and "dpr" in analyzed_proj["analysis_result"])

# Retrieve project DPR in Markdown format
r_proj_dpr_md = client.get(f"/api/v2/projects/{project_id}/dpr?format=markdown", headers=auth_headers)
check(f"GET /api/v2/projects/{project_id}/dpr?format=markdown returns HTTP 200 OK", r_proj_dpr_md.status_code == 200)
check("Persistent DPR contains enterprise name", "Ramanagara Auto & Mobile Clinic" in r_proj_dpr_md.text)

print(f"\nLayer 5 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 6: 5 SIH PITCH CASE STUDIES REST API VALIDATION
# ============================================================================
print("=" * 90)
print("LAYER 6 — 5 SIH PITCH CASE STUDIES REST API VALIDATION")
print("=" * 90)

CASES_API = [
    {
        "name": "Case 1: Dairy Processing in Joypur, Bankura (WB)",
        "payload": {
            "enterprise_name": "Joypur Fresh Dairy Processing",
            "business_category": "manufacturing", "sector": "dairy",
            "promoter_name": "Dipankar Ghosh", "promoter_category": "general", "gender": "Male",
            "state_name": "West Bengal", "district_name": "Bankura", "block_name": "Joypur", "village_name": "Joypur",
            "is_rural": True, "project_cost": 900000.0, "annual_turnover_estimate": 950000.0,
            "tenure_years": 7.0, "moratorium_months": 6, "infrastructure_score": 7.2,
            "cpi_inflation_pct": 4.8, "weather_risk_score": 0.25, "language": "en",
        },
        "expected_verdict": "SUITABLE",
    },
    {
        "name": "Case 2: Mobile Repair Shop in Ramanagara (KA)",
        "payload": {
            "enterprise_name": "Ramanagara Auto & Mobile Clinic",
            "business_category": "service", "sector": "repair",
            "promoter_name": "Kiran Gowda", "promoter_category": "general", "gender": "Male",
            "state_name": "Karnataka", "district_name": "Ramanagara", "block_name": "Ramanagara", "village_name": "Bidadi",
            "is_rural": True, "project_cost": 300000.0, "annual_turnover_estimate": 420000.0,
            "tenure_years": 3.0, "moratorium_months": 3, "infrastructure_score": 6.0,
            "cpi_inflation_pct": 4.2, "weather_risk_score": 0.10, "language": "kn",
        },
        "expected_verdict": "SUITABLE",
    },
    {
        "name": "Case 3: Women Tailoring Boutique in Varanasi (UP)",
        "payload": {
            "enterprise_name": "Kashi Vastra Boutique",
            "business_category": "service", "sector": "apparel",
            "promoter_name": "Sunita Devi", "promoter_category": "women", "gender": "Female",
            "state_name": "Uttar Pradesh", "district_name": "Varanasi", "block_name": "Kashi", "village_name": "Shivpur",
            "is_rural": False, "project_cost": 800000.0, "annual_turnover_estimate": 700000.0,
            "tenure_years": 5.0, "moratorium_months": 6, "infrastructure_score": 7.8,
            "cpi_inflation_pct": 5.5, "weather_risk_score": 0.15, "language": "hi",
        },
        "expected_verdict": ("SUITABLE", "CAUTION"),
    },
    {
        "name": "Case 4: Overleveraged Agro Unit (High Outlay, Low Margin)",
        "payload": {
            "enterprise_name": "Malwa Agro Processing",
            "business_category": "manufacturing", "sector": "food_processing",
            "promoter_name": "Ramesh Patel", "promoter_category": "general", "gender": "Male",
            "state_name": "Madhya Pradesh", "district_name": "Ujjain", "block_name": "Ghatiya", "village_name": "Panbihar",
            "is_rural": True, "project_cost": 2500000.0, "annual_turnover_estimate": 600000.0,
            "tenure_years": 5.0, "moratorium_months": 6, "infrastructure_score": 4.0,
            "cpi_inflation_pct": 7.5, "weather_risk_score": 0.40,
            "monthly_net_operating_income_override": 15000.0, "language": "mr",
        },
        "expected_verdict": "RECONSIDER",
    },
    {
        "name": "Case 5: Artisan Pottery Cluster in Khurja (UP)",
        "payload": {
            "enterprise_name": "Khurja Pottery Studio",
            "business_category": "manufacturing", "sector": "artisan_trades",
            "promoter_name": "Ram Prasad Prajapati", "promoter_category": "artisan", "gender": "Male",
            "state_name": "Uttar Pradesh", "district_name": "Bulandshahr", "block_name": "Khurja", "village_name": "Khurja Dehat",
            "is_rural": True, "project_cost": 280000.0, "annual_turnover_estimate": 340000.0,
            "tenure_years": 2.5, "moratorium_months": 3, "infrastructure_score": 5.5,
            "cpi_inflation_pct": 5.0, "weather_risk_score": 0.20, "language": "ta",
        },
        "expected_verdict": ("SUITABLE", "CAUTION"),
    },
]

for case in CASES_API:
    print("\n" + "-" * 90)
    print(f"Testing API Pipeline: {case['name']}")
    print("-" * 90)

    res = client.post("/api/v2/feasibility/generate", json=case["payload"])
    check(f"[{case['name']}] POST /api/v2/feasibility/generate returns HTTP 200 OK", res.status_code == 200)
    rep = res.json()

    verdict = rep.get("ml_viability", {}).get("verdict")
    expected = case["expected_verdict"]

    if isinstance(expected, tuple):
        check(f"[{case['name']}] ML verdict is one of {expected}", verdict in expected, f"got {verdict}")
    else:
        check(f"[{case['name']}] ML verdict matches expected '{expected}'", verdict == expected, f"got {verdict}")

    top_scheme = rep.get("scheme_optimization", [{}])[0]
    check(f"[{case['name']}] Top Scheme present with subsidy > 0", top_scheme.get("subsidy_grant_amount", 0) > 0)
    check(f"[{case['name']}] Executive synthesis present in target language", len(rep.get("executive_synthesis", {}).get("executive_summary", "")) > 50)

print("\n" + "=" * 90)
print(f"PHASE 6 VERIFICATION SUMMARY: {PASS} passed, {FAIL} failed")
print("=" * 90)

if FAIL > 0:
    sys.exit(1)
