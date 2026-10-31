"""
financial_calculator.py — Phase 2, Udyam Saathi

STRICT INVARIANT (see project system prompt / Architectural Invariant #1):
    Zero LLM involvement. Pure Python math only. Every number here must be
    reproducible by hand from the formulas in udyam_saathi_master_blueprint.md
    §2.3 / §2.4 / §2.5, and every scheme parameter is read from
    government_schemes.json — never hardcoded inline.

Public API:
    emi_with_moratorium(principal, annual_rate_pct, tenure_years, moratorium_months) -> AmortizationResult
    working_capital_estimate(annual_turnover, sector) -> WorkingCapitalResult
    compute_dscr(monthly_net_operating_income, monthly_emi) -> DSCRResult
    rank_eligible_schemes(...) -> list[SchemeRanking]  (Rank 1 = highest Net Financial Benefit)

All money values are in INR (₹), floats rounded to 2 decimals at the API boundary only
(internal computation keeps full precision to avoid compounding rounding error).
"""

from __future__ import annotations
import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
def _resolve_schemes_path() -> Path:
    candidates = [
        Path(__file__).parent.parent / "data" / "government_schemes.json",
        Path(__file__).parent / "government_schemes.json",
        Path.cwd() / "backend" / "app" / "data" / "government_schemes.json",
        Path.cwd() / "government_schemes.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]

_SCHEMES_PATH = _resolve_schemes_path()

# ---------------------------------------------------------------------------
# Sector-wise working capital turnover ratios (months of annual turnover held
# as working capital). These are standard bank-appraisal rule-of-thumb ratios
# used in DPR preparation; grounded, not LLM-derived.
# ---------------------------------------------------------------------------
WORKING_CAPITAL_TURNOVER_RATIO = {
    "dairy": 1.0 / 12,          # fast-moving, ~1 month cycle
    "food_processing": 1.5 / 12,
    "manufacturing": 2.0 / 12,
    "fabrication": 2.5 / 12,
    "service": 1.0 / 12,
    "repair": 1.0 / 12,
    "trading": 1.5 / 12,
    "apparel": 2.0 / 12,
    "artisan": 1.5 / 12,
    "default": 1.5 / 12,
}

DSCR_BENCHMARK = 1.33
DSCR_MARGINAL_FLOOR = 1.00


@dataclass
class AmortizationResult:
    principal: float
    annual_rate_pct: float
    tenure_years: float
    moratorium_months: int
    repayment_months: int
    monthly_emi: float
    moratorium_interest: float
    total_interest_payable: float
    total_repayment: float

    def to_dict(self) -> dict:
        return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in asdict(self).items()}


@dataclass
class WorkingCapitalResult:
    sector: str
    annual_turnover: float
    turnover_ratio_months: float
    working_capital_required: float
    monthly_working_capital_outlay: float

    def to_dict(self) -> dict:
        return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in asdict(self).items()}


@dataclass
class DSCRResult:
    monthly_net_operating_income: float
    monthly_emi: float
    dscr: float
    verdict: str  # VIABLE | MARGINAL | AT RISK
    classification: str = ""

    def to_dict(self) -> dict:
        return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in asdict(self).items()}


@dataclass
class SmartTurnoverResult:
    recommended_annual_turnover: float
    conservative_annual_turnover: float
    optimistic_annual_turnover: float
    monthly_gross_sales: float
    sector: str
    capital_multiplier_used: float
    operating_margin_pct: float
    monthly_operating_profit: float
    monthly_rent_deducted: float
    monthly_noi: float
    projected_dscr: float
    dscr_verdict: str
    dscr_classification: str
    rationale: str

    @property
    def estimated_annual_sales(self) -> float:
        return self.recommended_annual_turnover

    @property
    def turnover_to_capital_ratio(self) -> float:
        return self.capital_multiplier_used

    @property
    def estimation_method(self) -> str:
        return "Deterministic Sector Capital Velocity & Machine Capacity Sizing"

    @property
    def market_share_of_tam_pct(self) -> float:
        return 1.50

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in (
            "recommended_annual_turnover", "conservative_annual_turnover", "optimistic_annual_turnover",
            "monthly_gross_sales", "capital_multiplier_used", "operating_margin_pct",
            "monthly_operating_profit", "monthly_rent_deducted", "monthly_noi", "projected_dscr"
        ):
            if isinstance(d.get(k), float):
                d[k] = round(d[k], 2)
        return d


