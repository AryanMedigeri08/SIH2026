"""
demand.py — Demand-Side Data Layer & Feature Aggregator.

Document 2, Sections 17-22.

Ingests independent government indicators from Census, Mission Antyodaya,
and ODOP registries. Strictly avoids circular reasoning (never uses competitor
scarcity alone as proof of demand).
"""

from __future__ import annotations
import logging
from typing import Optional, Any

from .models import DemandFeatures
from app.core.adapters.population import PopulationAdapter
from app.core.adapters.amenities import AmenitiesAdapter
from app.core.adapters.odop import ODOPAdapter

logger = logging.getLogger("udyam_saathi.intelligence.demand")


class DemandFeatureStore:
    """
    Coordinates government dataset adapters to build the demand feature store.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.pop_adapter = PopulationAdapter()
        self.amenities_adapter = AmenitiesAdapter(api_key=api_key)
        self.odop_adapter = ODOPAdapter()

    def build_demand_features(
        self,
        state: str,
        district: str,
        village: str = "",
        pincode: Optional[str] = None,
        target_category: str = "",
        base_population_2011: Optional[float] = None,
    ) -> DemandFeatures:
        """
        Aggregate independent demand and infrastructure features.
        """
        sources = []
        data_years = {}

        # 1. Population & Demographics
        pop_res = self.pop_adapter.fetch_features(
            state=state,
            district=district,
            village=village,
            pincode=pincode,
            base_population_2011=base_population_2011,
        )
        pop = pop_res.get("projected_population", 5000)
        households = pop_res.get("projected_households", 1040)
        growth_rate = round(pop_res.get("annual_cagr", 0.012) * 100.0, 2)
        sources.append(pop_res.get("source_id", "CENSUS_2011_POPULATION"))
        data_years["population"] = pop_res.get("data_year", "2011-base")

        # 2. Village Infrastructure Amenities
        amen_res = self.amenities_adapter.fetch_features(
            state=state,
            district=district,
            village=village,
            pincode=pincode,
        )
        sources.append(amen_res.get("source_id", "MISSION_ANTYODAYA"))
        data_years["amenities"] = amen_res.get("data_year", "2019-2020")

        infra_score = amen_res.get("infrastructure_score", 5.0)
        power_hrs = amen_res.get("power_supply_hours", 18.0)
        road_ok = amen_res.get("all_weather_road", True)
        bank_ok = amen_res.get("commercial_bank_access", True)
        net_ok = amen_res.get("internet_access", True)
        storage_ok = amen_res.get("storage_access", False)

        # 3. ODOP Alignment
        odop_res = self.odop_adapter.fetch_features(
            state=state,
            district=district,
            village=village,
            pincode=pincode,
            target_category=target_category,
        )
        if odop_res.get("data_available"):
            sources.append(odop_res.get("source_id", "ODOP_REGISTRY"))
            data_years["odop"] = odop_res.get("data_year", "2022-2026")

        is_odop = odop_res.get("is_odop_aligned", False)
        odop_prod = odop_res.get("odop_product")

        # Determine if we have sufficient independent demand evidence
        has_evidence = pop > 0 and pop_res.get("data_available", False)

        return DemandFeatures(
            population=pop,
            households=households,
            annual_population_growth_pct=growth_rate,
            infrastructure_score=infra_score,
            power_supply_hours=power_hrs,
            all_weather_road=road_ok,
            commercial_bank_access=bank_ok,
            internet_access=net_ok,
            storage_access=storage_ok,
            is_odop_aligned=is_odop,
            odop_product_name=odop_prod,
            data_years=data_years,
            sources=list(dict.fromkeys(sources)),
            has_sufficient_demand_evidence=has_evidence,
        )
