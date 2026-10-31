"""
tests/test_three_pillars.py — Rigorous Verification Suite for the Three Pillars:
1. Dynamic Value-Driven Turnover & Bounded DSCR Spectrum (0.8x - 2.8x+)
2. Infinite AI Contextual + Deterministic Balanced Machinery Engine (sum == 55%)
3. Statutory Land & Operating Premises Model (Zero Land Outlay, Rent OPEX, Tailored Checklist)
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any

# Add backend core and backend root to path
backend_core = Path(__file__).resolve().parent.parent / "backend" / "app" / "core"
backend_root = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_core))
sys.path.insert(0, str(backend_root))

from financial_calculator import (
    compute_bounded_dscr,
    compute_dscr,
    estimate_smart_turnover,
    calculate_quarterly_amortization,
    SECTOR_ECONOMIC_PROFILES,
    emi_with_moratorium,
    rank_eligible_schemes,
)
from machinery_engine import (
    extract_contextual_machinery,
    normalize_and_balance_machinery,
    OFFLINE_MACHINERY_CATALOG,
    MACHINERY_LLM_MODEL,
)
from dpr_generator import build_bank_dpr, dpr_to_printable_markdown, dpr_to_html
from market_analyzer import project_population, estimate_tam, compute_msme_density
from risk_analyzer import RiskPoint
from swot_analyzer import SWOTMatrix


@dataclass
class MockPricing:
    cpi_inflation_pct: float = 5.2
    cpi_adjusted_unit_price_floor: float = 125.0

    def to_dict(self):
        return {"cpi_inflation_pct": self.cpi_inflation_pct, "cpi_adjusted_unit_price_floor": self.cpi_adjusted_unit_price_floor}


@dataclass
class MockML:
    verdict: str = "SUITABLE"
    confidence_pct: float = 88.5
    class_probabilities: Any = None
    feature_values: Any = None
    top_positive_factors: Any = None
    top_risk_factors: Any = None
    model_version: str = "XGBoost 10-D Viability Classifier"
    shap_explanation: Any = None
    global_feature_importance: Any = None

    def __post_init__(self):
        self.class_probabilities = {"SUITABLE": 0.885, "CAUTION": 0.10, "RECONSIDER": 0.015}
        self.feature_values = {"x1": 1.5, "x2": 2.0}
        self.top_positive_factors = ["Adequate debt service coverage ratio (DSCR >= 1.5x)"]
        self.top_risk_factors = ["Local competition saturation"]

    def to_dict(self):
        return {"verdict": self.verdict, "confidence_pct": self.confidence_pct}


@dataclass
class MockSynthesis:
    executive_summary: str = "The proposed enterprise demonstrates strong economic viability and healthy debt service buffer."
    strategic_recommendations: Any = None
    bank_appraisal_notes: str = "Promoter equity contribution verified at 10%. Working capital reserve sized conservatively."

    def __post_init__(self):
        self.strategic_recommendations = [
            "Formalize supply agreement with local milk collection cooperatives.",
            "Maintain 3-month working capital cash buffer for price stabilization.",
        ]

    def to_dict(self):
        return {
            "executive_summary": self.executive_summary,
            "strategic_recommendations": self.strategic_recommendations,
            "bank_appraisal_notes": self.bank_appraisal_notes,
        }


def test_pillar1_smart_turnover():
    print("\n--- Testing Pillar 1: Smart Turnover Auto-Sizing ---")
    project_cost = 1000000.0  # 10 Lakhs
    tam = 50000000.0  # 5 Crores local TAM

    # Dairy sector
    res_dairy = estimate_smart_turnover(project_cost, "dairy", capacity_factor=0.80, monthly_rent=3000.0, local_catchment_tam=tam)
    assert res_dairy.estimated_annual_sales > 0, "Dairy turnover must be positive"
    assert res_dairy.market_share_of_tam_pct < 100.0, "Turnover must be realistic fraction of TAM"
    assert res_dairy.turnover_to_capital_ratio > 0.5, "Velocity ratio must be sensible"
    print(f"  [PASS] Dairy Turnover: Rs.{res_dairy.estimated_annual_sales:,.2f} (Velocity: {res_dairy.turnover_to_capital_ratio:.2f}x)")

    # Retail sector (high velocity)
    res_retail = estimate_smart_turnover(project_cost, "retail", capacity_factor=0.80, monthly_rent=5000.0, local_catchment_tam=tam)
    assert res_retail.estimated_annual_sales > res_dairy.estimated_annual_sales, "Retail turnover velocity should exceed dairy"
    print(f"  [PASS] Retail Turnover: Rs.{res_retail.estimated_annual_sales:,.2f} (Velocity: {res_retail.turnover_to_capital_ratio:.2f}x)")


def test_pillar1_dynamic_dscr_bounds():
    print("\n--- Testing Pillar 1: Organic & Bounded DSCR Spectrum ---")

    # 1. Deficit / Negative NOI Guardrail
    dscr_def, verdict_def, class_def = compute_bounded_dscr(-5000.0, 12000.0)
    assert dscr_def == 0.0, "Negative NOI must clamp to exactly 0.00x"
    assert verdict_def == "AT RISK"
    assert "DEFICIT" in class_def
    print(f"  [PASS] Negative NOI guardrail: {dscr_def:.2f}x -> {verdict_def} ({class_def})")

    # 2. Zero / Negative EMI Guardrail (Debt-free)
    dscr_df, verdict_df, class_df = compute_bounded_dscr(50000.0, 0.0)
    assert dscr_df == 5.0, "Zero debt must cap safely at 5.00x without infinity"
    assert verdict_df == "VIABLE"
    print(f"  [PASS] Zero EMI debt-free cap: {dscr_df:.2f}x -> {verdict_df} ({class_df})")

    # 3. Healthy Typical Rural Range (e.g. 1.45x - 1.85x)
    dscr_norm, verdict_norm, class_norm = compute_bounded_dscr(20000.0, 13000.0)
    assert 1.45 <= dscr_norm <= 1.85, f"Expected 1.45-1.85, got {dscr_norm}"
    assert verdict_norm == "VIABLE"
    print(f"  [PASS] Standard SME range: {dscr_norm:.2f}x -> {verdict_norm} ({class_norm})")

    # 4. Prime / Mukesh Ambani-tier Range (e.g. 2.67x)
    dscr_prime, verdict_prime, class_prime = compute_bounded_dscr(40000.0, 15000.0)
    assert dscr_prime >= 2.0, f"Expected >= 2.0x, got {dscr_prime}"
    assert verdict_prime == "VIABLE"
    assert "PRIME" in class_prime or "EXCELLENT" in class_prime
    print(f"  [PASS] Prime Solvency Tier: {dscr_prime:.2f}x -> {verdict_prime} ({class_prime})")

    # 5. Extreme NOI Cap (Never thousands)
    dscr_huge, verdict_huge, _ = compute_bounded_dscr(1000000.0, 100.0)
    assert dscr_huge == 5.0, "Massive income must cleanly cap at 5.00x instead of 10,000x"
    print(f"  [PASS] Extreme NOI cap: {dscr_huge:.2f}x (never thousands)")


def test_pillar1_quarterly_amortization():
    print("\n--- Testing Pillar 1: Statutory SCA Quarterly Amortization ---")
    # Micro Scheme: Rs.1,25,000 loan @ 6.5% for 3 yrs, 3 mo moratorium (1 quarter)
    q_res = calculate_quarterly_amortization(125000.0, 6.5, 3.0, 3)
    assert q_res.moratorium_quarters == 1
    assert q_res.repayment_quarters == 11
    assert q_res.total_quarters == 12
    assert q_res.quarterly_installment > 0
    assert len(q_res.schedule) == 12
    assert q_res.schedule[-1].closing_principal == 0.0
    print(f"  [PASS] SCA Micro Scheme: 12 quarters, installment Rs.{q_res.quarterly_installment:,.2f}, final balance Rs.{q_res.schedule[-1].closing_principal}")


def test_pillar2_infinite_machinery_balance():
    print("\n--- Testing Pillar 2: Plant & Machinery 55% Exact Balance ---")
    project_cost = 1000000.0  # 10 Lakhs
    budget = project_cost * 0.55  # 5,50,000

    # 1. Ice Cream Manufacturing Unit
    ice_cream_sched = extract_contextual_machinery(
        enterprise_name="Joypur Ice Cream & Dairy Parlor",
        business_category="manufacturing",
        sector="ice_cream",
        allocated_machinery_budget=budget,
        use_ai=False,
    )
    items_sum = sum(it.total_cost_inr for it in ice_cream_sched.items)
    assert round(items_sum, 2) == budget, f"Sum {items_sum} != {budget}"
    assert ice_cream_sched.reconciliation_balanced is True
    assert len(ice_cream_sched.items) >= 4
    print(f"  [PASS] Ice Cream Unit ({len(ice_cream_sched.items)} items): Sum = Rs.{items_sum:,.2f} == Rs.{budget:,.2f} exactly")

    # 2. Custom Infinite Business: Turmeric Polishing & Spices Processing
    turmeric_sched = extract_contextual_machinery(
        enterprise_name="Kisan Turmeric Polisher & Agro Spices",
        business_category="manufacturing",
        sector="food_processing",
        allocated_machinery_budget=budget,
        use_ai=False,
    )
    t_sum = sum(it.total_cost_inr for it in turmeric_sched.items)
    assert round(t_sum, 2) == budget, f"Sum {t_sum} != {budget}"
    assert turmeric_sched.reconciliation_balanced is True
    print(f"  [PASS] Turmeric Unit ({len(turmeric_sched.items)} items): Sum = Rs.{t_sum:,.2f} == Rs.{budget:,.2f} exactly")

    # 3. Custom Arbitrary Outlay to verify penny-perfect rounding
    odd_budget = 373421.39
    odd_sched = normalize_and_balance_machinery(
        raw_items=[
            {"item_name": "M1", "specification": "S1", "quantity": 1, "cost_share_pct": 33.333, "power_specs": "1kW", "sourcing_channel": "OEM"},
            {"item_name": "M2", "specification": "S2", "quantity": 2, "cost_share_pct": 33.333, "power_specs": "2kW", "sourcing_channel": "OEM"},
            {"item_name": "M3", "specification": "S3", "quantity": 1, "cost_share_pct": 33.334, "power_specs": "3kW", "sourcing_channel": "OEM"},
        ],
        allocated_machinery_budget=odd_budget,
        capacity_summary="Test unit",
        connected_load_kw=6.0,
    )
    odd_sum = sum(it.total_cost_inr for it in odd_sched.items)
    assert round(odd_sum, 2) == odd_budget, f"Odd sum {odd_sum} != {odd_budget}"
    print(f"  [PASS] Odd Budget Penny Precision: Sum = Rs.{odd_sum:,.2f} == Rs.{odd_budget:,.2f} exactly")


def test_pillar3_land_and_operating_premises():
    print("\n--- Testing Pillar 3: Land Statutory Norms & Premises Models ---")

    pop = project_population(5000, "West Bengal", 2026)
    tam = estimate_tam(pop.projected_households, "dairy")
    dens = compute_msme_density(12000, 2500000)

    schemes = rank_eligible_schemes(
        project_cost=1000000.0,
        business_category="manufacturing",
        sector="dairy",
        promoter_category="obc",
        is_rural=True,
        tenure_years=7.0,
        moratorium_months=6,
    )
    scheme = schemes[0]
    amort = emi_with_moratorium(550000.0, 8.0, 7.0, 6)
    dscr_res = compute_dscr(25000.0, amort.monthly_emi)

    pricing = MockPricing()
    ml_pred = MockML()
    ai_synth = MockSynthesis()

    # 1. Rented Premise Case
    machinery_sched = extract_contextual_machinery("Test Dairy", "manufacturing", "dairy", 550000.0, use_ai=False)
    dpr_rented = build_bank_dpr(
        enterprise_name="Test Dairy Farm",
        business_category="manufacturing",
        sector="dairy",
        promoter_name="Sita Devi",
        promoter_category="obc",
        gender="female",
        state_name="West Bengal",
        district_name="Bankura",
        block_name="Joypur",
        village_name="Joypur",
        is_rural=True,
        project_cost=1000000.0,
        annual_turnover_estimate=1200000.0,
        tenure_years=7.0,
        moratorium_months=6,
        pop_projection=pop,
        tam_estimate=tam,
        msme_density=dens,
        ranked_schemes=[scheme],
        amortization=amort,
        dscr_result=dscr_res,
        risk_points=[],
        risk_verdict={"overall_severity": "LOW"},
        swot_matrix=SWOTMatrix(strengths=["Good"], weaknesses=[], opportunities=[], threats=[]),
        pricing_result=pricing,
        ml_prediction=ml_pred,
        ai_synthesis=ai_synth,
        machinery_schedule=machinery_sched.to_dict(),
        premise_type="rented",
        monthly_rent=3500.0,
    )

    outlay_rented = dpr_rented.section_2_capital_outlay_and_finance["capital_outlay"]
    finance_rented = dpr_rented.section_2_capital_outlay_and_finance["means_of_finance"]

    # Verify Statutory Zero Land Outlay
    assert outlay_rented["land_acquisition_outlay"] == 0.0, "Land acquisition outlay MUST be 0.0"
    assert "Ministry of MSME" in outlay_rented["land_compliance_note"] and "₹0.00" in outlay_rented["land_compliance_note"]
    assert finance_rented["reconciliation_balanced"] is True
    assert finance_rented["total_means_of_finance"] == outlay_rented["total_capital_outlay"]

    # Verify Rented Checklist Document DOC-LOC-03
    checklist = dpr_rented.section_7_statutory_checklist
    doc_loc = next((d for d in checklist if d.document_code == "DOC-LOC-03"), None)
    assert doc_loc is not None, "DOC-LOC-03 must be present"
    assert "Rent Agreement" in doc_loc.document_name
    print("  [PASS] Rented Premise: Zero Land Outlay, DOC-LOC-03 Lease requirement verified")

    # 2. Owned Land Case
    dpr_owned = build_bank_dpr(
        enterprise_name="Test Dairy Farm Owned",
        business_category="manufacturing",
        sector="dairy",
        promoter_name="Ramesh Kumar",
        promoter_category="sc",
        gender="male",
        state_name="Bihar",
        district_name="Patna",
        block_name="Danapur",
        village_name="Danapur",
        is_rural=True,
        project_cost=1000000.0,
        annual_turnover_estimate=1200000.0,
        tenure_years=7.0,
        moratorium_months=6,
        pop_projection=pop,
        tam_estimate=tam,
        msme_density=dens,
        ranked_schemes=[scheme],
        amortization=amort,
        dscr_result=dscr_res,
        risk_points=[],
        risk_verdict={"overall_severity": "LOW"},
        swot_matrix=SWOTMatrix(strengths=["Good"], weaknesses=[], opportunities=[], threats=[]),
        pricing_result=pricing,
        ml_prediction=ml_pred,
        ai_synthesis=ai_synth,
        machinery_schedule=machinery_sched.to_dict(),
        premise_type="owned",
        monthly_rent=0.0,
    )
    doc_loc_owned = next((d for d in dpr_owned.section_7_statutory_checklist if d.document_code == "DOC-LOC-03"), None)
    assert doc_loc_owned is not None
    assert "Patta / Khatiyan" in doc_loc_owned.document_name
    print("  [PASS] Owned Land: Patta/Khatiyan requirement in DOC-LOC-03 verified")

    # 3. Test Markdown and HTML output for BoQ and Land Note
    md = dpr_to_printable_markdown(dpr_rented)
    assert "Statutory Land Acquisition Compliance Note" in md
    assert "Itemized Plant, Machinery & Equipment Schedule" in md
    print("  [PASS] DPR Markdown output contains BoQ Table & Land Note")

    html = dpr_to_html(dpr_rented)
    assert "Statutory Land Acquisition Compliance Note" in html
    assert "Itemized Plant, Machinery & Equipment Schedule" in html
    print("  [PASS] DPR HTML output contains BoQ Table & Land Note")


if __name__ == "__main__":
    print("==================================================================")
    print("RUNNING THREE PILLARS RIGOROUS VERIFICATION SUITE")
    print("==================================================================")
    test_pillar1_smart_turnover()
    test_pillar1_dynamic_dscr_bounds()
    test_pillar1_quarterly_amortization()
    test_pillar2_infinite_machinery_balance()
    test_pillar3_land_and_operating_premises()
    print("\n==================================================================")
    print("ALL THREE PILLARS VERIFICATION TESTS PASSED SUCCESSFULLY (100%)!")
    print("==================================================================")
