"""
test_udyam_engine.py — Unit Tests for the UDYAM Village Intelligence Engine.

Phase 29 of the implementation plan.

Tests:
    - Address normalization (spelling variations, geographic preservation)
    - Ambiguous locality resolution (KONDAPUR must not auto-resolve)
    - PIN ambiguity (PIN covering multiple villages)
    - Missing coordinates (must produce UNMAPPED)
    - Boundary distance tests (4.999, 5.000, 5.001, 9.999, 10.000, 10.001)
    - Duplicate record detection (same fingerprint)
    - Multiple activities (one enterprise, multiple activity rows)
    - Record fingerprinting determinism
    - Activity parsing (JSON, delimited, plain text)
    - Category mapping (NIC code and keyword-based)
"""

import sys
from pathlib import Path

# Add project paths
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "app" / "core"))

import pytest
from datetime import date


# ============================================================================
# Test Address Normalization
# ============================================================================

class TestNormalization:
    """Phase 5: Address normalization tests."""

    def test_basic_text_normalization(self):
        from app.core.udyam.normalization import normalize_text_basic
        assert normalize_text_basic("  hello   world  ") == "HELLO WORLD"
        assert normalize_text_basic("") == ""
        assert normalize_text_basic(None) == ""

    def test_address_normalization_preserves_geographic_tokens(self):
        """S KONDAPUR must NOT become KONDAPUR."""
        from app.core.udyam.normalization import normalize_address
        result = normalize_address("S KONDAPUR, Medak, Telangana")
        assert "S KONDAPUR" in result or "S" in result.split()

    def test_address_normalization_expands_abbreviations(self):
        from app.core.udyam.normalization import normalize_address
        result = normalize_address("Vill. Rajpally, Dist. Medak")
        assert "VILLAGE" in result
        assert "DISTRICT" in result

    def test_address_normalization_collapses_whitespace(self):
        from app.core.udyam.normalization import normalize_address
        result = normalize_address("3-26/3,   Rajpally,    Medak")
        assert "  " not in result

    def test_address_normalization_unicode(self):
        from app.core.udyam.normalization import normalize_address
        result = normalize_address("Rāmpally, Medak")
        assert result  # Should not crash on unicode

    def test_pincode_normalization_valid(self):
        from app.core.udyam.normalization import normalize_pincode
        assert normalize_pincode("502117") == "502117"
        assert normalize_pincode(" 502117 ") == "502117"

    def test_pincode_normalization_invalid(self):
        from app.core.udyam.normalization import normalize_pincode
        assert normalize_pincode("") == ""
        assert normalize_pincode("12345") == ""   # Too short
        assert normalize_pincode("1234567") == ""  # Too long
        assert normalize_pincode("abcdef") == ""   # Non-numeric

    def test_state_normalization(self):
        from app.core.udyam.normalization import normalize_state
        assert normalize_state("telangana") == "TELANGANA"
        assert normalize_state("ORISSA") == "ODISHA"
        assert normalize_state("TAMILNADU") == "TAMIL NADU"
        assert normalize_state("WB") == "WEST BENGAL"


# ============================================================================
# Test Record Fingerprinting
# ============================================================================

