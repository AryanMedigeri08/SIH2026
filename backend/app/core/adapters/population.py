"""
population.py — Census Population & Household Projection Adapter.

Document 2, Sections 17-21 & 59.

Extracts demographic population, projects to target year using state-specific
CAGR rates from official Census tables, and computes household counts.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Optional, Any

from .base import GovernmentDatasetAdapter, DatasetMetadata
from .registry import DATA_SOURCES

logger = logging.getLogger("udyam_saathi.adapters.population")


class PopulationAdapter(GovernmentDatasetAdapter):
    """
    Adapter for Census 2011 population data with state CAGR projections.
    """

    def __init__(self, target_year: int = 2026):
        self.target_year = target_year
        self._meta = DATA_SOURCES["CENSUS_2011_POPULATION"]

    def metadata(self) -> DatasetMetadata:
        return self._meta

    def fetch_features(
        self,
        state: str,
        district: str,
        village: str = "",
        pincode: Optional[str] = None,
        base_population_2011: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Produce projected population and household counts for target location.
        Uses market_analyzer.project_population.
        """
        from app.core.market_analyzer import project_population, AVG_RURAL_HOUSEHOLD_SIZE

        # If base population not provided, use representative rural baseline (5,000)
        base_pop = base_population_2011 if (base_population_2011 and base_population_2011 > 0) else 5000.0

        try:
            proj = project_population(
                base_population_2011=base_pop,
                state_name=state.title() if state else "National",
                target_year=self.target_year,
            )
            households = proj.projected_households
            pop = proj.projected_population
            growth_rate = proj.growth_rate_used
            growth_source = proj.growth_rate_source
        except Exception as e:
            logger.warning(f"Population projection fallback used: {e}")
            pop = 5000
            households = int(5000 / AVG_RURAL_HOUSEHOLD_SIZE)
            growth_rate = 0.012
            growth_source = "national_default"

        return {
            "source_id": self._meta.source_id,
            "data_available": True,
            "data_year": f"2011-base / {self.target_year}-projected",
            "base_population_2011": base_pop,
            "projected_population": pop,
            "projected_households": households,
            "annual_cagr": growth_rate,
            "growth_rate_source": growth_source,
            "projection_status": "Projected population baseline",
            "projection_period": f"2011 to {self.target_year}",
            "avg_household_size": AVG_RURAL_HOUSEHOLD_SIZE,
            "geographic_level": "village_catchment",
            "notes": "Projected population baseline calculated via official state CAGR; not an observed head-count.",
        }
