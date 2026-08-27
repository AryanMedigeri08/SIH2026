"""
test_phase2.py — Udyam Saathi Phase 2 verification harness.

Two layers of testing:
  1. UNIT-LEVEL sanity checks on each module's math (hand-verifiable numbers).
  2. END-TO-END pipeline runs against the 5 SIH pitch case studies named in
     master_implementation_plan.md Phase 8 Step 8.2, chaining:
     market_analyzer -> financial_calculator -> risk_analyzer -> swot_analyzer -> pricing_engine
     exactly the way Router_Feasibility will orchestrate them in Phase 6.

Run: python3 test_phase2.py
Exits non-zero on any failed assertion.
"""

import json
import sys
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

from financial_calculator import (
    emi_with_moratorium, working_capital_estimate, compute_dscr, rank_eligible_schemes,
)
from market_analyzer import (
    project_population, estimate_tam, compute_msme_density, compute_competition_intensity,
)
from risk_analyzer import build_risk_matrix, overall_risk_verdict
from swot_analyzer import build_swot
from pricing_engine import compute_pricing

PASS = 0
FAIL = 0


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}  {detail}")


# ============================================================================
# LAYER 1: UNIT-LEVEL MATH SANITY CHECKS (hand-verifiable)
# ============================================================================
print("=" * 90)
print("LAYER 1 — UNIT-LEVEL MATH SANITY CHECKS")
print("=" * 90)

# --- EMI, zero moratorium, hand-computable ---
# L=100000, i=12%/yr -> r_m=1%/mo, N=12 months, standard EMI table value ~ 8884.88
a = emi_with_moratorium(100000, 12.0, 1, 0)
check("EMI(100000, 12%, 1yr, 0 moratorium) ~= 8884.88",
      abs(a.monthly_emi - 8884.88) < 1.0, f"got {a.monthly_emi:.2f}")
check("repayment_months == 12 when moratorium=0", a.repayment_months == 12)

# --- Moratorium reduces repayment months, increases total interest vs no-moratorium ---
b = emi_with_moratorium(500000, 11.0, 5, 6)
c = emi_with_moratorium(500000, 11.0, 5, 0)
check("moratorium case has fewer repayment months than non-moratorium",
      b.repayment_months == 54 and c.repayment_months == 60)
check("moratorium case has higher total interest than zero-moratorium (deferred interest capitalized)",
      b.total_interest_payable > c.total_interest_payable,
      f"moratorium={b.total_interest_payable:.2f} vs none={c.total_interest_payable:.2f}")

# --- Zero-interest edge case (PM Vishwakarma-style near-zero shouldn't break; test literal 0%) ---
z = emi_with_moratorium(120000, 0.0, 1, 0)
check("0% interest EMI == principal / months", abs(z.monthly_emi - 10000.0) < 0.01)
check("0% interest total_interest ~= 0", abs(z.total_interest_payable) < 0.01)

# --- Moratorium >= tenure must raise ---
try:
    emi_with_moratorium(100000, 10, 1, 12)
    check("moratorium >= tenure raises ValueError", False)
except ValueError:
    check("moratorium >= tenure raises ValueError", True)

# --- DSCR bucketing at exact boundaries ---
d1 = compute_dscr(1330, 1000)  # exactly 1.33
d2 = compute_dscr(1329, 1000)  # just under
d3 = compute_dscr(999, 1000)   # just under 1.0
check("DSCR 1.33 -> VIABLE", d1.verdict == "VIABLE", d1.verdict)
check("DSCR 1.329 -> MARGINAL", d2.verdict == "MARGINAL", d2.verdict)
check("DSCR 0.999 -> AT RISK", d3.verdict == "AT RISK", d3.verdict)

# --- Working capital ratio applied correctly ---
wc = working_capital_estimate(1200000, "dairy")
check("dairy WC ratio = 1/12 of annual turnover", abs(wc.working_capital_required - 100000.0) < 0.01,
      f"got {wc.working_capital_required}")

