"""
resolver.py — Geographic Resolution Engine.

Phase 10 of the implementation plan.

For each UDYAM business:
    Step 1: Extract geographic candidates from the address
    Step 2: Match candidates against the locality master
    Step 3: Use administrative hierarchy to disambiguate
    Step 4: Use PIN as a supporting signal (PIN != village)
    Step 5: Assign locality and coordinate confidence SEPARATELY

CRITICAL RULES:
    - Never fabricate coordinates (Phase 12)
    - Separate locality_confidence from coordinate_confidence (Phase 9)
    - If multiple sources disagree, do NOT average them (Phase 8)
    - Start with deterministic rules, not opaque ML (Phase 11)
"""

from __future__ import annotations
import logging
from typing import Optional
from ..models import (
    UdyamCanonicalRecord,
    GeographicResolution,
    GeographicCandidate,
    TargetLocation,
    LocalityConfidence,
    CoordinateConfidence,
    CoordinateSource,
    MarketZone,
)
from ..normalization import normalize_address, normalize_pincode
from .extraction import extract_geographic_candidates
from .gazetteer import Gazetteer
from .distance import calculate_distance, classify_market_zone

logger = logging.getLogger("udyam_saathi.resolver")


class GeographicResolver:
    """
    Resolves UDYAM business records to geographic locations with
    explicit confidence and provenance tracking.
    """

    def __init__(self, gazetteer: Gazetteer):
        self.gazetteer = gazetteer

    def resolve_record(
        self,
        record: UdyamCanonicalRecord,
        target: Optional[TargetLocation] = None,
        core_radius_km: float = 5.0,
        nearby_radius_km: float = 10.0,
    ) -> GeographicResolution:
        """
        Resolve a single UDYAM record to a geographic location.

        Steps per Phase 10:
            1. Extract geographic candidates from address
            2. Match against locality master
            3. Use admin hierarchy for disambiguation
            4. Use PIN as supporting signal
            5. Assign separate locality and coordinate confidence

        Args:
            record: The canonical UDYAM record to resolve
            target: Optional target location for distance calculation
            core_radius_km: Core market zone radius
            nearby_radius_km: Nearby market zone radius

        Returns:
            GeographicResolution with confidence scores and provenance
        """
        resolution = GeographicResolution(
            record_fingerprint=record.record_fingerprint,
        )

        # Step 1: Extract geographic candidates from the address
        normalized_addr = record.communication_address_normalized
        if not normalized_addr:
            normalized_addr = normalize_address(record.communication_address_raw)

        candidates = extract_geographic_candidates(
            normalized_address=normalized_addr,
            known_state=record.state_normalized,
            known_district=record.district_normalized,
            known_pincode=record.pincode_normalized,
        )
        resolution.locality_candidates = [c.to_dict() for c in candidates]

        if not candidates:
            resolution.locality_confidence = LocalityConfidence.UNKNOWN.value
            resolution.coordinate_confidence = CoordinateConfidence.UNKNOWN.value
            resolution.resolution_error = "ADDRESS_TOO_SPARSE"
            resolution.market_zone = MarketZone.UNMAPPED.value
            return resolution

        # Step 2 & 3: Match candidates against locality master with admin context
        best_match = self._find_best_match(
            candidates=candidates,
            state=record.state_normalized,
            district=record.district_normalized,
        )

        if best_match is not None:
            resolution.resolved_locality = best_match.normalized_name
            resolution.locality_confidence = self._compute_locality_confidence(
                best_match, candidates, record
            )

            # Coordinate from the match
            if best_match.latitude is not None and best_match.longitude is not None:
                resolution.latitude = best_match.latitude
                resolution.longitude = best_match.longitude
                resolution.coordinate_confidence = best_match.coordinate_confidence
                resolution.coordinate_source = best_match.source
                resolution.resolution_method = "gazetteer_match"
            else:
                # Locality resolved but no coordinate — this is a valid state
                resolution.coordinate_confidence = CoordinateConfidence.UNKNOWN.value
                resolution.coordinate_source = CoordinateSource.UNKNOWN.value
                resolution.resolution_method = "gazetteer_locality_only"
        else:
            # Step 4: Fall back to PIN as geographic signal
            pin_result = self._resolve_via_pincode(
                pincode=record.pincode_normalized,
                candidates=candidates,
                state=record.state_normalized,
                district=record.district_normalized,
            )

            if pin_result is not None:
                resolution.resolved_locality = pin_result.get("locality", "")
                resolution.locality_confidence = LocalityConfidence.LOW.value
                resolution.resolution_method = "pincode_centroid"

                if pin_result.get("latitude") is not None:
                    resolution.latitude = pin_result["latitude"]
                    resolution.longitude = pin_result["longitude"]
                    resolution.coordinate_confidence = CoordinateConfidence.LOW.value
                    resolution.coordinate_source = CoordinateSource.PINCODE_DIRECTORY.value
                else:
                    resolution.coordinate_confidence = CoordinateConfidence.UNKNOWN.value
            else:
                # Unresolved — preserve locality candidates but no coordinate
                # Extract the most prominent locality candidate
                locality_candidates = [
                    c for c in candidates
                    if c.entity_type in ("village", "locality", "hamlet", "town")
                ]
                if locality_candidates:
                    resolution.resolved_locality = locality_candidates[0].text
                    resolution.locality_confidence = LocalityConfidence.LOW.value
                else:
                    resolution.locality_confidence = LocalityConfidence.UNKNOWN.value

                resolution.coordinate_confidence = CoordinateConfidence.UNKNOWN.value
                resolution.resolution_error = "UNKNOWN_LOCALITY"
                resolution.resolution_method = "unresolved"

        # Distance calculation (only if both target and business have coordinates)
        if target is not None:
            resolution.distance_km = calculate_distance(
                target_lat=target.latitude,
                target_lon=target.longitude,
                business_lat=resolution.latitude,
                business_lon=resolution.longitude,
            )
            resolution.market_zone = classify_market_zone(
                distance_km=resolution.distance_km,
                core_radius_km=core_radius_km,
                nearby_radius_km=nearby_radius_km,
            ).value
        else:
            resolution.market_zone = MarketZone.UNMAPPED.value

        return resolution

    def resolve_batch(
        self,
        records: list[UdyamCanonicalRecord],
        target: Optional[TargetLocation] = None,
        core_radius_km: float = 5.0,
        nearby_radius_km: float = 10.0,
    ) -> list[GeographicResolution]:
        """
        Resolve a batch of UDYAM records.
        Returns one GeographicResolution per input record.
        """
        results = []
        for record in records:
            try:
                res = self.resolve_record(
                    record=record,
                    target=target,
                    core_radius_km=core_radius_km,
                    nearby_radius_km=nearby_radius_km,
                )
                results.append(res)
            except Exception as e:
                logger.error(
                    f"Resolution failed for {record.record_fingerprint[:12]}: {e}",
                    exc_info=True,
                )
                res = GeographicResolution(
                    record_fingerprint=record.record_fingerprint,
                    resolution_error=f"RESOLUTION_EXCEPTION: {type(e).__name__}: {str(e)[:100]}",
                    locality_confidence=LocalityConfidence.UNKNOWN.value,
                    coordinate_confidence=CoordinateConfidence.UNKNOWN.value,
                    market_zone=MarketZone.UNMAPPED.value,
                )
                results.append(res)

        return results

    def _find_best_match(
        self,
        candidates: list[GeographicCandidate],
        state: str,
        district: str,
    ) -> Optional:
        """
        Match locality candidates against the gazetteer.

        Uses admin hierarchy to disambiguate. State + District + Name
        is stronger than Name alone (Phase 10 Step 3).

        Returns the best matching LocalityMasterRecord or None.
        """
        best_match = None
        best_score = -1

        # Priority 1: Candidates extracted by admin markers (higher confidence)
        marker_candidates = [c for c in candidates if c.method == "admin_marker"]
        positional_candidates = [c for c in candidates if c.method == "positional_heuristic"]

        for candidate_list, base_score in [
            (marker_candidates, 10),
            (positional_candidates, 5),
        ]:
            for candidate in candidate_list:
                # Try with full admin context first (strongest disambiguation)
                matches = self.gazetteer.lookup_by_name(
                    name=candidate.text,
                    state=state,
                    district=district,
                )

                if matches:
                    # Multiple matches within same state+district
                    # Prefer the one with highest coordinate confidence
                    for match in matches:
                        score = base_score
                        if match.coordinate_confidence == CoordinateConfidence.HIGH.value:
                            score += 5
                        elif match.coordinate_confidence == CoordinateConfidence.MEDIUM.value:
                            score += 3
                        elif match.coordinate_confidence == CoordinateConfidence.LOW.value:
                            score += 1

                        # Prefer village-type matches over broader admin types
                        if match.village and match.village.upper() == candidate.text:
                            score += 3

                        if score > best_score:
                            best_score = score
                            best_match = match
                    continue

                # Try with state only (broader)
                matches = self.gazetteer.lookup_by_name(
                    name=candidate.text,
                    state=state,
                )
                if matches and len(matches) == 1:
                    # Unambiguous within state
                    match = matches[0]
                    score = base_score - 2  # Lower score than state+district match
                    if score > best_score:
                        best_score = score
                        best_match = match

        return best_match

    def _resolve_via_pincode(
        self,
        pincode: str,
        candidates: list[GeographicCandidate],
        state: str,
        district: str,
    ) -> Optional[dict]:
        """
        Use pincode as a supporting geographic signal.

        Per Phase 10 Step 4:
            PIN -> candidate geographic set (NOT PIN -> exact village)
            One PIN may cover multiple villages/localities.

        If pincode maps to a single locality matching our address candidates,
        use it. Otherwise, use the pincode centroid with LOW confidence.
        """
        if not pincode:
            return None

        clean_pin = normalize_pincode(pincode)
        if not clean_pin:
            return None

        pin_localities = self.gazetteer.lookup_by_pincode(clean_pin)
        if not pin_localities:
            return None

        # Try to match pincode localities against our address candidates
        candidate_names = {c.text.upper() for c in candidates}
        matching_pin_localities = [
            pl for pl in pin_localities
            if pl.get("office_name", "").upper() in candidate_names
            or any(
                cname in pl.get("office_name", "").upper()
                for cname in candidate_names
            )
        ]

        if len(matching_pin_localities) == 1:
            pl = matching_pin_localities[0]
            return {
                "locality": pl.get("office_name", ""),
                "latitude": pl.get("latitude"),
                "longitude": pl.get("longitude"),
                "confidence": "MEDIUM",
            }

        # No specific match — use first pincode entry as centroid approximation
        # This gives LOW confidence (we know the broad area, not the exact village)
        if pin_localities:
            pl = pin_localities[0]
            lat = pl.get("latitude")
            lon = pl.get("longitude")
            if lat is not None and lon is not None:
                return {
                    "locality": f"PIN-{clean_pin}",
                    "latitude": lat,
                    "longitude": lon,
                    "confidence": "LOW",
                }

        return None

    def _compute_locality_confidence(
        self,
        match,
        candidates: list[GeographicCandidate],
        record: UdyamCanonicalRecord,
    ) -> str:
        """
        Compute locality confidence based on match quality.

        Per Phase 11:
            HIGH: Exact locality + coordinate from authoritative source
            MEDIUM: Locality identified but some ambiguity
            LOW: Only broader geographic info
            UNKNOWN: No defensible assignment
        """
        # Check if the match was via admin marker (higher confidence)
        marker_candidates = [
            c for c in candidates
            if c.method == "admin_marker" and c.text == match.normalized_name
        ]

        if marker_candidates:
            # Admin-marker match with state+district context = HIGH
            return LocalityConfidence.HIGH.value

        # Check if the address explicitly contains the locality name
        if match.normalized_name in record.communication_address_normalized:
            return LocalityConfidence.MEDIUM.value

        return LocalityConfidence.LOW.value
