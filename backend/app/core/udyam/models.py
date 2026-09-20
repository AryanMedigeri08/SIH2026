"""
models.py — Canonical UDYAM Record Data Models.

Preserves raw government values alongside normalized representations.
Never overwrites raw fields. Implements deterministic record fingerprinting
for deduplication and change-detection.

This is NOT a government identifier — it is an internal deduplication mechanism.
"""

from __future__ import annotations
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from enum import Enum
from typing import Optional, Any


class CoordinateConfidence(str, Enum):
    HIGH = "HIGH"       # Exact locality identified, coordinate from authoritative source
    MEDIUM = "MEDIUM"   # Locality identified, coordinate from weaker/ambiguous source
    LOW = "LOW"         # Only broader geographic info available (district known, village unknown)
    UNKNOWN = "UNKNOWN" # No defensible geographic assignment


class LocalityConfidence(str, Enum):
    HIGH = "HIGH"       # Exact locality identified from address + administrative context
    MEDIUM = "MEDIUM"   # Probable locality, some ambiguity remains
    LOW = "LOW"         # Broad area identified, specific locality uncertain
    UNKNOWN = "UNKNOWN" # Cannot determine locality


class MarketZone(str, Enum):
    CORE_5KM = "CORE_5KM"
    NEARBY_10KM = "NEARBY_10KM"
    OUTSIDE_10KM = "OUTSIDE_10KM"
    UNMAPPED = "UNMAPPED"


class CoordinateSource(str, Enum):
    GOVERNMENT_CENSUS = "government_census"
    GOVERNMENT_ADMIN = "government_admin"
    PINCODE_DIRECTORY = "pincode_directory"
    OSM = "osm_derived"
    GEOCODER = "geocoder"
    MANUAL = "manual_verified"
    UNKNOWN = "unknown"


@dataclass
class UdyamRawRecord:
    """
    Verbatim fields exactly as received from the data.gov.in UDYAM API.
    No normalization applied. These values are immutable after ingestion.
    """
    lg_st_code: Optional[str] = None
    state: Optional[str] = None
    lg_dt_code: Optional[str] = None
    district: Optional[str] = None
    pincode: Optional[str] = None
    registration_date: Optional[str] = None
    enterprise_name: Optional[str] = None
    communication_address: Optional[str] = None
    activities: Optional[str] = None

    # Retrieval metadata
    api_resource_id: str = "8b68ae56-84cf-4728-a0a6-1be11028dea7"
    retrieved_at: Optional[str] = None
    api_offset: Optional[int] = None
    api_page: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class UdyamCanonicalRecord:
    """
    Canonical internal representation. Retains raw fields alongside normalized versions.
    The `record_fingerprint` is a deterministic SHA-256 hash for deduplication.
    It is NOT a government identifier.
    """
    # Raw preservation (immutable)
    enterprise_name_raw: str = ""
    state_raw: str = ""
    district_raw: str = ""
    pincode_raw: str = ""
    registration_date_raw: str = ""
    communication_address_raw: str = ""
    activities_raw: str = ""

    # Normalized versions
    enterprise_name_normalized: str = ""
    state_normalized: str = ""
    district_normalized: str = ""
    pincode_normalized: str = ""
    registration_date: Optional[date] = None
    communication_address_normalized: str = ""

    # Parsed activities (list of ActivityRecord)
    activities_parsed: list = field(default_factory=list)

    # Deterministic record fingerprint (internal dedup, NOT a govt ID)
    record_fingerprint: str = ""

    # LGD codes (if available from API)
    lg_st_code: Optional[str] = None
    lg_dt_code: Optional[str] = None

    # Retrieval metadata
    api_resource_id: str = "8b68ae56-84cf-4728-a0a6-1be11028dea7"
    retrieved_at: Optional[str] = None

    @property
    def enterprise_name(self) -> str:
        return self.enterprise_name_normalized or self.enterprise_name_raw

    @property
    def state(self) -> str:
        return self.state_normalized or self.state_raw

    @property
    def district(self) -> str:
        return self.district_normalized or self.district_raw

    @property
    def pincode(self) -> str:
        return self.pincode_normalized or self.pincode_raw

    @property
    def communication_address(self) -> str:
        return self.communication_address_normalized or self.communication_address_raw

    @property
    def activities(self) -> list:
        return self.activities_parsed

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.registration_date:
            d["registration_date"] = self.registration_date.isoformat()
        return d