# --- Population projection, hand-computable with national default rate ---
pop = project_population(10000, "Nowhereland", 2021, growth_rates={"state_cagr": {}, "national_default_cagr": 0.01})
expected = 10000 * (1.01 ** 10)
check("population projection matches P0*(1+r)^n for unmapped state (national default fallback)",
      abs(pop.projected_population - round(expected)) <= 1, f"got {pop.projected_population} expected ~{expected:.0f}")
check("growth_rate_source flags fallback correctly", pop.growth_rate_source == "national_default")

# --- TAM formula ---
tam = estimate_tam(1000, "dairy")  # penetration 0.42, freq 26, ticket 75
expected_units = 1000 * 0.42 * 26
expected_tam = expected_units * 75
check("TAM monthly_units matches households*penetration*frequency",
      abs(tam.monthly_units - expected_units) < 0.01)
check("TAM monthly_tam matches units*ticket_size",
      abs(tam.monthly_tam - expected_tam) < 0.01)

# --- MSME density graceful degradation when data missing ---
dens_missing = compute_msme_density(None, 50000)
check("MSME density returns data_available=False (not a crash) when input missing",
      dens_missing.data_available is False and dens_missing.msme_density_per_10k == 0.0)

# --- Scheme ranking: MUDRA Shishu should be eligible for a ₹40k service project, PMEGP should not (too small doesn't matter, but sector "all") ---
rankings = rank_eligible_schemes(
    project_cost=40000, business_category="service", sector="repair",
    promoter_category="general", is_rural=True, tenure_years=2,
)
shishu = next(r for r in rankings if r.scheme_id == "MUDRA_SHISHU")
check("MUDRA_SHISHU eligible for ₹40k repair project", shishu.eligible is True)
standup = next(r for r in rankings if r.scheme_id == "STANDUP_INDIA")
check("STANDUP_INDIA ineligible for general-category promoter (SC/ST/Women only)", standup.eligible is False)
check("ranked list rank numbers are sequential starting at 1",
      [r.rank for r in rankings] == list(range(1, len(rankings) + 1)))
check("eligible schemes sorted before ineligible schemes",
      all(rankings[i].eligible or not rankings[i+1].eligible for i in range(len(rankings)-1)) or
      all(r.eligible for r in rankings if r.rank <= sum(1 for x in rankings if x.eligible)),
      )