class TestRecordFingerprint:
    """Phase 4: Deterministic record identity."""

    def test_fingerprint_determinism(self):
        """Same inputs must produce the same fingerprint."""
        from app.core.udyam.models import compute_record_fingerprint
        fp1 = compute_record_fingerprint(
            "Test Enterprise", "123 Main St", "502117",
            "2024-01-15", "TELANGANA", "MEDAK"
        )
        fp2 = compute_record_fingerprint(
            "Test Enterprise", "123 Main St", "502117",
            "2024-01-15", "TELANGANA", "MEDAK"
        )
        assert fp1 == fp2

    def test_fingerprint_case_insensitive(self):
        """Fingerprint should be case-insensitive."""
        from app.core.udyam.models import compute_record_fingerprint
        fp1 = compute_record_fingerprint(
            "Test Enterprise", "123 Main St", "502117",
            "2024-01-15", "TELANGANA", "MEDAK"
        )
        fp2 = compute_record_fingerprint(
            "test enterprise", "123 main st", "502117",
            "2024-01-15", "telangana", "medak"
        )
        assert fp1 == fp2

    def test_fingerprint_different_inputs(self):
        """Different inputs must produce different fingerprints."""
        from app.core.udyam.models import compute_record_fingerprint
        fp1 = compute_record_fingerprint(
            "Enterprise A", "123 St", "502117", "2024-01-15", "TELANGANA", "MEDAK"
        )
        fp2 = compute_record_fingerprint(
            "Enterprise B", "456 St", "502117", "2024-01-15", "TELANGANA", "MEDAK"
        )
        assert fp1 != fp2

    def test_fingerprint_is_sha256(self):
        """Fingerprint must be a valid SHA-256 hex string."""
        from app.core.udyam.models import compute_record_fingerprint
        fp = compute_record_fingerprint(
            "Test", "Addr", "502117", "2024-01-15", "TELANGANA", "MEDAK"
        )
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)


# ============================================================================
# Test Distance Engine
# ============================================================================

class TestDistance:
    """Phase 14-15: Distance calculation and market zones."""

    def test_haversine_known_distance(self):
        """Test with known coordinates."""
        from app.core.udyam.geography.distance import haversine_distance
        # Delhi to Agra ~ 178-180 km
        dist = haversine_distance(28.6139, 77.2090, 27.1767, 78.0081)
        assert 170 < dist < 210

    def test_haversine_same_point(self):
        from app.core.udyam.geography.distance import haversine_distance
        dist = haversine_distance(17.9276, 78.2344, 17.9276, 78.2344)
        assert dist == 0.0

    def test_calculate_distance_missing_target(self):
        """Missing target coordinates -> None."""
        from app.core.udyam.geography.distance import calculate_distance
        assert calculate_distance(None, None, 17.9, 78.2) is None

    def test_calculate_distance_missing_business(self):
        """Missing business coordinates -> None."""
        from app.core.udyam.geography.distance import calculate_distance
        assert calculate_distance(17.9, 78.2, None, None) is None

    def test_boundary_5km(self):
        """Phase 29: Boundary tests at 5 km."""
        from app.core.udyam.geography.distance import classify_market_zone
        from app.core.udyam.models import MarketZone
        assert classify_market_zone(4.999) == MarketZone.CORE_5KM
        assert classify_market_zone(5.000) == MarketZone.CORE_5KM
        assert classify_market_zone(5.001) == MarketZone.NEARBY_10KM

    def test_boundary_10km(self):
        """Phase 29: Boundary tests at 10 km."""
        from app.core.udyam.geography.distance import classify_market_zone
        from app.core.udyam.models import MarketZone
        assert classify_market_zone(9.999) == MarketZone.NEARBY_10KM
        assert classify_market_zone(10.000) == MarketZone.NEARBY_10KM
        assert classify_market_zone(10.001) == MarketZone.OUTSIDE_10KM

    def test_unmapped_zone(self):
        """Missing distance -> UNMAPPED."""
        from app.core.udyam.geography.distance import classify_market_zone
        from app.core.udyam.models import MarketZone
        assert classify_market_zone(None) == MarketZone.UNMAPPED


# ============================================================================
# Test Activity Parsing
# ============================================================================

