"""
pipeline.py — UDYAM Village Intelligence Pipeline Orchestrator.

Orchestrates the full retrieval-normalize-resolve-distance-classify pipeline
as specified in Phase 41:

    retrieve → normalize → resolve → coordinate → distance → classify → parse activities → report

This is the main entry point for running market analysis against a target village.
"""

from __future__ import annotations
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field, asdict

from .models import (
    UdyamCanonicalRecord,
    GeographicResolution,
    TargetLocation,
    PipelineRunMetadata,
    MarketZone,
    LocalityConfidence,
    CoordinateConfidence,
)
from .client import UdyamClient
from .activities.parser import parse_activities
from .activities.categories import (
    enrich_activity_record,
    is_potential_competitor,
    is_potential_supply_chain,
    get_category_label,
)
from .geography.gazetteer import Gazetteer
from .geography.resolver import GeographicResolver
from .snapshot import snapshot_store

logger = logging.getLogger("udyam_saathi.pipeline")


@dataclass
class NearbyBusiness:
    """
    A nearby business identified in the market analysis.

    Per Phase 16: This is a "nearby_business", NOT automatically a "competitor".
    A business becomes a potential competitor only after category relevance
    is established.
    """
    record_fingerprint: str = ""
    enterprise_name: str = ""
    enterprise_name_raw: str = ""
    state: str = ""
    district: str = ""
    pincode: str = ""
    registration_date: Optional[str] = None
    communication_address: str = ""

    # Geographic resolution
    resolved_locality: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None
    market_zone: str = MarketZone.UNMAPPED.value
    locality_confidence: str = LocalityConfidence.UNKNOWN.value
    coordinate_confidence: str = CoordinateConfidence.UNKNOWN.value
    coordinate_source: str = ""

    # Activities
    activities_raw: str = ""
    activities_parsed: list = field(default_factory=list)
    primary_category: str = "UNKNOWN"
    primary_category_label: str = "Unclassified"
    category_confidence: str = "UNKNOWN"

    # Relationship to target
    is_potential_competitor: bool = False
    is_potential_supply_chain: bool = False
    relationship_type: str = "nearby_business"  # nearby | relevant | competitor | supplier

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class MarketAnalysisResult:
    """
    Complete result of a market analysis pipeline run.
    """
    # Target
    target: dict = field(default_factory=dict)

    # Geographic quality
    geographic_quality: dict = field(default_factory=dict)

    # Market summary
    market_summary: dict = field(default_factory=dict)

    # Business categories in the market
    business_categories: list = field(default_factory=list)

    # All nearby businesses (with relationship classification)
    nearby_businesses: list = field(default_factory=list)

    # Explicit limitations per Phase 37
    limitations: list = field(default_factory=list)

    # Pipeline metadata
    pipeline_metadata: dict = field(default_factory=dict)

    # Diagnostic report
    diagnostic_report: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class VillageIntelligencePipeline:
    """
    Main pipeline orchestrator for UDYAM village market intelligence.

    Usage:
        pipeline = VillageIntelligencePipeline(api_key="...")
        result = pipeline.analyze(
            state="TELANGANA",
            district="MEDAK",
            village="BALANAGAR",
            target_lat=17.9276,
            target_lon=78.2344,
            radius_km=10,
            business_category="DAIRY",
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        gazetteer: Optional[Gazetteer] = None,
    ):
        self.client = UdyamClient(api_key=api_key)
        self.gazetteer = gazetteer or Gazetteer()
        self.resolver = GeographicResolver(self.gazetteer)

    def analyze(
        self,
        state: str,
        district: str,
        village: str = "",
        target_lat: Optional[float] = None,
        target_lon: Optional[float] = None,
        radius_km: float = 10.0,
        core_radius_km: float = 5.0,
        business_category: str = "",
        pincode: Optional[str] = None,
        max_records: Optional[int] = None,
        snapshot_id: Optional[str] = None,
    ) -> MarketAnalysisResult:
        """
        Run the full village intelligence pipeline.

        Steps:
            1. Retrieve UDYAM records for the district (+ optional pincode or snapshot replay)
            2. Normalize all records
            3. Resolve geographic locations
            4. Calculate distances and classify market zones
            5. Parse and categorize activities
            6. Compute market summary metrics
            7. Generate diagnostic report
        """
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        start_time = time.monotonic()

        logger.info(
            f"[PIPELINE {run_id}] Starting analysis for "
            f"{village}, {district}, {state} (radius={radius_km}km)"
        )

        # Build target location
        target = TargetLocation(
            name=village,
            state=state.upper(),
            district=district.upper(),
            latitude=target_lat,
            longitude=target_lon,
            source="user_provided",
            confidence="HIGH" if target_lat and target_lon else "UNKNOWN",
        )

        # Initialize pipeline metadata
        metadata = PipelineRunMetadata(
            run_id=run_id,
            target_state=state.upper(),
            target_district=district.upper(),
            target_village=village,
            target_latitude=target_lat,
            target_longitude=target_lon,
            radius_km=radius_km,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        # Step 1: Retrieve or load UDYAM records
        if snapshot_id:
            logger.info(f"[PIPELINE {run_id}] Step 1: Loading records from snapshot {snapshot_id}")
            snap = snapshot_store.load(snapshot_id)
            if snap:
                records = []
                for r in snap.records:
                    if isinstance(r, dict):
                        records.append(UdyamCanonicalRecord(**{k: v for k, v in r.items() if k in UdyamCanonicalRecord.__dataclass_fields__}))
                    else:
                        records.append(r)
                metadata.snapshot_id = snapshot_id
                metadata.total_records_retrieved = len(records)
                metadata.api_reported_total = snap.record_count
            else:
                logger.warning(f"[PIPELINE {run_id}] Snapshot {snapshot_id} not found on disk.")
                records = []
        else:
            logger.info(f"[PIPELINE {run_id}] Step 1: Retrieving UDYAM records")
            if pincode:
                records, retrieval_meta = self.client.fetch_by_state_district_pincode(
                    state=state, district=district, pincode=pincode,
                    max_records=max_records,
                )
            else:
                records, retrieval_meta = self.client.fetch_by_district(
                    state=state, district=district,
                    max_records=max_records,
                )

            metadata.api_requests_made = retrieval_meta.pages_fetched
            metadata.total_records_retrieved = len(records)
            metadata.api_reported_total = retrieval_meta.api_total
            metadata.errors.extend(retrieval_meta.errors)

            if records:
                raw_dict_records = [asdict(r) if hasattr(r, '__dataclass_fields__') else r for r in records]
                snap = snapshot_store.create_snapshot(
                    source="UDYAM_MSME",
                    query_parameters={"state": state, "district": district, "pincode": pincode, "max_records": max_records},
                    records=raw_dict_records,
                )
                metadata.snapshot_id = snap.snapshot_id

        if not records:
            errors = retrieval_meta.errors if not snapshot_id else [f"Snapshot {snapshot_id} not found or empty."]
            logger.warning(
                f"[PIPELINE {run_id}] No records retrieved. "
                f"Errors: {errors}"
            )
            metadata.completed_at = datetime.now(timezone.utc).isoformat()
            metadata.execution_time_seconds = time.monotonic() - start_time
            return MarketAnalysisResult(
                target=target.to_dict(),
                limitations=[
                    "No UDYAM records could be retrieved for this district.",
                    "The data.gov.in API may be experiencing downtime.",
                ] + retrieval_meta.errors,
                pipeline_metadata=metadata.to_dict(),
                diagnostic_report=metadata.generate_report(),
            )

        logger.info(
            f"[PIPELINE {run_id}] Retrieved {len(records)} records"
        )

        # Step 2: Records are already normalized during retrieval (raw_to_canonical)

        # Step 3: Resolve geographic locations
        logger.info(f"[PIPELINE {run_id}] Step 3: Resolving geography")
        resolutions = self.resolver.resolve_batch(
            records=records,
            target=target,
            core_radius_km=core_radius_km,
            nearby_radius_km=radius_km,
        )

        # Step 4: Parse activities and categorize
        logger.info(f"[PIPELINE {run_id}] Step 4: Parsing activities")
        nearby_businesses = []
        for record, resolution in zip(records, resolutions):
            # Parse activities
            activities = parse_activities(record.activities_raw)
            enriched_activities = [enrich_activity_record(a) for a in activities]

            # Determine primary category
            primary_cat = "UNKNOWN"
            primary_cat_conf = "UNKNOWN"
            if enriched_activities:
                # Use the first activity with highest confidence
                best = max(
                    enriched_activities,
                    key=lambda a: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(a.category_confidence, 0)
                )
                primary_cat = best.normalized_category
                primary_cat_conf = best.category_confidence

            # Build nearby business record
            biz = NearbyBusiness(
                record_fingerprint=record.record_fingerprint,
                enterprise_name=record.enterprise_name_normalized,
                enterprise_name_raw=record.enterprise_name_raw,
                state=record.state_normalized,
                district=record.district_normalized,
                pincode=record.pincode_normalized,
                registration_date=(
                    record.registration_date.isoformat()
                    if hasattr(record.registration_date, "isoformat")
                    else str(record.registration_date) if record.registration_date else None
                ),
                communication_address=record.communication_address_normalized,
                resolved_locality=resolution.resolved_locality,
                latitude=resolution.latitude,
                longitude=resolution.longitude,
                distance_km=resolution.distance_km,
                market_zone=resolution.market_zone,
                locality_confidence=resolution.locality_confidence,
                coordinate_confidence=resolution.coordinate_confidence,
                coordinate_source=resolution.coordinate_source,
                activities_raw=record.activities_raw,
                activities_parsed=[a.to_dict() for a in enriched_activities],
                primary_category=primary_cat,
                primary_category_label=get_category_label(primary_cat),
                category_confidence=primary_cat_conf,
            )

            # Classify relationship to target
            if business_category and primary_cat != "UNKNOWN":
                target_cat = business_category.upper()
                if is_potential_competitor(target_cat, primary_cat):
                    biz.is_potential_competitor = True
                    biz.relationship_type = "potential_competitor"
                elif is_potential_supply_chain(target_cat, primary_cat):
                    biz.is_potential_supply_chain = True
                    biz.relationship_type = "potential_supplier"
                else:
                    biz.relationship_type = "nearby_business"
            else:
                biz.relationship_type = "nearby_business"

            nearby_businesses.append(biz)

        # Step 5: Compute market summary
        logger.info(f"[PIPELINE {run_id}] Step 5: Computing market summary")
        summary = self._compute_market_summary(
            nearby_businesses, business_category, metadata
        )

        # Step 6: Update metadata and generate report
        metadata.completed_at = datetime.now(timezone.utc).isoformat()
        metadata.execution_time_seconds = time.monotonic() - start_time

        # Confidence distribution
        for biz in nearby_businesses:
            # Locality confidence
            lc = biz.locality_confidence
            if lc == "HIGH": metadata.locality_high += 1
            elif lc == "MEDIUM": metadata.locality_medium += 1
            elif lc == "LOW": metadata.locality_low += 1
            else: metadata.locality_unknown += 1

            # Coordinate confidence
            cc = biz.coordinate_confidence
            if cc == "HIGH": metadata.coordinate_high += 1
            elif cc == "MEDIUM": metadata.coordinate_medium += 1
            elif cc == "LOW": metadata.coordinate_low += 1
            else: metadata.coordinate_unknown += 1

            # Market zones
            mz = biz.market_zone
            if mz == "CORE_5KM": metadata.core_5km += 1
            elif mz == "NEARBY_10KM": metadata.nearby_10km += 1
            elif mz == "OUTSIDE_10KM": metadata.outside_10km += 1
            else: metadata.unmapped += 1

        metadata.records_with_coordinates = sum(
            1 for b in nearby_businesses if b.latitude is not None
        )
        metadata.records_without_coordinates = (
            len(nearby_businesses) - metadata.records_with_coordinates
        )

        # Unique localities
        localities = {
            b.resolved_locality for b in nearby_businesses if b.resolved_locality
        }
        metadata.unique_localities_found = len(localities)
        metadata.localities_resolved = sum(
            1 for b in nearby_businesses
            if b.locality_confidence in ("HIGH", "MEDIUM")
        )
        metadata.localities_unresolved = sum(
            1 for b in nearby_businesses
            if b.locality_confidence in ("LOW", "UNKNOWN")
        )

        report = metadata.generate_report()

        logger.info(
            f"[PIPELINE {run_id}] Complete in {metadata.execution_time_seconds:.2f}s. "
            f"{len(nearby_businesses)} businesses processed."
        )

        # Build result
        result = MarketAnalysisResult(
            target=target.to_dict(),
            geographic_quality={
                "total_records": len(nearby_businesses),
                "with_coordinates": metadata.records_with_coordinates,
                "without_coordinates": metadata.records_without_coordinates,
                "locality_confidence_distribution": {
                    "HIGH": metadata.locality_high,
                    "MEDIUM": metadata.locality_medium,
                    "LOW": metadata.locality_low,
                    "UNKNOWN": metadata.locality_unknown,
                },
                "coordinate_confidence_distribution": {
                    "HIGH": metadata.coordinate_high,
                    "MEDIUM": metadata.coordinate_medium,
                    "LOW": metadata.coordinate_low,
                    "UNKNOWN": metadata.coordinate_unknown,
                },
            },
            market_summary=summary,
            business_categories=self._compute_category_distribution(nearby_businesses),
            nearby_businesses=[b.to_dict() for b in nearby_businesses],
            limitations=self._get_standard_limitations(),
            pipeline_metadata=metadata.to_dict(),
            diagnostic_report=report,
        )

        return result

    def _compute_market_summary(
        self,
        businesses: list[NearbyBusiness],
        target_category: str,
        metadata: PipelineRunMetadata,
    ) -> dict:
        """Compute descriptive market metrics (Phase 22 — no saturation score yet)."""
        core = [b for b in businesses if b.market_zone == "CORE_5KM"]
        nearby = [b for b in businesses if b.market_zone == "NEARBY_10KM"]

        # Category counts (not competitor counts — Phase 16)
        target_cat_upper = target_category.upper() if target_category else ""
        relevant_core = [
            b for b in core if b.primary_category == target_cat_upper
        ] if target_cat_upper else []
        relevant_nearby = [
            b for b in nearby if b.primary_category == target_cat_upper
        ] if target_cat_upper else []

        # Nearest relevant business distance
        relevant_with_dist = [
            b for b in businesses
            if b.primary_category == target_cat_upper
            and b.distance_km is not None
        ] if target_cat_upper else []
        nearest_distance = (
            min(b.distance_km for b in relevant_with_dist)
            if relevant_with_dist else None
        )

        # Competitor and supplier counts (only where category is known)
        competitors = [b for b in businesses if b.is_potential_competitor]
        suppliers = [b for b in businesses if b.is_potential_supply_chain]
        unmapped = [b for b in businesses if b.market_zone == "UNMAPPED"]

        return {
            "total_nearby_businesses": len(businesses),
            "core_5km_count": len(core),
            "nearby_10km_count": len(nearby),
            "unmapped_count": len(unmapped),
            "target_category": target_cat_upper,
            "target_category_label": get_category_label(target_cat_upper) if target_cat_upper else "",
            "category_relevant_core": len(relevant_core),
            "category_relevant_nearby": len(relevant_nearby),
            "potential_competitors": len(competitors),
            "potential_suppliers": len(suppliers),
            "nearest_relevant_distance_km": nearest_distance,
        }

    def _compute_category_distribution(
        self,
        businesses: list[NearbyBusiness],
    ) -> list[dict]:
        """Compute category distribution for the market."""
        cat_counts: dict[str, int] = {}
        for b in businesses:
            cat = b.primary_category
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        distribution = []
        for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
            distribution.append({
                "category": cat,
                "label": get_category_label(cat),
                "count": count,
                "share_pct": round(100 * count / len(businesses), 1) if businesses else 0,
            })
        return distribution

    def _get_standard_limitations(self) -> list[str]:
        """Per Phase 37: Required explicit limitations."""
        return [
            "UDYAM is not the complete universe of businesses. "
            "Results represent registered UDYAM MSMEs only, not every "
            "business physically operating in the market.",

            "Registration does not automatically prove current operating status. "
            "A registration record alone does not establish current activity.",

            "Address does not equal exact operating coordinates. "
            "Communication addresses can be incomplete or ambiguous.",

            "NIC/activity classification is not perfect semantic categorization. "
            "Raw activity data requires validation before high-confidence analysis.",

            "PIN is not equivalent to village. "
            "One PIN code may cover multiple villages/localities.",

            "Radius is an analytical approximation. "
            "A 5 km/10 km radius is not necessarily the true economic catchment.",
        ]