print(f"\nLayer 1 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 2: END-TO-END PIPELINE — 5 SIH PITCH CASE STUDIES
# ============================================================================
print("=" * 90)
print("LAYER 2 — END-TO-END PIPELINE: 5 SIH PITCH CASE STUDIES")
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
        "expected_scheme_hint": ("PMEGP", "PMFME"), "expected_dscr_min": 1.2,
    },
    {
        "name": "Case 2: Mobile Repair Shop in Ramanagara (KA)",
        "state": "Karnataka", "base_population_2011": 2100, "sector": "repair",
        "business_category": "service", "promoter_category": "general", "is_rural": True,
        "project_cost": 300000, "tenure_years": 3, "moratorium_months": 3,
        "annual_turnover_estimate": 420000, "infrastructure_score": 6.0,
        "cpi_inflation_pct": 4.2, "weather_risk_score": 0.1, "msme_total": 420,
        "sector_share_estimate": 0.08, "expected_monthly_units": 90,
        "expected_scheme_hint": ("MUDRA_KISHORE",), "expected_dscr_min": 1.3,
    },
    {
        "name": "Case 3: Women Tailoring Boutique in Varanasi (UP)",
        "state": "Uttar Pradesh", "base_population_2011": 3600, "sector": "apparel",
        "business_category": "service", "promoter_category": "women", "is_rural": False,
        "project_cost": 800000, "tenure_years": 5, "moratorium_months": 6,
        "annual_turnover_estimate": 700000, "infrastructure_score": 7.8,
        "cpi_inflation_pct": 5.5, "weather_risk_score": 0.15, "msme_total": 950,
        "sector_share_estimate": 0.04, "expected_monthly_units": 130,
        "expected_scheme_hint": ("STANDUP_INDIA", "PMEGP"), "expected_dscr_min": 1.1,
    },
    {
        "name": "Case 4: Overleveraged Agro Unit (High Outlay, Low Margin)",
        "state": "Madhya Pradesh", "base_population_2011": 2800, "sector": "food_processing",
        "business_category": "manufacturing", "promoter_category": "general", "is_rural": True,
        "project_cost": 2500000, "tenure_years": 5, "moratorium_months": 6,
        "annual_turnover_estimate": 600000, "infrastructure_score": 4.0,
        "cpi_inflation_pct": 7.5, "weather_risk_score": 0.4, "msme_total": 300,
        "sector_share_estimate": 0.10, "expected_monthly_units": 250,
        "expected_scheme_hint": ("PMFME", "PMEGP"), "expected_dscr_max": 1.0,
        "monthly_net_operating_income_override": 15000,  # ~50k/year margin implies thin monthly NOI
    },
    {
        "name": "Case 5: Artisan Pottery Cluster in Khurja (UP)",
        "state": "Uttar Pradesh", "base_population_2011": 5200, "sector": "artisan_trades",
        "business_category": "manufacturing", "promoter_category": "artisan", "is_rural": True,
        "project_cost": 280000, "tenure_years": 2.5, "moratorium_months": 3,
        "annual_turnover_estimate": 340000, "infrastructure_score": 5.5,
        "cpi_inflation_pct": 5.0, "weather_risk_score": 0.2, "msme_total": 610,
        "sector_share_estimate": 0.03, "expected_monthly_units": 500,
        "expected_scheme_hint": ("PM_VISHWAKARMA",), "expected_dscr_min": 1.0,
    },
]

all_reports = []