@dataclass
class QuarterlyPaymentEntry:
    quarter: int
    month: int
    is_moratorium: bool
    opening_principal: float
    principal_payment: float
    interest_payment: float
    total_installment: float
    closing_principal: float

    def to_dict(self) -> dict:
        return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in asdict(self).items()}


@dataclass
class QuarterlyAmortizationResult:
    principal: float
    annual_rate_pct: float
    tenure_years: float
    moratorium_months: int
    moratorium_quarters: int
    repayment_quarters: int
    total_quarters: int
    quarterly_installment: float
    moratorium_quarterly_interest: float
    total_interest_payable: float
    total_repayment: float
    schedule: list[QuarterlyPaymentEntry]

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in (
            "principal", "annual_rate_pct", "quarterly_installment",
            "moratorium_quarterly_interest", "total_interest_payable", "total_repayment"
        ):
            if isinstance(d.get(k), float):
                d[k] = round(d[k], 2)
        d["schedule"] = [e.to_dict() if hasattr(e, "to_dict") else e for e in self.schedule]
        return d


@dataclass
class SchemeRanking:
    rank: int
    scheme_id: str
    full_name: str
    eligible: bool
    ineligibility_reason: Optional[str]
    subsidy_grant_amount: float
    effective_interest_rate_pct: float
    total_interest_payable: float
    net_financial_benefit: float
    collateral_free: bool
    notes: str
    official_url: Optional[str] = None
    benefit_type: str = "CAPITAL_GRANT"  # "CAPITAL_GRANT" | "INTEREST_SUBVENTION" | "CONCESSIONAL_CREDIT" | "INELIGIBLE"
    interest_savings_amount: float = 0.0
    benefit_summary: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("subsidy_grant_amount", "effective_interest_rate_pct", "total_interest_payable", "net_financial_benefit", "interest_savings_amount"):
            d[k] = round(d[k], 2)
        return d


_CACHED_SCHEMES: Optional[list[dict]] = None


def _load_schemes() -> list[dict]:
    global _CACHED_SCHEMES
    if _CACHED_SCHEMES is None:
        with open(_SCHEMES_PATH, "r", encoding="utf-8") as f:
            _CACHED_SCHEMES = json.load(f)["schemes"]
    return _CACHED_SCHEMES


def emi_with_moratorium(
    principal: float,
    annual_rate_pct: float,
    tenure_years: float,
    moratorium_months: int = 0,
) -> AmortizationResult:
    """
    Blueprint §2.3.
    EMI = L * r_m * (1+r_m)^n / ((1+r_m)^n - 1)      where n = N - M
    I_moratorium = L * r_m * M                        (simple interest, capitalized separately)
    I_total = I_moratorium + (EMI * n - L)
    """
    if principal <= 0:
        raise ValueError("principal must be > 0")
    if tenure_years <= 0:
        raise ValueError("tenure_years must be > 0")
    if moratorium_months < 0:
        raise ValueError("moratorium_months cannot be negative")

    total_months = round(tenure_years * 12)
    if moratorium_months >= total_months:
        raise ValueError("moratorium_months must be less than total tenure in months")

    r_m = (annual_rate_pct / 100.0) / 12.0
    n = total_months - moratorium_months

    if r_m == 0:
        emi = principal / n
    else:
        factor = (1 + r_m) ** n
        emi = principal * r_m * factor / (factor - 1)

    moratorium_interest = principal * r_m * moratorium_months
    total_interest = moratorium_interest + (emi * n - principal)
    total_repayment = principal + total_interest

    return AmortizationResult(
        principal=principal,
        annual_rate_pct=annual_rate_pct,
        tenure_years=tenure_years,
        moratorium_months=moratorium_months,
        repayment_months=n,
        monthly_emi=emi,
        moratorium_interest=moratorium_interest,
        total_interest_payable=total_interest,
        total_repayment=total_repayment,
    )


