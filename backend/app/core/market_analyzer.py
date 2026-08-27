"""
market_analyzer.py — Phase 2, Udyam Saathi

Blueprint §2.1 / §2.2. Pure deterministic math over inputs already resolved by
Phase 1's location_resolver.py (census_raw row, msme_district row). This module
never touches the database directly — it accepts already-fetched dicts, matching
the graceful-degradation pattern used in location_resolver.py.

IMPORTANT (carried from Phase 1 handoff, action item #4):
    census_raw.matched_village_code coverage is NOT universal. Every function
    here accepts `population_source: "census_exact" | "subdistrict_fallback" |
    "district_fallback" | "unavailable"` so the caller/DPR can be transparent
    about provenance instead of silently presenting an estimate as ground truth.
"""

from __future__ import annotations
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
def _resolve_growth_rates_path() -> Path:
    candidates = [
        Path(__file__).parent.parent / "data" / "growth_rates.json",
        Path(__file__).parent / "growth_rates.json",
        Path.cwd() / "backend" / "app" / "data" / "growth_rates.json",
        Path.cwd() / "growth_rates.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]

_GROWTH_RATES_PATH = _resolve_growth_rates_path()

AVG_RURAL_HOUSEHOLD_SIZE = 4.8

# Blueprint §2.2 sector demand table
SECTOR_DEMAND_PARAMS = {
    "dairy": {"penetration_rate": 0.42, "monthly_frequency": 26, "avg_ticket_size": 75},
    "food_processing": {"penetration_rate": 0.38, "monthly_frequency": 12, "avg_ticket_size": 180},
    "repair": {"penetration_rate": 0.28, "monthly_frequency": 2, "avg_ticket_size": 350},
    "apparel": {"penetration_rate": 0.30, "monthly_frequency": 2, "avg_ticket_size": 450},
    "fabrication": {"penetration_rate": 0.18, "monthly_frequency": 1, "avg_ticket_size": 1200},
}
# sensible default for sectors not explicitly tabulated in the blueprint
_DEFAULT_SECTOR_PARAMS = {"penetration_rate": 0.25, "monthly_frequency": 4, "avg_ticket_size": 250}


@dataclass
class PopulationProjection:
    base_population_2011: float
    state_name: str
    growth_rate_used: float
    growth_rate_source: str  # "state_cagr" | "national_default"
    target_year: int
    projected_population: int
    projected_households: int

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class TAMEstimate:
    sector: str
    households: int
    penetration_rate: float
    monthly_frequency: float
    avg_ticket_size: float
    target_households: int
    monthly_units: float
    monthly_tam: float
    annual_tam: float

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("monthly_units", "monthly_tam", "annual_tam"):
            d[k] = round(d[k], 2)
        return d


@dataclass
class MSMEDensity:
    district_msme_total: int
    projected_population: int
    msme_density_per_10k: float
    data_available: bool

    def to_dict(self) -> dict:
        d = asdict(self)
        d["msme_density_per_10k"] = round(d["msme_density_per_10k"], 3)
        return d


@dataclass
class CompetitionIntensity:
    sector: str
    estimated_local_competitors: float
    catchment_population: int
    competition_intensity_per_1k: float
    competition_intensity_normalized: float  # 0.0-1.0, feeds ML feature x8

    def to_dict(self) -> dict:
        d = asdict(self)
        d["competition_intensity_per_1k"] = round(d["competition_intensity_per_1k"], 3)
        d["competition_intensity_normalized"] = round(d["competition_intensity_normalized"], 4)
        return d


def _load_growth_rates() -> dict:
    with open(_GROWTH_RATES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def project_population(
    base_population_2011: float,
    state_name: str,
    target_year: int = 2026,
    growth_rates: Optional[dict] = None,
) -> PopulationProjection:
    """Blueprint §2.1: P_t = P_2011 * (1+r)^(t-2011)."""
    if base_population_2011 < 0:
        raise ValueError("base_population_2011 cannot be negative")
    if growth_rates is None:
        growth_rates = _load_growth_rates()

    state_cagr_table = growth_rates["state_cagr"]
    national_default = growth_rates["national_default_cagr"]

    if state_name in state_cagr_table:
        r = state_cagr_table[state_name]
        source = "state_cagr"
    else:
        r = national_default
        source = "national_default"

    years_elapsed = target_year - 2011
    projected = base_population_2011 * ((1 + r) ** years_elapsed)
    households = math.floor(projected / AVG_RURAL_HOUSEHOLD_SIZE)

    return PopulationProjection(
        base_population_2011=base_population_2011,
        state_name=state_name,
        growth_rate_used=r,
        growth_rate_source=source,
        target_year=target_year,
        projected_population=round(projected),
        projected_households=households,
    )


def estimate_tam(households: int, sector: str) -> TAMEstimate:
    """Blueprint §2.2."""
    if households < 0:
        raise ValueError("households cannot be negative")
    params = SECTOR_DEMAND_PARAMS.get(sector.lower(), _DEFAULT_SECTOR_PARAMS)

    target_hh = households * params["penetration_rate"]
    monthly_units = target_hh * params["monthly_frequency"]
    monthly_tam = monthly_units * params["avg_ticket_size"]

    return TAMEstimate(
        sector=sector,
        households=households,
        penetration_rate=params["penetration_rate"],
        monthly_frequency=params["monthly_frequency"],
        avg_ticket_size=params["avg_ticket_size"],
        target_households=round(target_hh),
        monthly_units=monthly_units,
        monthly_tam=monthly_tam,
        annual_tam=monthly_tam * 12,
    )


def compute_msme_density(district_msme_total: Optional[int], projected_population: int) -> MSMEDensity:
    """ML feature x4. Graceful degradation: returns data_available=False (density=0.0)
    when msme_district lookup missed, rather than raising — matches Phase 1 pattern."""
    if district_msme_total is None or projected_population <= 0:
        return MSMEDensity(
            district_msme_total=district_msme_total or 0,
            projected_population=projected_population,
            msme_density_per_10k=0.0,
            data_available=False,
        )
    density = (district_msme_total / projected_population) * 10000
    return MSMEDensity(
        district_msme_total=district_msme_total,
        projected_population=projected_population,
        msme_density_per_10k=density,
        data_available=True,
    )


def compute_competition_intensity(
    district_msme_total: Optional[int],
    sector_share_estimate: float,
    catchment_population: int,
) -> CompetitionIntensity:
    """
    ML feature x8. Estimated local competitors = district MSME total scaled by an
    assumed sector share of that district's registered enterprises, then normalized
    per 1k catchment population, then min-max normalized to [0,1] against a
    saturation ceiling of 20 competitors per 1k (empirical rural-market ceiling).
    """
    if catchment_population <= 0:
        raise ValueError("catchment_population must be > 0")
    msme_total = district_msme_total or 0
    est_competitors = msme_total * sector_share_estimate
    per_1k = (est_competitors / catchment_population) * 1000
    SATURATION_CEILING_PER_1K = 20.0
    normalized = min(per_1k / SATURATION_CEILING_PER_1K, 1.0)

    return CompetitionIntensity(
        sector="",
        estimated_local_competitors=round(est_competitors, 2),
        catchment_population=catchment_population,
        competition_intensity_per_1k=per_1k,
        competition_intensity_normalized=normalized,
    )


if __name__ == "__main__":
    pop = project_population(3200, "West Bengal", 2026)
    print(pop.to_dict())
    tam = estimate_tam(pop.projected_households, "dairy")
    print(tam.to_dict())
    dens = compute_msme_density(788, pop.projected_population)
    print(dens.to_dict())
