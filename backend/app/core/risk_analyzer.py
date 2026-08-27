"""
risk_analyzer.py — Phase 2, Udyam Saathi

Blueprint §5 (DPR section 6) / master_implementation_plan.md Phase 2 Step 2.4.
8-point quantified risk engine. Every risk score is derived from a concrete
upstream number (DSCR, CPI inflation, infra score, weather score, etc.) —
never an LLM guess. Each risk carries an operational mitigation with a rupee
buffer wherever one is computable.

Risk score scale: 0 (negligible) - 10 (severe). Overall verdict bucketed the
same way DSCR is bucketed, for pitch-deck consistency.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class RiskPoint:
    risk_id: str
    title: str
    score: float             # 0-10
    severity: str             # LOW | MODERATE | HIGH | SEVERE
    basis: str                 # which upstream number this is grounded in
    mitigation: str
    rupee_buffer: Optional[float] = None
    data_source: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["score"] = round(d["score"], 2)
        if d["rupee_buffer"] is not None:
            d["rupee_buffer"] = round(d["rupee_buffer"], 2)
        return d


def _bucket(score: float) -> str:
    if score < 2.5:
        return "LOW"
    if score < 5.0:
        return "MODERATE"
    if score < 7.5:
        return "HIGH"
    return "SEVERE"


def build_risk_matrix(
    dscr: float,
    monthly_emi: float,
    projected_annual_tam: float,
    annual_turnover_estimate: float,
    competition_intensity_normalized: float,   # 0-1, from market_analyzer x8
    infrastructure_score: float,                # 0-10, from amenities (x5)
    cpi_inflation_pct: float,                    # x6
    weather_risk_score: float,                   # 0-1, x9
    working_capital_months_buffer: float,        # x7
    subsidy_coverage_ratio: float,                # x1
    is_seasonal_sector: bool = False,
) -> list[RiskPoint]:

    risks: list[RiskPoint] = []

    # 1. Debt Servicing Risk (grounded in DSCR)
    if dscr >= 1.33:
        score = max(0.0, 3.0 - (dscr - 1.33) * 2)
    elif dscr >= 1.0:
        score = 5.0 + (1.33 - dscr) * 5
    else:
        score = 8.0 + min((1.0 - dscr) * 5, 2.0)
    buffer = monthly_emi * 3  # 3-month EMI reserve, standard bank appraisal buffer
    risks.append(RiskPoint(
        risk_id="R1", title="Debt Servicing (DSCR) Risk", score=score, severity=_bucket(score),
        basis=f"DSCR = {dscr:.2f} (RBI benchmark >= 1.33)",
        mitigation=f"Maintain a 3-month EMI contingency reserve of ₹{buffer:,.0f} before disbursal; "
                    f"consider extending tenure or applying moratorium if DSCR < 1.33.",
        rupee_buffer=buffer, data_source="financial_calculator.py",
    ))

    # 2. Market Demand Shortfall Risk (TAM vs projected turnover): the closer the
    # promoter's turnover assumption sits to 100% of catchment TAM, the riskier
    # the assumption (little headroom); beyond 120% of TAM it's flagged as an
    # implausible/aggressive projection rather than scored as maximal risk.
    demand_ratio = annual_turnover_estimate / projected_annual_tam if projected_annual_tam > 0 else 1.0
    score = 10.0 * min(demand_ratio, 1.0) if demand_ratio <= 1.2 else 8.0
    risks.append(RiskPoint(
        risk_id="R2", title="Market Demand Saturation Risk", score=score, severity=_bucket(score),
        basis=f"Projected turnover ₹{annual_turnover_estimate:,.0f} vs Annual TAM ₹{projected_annual_tam:,.0f} "
              f"({demand_ratio*100:.1f}% of catchment TAM)",
        mitigation="If turnover assumption exceeds 60% of catchment TAM, diversify product mix or expand "
                    "catchment radius before scaling capacity further.",
        data_source="market_analyzer.py",
    ))

    # 3. Competition Saturation Risk
    score = competition_intensity_normalized * 10
    risks.append(RiskPoint(
        risk_id="R3", title="Local Competition Saturation Risk", score=score, severity=_bucket(score),
        basis=f"Normalized competition intensity = {competition_intensity_normalized:.2f} (0=none, 1=saturated)",
        mitigation="Differentiate via pricing, quality certification (e.g. FSSAI for food units), or "
                    "underserved sub-catchment targeting.",
        data_source="market_analyzer.py (MSME + demographics)",
    ))

    # 4. Infrastructure Readiness Risk (inverse of infra score, x5 is 0-10)
    score = max(0.0, 10 - infrastructure_score)
    gap_buffer = score * 5000  # rough ₹5k per missing infra point as a contingency logistics buffer
    risks.append(RiskPoint(
        risk_id="R4", title="Infrastructure Readiness Risk", score=score, severity=_bucket(score),
        basis=f"Infrastructure score = {infrastructure_score:.1f}/10 (road+haat+power+bank+PDS composite)",
        mitigation=f"Budget an additional ₹{gap_buffer:,.0f} logistics/backup-power contingency if score < 7; "
                    f"prioritize sites with paved road + grid power access.",
        rupee_buffer=gap_buffer if gap_buffer > 0 else None,
        data_source="village_amenities_cache (data.gov.in)",
    ))

    # 5. Weather / Climate Risk
    score = weather_risk_score * 10
    risks.append(RiskPoint(
        risk_id="R5", title="Weather & Seasonal Disruption Risk", score=score, severity=_bucket(score),
        basis=f"Weather risk score = {weather_risk_score:.2f} (0-1, heavy-rain-day fraction)",
        mitigation="Build a monsoon-season buffer stock / covered storage; for weather-exposed sectors "
                    "(dairy, agri-processing) budget 1 extra month of working capital during peak monsoon.",
        data_source="Open-Meteo (lat/long keyed, see Phase 1 handoff)",
    ))

    # 6. Inflation / CPI Risk
    score = min(max(cpi_inflation_pct, 0) / 2.0, 10.0)  # 20% inflation -> score 10
    risks.append(RiskPoint(
        risk_id="R6", title="Input Cost Inflation Risk", score=score, severity=_bucket(score),
        basis=f"State rural CPI inflation = {cpi_inflation_pct:.2f}%",
        mitigation="Re-price product/service annually in line with CPI (see pricing_engine.py); "
                    "lock raw-material supplier contracts for 6-12 months where feasible.",
        data_source="cpi_data (MoSPI)",
    ))

    # 7. Scheme / Subsidy Dependency Risk
    score = subsidy_coverage_ratio * 10  # higher reliance on subsidy = higher risk if disbursal is delayed
    risks.append(RiskPoint(
        risk_id="R7", title="Subsidy Disbursal Dependency Risk", score=score, severity=_bucket(score),
        basis=f"Subsidy coverage ratio = {subsidy_coverage_ratio:.2f} (subsidy / total project cost)",
        mitigation="Do not sequence machinery procurement solely on subsidy receipt; arrange bridge "
                    "financing or phased procurement so operations aren't stalled by disbursal delays.",
        data_source="government_schemes.json",
    ))

    # 8. Working Capital Buffer / Liquidity Risk
    score = max(0.0, 10 - working_capital_months_buffer * (10 / 6))  # 6 months buffer = score 0
    risks.append(RiskPoint(
        risk_id="R8", title="Working Capital Liquidity Risk", score=score, severity=_bucket(score),
        basis=f"Working capital buffer = {working_capital_months_buffer:.1f} months of promoter margin coverage",
        mitigation="Target a minimum 3-month working capital buffer before launch; renegotiate supplier "
                    "credit terms (30-45 days) to reduce cash-cycle pressure.",
        data_source="financial_calculator.py",
    ))

    if is_seasonal_sector:
        for r in risks:
            if r.risk_id in ("R2", "R5"):
                r.score = min(r.score * 1.15, 10.0)
                r.severity = _bucket(r.score)

    return risks


def overall_risk_verdict(risks: list[RiskPoint]) -> dict:
    avg_score = sum(r.score for r in risks) / len(risks) if risks else 0.0
    severe_count = sum(1 for r in risks if r.severity in ("HIGH", "SEVERE"))
    return {
        "average_risk_score": round(avg_score, 2),
        "overall_severity": _bucket(avg_score),
        "high_or_severe_risk_count": severe_count,
        "total_risk_points": len(risks),
    }


if __name__ == "__main__":
    risks = build_risk_matrix(
        dscr=1.45, monthly_emi=9500, projected_annual_tam=1500000, annual_turnover_estimate=600000,
        competition_intensity_normalized=0.3, infrastructure_score=6.5, cpi_inflation_pct=5.2,
        weather_risk_score=0.2, working_capital_months_buffer=2.5, subsidy_coverage_ratio=0.35,
    )
    for r in risks:
        print(r.to_dict())
    print(overall_risk_verdict(risks))
