"""
amenities.py — Mission Antyodaya 613 Village Amenities & Infrastructure Adapter.

Document 2, Sections 17-21 & 59.

Extracts village infrastructure availability (electricity hours, paved roads,
banking touchpoints, internet/telecom, warehousing) from Data.gov.in / Mission
Antyodaya OGD resource files with 24-hour in-memory caching and regional baselines.
"""

from __future__ import annotations
import logging
from typing import Optional, Any

from .base import GovernmentDatasetAdapter, DatasetMetadata
from .registry import DATA_SOURCES

logger = logging.getLogger("udyam_saathi.adapters.amenities")


class AmenitiesAdapter(GovernmentDatasetAdapter):
    """
    Adapter for Mission Antyodaya 613 Village Amenities Dataset.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._meta = DATA_SOURCES["MISSION_ANTYODAYA"]
        self.api_key = api_key

    def metadata(self) -> DatasetMetadata:
        return self._meta

    def fetch_features(
        self,
        state: str,
        district: str,
        village: str = "",
        pincode: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Produce infrastructure features for target village/district.
        Calls app.core.amenities_client.fetch_village_amenities.
        """
        from app.core.amenities_client import fetch_village_amenities

        try:
            res = fetch_village_amenities(
                state_name=state.strip(),
                district_name=district.strip(),
                village_name=village.strip() if village else "N/A",
                api_key=self.api_key,
            )

            is_fallback = (res.provenance == "regional_baseline")
            join_lvl = "village" if (res.provenance == "data_gov_in_live" and village) else ("regional_baseline" if is_fallback else "district_baseline")

            return {
                "source_id": self._meta.source_id,
                "data_available": True,
                "data_year": "2019-2020",
                "power_supply_hours": res.power_supply_hours_per_day,
                "all_weather_road": res.has_all_weather_road,
                "commercial_bank_access": res.has_bank_or_atm_within_5km,
                "internet_access": res.has_broadband_internet,
                "storage_access": res.has_cold_storage_or_warehouse,
                "infrastructure_score": res.infrastructure_score,
                "is_fallback_baseline": is_fallback,
                "join_level": join_lvl,
                "provenance": res.provenance,
                "raw_indicators_count": res.total_metrics_queried,
            }
        except Exception as e:
            logger.warning(f"Amenities fetch error for {district}, {state}: {e}")
            return {
                "source_id": self._meta.source_id,
                "data_available": False,
                "data_year": "2019-2020",
                "power_supply_hours": 14.0,
                "all_weather_road": True,
                "commercial_bank_access": True,
                "internet_access": True,
                "storage_access": False,
                "infrastructure_score": 6.0,
                "is_fallback_baseline": True,
                "raw_indicators_count": 0,
            }
