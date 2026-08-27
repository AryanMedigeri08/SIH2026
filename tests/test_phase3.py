"""
test_phase3.py — Udyam Saathi Phase 3 Verification Harness.

Four Layers of Verification:
  1. FEATURE EXTRACTOR: Unit checks on 10-D extraction, default fallbacks, clamping, and array shapes.
  2. MODEL ARTIFACT & METADATA: Verification of viability_xgb.joblib and model_metadata.json.
  3. INFERENCE ENGINE: Latency benchmark (<10ms), probability normalization, explainability factors,
     and zero-crash deterministic fallback under missing model artifact.
  4. 5 SIH PITCH CASE STUDIES: End-to-end integration chaining Phase 2 math directly into Phase 3 ML
     inference, verifying predicted verdicts against the SIH pitch master plan.

Run: python test_phase3.py
"""

from __future__ import annotations
import json
import math
import sys
import time
from pathlib import Path
import numpy as np

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
from feature_extractor import (
    FeatureVector, extract_features, extract_features_from_pipeline_objects,
    FEATURE_NAMES, DEFAULT_FEATURE_VALUES, FEATURE_BOUNDS,
)
from inference import predict_viability, ViabilityModelLoader, ViabilityPrediction

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
# LAYER 1: FEATURE EXTRACTOR UNIT TESTS
# ============================================================================
print("=" * 90)
print("LAYER 1 — FEATURE EXTRACTOR UNIT TESTS")
print("=" * 90)

# 1. Full explicit extraction
fv1 = extract_features(
    dscr=1.75,
    subsidy_grant_amount=150000,
    total_project_cost=600000,
    loan_principal=390000,
    annual_turnover=800000,
    projected_population=5000,
    msme_density_per_10k=15.0,
    infrastructure_score=8.0,
    cpi_inflation_pct=5.2,
    working_capital_months_buffer=4.0,
    competition_intensity=0.25,
    weather_risk_score=0.10,
)
check("Feature vector has 10 attributes", len(fv1.to_dict()) == 10)
check("Numpy array has shape (10,)", fv1.to_array().shape == (10,))
check("Derived subsidy_coverage_ratio == 150k/600k (0.25)", abs(fv1.subsidy_coverage_ratio - 0.25) < 1e-4)
check("Derived loan_to_income_ratio == 390k/800k (0.4875)", abs(fv1.loan_to_income_ratio - 0.4875) < 1e-4)
check("Derived log_projected_population == log10(5000) ~= 3.699", abs(fv1.log_projected_population - math.log10(5000)) < 1e-3)

# 2. Missing values fallback to safe medians
fv_empty = extract_features()
check("Missing infrastructure_score falls back to default 6.0", fv_empty.infrastructure_score == DEFAULT_FEATURE_VALUES["infrastructure_score"])
check("Missing cpi_inflation_pct falls back to default 5.0", fv_empty.cpi_inflation_pct == DEFAULT_FEATURE_VALUES["cpi_inflation_pct"])
check("Missing weather_risk_score falls back to default 0.20", fv_empty.weather_risk_score == DEFAULT_FEATURE_VALUES["weather_risk_score"])
check("Missing dscr falls back to default 1.33", fv_empty.dscr == DEFAULT_FEATURE_VALUES["dscr"])

# 3. Clamping of extreme out-of-bounds inputs
fv_extreme = extract_features(
    dscr=99.0,                      # bound [0.0, 5.0]
    subsidy_coverage_ratio=2.5,     # bound [0.0, 1.0]
    infrastructure_score=15.0,      # bound [0.0, 10.0]
    weather_risk_score=-0.5,        # bound [0.0, 1.0]
)
check("Extreme DSCR (99.0) clamped to 5.0", fv_extreme.dscr == 5.0)
check("Extreme subsidy ratio (2.5) clamped to 1.0", fv_extreme.subsidy_coverage_ratio == 1.0)
check("Extreme infra score (15.0) clamped to 10.0", fv_extreme.infrastructure_score == 10.0)
check("Negative weather score (-0.5) clamped to 0.0", fv_extreme.weather_risk_score == 0.0)