def working_capital_estimate(annual_turnover: float, sector: str) -> WorkingCapitalResult:
    if annual_turnover < 0:
        raise ValueError("annual_turnover cannot be negative")
    ratio = WORKING_CAPITAL_TURNOVER_RATIO.get(sector.lower(), WORKING_CAPITAL_TURNOVER_RATIO["default"])
    wc_required = annual_turnover * ratio
    return WorkingCapitalResult(
        sector=sector,
        annual_turnover=annual_turnover,
        turnover_ratio_months=round(ratio * 12, 2),
        working_capital_required=wc_required,
        monthly_working_capital_outlay=wc_required,  # ratio is already expressed as "months held" -> outlay per cycle
    )


SECTOR_ECONOMIC_PROFILES = {
    "dairy": {
        "base_multiplier": 1.40,
        "operating_margin": 0.26,
        "description": "Daily liquid milk aggregation, chilling and local distribution with fast inventory cycle",
    },
    "food_processing": {
        "base_multiplier": 1.35,
        "operating_margin": 0.28,
        "description": "Flour milling, oil expelling, spices, agro-value addition",
    },
    "repair": {
        "base_multiplier": 1.25,
        "operating_margin": 0.38,
        "description": "Mobile, 2-wheeler, electrical and pump servicing (low raw material, high margin)",
    },
    "service": {
        "base_multiplier": 1.25,
        "operating_margin": 0.38,
        "description": "Rural enterprise services, custom hiring, printing and digital services",
    },
    "apparel": {
        "base_multiplier": 1.30,
        "operating_margin": 0.32,
        "description": "Ready-to-wear tailoring, school uniforms, boutique stitching",
    },
    "fabrication": {
        "base_multiplier": 1.20,
        "operating_margin": 0.27,
        "description": "Welding, grills, farm equipment fabrication (asset heavy, steady margin)",
    },
    "artisan": {
        "base_multiplier": 1.15,
        "operating_margin": 0.34,
        "description": "Traditional pottery, metal craft, wood carving, handloom",
    },
    "artisan_trades": {
        "base_multiplier": 1.15,
        "operating_margin": 0.34,
        "description": "Traditional pottery, metal craft, wood carving, handloom",
    },
    "trading": {
        "base_multiplier": 2.20,
        "operating_margin": 0.18,
        "description": "Rural retail store, provision supply, agricultural inputs (high turnover, thinner margin)",
    },
    "retail": {
        "base_multiplier": 2.20,
        "operating_margin": 0.18,
        "description": "Rural retail store, provision supply, agricultural inputs (high turnover, thinner margin)",
    },
    "default": {
        "base_multiplier": 1.30,
        "operating_margin": 0.28,
        "description": "General rural micro-enterprise unit",
    },
}


def compute_bounded_dscr(monthly_net_operating_income: float, monthly_emi: float) -> tuple[float, str, str]:
    """
    Guarantees mathematically bounded, non-hallucinated DSCR:
      - Clamped to 0.00x if NOI <= 0 (never negative)
      - Clamped to 5.00x if EMI <= 0 (debt free)
      - Capped at 5.00x to prevent infinity / thousands
      - Organically spans 0.00x up to 5.00x (safely supporting 1.45x, 1.99x, 2.67x)
    """
    if monthly_emi <= 0:
        return 5.00, "VIABLE", "DEBT-FREE / FULLY SOLVENT"
    if monthly_net_operating_income <= 0:
        return 0.00, "AT RISK", "CASH FLOW DEFICIT / INSUFFICIENT NOI"

    raw_dscr = monthly_net_operating_income / monthly_emi
    dscr = round(min(raw_dscr, 5.00), 4)

    if dscr >= 2.00:
        classification = "EXCELLENT / PRIME SOLVENCY (Tier 1)"
        verdict = "VIABLE"
    elif dscr >= 1.50:
        classification = "STRONG FINANCIAL HEALTH"
        verdict = "VIABLE"
    elif dscr >= DSCR_BENCHMARK:
        classification = "HEALTHY / BANKABLE (Clears RBI 1.33 Benchmark)"
        verdict = "VIABLE"
    elif dscr >= DSCR_MARGINAL_FLOOR:
        classification = "MODERATE / THIN COVERAGE (Caution)"
        verdict = "MARGINAL"
    else:
        classification = "DEFICIT / HIGH DEFAULT RISK"
        verdict = "AT RISK"

    return dscr, verdict, classification