for case in CASES:
    print("\n" + "-" * 90)
    print(case["name"])
    print("-" * 90)

    # 1. Market sizing
    pop = project_population(case["base_population_2011"], case["state"], 2026)
    tam = estimate_tam(pop.projected_households, case["sector"])
    dens = compute_msme_density(case["msme_total"], pop.projected_population)
    comp = compute_competition_intensity(case["msme_total"], case["sector_share_estimate"], pop.projected_population)

    # 2. Financial core
    wc = working_capital_estimate(case["annual_turnover_estimate"], case["sector"])
    schemes = rank_eligible_schemes(
        project_cost=case["project_cost"], business_category=case["business_category"],
        sector=case["sector"], promoter_category=case["promoter_category"], is_rural=case["is_rural"],
        tenure_years=case["tenure_years"], moratorium_months=case["moratorium_months"],
    )
    top_scheme = next((r for r in schemes if r.eligible), schemes[0])
    # loan principal net of top scheme's subsidy, matching rank_eligible_schemes' own internal logic
    promoter_pct = 0.05 if case["promoter_category"] != "general" else 0.10
    loan_principal = max(case["project_cost"] - top_scheme.subsidy_grant_amount - case["project_cost"] * promoter_pct, 1)
    amort = emi_with_moratorium(loan_principal, top_scheme.effective_interest_rate_pct, case["tenure_years"], case["moratorium_months"])

    monthly_noi = case.get("monthly_net_operating_income_override", case["annual_turnover_estimate"] * 0.30 / 12)
    dscr = compute_dscr(monthly_noi, amort.monthly_emi)

    subsidy_coverage_ratio = top_scheme.subsidy_grant_amount / case["project_cost"] if case["project_cost"] else 0
    wc_months_buffer = (case["project_cost"] * promoter_pct) / wc.monthly_working_capital_outlay if wc.monthly_working_capital_outlay else 0

    # 3. Risk matrix
    risks = build_risk_matrix(
        dscr=dscr.dscr, monthly_emi=amort.monthly_emi, projected_annual_tam=tam.annual_tam,
        annual_turnover_estimate=case["annual_turnover_estimate"],
        competition_intensity_normalized=comp.competition_intensity_normalized,
        infrastructure_score=case["infrastructure_score"], cpi_inflation_pct=case["cpi_inflation_pct"],
        weather_risk_score=case["weather_risk_score"], working_capital_months_buffer=wc_months_buffer,
        subsidy_coverage_ratio=subsidy_coverage_ratio,
    )
    risk_verdict = overall_risk_verdict(risks)

    # 4. SWOT (verdict feeds SWOT text; Phase 3 ML model isn't built yet, so we
    #    derive a provisional deterministic proxy verdict from DSCR + risk score
    #    purely for this Phase 2 test — Phase 3 XGBoost will replace this)
    if dscr.dscr >= 1.33 and risk_verdict["average_risk_score"] < 5.0:
        proxy_verdict = "SUITABLE"
    elif dscr.dscr >= 1.0:
        proxy_verdict = "CAUTION"
    else:
        proxy_verdict = "RECONSIDER"

    swot = build_swot(
        dscr=dscr.dscr, subsidy_grant_amount=top_scheme.subsidy_grant_amount,
        subsidy_scheme_name=top_scheme.full_name, project_cost=case["project_cost"],
        infrastructure_score=case["infrastructure_score"], projected_annual_tam=tam.annual_tam,
        annual_turnover_estimate=case["annual_turnover_estimate"],
        competition_intensity_normalized=comp.competition_intensity_normalized,
        msme_density_per_10k=dens.msme_density_per_10k, cpi_inflation_pct=case["cpi_inflation_pct"],
        weather_risk_score=case["weather_risk_score"], ml_viability_verdict=proxy_verdict,
        ml_confidence_pct=0.0,
    )

    # 5. Pricing
    pricing = compute_pricing(
        monthly_emi=amort.monthly_emi, monthly_working_capital_outlay=wc.monthly_working_capital_outlay,
        expected_monthly_units=case["expected_monthly_units"], cpi_inflation_pct=case["cpi_inflation_pct"],
    )

    report = {
        "case": case["name"], "population_projection": pop.to_dict(), "tam": tam.to_dict(),
        "msme_density": dens.to_dict(), "competition": comp.to_dict(), "working_capital": wc.to_dict(),
        "top_scheme": top_scheme.to_dict(), "amortization": amort.to_dict(), "dscr": dscr.to_dict(),
        "risk_verdict": risk_verdict, "proxy_viability_verdict": proxy_verdict,
        "pricing": pricing.to_dict(),
    }
    all_reports.append(report)

    print(f"  Projected 2026 population: {pop.projected_population:,} | Households: {pop.projected_households:,}")
    print(f"  Annual TAM: Rs.{tam.annual_tam:,.0f}")
    print(f"  Top scheme: {top_scheme.scheme_id} | Subsidy: Rs.{top_scheme.subsidy_grant_amount:,.0f} | "
          f"Eligible: {top_scheme.eligible}")
    print(f"  EMI: Rs.{amort.monthly_emi:,.2f}/mo | DSCR: {dscr.dscr:.2f} ({dscr.verdict})")
    print(f"  Risk verdict: {risk_verdict['overall_severity']} (avg {risk_verdict['average_risk_score']}/10, "
          f"{risk_verdict['high_or_severe_risk_count']} high/severe points)")
    print(f"  Proxy viability verdict: {proxy_verdict}")
    print(f"  CPI-adjusted price floor: Rs.{pricing.cpi_adjusted_unit_price_floor:.2f}/unit")

    # --- assertions per case ---
    check(f"[{case['name']}] top scheme is eligible", top_scheme.eligible)
    if "expected_scheme_hint" in case:
        # NOTE: the pitch narrative (master_implementation_plan.md Phase 8) names a specific
        # scheme per case, but rank_eligible_schemes() ranks purely by Net_Benefit
        # (Subsidy - Total_Interest) per blueprint §2.5. When PMEGP's larger subsidy slab
        # beats a narrative scheme's net benefit, PMEGP correctly outranks it — that is the
        # deterministic-optimizer behaving exactly as designed, not a bug. We therefore only
        # assert the narrative scheme is ELIGIBLE and present in the ranked table (so it still
        # surfaces in the DPR's "Top 5 Ranked Schemes"), not that it is literally rank #1.
        hinted_present_and_eligible = any(
            r.scheme_id in case["expected_scheme_hint"] and r.eligible for r in schemes
        )
        check(f"[{case['name']}] narrative-hinted scheme {case['expected_scheme_hint']} is present & eligible in ranked table",
              hinted_present_and_eligible,
              f"top={top_scheme.scheme_id}; eligible schemes={[r.scheme_id for r in schemes if r.eligible]}")
    if "expected_dscr_min" in case:
        check(f"[{case['name']}] DSCR >= {case['expected_dscr_min']}", dscr.dscr >= case["expected_dscr_min"],
              f"got {dscr.dscr:.2f}")
    if "expected_dscr_max" in case:
        check(f"[{case['name']}] DSCR <= {case['expected_dscr_max']} (overleveraged case)",
              dscr.dscr <= case["expected_dscr_max"], f"got {dscr.dscr:.2f}")
    check(f"[{case['name']}] all money outputs are non-negative",
          amort.monthly_emi >= 0 and wc.working_capital_required >= 0 and tam.annual_tam >= 0)
    check(f"[{case['name']}] SWOT matrix has content in all 4 quadrants",
          all(len(getattr(swot, q)) > 0 for q in ("strengths", "weaknesses", "opportunities", "threats")))

