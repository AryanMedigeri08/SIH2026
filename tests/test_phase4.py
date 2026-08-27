"""
test_phase4.py — Udyam Saathi Phase 4 Verification Harness.

Four Layers of Verification:
  1. PROMPT CONSTRUCTION & INVARIANT CHECKS: Verifies exact injection of Tier 1 & Tier 2 numbers,
     zero financial recalculation instructions, and valid target language prompt framing.
  2. SHA-256 CACHE ENGINE: Verifies deterministic hash generation, instantaneous memory replay (<1ms),
     language-sensitive cache isolation, and cache stats.
  3. MULTI-LINGUAL DETERMINISTIC FALLBACK: Tests all 6 supported languages (EN, HI, MR, TA, TE, KN)
     under forced offline conditions, verifying 100% zero-crash operation, non-empty outputs, and 4 recommendations.
  4. 5 SIH PITCH CASE STUDIES FULL PIPELINE INTEGRATION: Chains Phase 1 -> Phase 2 -> Phase 3 -> Phase 4
     end-to-end, producing complete multi-lingual executive synthesis payloads.

Run: python test_phase4.py
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
from executive_synthesizer import (
    ExecutiveSynthesis, SynthesisCache, generate_executive_synthesis,
    get_deterministic_narrative, _build_synthesis_prompt, SUPPORTED_LANGUAGES,
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
# LAYER 1: PROMPT CONSTRUCTION & ARCHITECTURAL INVARIANTS
# ============================================================================
print("=" * 90)
print("LAYER 1 — PROMPT CONSTRUCTION & ARCHITECTURAL INVARIANTS")
print("=" * 90)

test_payload = {
    "enterprise_name": "Kashi Silk Weaving Unit",
    "business_category": "manufacturing",
    "sector": "apparel",
    "location_str": "Varanasi, Uttar Pradesh",
    "project_cost": 850000.0,
    "promoter_margin_amount": 85000.0,
    "top_scheme_name": "Stand-Up India",
    "subsidy_amount": 0.0,
    "subsidy_pct": 0.0,
    "effective_loan": 765000.0,
    "monthly_emi": 15420.50,
    "dscr": 1.48,
    "dscr_verdict": "VIABLE",
    "annual_tam": 4500000.0,
    "cpi_adjusted_price_floor": 480.0,
    "ml_verdict": "SUITABLE",
    "ml_confidence_pct": 97.4,
    "top_positive_driver": "Conservative loan-to-turnover leverage",
    "top_risk_factor": "Raw silk input inflation",
    "key_risks": ["Raw material inflation", "Weaving machinery power stability"],
}

sys_prompt, user_prompt = _build_synthesis_prompt(test_payload, language="hi")

check("System prompt mandates ZERO FINANCIAL RECALCULATION", "ZERO FINANCIAL RECALCULATION" in sys_prompt)
check("System prompt specifies Hindi language output", "Hindi (हिन्दी)" in sys_prompt)
check("User prompt contains exact project cost (₹850,000.00)", "₹850,000.00" in user_prompt)
check("User prompt contains exact DSCR (1.48)", "1.48" in user_prompt)
check("User prompt contains exact monthly EMI (₹15,420.50)", "₹15,420.50" in user_prompt)
check("User prompt contains ML verdict (SUITABLE) and confidence (97.4%)", "SUITABLE" in user_prompt and "97.4%" in user_prompt)
check("User prompt contains top scheme (Stand-Up India)", "Stand-Up India" in user_prompt)

print(f"\nLayer 1 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 2: SHA-256 CACHE ENGINE VERIFICATION
# ============================================================================
print("=" * 90)
print("LAYER 2 — SHA-256 IN-MEMORY CACHE ENGINE")
print("=" * 90)

cache = SynthesisCache()
cache.clear()

hash_en = cache.compute_hash(test_payload, "en")
hash_hi = cache.compute_hash(test_payload, "hi")

check("SHA-256 hash is a 64-character hex string", len(hash_en) == 64)
check("Language change produces a distinct SHA-256 hash", hash_en != hash_hi)

# Identical payload produces identical hash
hash_en_repeat = cache.compute_hash(test_payload, "en")
check("Identical payload produces identical SHA-256 hash", hash_en == hash_en_repeat)

# First generation (Cache Miss)
synth1 = generate_executive_synthesis(test_payload, language="en", force_fallback=True)
check("First call is not cached (is_cached is False)", synth1.is_cached is False)
check("Cache records 1 item after storage", cache.stats()["items_count"] == 1)

# Second generation (Cache Hit)
synth2 = generate_executive_synthesis(test_payload, language="en")
check("Second call returns from memory cache (is_cached is True)", synth2.is_cached is True)
check("Cached latency is sub-millisecond (< 1.0ms)", synth2.latency_ms < 1.0, f"got {synth2.latency_ms}ms")
check("Cache hits count incremented to 1", cache.stats()["hits"] == 1)
check("Cached content matches original executive summary", synth2.executive_summary == synth1.executive_summary)

# Cache isolation across languages
synth_hi = generate_executive_synthesis(test_payload, language="hi", force_fallback=True)
check("Hindi call creates a separate cache entry", synth_hi.language == "hi" and cache.stats()["items_count"] == 2)

print(f"\nLayer 2 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 3: MULTI-LINGUAL DETERMINISTIC FALLBACK (All 6 Languages)
# ============================================================================
print("=" * 90)
print("LAYER 3 — MULTI-LINGUAL DETERMINISTIC FALLBACK (6 Languages)")
print("=" * 90)

for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
    res = get_deterministic_narrative(
        enterprise_name="Ramanagara Auto Electricals",
        business_category="service",
        sector="repair",
        location_str="Ramanagara, Karnataka",
        project_cost=300000.0,
        top_scheme_name="MUDRA Kishore",
        subsidy_amount=0.0,
        effective_loan=270000.0,
        monthly_emi=6874.67,
        dscr=1.53,
        dscr_verdict="VIABLE",
        ml_verdict="SUITABLE",
        ml_confidence_pct=98.4,
        cpi_adjusted_price_floor=577.89,
        key_risks=["Competitor pricing pressure", "Monsoon footfall variation"],
        language=lang_code,
    )

    check(f"[{lang_name}] Executive summary is non-empty", len(res.executive_summary) > 50)
    check(f"[{lang_name}] Contains exactly 4 strategic recommendations", len(res.strategic_recommendations) == 4)
    check(f"[{lang_name}] Bank credit appraisal notes is non-empty", len(res.bank_appraisal_notes) > 30)
    check(f"[{lang_name}] Summary contains project cost ₹300,000", "300,000" in res.executive_summary or "300000" in res.executive_summary)
    check(f"[{lang_name}] Summary contains DSCR (1.53)", "1.53" in res.executive_summary)
    check(f"[{lang_name}] Summary contains ML verdict (SUITABLE)", "SUITABLE" in res.executive_summary)

print(f"\nLayer 3 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 4: 5 SIH PITCH CASE STUDIES — FULL 4-TIER PIPELINE INTEGRATION
# ============================================================================
print("=" * 90)
print("LAYER 4 — 5 SIH PITCH CASE STUDIES: FULL 4-TIER PIPELINE INTEGRATION")
print("=" * 90)

CASES_PHASE4 = [
    {
        "name": "Case 1: Dairy Processing in Joypur, Bankura (WB)",
        "state": "West Bengal", "base_population_2011": 4200, "sector": "dairy",
        "business_category": "manufacturing", "promoter_category": "general", "is_rural": True,
        "project_cost": 900000, "tenure_years": 7, "moratorium_months": 6,
        "annual_turnover_estimate": 950000, "infrastructure_score": 7.2,
        "cpi_inflation_pct": 4.8, "weather_risk_score": 0.25, "msme_total": 788,
        "sector_share_estimate": 0.05, "expected_monthly_units": 780,
        "language": "en",
    },
    {
        "name": "Case 2: Mobile Repair Shop in Ramanagara (KA)",
        "state": "Karnataka", "base_population_2011": 2100, "sector": "repair",
        "business_category": "service", "promoter_category": "general", "is_rural": True,
        "project_cost": 300000, "tenure_years": 3, "moratorium_months": 3,
        "annual_turnover_estimate": 420000, "infrastructure_score": 6.0,
        "cpi_inflation_pct": 4.2, "weather_risk_score": 0.1, "msme_total": 420,
        "sector_share_estimate": 0.08, "expected_monthly_units": 90,
        "language": "kn",  # Kannada
    },
    {
        "name": "Case 3: Women Tailoring Boutique in Varanasi (UP)",
        "state": "Uttar Pradesh", "base_population_2011": 3600, "sector": "apparel",
        "business_category": "service", "promoter_category": "women", "is_rural": False,
        "project_cost": 800000, "tenure_years": 5, "moratorium_months": 6,
        "annual_turnover_estimate": 700000, "infrastructure_score": 7.8,
        "cpi_inflation_pct": 5.5, "weather_risk_score": 0.15, "msme_total": 950,
        "sector_share_estimate": 0.04, "expected_monthly_units": 130,
        "language": "hi",  # Hindi
    },
    {
        "name": "Case 4: Overleveraged Agro Unit (High Outlay, Low Margin)",
        "state": "Madhya Pradesh", "base_population_2011": 2800, "sector": "food_processing",
        "business_category": "manufacturing", "promoter_category": "general", "is_rural": True,
        "project_cost": 2500000, "tenure_years": 5, "moratorium_months": 6,
        "annual_turnover_estimate": 600000, "infrastructure_score": 4.0,
        "cpi_inflation_pct": 7.5, "weather_risk_score": 0.4, "msme_total": 300,
        "sector_share_estimate": 0.10, "expected_monthly_units": 250,
        "monthly_net_operating_income_override": 15000,
        "language": "mr",  # Marathi
    },
    {
        "name": "Case 5: Artisan Pottery Cluster in Khurja (UP)",
        "state": "Uttar Pradesh", "base_population_2011": 5200, "sector": "artisan_trades",
        "business_category": "manufacturing", "promoter_category": "artisan", "is_rural": True,
        "project_cost": 280000, "tenure_years": 2.5, "moratorium_months": 3,
        "annual_turnover_estimate": 340000, "infrastructure_score": 5.5,
        "cpi_inflation_pct": 5.0, "weather_risk_score": 0.2, "msme_total": 610,
        "sector_share_estimate": 0.03, "expected_monthly_units": 500,
        "language": "ta",  # Tamil
    },
]

phase4_full_reports = []

for case in CASES_PHASE4:
    print("\n" + "-" * 90)
    print(f"{case['name']} — Target Language: {case['language'].upper()} ({SUPPORTED_LANGUAGES[case['language']]})")
    print("-" * 90)

    # 1. Phase 2 Market & Demographics
    pop = project_population(case["base_population_2011"], case["state"], 2026)
    tam = estimate_tam(pop.projected_households, case["sector"])
    dens = compute_msme_density(case["msme_total"], pop.projected_population)
    comp = compute_competition_intensity(case["msme_total"], case["sector_share_estimate"], pop.projected_population)

    # 2. Phase 2 Financial & Scheme Calculations
    wc = working_capital_estimate(case["annual_turnover_estimate"], case["sector"])
    schemes = rank_eligible_schemes(
        project_cost=case["project_cost"], business_category=case["business_category"],
        sector=case["sector"], promoter_category=case["promoter_category"], is_rural=case["is_rural"],
        tenure_years=case["tenure_years"], moratorium_months=case["moratorium_months"],
    )
    top_scheme = next((r for r in schemes if r.eligible), schemes[0])
    promoter_pct = 0.05 if case["promoter_category"] != "general" else 0.10
    promoter_margin_val = case["project_cost"] * promoter_pct
    loan_principal = max(case["project_cost"] - top_scheme.subsidy_grant_amount - promoter_margin_val, 1)
    amort = emi_with_moratorium(loan_principal, top_scheme.effective_interest_rate_pct, case["tenure_years"], case["moratorium_months"])

    monthly_noi = case.get("monthly_net_operating_income_override", case["annual_turnover_estimate"] * 0.30 / 12)
    dscr = compute_dscr(monthly_noi, amort.monthly_emi)

    # 3. Phase 3 Feature Extraction & ML Inference
    fv = extract_features_from_pipeline_objects(
        pop_proj=pop,
        tam_est=tam,
        msme_dens=dens,
        comp_int=comp,
        top_scheme=top_scheme,
        amort_res=amort,
        dscr_res=dscr,
        wc_res=wc,
        project_cost=case["project_cost"],
        annual_turnover=case["annual_turnover_estimate"],
        infrastructure_score=case["infrastructure_score"],
        cpi_inflation_pct=case["cpi_inflation_pct"],
        weather_risk_score=case["weather_risk_score"],
        promoter_margin_amount=promoter_margin_val,
    )
    ml_pred = predict_viability(fv)

    # 4. Phase 2 Pricing & Risk
    pricing = compute_pricing(
        monthly_emi=amort.monthly_emi, monthly_working_capital_outlay=wc.monthly_working_capital_outlay,
        expected_monthly_units=case["expected_monthly_units"], cpi_inflation_pct=case["cpi_inflation_pct"],
    )
    subsidy_coverage_ratio = top_scheme.subsidy_grant_amount / case["project_cost"] if case["project_cost"] else 0
    wc_months_buffer = promoter_margin_val / wc.monthly_working_capital_outlay if wc.monthly_working_capital_outlay else 0

    risks = build_risk_matrix(
        dscr=dscr.dscr, monthly_emi=amort.monthly_emi, projected_annual_tam=tam.annual_tam,
        annual_turnover_estimate=case["annual_turnover_estimate"],
        competition_intensity_normalized=comp.competition_intensity_normalized,
        infrastructure_score=case["infrastructure_score"], cpi_inflation_pct=case["cpi_inflation_pct"],
        weather_risk_score=case["weather_risk_score"], working_capital_months_buffer=wc_months_buffer,
        subsidy_coverage_ratio=subsidy_coverage_ratio,
    )
    risk_verdict = overall_risk_verdict(risks)

    # 5. Phase 4 AI Synthesis Payload Construction & Execution
    synthesis_input = {
        "enterprise_name": case["name"],
        "business_category": case["business_category"],
        "sector": case["sector"],
        "location_str": f"{case['state']} (Catchment Pop: {pop.projected_population:,})",
        "project_cost": case["project_cost"],
        "promoter_margin_amount": promoter_margin_val,
        "top_scheme_name": f"{top_scheme.scheme_id} ({top_scheme.full_name})",
        "subsidy_amount": top_scheme.subsidy_grant_amount,
        "subsidy_pct": subsidy_coverage_ratio * 100,
        "effective_loan": loan_principal,
        "monthly_emi": amort.monthly_emi,
        "dscr": dscr.dscr,
        "dscr_verdict": dscr.verdict,
        "annual_tam": tam.annual_tam,
        "cpi_adjusted_price_floor": pricing.cpi_adjusted_unit_price_floor,
        "ml_verdict": ml_pred.verdict,
        "ml_confidence_pct": ml_pred.confidence_pct,
        "top_positive_driver": ml_pred.top_positive_factors[0],
        "top_risk_factor": ml_pred.top_risk_factors[0],
        "key_risks": [r.title for r in risks if r.severity in ("HIGH", "SEVERE", "MODERATE")][:2],
    }

    synthesis = generate_executive_synthesis(
        payload=synthesis_input,
        language=case["language"],
    )

    report_entry = {
        "case": case["name"],
        "language": case["language"],
        "synthesis": synthesis.to_dict(),
        "ml_prediction": ml_pred.to_dict(),
        "dscr": dscr.to_dict(),
        "top_scheme": top_scheme.to_dict(),
    }
    phase4_full_reports.append(report_entry)

    print(f"  Synthesis Model: {synthesis.model_name} | Latency: {synthesis.latency_ms:.2f}ms | Cached: {synthesis.is_cached}")
    print(f"  Summary Preview: {synthesis.executive_summary[:120]}...")
    print(f"  Recommendations Count: {len(synthesis.strategic_recommendations)}")
    print(f"  Bank Notes Preview: {synthesis.bank_appraisal_notes[:100]}...")

    check(f"[{case['name']}] Synthesis generated successfully", len(synthesis.executive_summary) > 0)
    check(f"[{case['name']}] Recommendations has 4 items", len(synthesis.strategic_recommendations) == 4)
    check(f"[{case['name']}] Target language '{case['language']}' respected", synthesis.language == case["language"])

# Save complete Phase 4 test report
out_dir = _ROOT / "To be Deleted"
out_dir.mkdir(parents=True, exist_ok=True)
with open(out_dir / "phase4_test_report.json", "w", encoding="utf-8") as f:
    json.dump(phase4_full_reports, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 90)
print(f"PHASE 4 VERIFICATION SUMMARY: {PASS} passed, {FAIL} failed")
print("=" * 90)
print("Integrated case report written to phase4_test_report.json")

if FAIL > 0:
    sys.exit(1)
