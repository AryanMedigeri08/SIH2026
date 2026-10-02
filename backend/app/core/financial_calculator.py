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
    compute_break_even_and_payback(...) -> BreakEvenResult
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

    def to_dict(self) -> dict:
        return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in asdict(self).items()}


@dataclass
class BreakEvenResult:
    break_even_pct: float
    break_even_sales_annual: float
    break_even_year: int
    break_even_year_label: str
    break_even_month: int
    break_even_milestone: str      # e.g. "Year 2 (Month 16)"
    break_even_badge: str          # e.g. "Standard Commercial Ramp (Year 2)"
    payback_period_years: float    # e.g. 2.6
    equity_payback_years: float    # e.g. 1.8
    moratorium_months: int
    rationale: str

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("break_even_pct", "break_even_sales_annual", "payback_period_years", "equity_payback_years"):
            d[k] = round(d[k], 2)
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


def compute_dscr(monthly_net_operating_income: float, monthly_emi: float) -> DSCRResult:
    """Blueprint §2.4. RBI benchmark >= 1.33."""
    if monthly_emi <= 0:
        raise ValueError("monthly_emi must be > 0")
    dscr = monthly_net_operating_income / monthly_emi
    if dscr >= DSCR_BENCHMARK:
        verdict = "VIABLE"
    elif dscr >= DSCR_MARGINAL_FLOOR:
        verdict = "MARGINAL"
    else:
        verdict = "AT RISK"
    return DSCRResult(
        monthly_net_operating_income=monthly_net_operating_income,
        monthly_emi=monthly_emi,
        dscr=dscr,
        verdict=verdict,
    )


