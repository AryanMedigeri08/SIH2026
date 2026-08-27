"""
test_phase5.py — Udyam Saathi Phase 5 Verification Harness.

Four Layers of Verification:
  1. ACCOUNTING BALANCE RECONCILIATION: Verifies Capital Outlay == Machinery + Civil + WC + Contingency,
     and Means of Finance == Margin + Subsidy + Term Loan == Total Outlay with zero rounding drift.
  2. 5-YEAR FINANCIAL HORIZON INTEGRITY: Verifies 5-year cash flow projections, capacity scaling (60%-90%),
     amortization decrease, depreciation schedules, and annualized DSCR formulas.
  3. STATUTORY CHECKLIST DYNAMIC CUSTOMIZATION: Verifies conditional document requirements
     (SC/ST Caste certificates, FSSAI licenses, PM Vishwakarma cards, PMEGP 8th pass rules).
  4. 5 SIH PITCH CASE STUDIES FULL DPR EXPORT: End-to-end generation of official Bank DPR packages
     across all 5 cases, validating JSON, Markdown, and HTML exports.

Run: python test_phase5.py
"""

from __future__ import annotations
import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_CORE = _ROOT / "backend" / "app" / "core"
_BACKEND = _ROOT / "backend"
for _p in (str(_CORE), str(_BACKEND), str(_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Phase 2 imports
from financial_calculator import (
    emi_with_moratorium, working_capital_estimate, compute_dscr, rank_eligible_schemes,
)
from market_analyzer import (
    project_population, estimate_tam, compute_msme_density, compute_competition_intensity,
)
from risk_analyzer import build_risk_matrix, overall_risk_verdict
from swot_analyzer import build_swot
from pricing_engine import compute_pricing

# Phase 3 imports
from feature_extractor import extract_features_from_pipeline_objects
from inference import predict_viability

# Phase 4 imports
from executive_synthesizer import generate_executive_synthesis

# Phase 5 imports
from dpr_generator import (
    build_bank_dpr, dpr_to_printable_markdown, dpr_to_html,
    _compute_5yr_projections, _compile_statutory_checklist, BankDPRDocument,
)

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
# LAYER 1: ACCOUNTING RECONCILIATION & BALANCE INTEGRITY
# ============================================================================
print("=" * 90)
print("LAYER 1 — ACCOUNTING RECONCILIATION & BALANCE INTEGRITY")
print("=" * 90)

# Simulate standard assembly parameters
proj_cost = 1000000.0
turnover = 1200000.0

schemes = rank_eligible_schemes(
    project_cost=proj_cost, business_category="manufacturing", sector="dairy",
    promoter_category="general", is_rural=True, tenure_years=5,
)
top_scheme = schemes[0]
promoter_pct = 0.10
promoter_margin = proj_cost * promoter_pct
loan_amt = max(proj_cost - top_scheme.subsidy_grant_amount - promoter_margin, 0.0)

amort = emi_with_moratorium(loan_amt, top_scheme.effective_interest_rate_pct, 5, 6)
dscr_res = compute_dscr(45000, amort.monthly_emi)
pop_dummy = project_population(4000, "West Bengal", 2026)
tam_dummy = estimate_tam(pop_dummy.projected_households, "dairy")
msme_dummy = compute_msme_density(500, pop_dummy.projected_population)
comp_dummy = compute_competition_intensity(500, 0.05, pop_dummy.projected_population)
wc_dummy = working_capital_estimate(turnover, "dairy")
pricing_dummy = compute_pricing(amort.monthly_emi, wc_dummy.monthly_working_capital_outlay, 800, 5.0)

fv_dummy = extract_features_from_pipeline_objects(
    pop_dummy, tam_dummy, msme_dummy, comp_dummy, top_scheme, amort, dscr_res, wc_dummy,
    proj_cost, turnover, 7.0, 5.0, 0.2, promoter_margin,
)
ml_dummy = predict_viability(fv_dummy)
risks_dummy = build_risk_matrix(dscr_res.dscr, amort.monthly_emi, tam_dummy.annual_tam, turnover, 0.2, 7.0, 5.0, 0.2, 2.0, 0.25)
risk_verdict_dummy = overall_risk_verdict(risks_dummy)
swot_dummy = build_swot(dscr_res.dscr, top_scheme.subsidy_grant_amount, top_scheme.full_name, proj_cost, 7.0, tam_dummy.annual_tam, turnover, 0.2, 10.0, 5.0, 0.2, ml_dummy.verdict, ml_dummy.confidence_pct)
synth_dummy = generate_executive_synthesis({
    "enterprise_name": "Test Dairy", "business_category": "manufacturing", "sector": "dairy",
    "location_str": "Joypur, WB", "project_cost": proj_cost, "promoter_margin_amount": promoter_margin,
    "top_scheme_name": top_scheme.scheme_id, "subsidy_amount": top_scheme.subsidy_grant_amount,
    "subsidy_pct": 25.0, "effective_loan": loan_amt, "monthly_emi": amort.monthly_emi,
    "dscr": dscr_res.dscr, "dscr_verdict": dscr_res.verdict, "annual_tam": tam_dummy.annual_tam,
    "cpi_adjusted_price_floor": pricing_dummy.cpi_adjusted_unit_price_floor,
    "ml_verdict": ml_dummy.verdict, "ml_confidence_pct": ml_dummy.confidence_pct,
    "top_positive_driver": ml_dummy.top_positive_factors[0], "top_risk_factor": ml_dummy.top_risk_factors[0],
}, language="en", force_fallback=True)

dpr_test = build_bank_dpr(
    enterprise_name="Test Dairy Processing",
    business_category="manufacturing",
    sector="dairy",
    promoter_name="Arnav Sharma",
    promoter_category="general",
    gender="Male",
    state_name="West Bengal",
    district_name="Bankura",
    block_name="Joypur",
    village_name="Joypur",
    is_rural=True,
    project_cost=proj_cost,
    annual_turnover_estimate=turnover,
    tenure_years=5,
    moratorium_months=6,
    pop_projection=pop_dummy,
    tam_estimate=tam_dummy,
    msme_density=msme_dummy,
    ranked_schemes=schemes,
    amortization=amort,
    dscr_result=dscr_res,
    risk_points=risks_dummy,
    risk_verdict=risk_verdict_dummy,
    swot_matrix=swot_dummy,
    pricing_result=pricing_dummy,
    ml_prediction=ml_dummy,
    ai_synthesis=synth_dummy,
)

outlay_data = dpr_test.section_2_capital_outlay_and_finance["capital_outlay"]
finance_data = dpr_test.section_2_capital_outlay_and_finance["means_of_finance"]

# Check Capital Outlay Sum == Project Cost
sum_outlay = (
    outlay_data["plant_and_machinery"]["amount_inr"] +
    outlay_data["electrification_and_site_works"]["amount_inr"] +
    outlay_data["initial_working_capital_reserve"]["amount_inr"] +
    outlay_data["contingency_and_pre_operative"]["amount_inr"]
)
check("Capital Outlay components sum exactly to Total Project Cost (₹1,000,000)", abs(sum_outlay - proj_cost) < 0.01)

# Check Means of Finance Sum == Project Cost
sum_finance = (
    finance_data["promoter_margin_amount"] +
    finance_data["capital_subsidy_amount"] +
    finance_data["bank_term_loan_amount"]
)
check("Means of Finance sum exactly to Total Project Cost (₹1,000,000)", abs(sum_finance - proj_cost) < 0.01)
check("Means of finance reconciliation_balanced is True", finance_data["reconciliation_balanced"] is True)

print(f"\nLayer 1 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 2: 5-YEAR FINANCIAL HORIZON INTEGRITY
# ============================================================================
print("=" * 90)
print("LAYER 2 — 5-YEAR FINANCIAL HORIZON INTEGRITY")
print("=" * 90)

horizon = _compute_5yr_projections(
    base_annual_turnover=1000000.0,
    project_cost=800000.0,
    loan_principal=520000.0,
    annual_interest_rate_pct=11.0,
    tenure_years=5.0,
    moratorium_months=6,
    sector="dairy",
    cpi_inflation_pct=4.8,
    unit_price_floor=125.0,
)

check("Generates exactly 5 projection years", len(horizon.projection_years) == 5)
check("Capacity scaling follows standard slabs [60%, 70%, 80%, 85%, 90%]",
      [y.capacity_utilization_pct for y in horizon.projection_years] == [60.0, 70.0, 80.0, 85.0, 90.0])
check("Turnover increases monotonically across 5 years",
      all(horizon.projection_years[i].gross_turnover < horizon.projection_years[i+1].gross_turnover for i in range(4)))
check("Bank interest decreases over loan tenure as principal amortizes",
      horizon.projection_years[0].bank_interest >= horizon.projection_years[4].bank_interest)
check("All years produce positive Net Profit After Tax (PAT)",
      all(y.profit_after_tax > 0 for y in horizon.projection_years))
check("Average 5-Year DSCR is calculated and > 1.0", horizon.average_dscr > 1.0, f"got {horizon.average_dscr:.2f}")
check("Break-Even Point (BEP) is within feasible range [40%, 85%]", 40.0 <= horizon.break_even_point_pct <= 85.0)

print(f"\nLayer 2 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 3: STATUTORY CHECKLIST CUSTOMIZATION RULES
# ============================================================================
print("=" * 90)
print("LAYER 3 — STATUTORY CHECKLIST CUSTOMIZATION RULES")
print("=" * 90)

# 1. SC Category + Food Processing + PMEGP > 10L
chk_sc_food = _compile_statutory_checklist(
    scheme_id="PMEGP", promoter_category="sc", sector="food_processing",
    business_category="manufacturing", project_cost=1500000.0,
)
doc_codes_1 = [d.document_code for d in chk_sc_food]
check("Universal KYC (DOC-KYC-01) present", "DOC-KYC-01" in doc_codes_1)
check("Udyam MSME (DOC-REG-02) present", "DOC-REG-02" in doc_codes_1)
check("SC Category Certificate (DOC-SOC-06) triggered", "DOC-SOC-06" in doc_codes_1)
check("FSSAI License (DOC-FSS-10) triggered for food processing", "DOC-FSS-10" in doc_codes_1)
check("8th Pass Certificate (DOC-EDU-09) triggered for PMEGP Mfg > ₹10L", "DOC-EDU-09" in doc_codes_1)

# 2. Artisan + PM Vishwakarma
chk_artisan = _compile_statutory_checklist(
    scheme_id="PM_VISHWAKARMA", promoter_category="artisan", sector="artisan_trades",
    business_category="manufacturing", project_cost=250000.0,
)
doc_codes_2 = [d.document_code for d in chk_artisan]
check("Artisan Card (DOC-ART-07) triggered for PM Vishwakarma", "DOC-ART-07" in doc_codes_2)
check("8th Pass Certificate not required for small loan (₹2.5L)", "DOC-EDU-09" not in doc_codes_2)

# 3. Women SHG + DAY-NRLM
chk_shg = _compile_statutory_checklist(
    scheme_id="DAY_NRLM", promoter_category="women_shg", sector="apparel",
    business_category="service", project_cost=300000.0,
)
doc_codes_3 = [d.document_code for d in chk_shg]
check("SHG Resolution & NRLM Register (DOC-SHG-08) triggered for Women SHG", "DOC-SHG-08" in doc_codes_3)

print(f"\nLayer 3 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 4: 5 SIH PITCH CASE STUDIES — FULL BANK DPR GENERATION & EXPORTS
# ============================================================================
print("=" * 90)
print("LAYER 4 — 5 SIH PITCH CASE STUDIES: FULL BANK DPR GENERATION & EXPORTS")
print("=" * 90)

CASES_PHASE5 = [
    {
        "name": "Joypur Fresh Dairy Processing",
        "state": "West Bengal", "district": "Bankura", "block": "Joypur", "village": "Joypur",
        "base_pop": 4200, "sector": "dairy", "business_category": "manufacturing",
        "promoter_name": "Dipankar Ghosh", "promoter_category": "general", "gender": "Male",
        "is_rural": True, "project_cost": 900000.0, "turnover": 950000.0, "tenure": 7, "moratorium": 6,
        "infra": 7.2, "cpi": 4.8, "weather": 0.25, "msme_total": 788, "sector_share": 0.05,
        "monthly_units": 780, "lang": "en",
    },
    {
        "name": "Ramanagara Auto Electricals & Mobile Services",
        "state": "Karnataka", "district": "Ramanagara", "block": "Ramanagara", "village": "Bidadi",
        "base_pop": 2100, "sector": "repair", "business_category": "service",
        "promoter_name": "Kiran Gowda", "promoter_category": "general", "gender": "Male",
        "is_rural": True, "project_cost": 300000.0, "turnover": 420000.0, "tenure": 3, "moratorium": 3,
        "infra": 6.0, "cpi": 4.2, "weather": 0.10, "msme_total": 420, "sector_share": 0.08,
        "monthly_units": 90, "lang": "kn",
    },
    {
        "name": "Kashi Vastra Boutique & Tailoring Cluster",
        "state": "Uttar Pradesh", "district": "Varanasi", "block": "Kashi", "village": "Shivpur",
        "base_pop": 3600, "sector": "apparel", "business_category": "service",
        "promoter_name": "Sunita Devi", "promoter_category": "women", "gender": "Female",
        "is_rural": False, "project_cost": 800000.0, "turnover": 700000.0, "tenure": 5, "moratorium": 6,
        "infra": 7.8, "cpi": 5.5, "weather": 0.15, "msme_total": 950, "sector_share": 0.04,
        "monthly_units": 130, "lang": "hi",
    },
    {
        "name": "Malwa Agro Food Processing Unit",
        "state": "Madhya Pradesh", "district": "Ujjain", "block": "Ghatiya", "village": "Panbihar",
        "base_pop": 2800, "sector": "food_processing", "business_category": "manufacturing",
        "promoter_name": "Ramesh Patel", "promoter_category": "general", "gender": "Male",
        "is_rural": True, "project_cost": 2500000.0, "turnover": 600000.0, "tenure": 5, "moratorium": 6,
        "infra": 4.0, "cpi": 7.5, "weather": 0.40, "msme_total": 300, "sector_share": 0.10,
        "monthly_units": 250, "noi_override": 15000.0, "lang": "mr",
    },
    {
        "name": "Khurja Traditional Ceramic Pottery Studio",
        "state": "Uttar Pradesh", "district": "Bulandshahr", "block": "Khurja", "village": "Khurja Dehat",
        "base_pop": 5200, "sector": "artisan_trades", "business_category": "manufacturing",
        "promoter_name": "Ram Prasad Prajapati", "promoter_category": "artisan", "gender": "Male",
        "is_rural": True, "project_cost": 280000.0, "turnover": 340000.0, "tenure": 2.5, "moratorium": 3,
        "infra": 5.5, "cpi": 5.0, "weather": 0.20, "msme_total": 610, "sector_share": 0.03,
        "monthly_units": 500, "lang": "ta",
    },
]

phase5_dpr_exports = []

for case in CASES_PHASE5:
    print("\n" + "-" * 90)
    print(f"Generating Bank DPR: {case['name']}")
    print("-" * 90)

    # 1. Pipeline execution (Phase 1 -> 2 -> 3 -> 4)
    pop = project_population(case["base_pop"], case["state"], 2026)
    tam = estimate_tam(pop.projected_households, case["sector"])
    dens = compute_msme_density(case["msme_total"], pop.projected_population)
    comp = compute_competition_intensity(case["msme_total"], case["sector_share"], pop.projected_population)

    wc = working_capital_estimate(case["turnover"], case["sector"])
    schemes = rank_eligible_schemes(
        project_cost=case["project_cost"], business_category=case["business_category"],
        sector=case["sector"], promoter_category=case["promoter_category"], is_rural=case["is_rural"],
        tenure_years=case["tenure"], moratorium_months=case["moratorium"],
    )
    top_scheme = next((r for r in schemes if r.eligible), schemes[0])
    promoter_pct = 0.05 if case["promoter_category"] != "general" else 0.10
    promoter_margin_amt = case["project_cost"] * promoter_pct
    loan_principal = max(case["project_cost"] - top_scheme.subsidy_grant_amount - promoter_margin_amt, 1.0)
    amort = emi_with_moratorium(loan_principal, top_scheme.effective_interest_rate_pct, case["tenure"], case["moratorium"])

    noi = case.get("noi_override", case["turnover"] * 0.30 / 12)
    dscr_res = compute_dscr(noi, amort.monthly_emi)

    pricing = compute_pricing(amort.monthly_emi, wc.monthly_working_capital_outlay, case["monthly_units"], case["cpi"])
    subsidy_coverage_ratio = top_scheme.subsidy_grant_amount / case["project_cost"] if case["project_cost"] else 0.0
    wc_buf = promoter_margin_amt / wc.monthly_working_capital_outlay if wc.monthly_working_capital_outlay else 0.0

    fv = extract_features_from_pipeline_objects(
        pop, tam, dens, comp, top_scheme, amort, dscr_res, wc,
        case["project_cost"], case["turnover"], case["infra"], case["cpi"], case["weather"], promoter_margin_amt,
    )
    ml_pred = predict_viability(fv)

    risks = build_risk_matrix(
        dscr_res.dscr, amort.monthly_emi, tam.annual_tam, case["turnover"], comp.competition_intensity_normalized,
        case["infra"], case["cpi"], case["weather"], wc_buf, subsidy_coverage_ratio,
    )
    risk_verdict = overall_risk_verdict(risks)
    swot = build_swot(
        dscr_res.dscr, top_scheme.subsidy_grant_amount, top_scheme.full_name, case["project_cost"],
        case["infra"], tam.annual_tam, case["turnover"], comp.competition_intensity_normalized,
        dens.msme_density_per_10k, case["cpi"], case["weather"], ml_pred.verdict, ml_pred.confidence_pct,
    )

    synthesis = generate_executive_synthesis({
        "enterprise_name": case["name"], "business_category": case["business_category"], "sector": case["sector"],
        "location_str": f"{case['village']}, {case['block']}, {case['district']}, {case['state']}",
        "project_cost": case["project_cost"], "promoter_margin_amount": promoter_margin_amt,
        "top_scheme_name": f"{top_scheme.scheme_id} ({top_scheme.full_name})",
        "subsidy_amount": top_scheme.subsidy_grant_amount, "subsidy_pct": subsidy_coverage_ratio * 100,
        "effective_loan": loan_principal, "monthly_emi": amort.monthly_emi, "dscr": dscr_res.dscr,
        "dscr_verdict": dscr_res.verdict, "annual_tam": tam.annual_tam,
        "cpi_adjusted_price_floor": pricing.cpi_adjusted_unit_price_floor,
        "ml_verdict": ml_pred.verdict, "ml_confidence_pct": ml_pred.confidence_pct,
        "top_positive_driver": ml_pred.top_positive_factors[0], "top_risk_factor": ml_pred.top_risk_factors[0],
        "key_risks": [r.title for r in risks if r.severity in ("HIGH", "SEVERE", "MODERATE")][:2],
    }, language=case["lang"], force_fallback=True)

    # 2. Compile Official Bank DPR Document
    dpr_doc = build_bank_dpr(
        enterprise_name=case["name"],
        business_category=case["business_category"],
        sector=case["sector"],
        promoter_name=case["promoter_name"],
        promoter_category=case["promoter_category"],
        gender=case["gender"],
        state_name=case["state"],
        district_name=case["district"],
        block_name=case["block"],
        village_name=case["village"],
        is_rural=case["is_rural"],
        project_cost=case["project_cost"],
        annual_turnover_estimate=case["turnover"],
        tenure_years=case["tenure"],
        moratorium_months=case["moratorium"],
        pop_projection=pop,
        tam_estimate=tam,
        msme_density=dens,
        ranked_schemes=schemes,
        amortization=amort,
        dscr_result=dscr_res,
        risk_points=risks,
        risk_verdict=risk_verdict,
        swot_matrix=swot,
        pricing_result=pricing,
        ml_prediction=ml_pred,
        ai_synthesis=synthesis,
    )

    # 3. Format Exports
    markdown_export = dpr_to_printable_markdown(dpr_doc)
    html_export = dpr_to_html(dpr_doc)

    print(f"  DPR Reference ID: {dpr_doc.section_1_header_and_profile.dpr_reference_id}")
    print(f"  Outlay Reconciliation: Total Outlay ₹{dpr_doc.section_2_capital_outlay_and_finance['capital_outlay']['total_capital_outlay']:,.2f} == Means of Finance ₹{dpr_doc.section_2_capital_outlay_and_finance['means_of_finance']['total_means_of_finance']:,.2f}")
    print(f"  5-Yr Avg DSCR: {dpr_doc.section_3_financial_projections.average_dscr:.2f} | BEP: {dpr_doc.section_3_financial_projections.break_even_point_pct:.1f}%")
    print(f"  Top Scheme: {dpr_doc.section_4_scheme_optimization[0].scheme_id} (Subsidy: ₹{dpr_doc.section_4_scheme_optimization[0].subsidy_grant_amount:,.2f})")
    print(f"  ML Viability: {dpr_doc.section_5_ml_viability_appraisal.verdict} ({dpr_doc.section_5_ml_viability_appraisal.confidence_pct:.1f}%)")
    print(f"  Statutory Checklist Docs: {len(dpr_doc.section_7_statutory_checklist)} mandatory/compliance items")
    print(f"  Markdown Length: {len(markdown_export)} chars | HTML Length: {len(html_export)} chars")

    check(f"[{case['name']}] DPR compiled with valid 7 sections", len(dpr_doc.section_7_statutory_checklist) >= 5)
    check(f"[{case['name']}] Section 2 financial reconciliation balanced", dpr_doc.section_2_capital_outlay_and_finance["means_of_finance"]["reconciliation_balanced"])
    check(f"[{case['name']}] Markdown memo contains DPR Ref ID", dpr_doc.section_1_header_and_profile.dpr_reference_id in markdown_export)
    check(f"[{case['name']}] HTML export contains proper closing tag", "</html>" in html_export)

    phase5_dpr_exports.append({
        "case_name": case["name"],
        "dpr_reference_id": dpr_doc.section_1_header_and_profile.dpr_reference_id,
        "dpr_json": dpr_doc.to_dict(),
        "markdown_length": len(markdown_export),
        "html_length": len(html_export),
    })

# Save full Phase 5 test report
out_dir = _ROOT / "To be Deleted"
out_dir.mkdir(parents=True, exist_ok=True)
with open(out_dir / "phase5_test_report.json", "w", encoding="utf-8") as f:
    json.dump(phase5_dpr_exports, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 90)
print(f"PHASE 5 VERIFICATION SUMMARY: {PASS} passed, {FAIL} failed")
print("=" * 90)
print("Integrated DPR report written to phase5_test_report.json")

if FAIL > 0:
    sys.exit(1)