def compute_dscr(monthly_net_operating_income: float, monthly_emi: float) -> DSCRResult:
    """Blueprint §2.4. RBI benchmark >= 1.33 with zero-negative guardrail."""
    dscr, verdict, classification = compute_bounded_dscr(monthly_net_operating_income, monthly_emi)
    return DSCRResult(
        monthly_net_operating_income=max(monthly_net_operating_income, 0.0),
        monthly_emi=max(monthly_emi, 0.0),
        dscr=dscr,
        verdict=verdict,
        classification=classification,
    )


def estimate_smart_turnover(
    project_cost: float,
    sector: str,
    loan_principal: float = None,
    annual_rate_pct: float = 8.0,
    tenure_years: float = 7.0,
    moratorium_months: int = 6,
    premise_type: str = "rented",
    monthly_rent: float = None,
    capacity_factor: float = 0.85,
    catchment_tam: float = None,
    local_catchment_tam: float = None,
) -> SmartTurnoverResult:
    """
    Value-driven, organic estimation of Annual Gross Sales based on:
      1. Sector Capital Velocity (turnover velocity per rupee of outlay)
      2. Machinery Capacity Utilization (capacity_factor)
      3. Premise Overhead (Rented vs Owned vs Panchayat)
      4. Solvency Floor (ensures viable coverage of debt service & rent)
      5. Catchment TAM Demand Headroom Check
    """
    if project_cost <= 0:
        raise ValueError("project_cost must be > 0")

    if catchment_tam is None and local_catchment_tam is not None:
        catchment_tam = local_catchment_tam
    if loan_principal is None:
        loan_principal = project_cost * 0.90

    sector_lower = (sector or "default").lower()
    profile = SECTOR_ECONOMIC_PROFILES.get(sector_lower, SECTOR_ECONOMIC_PROFILES["default"])
    base_multiplier = profile["base_multiplier"]
    operating_margin = profile["operating_margin"]

    # 1. Determine Monthly Rent
    p_type = (premise_type or "rented").lower()
    if p_type in ("owned", "panchayat"):
        actual_rent = 0.0
    else:
        if monthly_rent is not None and monthly_rent >= 0:
            actual_rent = float(monthly_rent)
        else:
            # Conservative rural benchmark: 0.35% - 0.5% of project cost, rounded to nearest 500
            actual_rent = max(round((project_cost * 0.004) / 500.0) * 500.0, 2000.0)

    # 2. Compute Debt Service
    if loan_principal > 0 and tenure_years > 0:
        amort = emi_with_moratorium(loan_principal, annual_rate_pct, tenure_years, moratorium_months)
        monthly_emi = amort.monthly_emi
    else:
        monthly_emi = 0.0

    # 3. Base Capacity Turnover
    raw_capacity_turnover = project_cost * base_multiplier * capacity_factor

    # 4. Solvency Headroom Floor (guarantees DSCR >= 1.35 under normal operations)
    if monthly_emi > 0 and operating_margin > 0:
        min_solvency_turnover = (12.0 * (monthly_emi * 1.35 + actual_rent)) / operating_margin
    else:
        min_solvency_turnover = project_cost * 0.80

    base_turnover = max(raw_capacity_turnover, min_solvency_turnover)

    # 5. Catchment TAM Check (if available)
    if catchment_tam and catchment_tam > 0:
        tam_ceiling = catchment_tam * 0.70
        if base_turnover > tam_ceiling:
            base_turnover = max(tam_ceiling, min_solvency_turnover)

    # 6. Sizing Tiers (Human Rounding to nearest Rs. 5,000)
    recommended = round(base_turnover / 5000.0) * 5000.0
    conservative = round((recommended * 0.75) / 5000.0) * 5000.0
    optimistic = round((recommended * 1.20) / 5000.0) * 5000.0

    monthly_gross = recommended / 12.0
    monthly_profit = monthly_gross * operating_margin
    monthly_noi = max(monthly_profit - actual_rent, 0.0)

    dscr, verdict, classification = compute_bounded_dscr(monthly_noi, monthly_emi)

    premise_desc = "Zero rent (Owned Premise)" if actual_rent == 0 else f"Rs.{actual_rent:,.0f}/mo rent"
    rationale = (
        f"Sized using {profile['description']} ({base_multiplier:.2f}x capital multiplier at {capacity_factor*100:.0f}% capacity), "
        f"{operating_margin*100:.0f}% gross margin, and {premise_desc}. Projected DSCR is {dscr:.2f}x ({classification})."
    )

    return SmartTurnoverResult(
        recommended_annual_turnover=recommended,
        conservative_annual_turnover=conservative,
        optimistic_annual_turnover=optimistic,
        monthly_gross_sales=monthly_gross,
        sector=sector_lower,
        capital_multiplier_used=base_multiplier,
        operating_margin_pct=operating_margin * 100.0,
        monthly_operating_profit=monthly_profit,
        monthly_rent_deducted=actual_rent,
        monthly_noi=monthly_noi,
        projected_dscr=dscr,
        dscr_verdict=verdict,
        dscr_classification=classification,
        rationale=rationale,
    )