@dataclass
class ActivityRecord:
    """
    A single parsed activity from the Activities JSON field.
    One enterprise may produce multiple ActivityRecord rows.
    """
    nic_code: str = ""
    nic_description_raw: str = ""
    activity_description: str = ""

    # Normalized category mapping (Phase 19+)
    normalized_category: str = "UNKNOWN"
    category_confidence: str = "UNKNOWN"
    validation_source: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GeographicCandidate:
    """
    A potential geographic entity extracted from an address.
    Multiple candidates may be returned per address.
    """
    text: str = ""
    entity_type: str = "LOCALITY"  # village, hamlet, ward, town, taluka, mandal, etc.
    position: int = 0              # character position in original address
    method: str = ""               # how this candidate was identified
    confidence: str = "UNKNOWN"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LocalityMasterRecord:
    """
    A record in the geographic reference database.
    Every coordinate has explicit provenance.
    """
    locality_id: str = ""
    state: str = ""
    district: str = ""
    subdistrict: str = ""
    block: str = ""
    taluka: str = ""
    mandal: str = ""
    gram_panchayat: str = ""
    village: str = ""
    normalized_name: str = ""

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    source: str = ""
    source_url: str = ""
    source_record_id: str = ""

    coordinate_confidence: str = CoordinateConfidence.UNKNOWN.value
    administrative_confidence: str = "UNKNOWN"

    valid_from: Optional[str] = None
    valid_to: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TargetLocation:
    """
    The target village/locality for a market analysis query.
    The target itself requires provenance.
    """
    name: str = ""
    state: str = ""
    district: str = ""
    subdistrict: str = ""
    mandal: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: str = ""
    source_url: str = ""
    confidence: str = CoordinateConfidence.UNKNOWN.value

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GeographicResolution:
    """
    The result of resolving a UDYAM record to a geographic location.
    Separates locality confidence from coordinate confidence.
    """
    record_fingerprint: str = ""

    # Locality resolution
    resolved_locality: str = ""
    locality_candidates: list = field(default_factory=list)
    locality_confidence: str = LocalityConfidence.UNKNOWN.value

    # Coordinate resolution
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coordinate_confidence: str = CoordinateConfidence.UNKNOWN.value
    coordinate_source: str = CoordinateSource.UNKNOWN.value
    coordinate_source_url: str = ""

    # Distance from target (NULL if coordinates missing)
    distance_km: Optional[float] = None
    market_zone: str = MarketZone.UNMAPPED.value

    # Error tracking
    resolution_error: str = ""
    resolution_method: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PipelineRunMetadata:
    """
    Diagnostic metadata for a single pipeline run.
    Every pipeline run generates this for observability.
    """
    run_id: str = ""
    target_state: str = ""
    target_district: str = ""
    target_village: str = ""
    target_latitude: Optional[float] = None
    target_longitude: Optional[float] = None
    radius_km: float = 10.0
    snapshot_id: str = ""

    # Retrieval stats
    api_requests_made: int = 0
    total_records_retrieved: int = 0
    api_reported_total: int = 0
    cache_hits: int = 0
    duplicate_records_detected: int = 0

    # Resolution stats
    unique_localities_found: int = 0
    localities_resolved: int = 0
    localities_unresolved: int = 0
    records_with_coordinates: int = 0
    records_without_coordinates: int = 0

    # Confidence distribution
    locality_high: int = 0
    locality_medium: int = 0
    locality_low: int = 0
    locality_unknown: int = 0
    coordinate_high: int = 0
    coordinate_medium: int = 0
    coordinate_low: int = 0
    coordinate_unknown: int = 0

    # Market zone distribution
    core_5km: int = 0
    nearby_10km: int = 0
    outside_10km: int = 0
    unmapped: int = 0

    # Timing
    execution_time_seconds: float = 0.0
    manual_corrections: int = 0
    started_at: str = ""
    completed_at: str = ""

    # Errors
    errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def generate_report(self) -> str:
        """Generate the diagnostic report per Phase 28."""
        lines = [
            "=" * 60,
            "GEOGRAPHIC RESOLUTION REPORT",
            "=" * 60,
            "",
            f"Target:",
            f"  {self.target_village}, {self.target_district}, {self.target_state}",
            f"  Coordinates: ({self.target_latitude}, {self.target_longitude})",
            f"  Radius: {self.radius_km} km",
            "",
            f"UDYAM records:          {self.total_records_retrieved}",
            f"API reported total:     {self.api_reported_total}",
            f"Duplicates detected:    {self.duplicate_records_detected}",
            f"Cache hits:             {self.cache_hits}",
            "",
            f"Unique localities:      {self.unique_localities_found}",
            f"Localities resolved:    {self.localities_resolved}",
            f"Unresolved:             {self.localities_unresolved}",
            "",
            "Locality Confidence:",
            f"  HIGH:     {self.locality_high}",
            f"  MEDIUM:   {self.locality_medium}",
            f"  LOW:      {self.locality_low}",
            f"  UNKNOWN:  {self.locality_unknown}",
            "",
            "Coordinate Confidence:",
            f"  HIGH:     {self.coordinate_high}",
            f"  MEDIUM:   {self.coordinate_medium}",
            f"  LOW:      {self.coordinate_low}",
            f"  UNKNOWN:  {self.coordinate_unknown}",
            "",
            "Market Zones:",
            f"  <= 5 km:      {self.core_5km}",
            f"  5-10 km:      {self.nearby_10km}",
            f"  > 10 km:      {self.outside_10km}",
            f"  UNMAPPED:     {self.unmapped}",
            "",
            f"Execution time:         {self.execution_time_seconds:.2f}s",
            f"Manual corrections:     {self.manual_corrections}",
            f"API requests:           {self.api_requests_made}",
            "",
        ]
        if self.errors:
            lines.append("Errors:")
            for err in self.errors:
                lines.append(f"  - {err}")
        lines.append("=" * 60)
        return "\n".join(lines)