print(f"\nLayer 1 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 2: MODEL ARTIFACT & METADATA VERIFICATION
# ============================================================================
print("=" * 90)
print("LAYER 2 — MODEL ARTIFACT & METADATA VERIFICATION")
print("=" * 90)

model_file = _ROOT / "backend" / "app" / "data" / "viability_xgb.joblib"
if not model_file.exists():
    model_file = _ROOT / "viability_xgb.joblib"

meta_file = _ROOT / "backend" / "app" / "data" / "model_metadata.json"
if not meta_file.exists():
    meta_file = _ROOT / "model_metadata.json"

check("viability_xgb.joblib exists", model_file.exists())
check("model_metadata.json exists", meta_file.exists())

with open(meta_file, "r", encoding="utf-8") as f:
    meta = json.load(f)

check("Metadata model_type is XGBClassifier", meta.get("model_type") == "XGBClassifier")
check("Feature count == 10", meta.get("feature_count") == 10)
check("5-Fold CV mean accuracy >= 95.0%", meta["cross_validation"]["mean_accuracy"] >= 0.95,
      f"got {meta['cross_validation']['mean_accuracy'] * 100:.2f}%")
check("Hold-out Test accuracy >= 95.0%", meta["test_metrics"]["test_accuracy"] >= 0.95,
      f"got {meta['test_metrics']['test_accuracy'] * 100:.2f}%")
check("Ranked feature importances present for all 10 features", len(meta["feature_importances_ranked"]) == 10)
check("Top feature gain is 'dscr'", meta["feature_importances_ranked"][0]["feature_name"] == "dscr")

print(f"\nLayer 2 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 3: INFERENCE ENGINE & FALLBACK TESTS
# ============================================================================
print("=" * 90)
print("LAYER 3 — INFERENCE ENGINE & FALLBACK TESTS")
print("=" * 90)

# Canonical suitable profile
fv_suit = extract_features(
    dscr=2.25, subsidy_coverage_ratio=0.35, loan_to_income_ratio=0.8,
    log_projected_population=3.9, msme_density_per_10k=12.0, infrastructure_score=8.5,
    cpi_inflation_pct=4.2, working_capital_months_buffer=4.0, competition_intensity=0.15,
    weather_risk_score=0.10,
)
pred_suit = predict_viability(fv_suit)

check("Canonical viable enterprise predicted as SUITABLE", pred_suit.verdict == "SUITABLE", f"got {pred_suit.verdict}")
check("Confidence score >= 85.0%", pred_suit.confidence_pct >= 85.0, f"got {pred_suit.confidence_pct:.2f}%")
prob_sum = sum(pred_suit.class_probabilities.values())
check("Probabilities sum to 1.0", abs(prob_sum - 1.0) < 1e-3, f"got {prob_sum}")
check("Contains non-empty top positive factors", len(pred_suit.top_positive_factors) > 0)
check("Contains non-empty top risk factors", len(pred_suit.top_risk_factors) > 0)
check("Inference used trained model (is_fallback is False)", pred_suit.is_fallback is False)

# Canonical distressed / overleveraged profile
fv_recon = extract_features(
    dscr=0.45, subsidy_coverage_ratio=0.0, loan_to_income_ratio=4.8,
    log_projected_population=3.2, msme_density_per_10k=4.0, infrastructure_score=3.5,
    cpi_inflation_pct=9.5, working_capital_months_buffer=0.5, competition_intensity=0.85,
    weather_risk_score=0.60,
)
pred_recon = predict_viability(fv_recon)
check("Canonical distressed enterprise predicted as RECONSIDER", pred_recon.verdict == "RECONSIDER", f"got {pred_recon.verdict}")
check("Distressed enterprise has high RECONSIDER probability", pred_recon.class_probabilities["RECONSIDER"] > 0.80)

# Inference Latency Benchmark (<10ms)
start_t = time.perf_counter()
for _ in range(100):
    predict_viability(fv_suit)
elapsed_ms = (time.perf_counter() - start_t) * 10  # ms per inference (1000/100)
check("Average inference latency < 5.0ms", elapsed_ms < 5.0, f"got {elapsed_ms:.2f}ms")

# Deterministic Fallback Mode (passing non-existent model path)
dummy_path = Path(__file__).parent / "non_existent_model.joblib"
pred_fallback = predict_viability(fv_recon, model_path=dummy_path)
check("Fallback mode activates when model path is invalid (is_fallback is True)", pred_fallback.is_fallback is True)
check("Fallback model version is 'rule_fallback_v1.0'", pred_fallback.model_version == "rule_fallback_v1.0")
check("Fallback correctly classifies distressed profile as RECONSIDER", pred_fallback.verdict == "RECONSIDER")

print(f"\nLayer 3 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 4: END-TO-END 5 SIH PITCH CASE STUDIES (Phase 2 + Phase 3 Integration)
# ============================================================================
print("=" * 90)
print("LAYER 4 — END-TO-END 5 SIH PITCH CASE STUDIES INTEGRATION")
print("=" * 90)

CASES = [
    {
        "name": "Case 1: Dairy Processing in Joypur, Bankura (WB)",
        "state": "West Bengal", "base_population_2011": 4200, "sector": "dairy",
        "business_category": "manufacturing", "promoter_category": "general", "is_rural": True,
        "project_cost": 900000, "tenure_years": 7, "moratorium_months": 6,
        "annual_turnover_estimate": 950000, "infrastructure_score": 7.2,
        "cpi_inflation_pct": 4.8, "weather_risk_score": 0.25, "msme_total": 788,
        "sector_share_estimate": 0.05, "expected_monthly_units": 780,
        "expected_verdict": "SUITABLE",
    },
    {
        "name": "Case 2: Mobile Repair Shop in Ramanagara (KA)",
        "state": "Karnataka", "base_population_2011": 2100, "sector": "repair",
        "business_category": "service", "promoter_category": "general", "is_rural": True,
        "project_cost": 300000, "tenure_years": 3, "moratorium_months": 3,
        "annual_turnover_estimate": 420000, "infrastructure_score": 6.0,
        "cpi_inflation_pct": 4.2, "weather_risk_score": 0.1, "msme_total": 420,
        "sector_share_estimate": 0.08, "expected_monthly_units": 90,
        "expected_verdict": "SUITABLE",
    },
    {
        "name": "Case 3: Women Tailoring Boutique in Varanasi (UP)",
        "state": "Uttar Pradesh", "base_population_2011": 3600, "sector": "apparel",
        "business_category": "service", "promoter_category": "women", "is_rural": False,
        "project_cost": 800000, "tenure_years": 5, "moratorium_months": 6,
        "annual_turnover_estimate": 700000, "infrastructure_score": 7.8,
        "cpi_inflation_pct": 5.5, "weather_risk_score": 0.15, "msme_total": 950,
        "sector_share_estimate": 0.04, "expected_monthly_units": 130,
        "expected_verdict": ("SUITABLE", "CAUTION"),  # acceptable range for moderate leverage
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
        "expected_verdict": "RECONSIDER",
    },
    {
        "name": "Case 5: Artisan Pottery Cluster in Khurja (UP)",
        "state": "Uttar Pradesh", "base_population_2011": 5200, "sector": "artisan_trades",
        "business_category": "manufacturing", "promoter_category": "artisan", "is_rural": True,
        "project_cost": 280000, "tenure_years": 2.5, "moratorium_months": 3,
        "annual_turnover_estimate": 340000, "infrastructure_score": 5.5,
        "cpi_inflation_pct": 5.0, "weather_risk_score": 0.2, "msme_total": 610,
        "sector_share_estimate": 0.03, "expected_monthly_units": 500,
        "expected_verdict": ("SUITABLE", "CAUTION"),
    },
]

phase3_full_reports = []

for case in CASES:
    print("\n" + "-" * 90)
    print(case["name"])
    print("-" * 90)

    # 1. Phase 2 Market sizing
    pop = project_population(case["base_population_2011"], case["state"], 2026)
    tam = estimate_tam(pop.projected_households, case["sector"])
    dens = compute_msme_density(case["msme_total"], pop.projected_population)
    comp = compute_competition_intensity(case["msme_total"], case["sector_share_estimate"], pop.projected_population)

    # 2. Phase 2 Financial core
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

    # 4. Phase 2 Risk & SWOT enriched with ML prediction
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

    swot = build_swot(
        dscr=dscr.dscr, subsidy_grant_amount=top_scheme.subsidy_grant_amount,
        subsidy_scheme_name=top_scheme.full_name, project_cost=case["project_cost"],
        infrastructure_score=case["infrastructure_score"], projected_annual_tam=tam.annual_tam,
        annual_turnover_estimate=case["annual_turnover_estimate"],
        competition_intensity_normalized=comp.competition_intensity_normalized,
        msme_density_per_10k=dens.msme_density_per_10k, cpi_inflation_pct=case["cpi_inflation_pct"],
        weather_risk_score=case["weather_risk_score"], ml_viability_verdict=ml_pred.verdict,
        ml_confidence_pct=ml_pred.confidence_pct,
    )

    pricing = compute_pricing(
        monthly_emi=amort.monthly_emi, monthly_working_capital_outlay=wc.monthly_working_capital_outlay,
        expected_monthly_units=case["expected_monthly_units"], cpi_inflation_pct=case["cpi_inflation_pct"],
    )

    report = {
        "case": case["name"],
        "dscr": dscr.to_dict(),
        "ml_viability": ml_pred.to_dict(),
        "risk_verdict": risk_verdict,
        "swot": swot.to_dict(),
        "pricing": pricing.to_dict(),
    }
    phase3_full_reports.append(report)

    print(f"  DSCR: {dscr.dscr:.2f} ({dscr.verdict}) | Top Scheme: {top_scheme.scheme_id}")
    print(f"  ML Verdict: {ml_pred.verdict} (Confidence: {ml_pred.confidence_pct:.1f}%)")
    print(f"  Probabilities: {ml_pred.class_probabilities}")
    print(f"  Key Positive: {ml_pred.top_positive_factors[0]}")
    print(f"  Key Risk: {ml_pred.top_risk_factors[0]}")

    expected = case["expected_verdict"]
    if isinstance(expected, tuple):
        check(f"[{case['name']}] ML verdict is one of {expected}", ml_pred.verdict in expected, f"got {ml_pred.verdict}")
    else:
        check(f"[{case['name']}] ML verdict matches expected '{expected}'", ml_pred.verdict == expected, f"got {ml_pred.verdict}")

    check(f"[{case['name']}] SWOT matrix contains ML viability reference",
          any("ML viability" in item.text for item in (swot.strengths + swot.weaknesses + swot.threats)))

# Case 4 specifically verified as RECONSIDER
case4_pred = phase3_full_reports[3]["ml_viability"]
check("Case 4 (Overleveraged Agro) ML Verdict is strictly RECONSIDER", case4_pred["verdict"] == "RECONSIDER")
check("Case 4 RECONSIDER probability > 80%", case4_pred["class_probabilities"]["RECONSIDER"] > 0.80)

# Save integrated test report
out_dir = _ROOT / "To be Deleted"
out_dir.mkdir(parents=True, exist_ok=True)
with open(out_dir / "phase3_test_report.json", "w", encoding="utf-8") as f:
    json.dump(phase3_full_reports, f, indent=2)

print("\n" + "=" * 90)
print(f"PHASE 3 VERIFICATION SUMMARY: {PASS} passed, {FAIL} failed")
print("=" * 90)
print("Integrated case report written to phase3_test_report.json")

if FAIL > 0:
    sys.exit(1)
