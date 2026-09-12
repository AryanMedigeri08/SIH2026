"""
distance.py — Haversine Distance Engine & Market Zone Classifier.

Phase 14 & 15 of the implementation plan.

Calculates geodesic distance between two geographic points using the
Haversine formula. Classifies businesses into configurable market zones.

Rules:
    - If coordinates are missing: distance_km = NULL, zone = UNMAPPED
    - Do NOT calculate from incomplete coordinates
    - Radius must remain configurable (not hardcoded to 5/10 km)
"""

from __future__ import annotations
import math
from typing import Optional
from ..models import MarketZone


# Earth's mean radius in kilometers
EARTH_RADIUS_KM = 6371.0


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.

    Args:
        lat1, lon1: Target location coordinates (degrees)
        lat2, lon2: Business location coordinates (degrees)

    Returns:
        Distance in kilometers
    """
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def calculate_distance(
    target_lat: Optional[float],
    target_lon: Optional[float],
    business_lat: Optional[float],
    business_lon: Optional[float],
) -> Optional[float]:
    """
    Calculate distance between target and business locations.
    Returns None if either coordinate pair is missing or invalid.

    Per Phase 14: Do NOT calculate from incomplete coordinates.
    """
    if target_lat is None or target_lon is None:
        return None
    if business_lat is None or business_lon is None:
        return None

    # Validate coordinate ranges
    if not (-90 <= target_lat <= 90 and -180 <= target_lon <= 180):
        return None
    if not (-90 <= business_lat <= 90 and -180 <= business_lon <= 180):
        return None

    return haversine_distance(target_lat, target_lon, business_lat, business_lon)


def classify_market_zone(
    distance_km: Optional[float],
    core_radius_km: float = 5.0,
    nearby_radius_km: float = 10.0,
) -> MarketZone:
    """
    Classify a business into a market zone based on distance from target.

    Per Phase 15:
        distance <= core_radius     -> CORE_5KM
        core < distance <= nearby   -> NEARBY_10KM
        distance > nearby           -> OUTSIDE_10KM
        coordinate unavailable      -> UNMAPPED

    The radii are configurable — do NOT permanently hardcode 5/10 km.
    """
    if distance_km is None:
        return MarketZone.UNMAPPED

    if distance_km <= core_radius_km:
        return MarketZone.CORE_5KM
    elif distance_km <= nearby_radius_km:
        return MarketZone.NEARBY_10KM
    else:
        return MarketZone.OUTSIDE_10KM


def classify_with_custom_zones(
    distance_km: Optional[float],
    zone_boundaries: list[tuple[str, float]],
) -> str:
    """
    Classify using custom zone boundaries.

    Args:
        distance_km: Distance in km (None if unmapped)
        zone_boundaries: List of (zone_name, max_distance_km) tuples,
                        sorted by max_distance ascending.
                        Example: [("WALKING_3KM", 3), ("LOCAL_5KM", 5), ("MARKET_10KM", 10)]

    Returns:
        Zone name string, or "UNMAPPED" if distance is None,
        or "OUTSIDE" if distance exceeds all boundaries.
    """
    if distance_km is None:
        return "UNMAPPED"

    for zone_name, max_dist in sorted(zone_boundaries, key=lambda x: x[1]):
        if distance_km <= max_dist:
            return zone_name

    return "OUTSIDE"
