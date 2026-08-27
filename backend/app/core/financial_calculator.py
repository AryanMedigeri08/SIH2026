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

    def to_dict(self) -> dict:
        return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in asdict(self).items()}


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

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("subsidy_grant_amount", "effective_interest_rate_pct", "total_interest_payable", "net_financial_benefit"):
            d[k] = round(d[k], 2)
        return d


def _load_schemes() -> list[dict]:
    with open(_SCHEMES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["schemes"]


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

        # --- compute subsidy grant amount ---
        slabs = s["subsidy_slabs"]
        subsidy = 0.0
        if "flat_pct" in slabs and slabs["flat_pct"] > 0:
            subsidy = project_cost * slabs["flat_pct"]
            cap = slabs.get("cap_amount", 0)
            if cap:
                subsidy = min(subsidy, cap)
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
            subsidy = project_cost * pct

        # --- effective interest rate (accounting for subvention / fixed rate schemes) ---
        if "fixed_interest_rate_pct" in s:
            eff_rate = s["fixed_interest_rate_pct"] * 100
        elif "effective_interest_rate_pct" in s:
            eff_rate = s["effective_interest_rate_pct"] * 100
        else:
            subvention = s.get("interest_subvention_pct", 0.0)
            eff_rate = max(default_bank_interest_rate_pct - (subvention * 100), 0.0)

        # --- loan principal financed under this scheme ---
        # Stand-Up India: composite loan coverage; others: project cost minus subsidy minus promoter contribution
        if "composite_loan_coverage_pct" in s:
            loan_principal = project_cost * s["composite_loan_coverage_pct"]
        else:
            promoter_pct = s["promoter_contribution_pct"].get(
                "special" if _category_is_special(promoter_category) else "general", 0.10
            )
            loan_principal = max(project_cost - subsidy - (project_cost * promoter_pct), 0.0)

        # --- total interest payable over tenure, via the same amortization engine ---
        total_interest = 0.0
        if loan_principal > 0:
            try:
                amort = emi_with_moratorium(loan_principal, eff_rate, tenure_years, moratorium_months)
                total_interest = amort.total_interest_payable
            except ValueError:
                total_interest = 0.0

        net_benefit = subsidy - total_interest

        results.append(
            SchemeRanking(
                rank=0,  # assigned after sort
                scheme_id=s["scheme_id"],
                full_name=s["full_name"],
                eligible=eligible,
                ineligibility_reason="; ".join(reasons) if reasons else None,
                subsidy_grant_amount=subsidy,
                effective_interest_rate_pct=eff_rate,
                total_interest_payable=total_interest,
                net_financial_benefit=net_benefit,
                collateral_free=(s.get("collateral_free_limit", 0) >= loan_principal) if loan_principal else True,
                notes=s.get("notes", ""),
                official_url=s.get("official_url"),
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