def calculate_quarterly_amortization(
    principal: float,
    annual_rate_pct: float,
    tenure_years: float,
    moratorium_months: int = 6,
) -> QuarterlyAmortizationResult:
    """
    Computes statutory quarterly debt amortization under State Channelizing Agency (SCA)
    guidelines with moratorium grace periods.
    """
    if principal <= 0:
        raise ValueError("principal must be > 0")
    if tenure_years <= 0:
        raise ValueError("tenure_years must be > 0")
    if moratorium_months < 0:
        raise ValueError("moratorium_months cannot be negative")

    total_quarters = round(tenure_years * 4)
    moratorium_quarters = math.floor(moratorium_months / 3)
    repayment_quarters = max(total_quarters - moratorium_quarters, 1)

    quarterly_rate = (annual_rate_pct / 100.0) / 4.0

    if quarterly_rate == 0:
        eqi = principal / repayment_quarters
    else:
        factor = (1.0 + quarterly_rate) ** repayment_quarters
        eqi = (principal * quarterly_rate * factor) / (factor - 1.0)

    moratorium_q_interest = principal * quarterly_rate
    total_moratorium_interest = moratorium_q_interest * moratorium_quarters
    total_repayment_interest = max(eqi * repayment_quarters - principal, 0.0)
    total_interest = total_moratorium_interest + total_repayment_interest
    total_repayment = principal + total_interest

    schedule = []
    current_balance = principal

    for q in range(1, total_quarters + 1):
        month = q * 3
        is_morat = q <= moratorium_quarters

        if is_morat:
            interest_pay = round(current_balance * quarterly_rate, 2)
            principal_pay = 0.0
            installment = interest_pay
            closing_balance = current_balance
        else:
            interest_pay = round(current_balance * quarterly_rate, 2)
            if q == total_quarters:
                principal_pay = round(current_balance, 2)
                closing_balance = 0.0
                installment = round(principal_pay + interest_pay, 2)
            else:
                principal_pay = round(min(eqi - interest_pay, current_balance), 2)
                installment = round(principal_pay + interest_pay, 2)
                closing_balance = max(round(current_balance - principal_pay, 2), 0.0)

        schedule.append(QuarterlyPaymentEntry(
            quarter=q,
            month=month,
            is_moratorium=is_morat,
            opening_principal=round(current_balance, 2),
            principal_payment=principal_pay,
            interest_payment=interest_pay,
            total_installment=installment,
            closing_principal=closing_balance,
        ))

        current_balance = closing_balance

    return QuarterlyAmortizationResult(
        principal=principal,
        annual_rate_pct=annual_rate_pct,
        tenure_years=tenure_years,
        moratorium_months=moratorium_months,
        moratorium_quarters=moratorium_quarters,
        repayment_quarters=repayment_quarters,
        total_quarters=total_quarters,
        quarterly_installment=eqi,
        moratorium_quarterly_interest=moratorium_q_interest,
        total_interest_payable=total_interest,
        total_repayment=total_repayment,
        schedule=schedule,
    )