def compute_record_fingerprint(
    enterprise_name: str,
    communication_address: str,
    pincode: str,
    registration_date: str,
    state: str,
    district: str,
) -> str:
    """
    Create a deterministic local record fingerprint for deduplication.
    Normalize inputs before hashing. This is NOT a government identifier.

    Per Phase 4 of the implementation plan.
    """
    # Normalize each component
    parts = []
    for raw_val in [enterprise_name, communication_address, pincode,
                    registration_date, state, district]:
        val = str(raw_val or "").strip()
        # Unicode normalization
        val = unicodedata.normalize("NFKD", val)
        # Collapse whitespace
        val = re.sub(r'\s+', ' ', val)
        # Uppercase
        val = val.upper()
        parts.append(val)

    canonical_string = "|".join(parts)
    return hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()


def parse_registration_date(raw_date: str) -> Optional[date]:
    """
    Parse the RegistrationDate field from the UDYAM API.
    Handles multiple known formats gracefully. Returns None on failure.
    """
    if not raw_date or not raw_date.strip():
        return None

    raw_date = raw_date.strip()
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%Y-%m-%dT%H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw_date, fmt).date()
        except ValueError:
            continue
    return None


def raw_to_canonical(raw: UdyamRawRecord) -> UdyamCanonicalRecord:
    """
    Convert a raw API record into the canonical internal representation.
    Preserves all raw fields. Normalizes where safe.
    """
    from .normalization import normalize_text_basic

    enterprise_norm = normalize_text_basic(raw.enterprise_name or "")
    state_norm = normalize_text_basic(raw.state or "")
    district_norm = normalize_text_basic(raw.district or "")
    pincode_norm = (raw.pincode or "").strip()
    address_norm = normalize_text_basic(raw.communication_address or "")
    reg_date = parse_registration_date(raw.registration_date or "")

    fingerprint = compute_record_fingerprint(
        enterprise_name=raw.enterprise_name or "",
        communication_address=raw.communication_address or "",
        pincode=raw.pincode or "",
        registration_date=raw.registration_date or "",
        state=raw.state or "",
        district=raw.district or "",
    )

    try:
        from .activities.parser import parse_activities
        parsed_acts = parse_activities(raw.activities or "")
    except Exception:
        parsed_acts = []

    return UdyamCanonicalRecord(
        enterprise_name_raw=raw.enterprise_name or "",
        state_raw=raw.state or "",
        district_raw=raw.district or "",
        pincode_raw=raw.pincode or "",
        registration_date_raw=raw.registration_date or "",
        communication_address_raw=raw.communication_address or "",
        activities_raw=raw.activities or "",
        activities_parsed=parsed_acts,
        enterprise_name_normalized=enterprise_norm,
        state_normalized=state_norm,
        district_normalized=district_norm,
        pincode_normalized=pincode_norm,
        registration_date=reg_date,
        communication_address_normalized=address_norm,
        record_fingerprint=fingerprint,
        lg_st_code=raw.lg_st_code,
        lg_dt_code=raw.lg_dt_code,
        api_resource_id=raw.api_resource_id,
        retrieved_at=raw.retrieved_at,
    )