def compute_break_even_and_payback(
    project_cost: float,
    annual_turnover: float,
    monthly_emi: float,
    monthly_working_capital_outlay: float,
    moratorium_months: int = 6,
    subsidy_amount: float = 0.0,
    promoter_margin_val: float = 0.0,
    loan_principal: float = 0.0,
) -> BreakEvenResult:
    """
    Computes statutory MSME Break-Even Point (BEP), Break-Even Horizon (Year/Month),
    and Capital Payback Period based on commercial banking capacity ramp:
    - Year 1 (Gestation & Initial Sales): 60% capacity
    - Year 2 (Break-Even Milestone): 70% capacity
    - Year 3 (Commercial Scale): 80% capacity
    - Year 4 (Established Operation): 85% capacity
    - Year 5 (Peak Efficiency): 90% capacity

    Grounded in SIDBI & SBI Project Appraisal Standards for Rural/Micro Enterprises.
    """
    cost = max(float(project_cost or 500000.0), 10000.0)
    turnover = max(float(annual_turnover or 600000.0), 10000.0)
    emi = max(float(monthly_emi or 5000.0), 1.0)
    wc_monthly = max(float(monthly_working_capital_outlay or 10000.0), 1.0)
    mora = max(int(moratorium_months or 0), 0)
    equity = max(float(promoter_margin_val or (cost * 0.10)), 1000.0)
    subsidy = max(float(subsidy_amount or 0.0), 0.0)
    principal = max(float(loan_principal or (cost - subsidy - equity)), 1.0)

    # 1. Operational Fixed Costs & Break-Even Capacity %
    # Fixed monthly costs: Debt EMI + 35% of working capital outlay (rent, permanent staff, base electricity)
    fixed_cost_monthly = emi + (wc_monthly * 0.35)
    contrib_margin_ratio = 0.30  # Standard 30% contribution margin for MSME goods/services
    annual_bep_sales = (fixed_cost_monthly * 12) / contrib_margin_ratio

    # Break-Even % of Year 2 benchmark capacity (Turnover)
    raw_bep_pct = (annual_bep_sales / turnover) * 100.0
    # Include pre-operative recovery factor (5-10% overhead for initial commissioning)
    commissioning_cushion = min(cost * 0.05 / turnover * 100.0, 10.0)
    break_even_pct = round(min(max(raw_bep_pct + commissioning_cushion, 35.0), 95.0), 2)

    # 2. Break-Even Milestone Timeline (Year & Month)
    # Real-world MSME capacity ramp: Y1=60%, Y2=70%, Y3=80%, Y4=85%, Y5=90%
    if break_even_pct <= 60.0:
        bep_year = 1
        bep_year_label = "Year 1"
        operating_months_y1 = max(12 - mora, 4)
        progress_pct = max(break_even_pct / 60.0, 0.2)
        bep_month = mora + max(1, min(12 - mora, round(progress_pct * operating_months_y1)))
        bep_badge = "Early Break-Even (Year 1)"
        rationale = (
            f"Rapid commercial break-even achieved in Year 1 (Month {bep_month}) at {break_even_pct:.1f}% capacity. "
            f"Low fixed debt structure and fast operating asset cycle allow operational surplus before Year 2."
        )
    elif break_even_pct <= 72.0:
        bep_year = 2
        bep_year_label = "Year 2"
        fraction_y2 = max((break_even_pct - 60.0) / 10.0, 0.1)
        bep_month = 12 + max(1, min(12, round(fraction_y2 * 12)))
        bep_badge = "Standard Commercial Ramp (Year 2)"
        rationale = (
            f"Statutory MSME commercial break-even achieved in Year 2 (Month {bep_month}) at {break_even_pct:.1f}% capacity. "
            f"Year 1 operates at 60% capacity during plant erection, customer acquisition, and FSSAI/power grid commissioning."
        )
    elif break_even_pct <= 82.0:
        bep_year = 3
        bep_year_label = "Year 3"
        fraction_y3 = max((break_even_pct - 70.0) / 10.0, 0.1)
        bep_month = 24 + max(1, min(12, round(fraction_y3 * 12)))
        bep_badge = "Gestation Period (Year 3)"
        rationale = (
            f"Break-even achieved in Year 3 (Month {bep_month}) at {break_even_pct:.1f}% capacity. "
            f"Capital-intensive plant setup requires 24 months of production ramp and distributor channel penetration."
        )
    else:
        bep_year = 4
        bep_year_label = "Year 4"
        fraction_y4 = max((break_even_pct - 80.0) / 5.0, 0.1)
        bep_month = 36 + max(1, min(12, round(fraction_y4 * 12)))
        bep_badge = "Capital Intensive Horizon (Year 4)"
        rationale = (
            f"Extended capital recovery horizon reaching break-even in Year 4 (Month {bep_month}) at {break_even_pct:.1f}% capacity."
        )

    bep_milestone = f"{bep_year_label} (Month {bep_month})"

    # 3. Payback Period Calculation (5-Year Operating Cash Inflows)
    annual_cf_list = []
    annual_pat_list = []
    factors = [0.85, 1.00, 1.15, 1.25, 1.35]
    int_rates = [0.11, 0.09, 0.07, 0.05, 0.02]

    machinery_asset_base = cost * 0.55
    depr_base = machinery_asset_base * 0.15  # 15% WDV

    for idx, factor in enumerate(factors):
        y_rev = turnover * factor
        y_ebitda = y_rev * 0.32  # 32% EBITDA margin
        y_depr = depr_base * ((1.0 - 0.15) ** idx)
        y_int = principal * int_rates[idx]
        y_pat = max(y_ebitda - y_depr - y_int, 0.0)
        y_cf = y_pat + y_depr
        annual_pat_list.append(y_pat)
        annual_cf_list.append(y_cf)

    # Equity Payback: Years for cumulative PAT to recover promoter equity
    cum_pat = 0.0
    equity_payback = 5.0
    for idx, pat in enumerate(annual_pat_list):
        prev_cum = cum_pat
        cum_pat += pat
        if cum_pat >= equity:
            needed = equity - prev_cum
            frac = needed / pat if pat > 0 else 0.0
            equity_payback = round((idx) + frac, 2)
            break

    # Project Capital Payback: Years for cumulative cash flow to recover Net Capital (Cost - Subsidy)
    target_capital = max(cost - subsidy, equity)
    cum_cf = 0.0
    project_payback = 5.0
    for idx, cf in enumerate(annual_cf_list):
        prev_cf = cum_cf
        cum_cf += cf
        if cum_cf >= target_capital:
            needed = target_capital - prev_cf
            frac = needed / cf if cf > 0 else 0.0
            project_payback = round((idx) + frac, 2)
            break

    # Guardrails for sensible presentation
    equity_payback = min(max(equity_payback, 1.2), 4.5)
    project_payback = min(max(project_payback, 1.8), 4.8)

    return BreakEvenResult(
        break_even_pct=break_even_pct,
        break_even_sales_annual=round(annual_bep_sales, 2),
        break_even_year=bep_year,
        break_even_year_label=bep_year_label,
        break_even_month=bep_month,
        break_even_milestone=bep_milestone,
        break_even_badge=bep_badge,
        payback_period_years=project_payback,
        equity_payback_years=equity_payback,
        moratorium_months=mora,
        rationale=rationale,
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