# Case 4 should specifically be the RECONSIDER / AT RISK case
case4_report = all_reports[3]
check("Case 4 (overleveraged) DSCR verdict is AT RISK or MARGINAL",
      case4_report["dscr"]["verdict"] in ("AT RISK", "MARGINAL"), case4_report["dscr"]["verdict"])
check("Case 4 (overleveraged) proxy viability verdict is CAUTION or RECONSIDER",
      case4_report["proxy_viability_verdict"] in ("CAUTION", "RECONSIDER"), case4_report["proxy_viability_verdict"])

# ============================================================================
# LAYER 3: NO-LLM / ZERO-DEPENDENCY INVARIANT CHECK
# ============================================================================
print("\n" + "=" * 90)
print("LAYER 3 — ARCHITECTURAL INVARIANT CHECK (zero LLM / zero network calls)")
print("=" * 90)
import ast

for mod_file in ["financial_calculator.py", "market_analyzer.py", "risk_analyzer.py", "swot_analyzer.py", "pricing_engine.py"]:
    file_path = _CORE / mod_file
    with open(file_path, encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    forbidden = imports & {"requests", "httpx", "urllib", "groq", "openai", "socket", "aiohttp"}
    check(f"{mod_file} imports zero network/LLM libraries", len(forbidden) == 0, f"found: {forbidden}")
    check(f"{mod_file} imports only stdlib + json/math/dataclasses/pathlib",
          imports.issubset({"json", "math", "dataclasses", "pathlib", "typing", "__future__", "ast"}),
          f"imports: {imports}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 90)
print(f"TOTAL: {PASS} passed, {FAIL} failed")
print("=" * 90)

out_dir = _ROOT / "To be Deleted"
out_dir.mkdir(parents=True, exist_ok=True)
with open(out_dir / "phase2_test_report.json", "w", encoding="utf-8") as f:
    json.dump(all_reports, f, indent=2)
print("\nFull case-study reports written to To be Deleted/phase2_test_report.json")

if FAIL > 0:
    sys.exit(1)
