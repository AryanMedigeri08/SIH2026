"""
swot_analyzer.py — Grounded SWOT Analysis Engine with Deterministic Fallback.
Udyam Saathi (SIH 2026 PS 26091).

Builds a grounded SWOT matrix:
- Primary Mode: LLM-synthesized via Groq with structured data sources and language awareness.
- Fallback Mode: 100% deterministic rules mapped from concrete upstream financial,
  infrastructure, demographic, inflation, weather, and ML signals.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass
class SWOTItem:
    text: str
    data_source: str = "Market Feasibility Signal"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class SWOTMatrix:
    strengths: list[SWOTItem]
    weaknesses: list[SWOTItem]
    opportunities: list[SWOTItem]
    threats: list[SWOTItem]

    def to_dict(self) -> dict[str, list[dict[str, str]]]:
        return {
            "strengths": [i.to_dict() for i in self.strengths],
            "weaknesses": [i.to_dict() for i in self.weaknesses],
            "opportunities": [i.to_dict() for i in self.opportunities],
            "threats": [i.to_dict() for i in self.threats],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SWOTMatrix:
        def _parse_list(items: Any, default_src: str) -> list[SWOTItem]:
            if not isinstance(items, list):
                return []
            result: list[SWOTItem] = []
            for item in items:
                if isinstance(item, dict):
                    text = str(item.get("text", "")).strip()
                    src = str(item.get("data_source", default_src)).strip()
                    if text:
                        result.append(SWOTItem(text=text, data_source=src))
                elif isinstance(item, str) and item.strip():
                    result.append(SWOTItem(text=item.strip(), data_source=default_src))
                elif hasattr(item, "text"):
                    result.append(SWOTItem(text=getattr(item, "text", ""), data_source=getattr(item, "data_source", default_src)))
            return result

        return cls(
            strengths=_parse_list(data.get("strengths"), "RBI Banking Guidelines & Amortization Ratios"),
            weaknesses=_parse_list(data.get("weaknesses"), "Data.gov.in District Amenities Registry"),
            opportunities=_parse_list(data.get("opportunities"), "Census 2011 Catchment Demographics"),
            threats=_parse_list(data.get("threats"), "MoSPI CPI Inflation & Weather Telemetry"),
        )


def build_swot(
    dscr: float,
    subsidy_grant_amount: float,
    subsidy_scheme_name: str,
    project_cost: float,
    infrastructure_score: float,
    projected_annual_tam: float,
    annual_turnover_estimate: float,
    competition_intensity_normalized: float,
    msme_density_per_10k: float,
    cpi_inflation_pct: float,
    weather_risk_score: float,
    ml_viability_verdict: str,       # SUITABLE | CAUTION | RECONSIDER
    ml_confidence_pct: float,
) -> SWOTMatrix:
    """
    Deterministic rule-based SWOT generator. Serves as ground-truth baseline
    and offline fallback whenever LLM synthesis is unavailable.
    """
    strengths: list[SWOTItem] = []
    weaknesses: list[SWOTItem] = []
    opportunities: list[SWOTItem] = []
    threats: list[SWOTItem] = []

    # --- Strengths ---
    if dscr >= 1.33:
        strengths.append(SWOTItem(
            f"Strong debt-servicing capacity: DSCR of {dscr:.2f} clears the RBI benchmark of 1.33.",
            "RBI Prudential Banking Guidelines & Amortization Ratios",
        ))
    if subsidy_grant_amount > 0:
        cost_denom = project_cost if project_cost > 0 else 1.0
        strengths.append(SWOTItem(
            f"₹{subsidy_grant_amount:,.0f} capital subsidy secured under {subsidy_scheme_name} "
            f"({subsidy_grant_amount/cost_denom*100:.1f}% of project cost), reducing effective debt burden.",
            "Statutory MSME Scheme Guidelines (government_schemes.json)",
        ))
    if infrastructure_score >= 7.0:
        strengths.append(SWOTItem(
            f"High site infrastructure readiness (score {infrastructure_score:.1f}/10): road, power, and "
            f"market access already in place, lowering setup risk.",
            "Data.gov.in 613 District Resource Registry (district_resources.json)",
        ))
    if ml_viability_verdict == "SUITABLE":
        strengths.append(SWOTItem(
            f"ML viability classifier rates this enterprise SUITABLE with {ml_confidence_pct:.1f}% confidence "
            f"across 10 weighted factors.",
            "Supervised XGBoost Viability Classifier (viability_xgb.joblib)",
        ))

    # Fallback strength if empty
    if not strengths:
        strengths.append(SWOTItem(
            f"Active enterprise project with ₹{project_cost:,.0f} capital outlay under {subsidy_scheme_name}.",
            "Enterprise Capital Outlay Plan",
        ))

    # --- Weaknesses ---
    if dscr < 1.33:
        weaknesses.append(SWOTItem(
            f"DSCR of {dscr:.2f} is below the RBI-preferred 1.33 threshold, indicating thin debt-servicing headroom.",
            "RBI Prudential Banking Guidelines & Amortization Ratios",
        ))
    if ml_viability_verdict == "CAUTION":
        weaknesses.append(SWOTItem(
            f"ML viability classifier rates this enterprise CAUTION with {ml_confidence_pct:.1f}% confidence, indicating moderate sensitivity to operating variables.",
            "Supervised XGBoost Viability Classifier (viability_xgb.joblib)",
        ))
    if infrastructure_score < 5.0:
        weaknesses.append(SWOTItem(
            f"Low site infrastructure readiness (score {infrastructure_score:.1f}/10): expect added logistics "
            f"or backup-power cost.",
            "Data.gov.in 613 District Resource Registry (district_resources.json)",
        ))
    if msme_density_per_10k < 5.0:
        weaknesses.append(SWOTItem(
            f"Thin local MSME ecosystem ({msme_density_per_10k:.2f} registered enterprises per 10,000 population) "
            f"may mean limited ancillary supplier/service support nearby.",
            "Ministry of MSME District Enterprise Registry (msme_district)",
        ))
    if not weaknesses:
        weaknesses.append(SWOTItem(
            "No material weaknesses flagged against current thresholds; monitor DSCR and infrastructure "
            "readiness as project scales.",
            "RBI Banking Guidelines & District Amenities Registry",
        ))

    # --- Opportunities ---
    demand_headroom = max(projected_annual_tam - annual_turnover_estimate, 0)
    if demand_headroom > 0:
        opportunities.append(SWOTItem(
            f"₹{demand_headroom:,.0f}/year of unmet catchment demand (TAM ₹{projected_annual_tam:,.0f} vs "
            f"projected turnover ₹{annual_turnover_estimate:,.0f}) available for scale-up.",
            "Census 2011 Catchment TAM & Household Demographics (census_raw)",
        ))
    if competition_intensity_normalized < 0.4:
        opportunities.append(SWOTItem(
            f"Low competitive saturation (normalized intensity {competition_intensity_normalized:.2f}/1.0) "
            f"leaves room for first-mover / early-market positioning.",
            "Census 2011 Catchment TAM & Household Demographics (census_raw)",
        ))
    opportunities.append(SWOTItem(
        "Additional scheme stacking (e.g. state-level top-up subsidies) may further reduce effective "
        "capital cost — recommend checking state MSME department for local top-ups.",
        "National & State MSME Schemes (government_schemes.json)",
    ))

    # --- Threats ---
    if cpi_inflation_pct > 6.0:
        threats.append(SWOTItem(
            f"Elevated rural CPI inflation ({cpi_inflation_pct:.2f}%) may erode margins unless prices are "
            f"re-adjusted annually.",
            "MoSPI State Rural CPI Inflation Series",
        ))
    if weather_risk_score > 0.3:
        threats.append(SWOTItem(
            f"Meaningful weather-disruption exposure (risk score {weather_risk_score:.2f}/1.0); heavy-rain "
            f"days could interrupt supply or footfall.",
            "IMD & Open-Meteo Weather Telemetry",
        ))
    if competition_intensity_normalized >= 0.6:
        threats.append(SWOTItem(
            f"High local competition saturation (normalized intensity {competition_intensity_normalized:.2f}/1.0) "
            f"could compress margins or slow customer acquisition.",
            "Ministry of MSME District Enterprise Registry (msme_district)",
        ))
    if ml_viability_verdict == "RECONSIDER":
        threats.append(SWOTItem(
            f"ML viability classifier flags RECONSIDER with {ml_confidence_pct:.1f}% confidence — "
            f"underlying financial/market ratios should be revisited before proceeding.",
            "Supervised XGBoost Viability Classifier (viability_xgb.joblib)",
        ))
    if not threats:
        threats.append(SWOTItem(
            "No high-severity external threats flagged against current inflation, weather, or competition data.",
            "MoSPI CPI / IMD Weather / MSME Registry",
        ))

    return SWOTMatrix(strengths=strengths, weaknesses=weaknesses, opportunities=opportunities, threats=threats)


if __name__ == "__main__":
    swot = build_swot(
        dscr=1.45, subsidy_grant_amount=175000, subsidy_scheme_name="PMEGP", project_cost=500000,
        infrastructure_score=6.5, projected_annual_tam=1500000, annual_turnover_estimate=600000,
        competition_intensity_normalized=0.3, msme_density_per_10k=8.2, cpi_inflation_pct=5.2,
        weather_risk_score=0.2, ml_viability_verdict="SUITABLE", ml_confidence_pct=91.4,
    )
    import json
    print(json.dumps(swot.to_dict(), indent=2))