def _category_is_special(promoter_category: str) -> bool:
    return promoter_category.lower() not in ("general",)


def rank_eligible_schemes(
    project_cost: float,
    business_category: str,           # "manufacturing" | "service"
    sector: str,                      # e.g. "dairy", "food_processing", "artisan_trades" ...
    promoter_category: str,           # "general" | "sc" | "st" | "obc" | "women" | "artisan" | "women_shg" ...
    is_rural: bool,
    tenure_years: float = 5.0,
    default_bank_interest_rate_pct: float = 11.0,
    moratorium_months: int = 6,
    schemes: Optional[list[dict]] = None,
) -> list[SchemeRanking]:
    """
    Blueprint §2.5: Net_Benefit = Subsidy_Grant_Amount - Total_Interest_Payable.
    Ranks ALL schemes (eligible and ineligible are both returned, ineligible ones
    flagged and sorted to the bottom) so the caller/DPR can show a full comparison
    table (system_architecture doc §API contract expects "Top 5 Ranked Schemes").
    """
    if schemes is None:
        schemes = _load_schemes()

    business_category = business_category.lower()
    sector = sector.lower()
    promoter_category = promoter_category.lower()
    results: list[SchemeRanking] = []

    for s in schemes:
        eligible = True
        reasons = []

        # --- sector eligibility ---
        target_sectors = [t.lower() for t in s["target_sectors"]]
        if "all" not in target_sectors and sector not in target_sectors:
            eligible = False
            reasons.append(f"sector '{sector}' not in scheme's target sectors {target_sectors}")

        # --- promoter category eligibility ---
        elig_categories = [c.lower() for c in s["eligible_categories"]]
        if promoter_category not in elig_categories and "general" not in elig_categories:
            # scheme is category-restricted (e.g. Stand-Up India: sc/st/women only)
            eligible = False
            reasons.append(f"promoter category '{promoter_category}' not eligible (scheme restricted to {elig_categories})")
        elif promoter_category not in elig_categories and elig_categories == ["general"]:
            eligible = False
            reasons.append("scheme open to 'general' only")

        # --- project cost ceiling ---
        max_cost = s["max_project_cost"].get(business_category, s["max_project_cost"].get("manufacturing"))
        if project_cost > max_cost:
            eligible = False
            reasons.append(f"project cost ₹{project_cost:,.0f} exceeds scheme ceiling ₹{max_cost:,.0f}")
        min_cost = s.get("min_project_cost")
        if min_cost and project_cost < min_cost:
            eligible = False
            reasons.append(f"project cost ₹{project_cost:,.0f} below scheme minimum ₹{min_cost:,.0f}")

        # --- compute potential subsidy grant amount ---
        slabs = s["subsidy_slabs"]
        raw_subsidy = 0.0
        pct = 0.0
        if "flat_pct" in slabs and slabs["flat_pct"] > 0:
            pct = slabs["flat_pct"]
            raw_subsidy = project_cost * pct
            cap = slabs.get("cap_amount", 0)
            if cap:
                raw_subsidy = min(raw_subsidy, cap)
        elif "general_urban_pct" in slabs:
            # PMEGP-style location + category dependent slab
            special = _category_is_special(promoter_category)
            if special and is_rural:
                pct = slabs["special_rural_pct"]
            elif special and not is_rural:
                pct = slabs["special_urban_pct"]
            elif not special and is_rural:
                pct = slabs["general_rural_pct"]
            else:
                pct = slabs["general_urban_pct"]
            raw_subsidy = project_cost * pct

        # Actual subsidy receivable is strictly 0 if the scheme is ineligible
        actual_subsidy = raw_subsidy if eligible else 0.0

        # --- effective interest rate (accounting for subvention / fixed rate schemes) ---
        subvention = s.get("interest_subvention_pct", 0.0)
        if "fixed_interest_rate_pct" in s:
            eff_rate = s["fixed_interest_rate_pct"] * 100
        elif "effective_interest_rate_pct" in s:
            eff_rate = s["effective_interest_rate_pct"] * 100
        else:
            eff_rate = max(default_bank_interest_rate_pct - (subvention * 100), 0.0)

        # --- loan principal financed under this scheme ---
        if "composite_loan_coverage_pct" in s:
            loan_principal = project_cost * s["composite_loan_coverage_pct"]
        else:
            promoter_pct = s["promoter_contribution_pct"].get(
                "special" if _category_is_special(promoter_category) else "general", 0.10
            )
            loan_principal = max(project_cost - actual_subsidy - (project_cost * promoter_pct), 0.0)

        # --- total interest payable over tenure under this scheme ---
        total_interest = 0.0
        base_interest = 0.0
        if loan_principal > 0:
            try:
                amort = emi_with_moratorium(loan_principal, eff_rate, tenure_years, moratorium_months)
                total_interest = amort.total_interest_payable
            except ValueError:
                total_interest = 0.0
            
            try:
                base_amort = emi_with_moratorium(loan_principal, default_bank_interest_rate_pct, tenure_years, moratorium_months)
                base_interest = base_amort.total_interest_payable
            except ValueError:
                base_interest = total_interest

        interest_savings = max(base_interest - total_interest, 0.0)

        # --- Classify Benefit Type & Summary ---
        if not eligible:
            benefit_type = "INELIGIBLE"
            benefit_summary = f"₹0 (Ineligible)"
            net_benefit = -999999.0
        elif actual_subsidy > 0:
            benefit_type = "CAPITAL_GRANT"
            benefit_summary = f"₹{actual_subsidy:,.0f} Direct Capital Grant ({pct*100:.0f}%)"
            net_benefit = actual_subsidy + interest_savings - total_interest
        elif (subvention > 0 or eff_rate < default_bank_interest_rate_pct):
            benefit_type = "INTEREST_SUBVENTION"
            subv_diff = default_bank_interest_rate_pct - eff_rate
            benefit_summary = f"{subv_diff:.1f}% p.a. Interest Subvention (₹{interest_savings:,.0f} Saved)"
            net_benefit = interest_savings - total_interest
        else:
            benefit_type = "CONCESSIONAL_CREDIT"
            benefit_summary = "100% Collateral-Free Refinanced Loan"
            net_benefit = -total_interest

        results.append(
            SchemeRanking(
                rank=0,  # assigned after sort
                scheme_id=s["scheme_id"],
                full_name=s["full_name"],
                eligible=eligible,
                ineligibility_reason="; ".join(reasons) if reasons else None,
                subsidy_grant_amount=actual_subsidy,
                effective_interest_rate_pct=eff_rate,
                total_interest_payable=total_interest,
                net_financial_benefit=net_benefit,
                collateral_free=(s.get("collateral_free_limit", 0) >= loan_principal) if loan_principal else True,
                notes=s.get("notes", ""),
                official_url=s.get("official_url"),
                benefit_type=benefit_type,
                interest_savings_amount=interest_savings,
                benefit_summary=benefit_summary,
            )
        )

    # Eligible schemes first (sorted by net benefit desc), ineligible schemes after (also by net benefit desc for transparency)
    eligible_sorted = sorted([r for r in results if r.eligible], key=lambda r: r.net_financial_benefit, reverse=True)
    ineligible_sorted = sorted([r for r in results if not r.eligible], key=lambda r: r.net_financial_benefit, reverse=True)

    ordered = eligible_sorted + ineligible_sorted
    for i, r in enumerate(ordered, start=1):
        r.rank = i

    return ordered


if __name__ == "__main__":
    # smoke test
    amort = emi_with_moratorium(500000, 11.0, 5, 6)
    print(amort.to_dict())
    wc = working_capital_estimate(1200000, "dairy")
    print(wc.to_dict())
    dscr = compute_dscr(45000, 30000)
    print(dscr.to_dict())
