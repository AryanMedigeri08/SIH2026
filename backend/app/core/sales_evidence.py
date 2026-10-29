"""Forecast evidence collection without substituting defaults for observations."""
import asyncio
import logging

logger = logging.getLogger(__name__)


async def registered_market_context(input_data):
    try:
        from app.routers.market_intelligence import get_pipeline
        result = await asyncio.wait_for(get_pipeline().analyze(
            state=input_data.state_name, district=input_data.district_name,
            village=input_data.village_name, business_category=input_data.sector,
            target_lat=input_data.latitude, target_lon=input_data.longitude,
            radius_km=10, core_radius_km=5, max_records=100), timeout=8)
        data = result.to_dict()
        return {"status": "partial_registered_business_sample", "source": "UDYAM",
                "market_summary": data.get("market_summary", {}),
                "geographic_quality": data.get("geographic_quality", {}),
                "retrieval": data.get("pipeline_metadata", {}),
                "business_categories": data.get("business_categories", {}),
                "business_sample": [{key: row.get(key) for key in (
                    "enterprise_name", "primary_category", "distance_km", "market_zone", "relationship_type", "coordinate_confidence"
                )} for row in data.get("nearby_businesses", [])[:25]],
                "limitations": data.get("limitations", []),
                "notice": "Registered business sample, not a complete count or proof of active trading. No sales/price evidence."}
    except Exception as exc:
        logger.info("Forecast UDYAM evidence unavailable (%s)", type(exc).__name__)
        return {"status": "unavailable", "source": "UDYAM", "notice": "No successful local registered-business retrieval for this forecast."}


def regional_evidence(census, pop, msme, amenities, cpi, odop, registered):
    return {
        "demographics": {"status": "projected" if census.get("provenance", "").startswith("census_") else "fallback",
                         "source": "Census 2011 lookup plus state growth assumptions", "reference_year": 2011,
                         "lookup": census, "projection": pop.to_dict(),
                         "notice": "Population and households are potential market context, not active customers. Name matching is not independently verified."},
        "district_msme": msme, "registered_businesses": registered,
        "amenities": amenities.to_dict(), "cpi": cpi, "odop": odop,
    }