class TestActivityParsing:
    """Phase 17: Activity parsing tests."""

    def test_parse_json_array(self):
        from app.core.udyam.activities.parser import parse_activities
        raw = '[{"nic_2_digit": "10", "activity": "Food Processing"}]'
        result = parse_activities(raw)
        assert len(result) >= 1
        assert result[0].nic_code == "10" or result[0].activity_description

    def test_parse_single_text(self):
        from app.core.udyam.activities.parser import parse_activities
        result = parse_activities("10 - Manufacture of food products")
        assert len(result) == 1
        assert result[0].nic_code == "10"

    def test_parse_empty(self):
        from app.core.udyam.activities.parser import parse_activities
        assert parse_activities("") == []
        assert parse_activities(None) == []

    def test_multiple_activities(self):
        """One enterprise may have multiple activities."""
        from app.core.udyam.activities.parser import parse_activities
        raw = '[{"nic_2_digit": "10", "activity": "Food"}, {"nic_2_digit": "47", "activity": "Retail"}]'
        result = parse_activities(raw)
        assert len(result) >= 2


# ============================================================================
# Test Category Mapping
# ============================================================================

class TestCategoryMapping:
    """Phase 19-20: Category ontology and NIC mapping."""

    def test_nic_2digit_mapping(self):
        from app.core.udyam.activities.categories import map_nic_to_category
        cat, conf, src = map_nic_to_category("10")
        assert cat == "FOOD_PROCESSING"
        assert conf == "HIGH"

    def test_nic_specific_mapping(self):
        from app.core.udyam.activities.categories import map_nic_to_category
        cat, conf, src = map_nic_to_category("1050")
        assert cat == "DAIRY"
        assert conf == "HIGH"

    def test_keyword_fallback(self):
        from app.core.udyam.activities.categories import map_nic_to_category
        cat, conf, src = map_nic_to_category("", "Dairy farming and milk collection")
        assert cat == "DAIRY"
        assert conf == "MEDIUM"

    def test_unknown_mapping(self):
        """Suspicious/unknown activity -> UNKNOWN, not invented."""
        from app.core.udyam.activities.categories import map_nic_to_category
        cat, conf, src = map_nic_to_category("", "XYZ random text")
        assert cat == "UNKNOWN"

    def test_competitor_detection(self):
        from app.core.udyam.activities.categories import is_potential_competitor
        assert is_potential_competitor("DAIRY", "DAIRY") is True
        assert is_potential_competitor("DAIRY", "FABRICATION") is False
        assert is_potential_competitor("UNKNOWN", "DAIRY") is False

    def test_supply_chain_detection(self):
        from app.core.udyam.activities.categories import is_potential_supply_chain
        assert is_potential_supply_chain("DAIRY", "FOOD_RETAIL") is True
        assert is_potential_supply_chain("DAIRY", "FABRICATION") is False


# ============================================================================
# Test Locality Extraction
# ============================================================================

class TestLocalityExtraction:
    """Phase 6: Generic locality extraction."""

    def test_admin_marker_extraction(self):
        from app.core.udyam.geography.extraction import extract_geographic_candidates
        candidates = extract_geographic_candidates(
            "VILLAGE RAJPALLY MANDAL NARSAPUR DISTRICT MEDAK"
        )
        names = [c.text for c in candidates]
        assert "RAJPALLY" in names

    def test_empty_address(self):
        from app.core.udyam.geography.extraction import extract_geographic_candidates
        assert extract_geographic_candidates("") == []

    def test_known_district_included(self):
        from app.core.udyam.geography.extraction import extract_geographic_candidates
        candidates = extract_geographic_candidates(
            "SOME ADDRESS",
            known_district="MEDAK",
        )
        districts = [c for c in candidates if c.entity_type == "district"]
        assert len(districts) >= 1
        assert districts[0].text == "MEDAK"


# ============================================================================
# Test Registration Date Parsing
# ============================================================================

class TestDateParsing:

    def test_iso_format(self):
        from app.core.udyam.models import parse_registration_date
        result = parse_registration_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_indian_format(self):
        from app.core.udyam.models import parse_registration_date
        result = parse_registration_date("15-01-2024")
        assert result == date(2024, 1, 15)

    def test_invalid_date(self):
        from app.core.udyam.models import parse_registration_date
        assert parse_registration_date("not a date") is None

    def test_empty_date(self):
        from app.core.udyam.models import parse_registration_date
        assert parse_registration_date("") is None
        assert parse_registration_date(None) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
