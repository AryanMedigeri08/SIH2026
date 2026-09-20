"""
extraction.py — Generic Locality Extraction from UDYAM Communication Addresses.

Phase 6 of the implementation plan.

Extracts multiple geographic candidate entities from a normalized address.
Returns candidates with type, position, and extraction method.

Does NOT collapse multiple candidates into one geographic truth.
Does NOT create giant hardcoded state/district-specific alias dictionaries.

Entity types: village, hamlet, ward, town, taluka, tehsil, mandal,
              block, gram_panchayat, post_office, district, state, pincode
"""

from __future__ import annotations
import re
from typing import Optional
from ..models import GeographicCandidate


# Administrative keyword markers that signal the following/preceding
# token is a specific entity type. These are generic across India.
_ADMIN_MARKERS = {
    # village/locality markers
    "VILLAGE": "village",
    "VILL": "village",
    "GRAM": "village",

    # hamlet markers
    "HAMLET": "hamlet",
    "TOLA": "hamlet",
    "MAJRA": "hamlet",
    "PADA": "hamlet",
    "WADI": "hamlet",

    # ward markers
    "WARD": "ward",

    # town markers
    "TOWN": "town",
    "NAGAR": "town",
    "PURA": "town",
    "CITY": "town",

    # taluka/tehsil/mandal markers
    "TALUKA": "taluka",
    "TALUK": "taluka",
    "TEHSIL": "tehsil",
    "MANDAL": "mandal",
    "MDL": "mandal",

    # block markers
    "BLOCK": "block",
    "BLK": "block",

    # gram panchayat markers
    "GRAM PANCHAYAT": "gram_panchayat",
    "GP": "gram_panchayat",
    "PANCHAYAT": "gram_panchayat",

    # post office markers
    "POST OFFICE": "post_office",
    "POST": "post_office",
    "PO": "post_office",

    # district markers
    "DISTRICT": "district",
    "DIST": "district",
    "DT": "district",

    # state markers
    "STATE": "state",
}


# Noise tokens that should not be extracted as locality candidates
_NOISE_TOKENS = {
    "NEAR", "BEHIND", "BESIDE", "OPPOSITE", "FRONT", "BACK",
    "FLOOR", "PLOT", "SURVEY", "GAT", "KHASRA", "KHATA",
    "SHOP", "HOUSE", "FLAT", "ROOM", "BUILDING",
    "ROAD", "STREET", "LANE", "NAGAR", "COLONY", "LAYOUT",
    "CROSS", "MAIN", "BYE", "PASS",
    "INDUSTRIAL", "ESTATE", "AREA", "ZONE", "COMPLEX",
    "SHED", "GODOWN", "FACTORY", "UNIT", "WORKS",
    "NORTH", "SOUTH", "EAST", "WEST",
    "NEW", "OLD", "BIG", "SMALL",
    "NO", "NUMBER",
    "AND", "THE", "OF", "AT", "IN", "TO",
    "H", "C", "O",  # Common abbreviation noise (H/O = House Of, C/O = Care Of)
}


# Patterns that indicate a token is a house/survey number, not a place name
_NUMBER_PATTERNS = [
    re.compile(r'^\d+$'),                     # Pure number
    re.compile(r'^\d+[-/]\d+'),               # Number range: 3-26, 3/26
    re.compile(r'^\d+[A-Z]?$'),               # Number with suffix: 12A
    re.compile(r'^[A-Z]\d+$'),                # Letter-number: H123
]


def extract_geographic_candidates(
    normalized_address: str,
    known_state: str = "",
    known_district: str = "",
    known_pincode: str = "",
) -> list[GeographicCandidate]:
    """
    Extract potential geographic entities from a normalized address string.

    Returns multiple candidates ranked by extraction method.
    Does NOT determine the final correct locality — that is the resolver's job.

    Args:
        normalized_address: Address already processed by normalize_address()
        known_state: State from the UDYAM record (for context, not for extraction)
        known_district: District from the UDYAM record
        known_pincode: Pincode from the UDYAM record

    Returns:
        List of GeographicCandidate objects with type, position, and method
    """
    if not normalized_address:
        return []

    candidates: list[GeographicCandidate] = []
    tokens = normalized_address.split()

    # Strategy 1: Administrative marker extraction
    # Look for patterns like "VILLAGE RAJPALLY" or "MANDAL NARSAPUR"
    candidates.extend(
        _extract_by_admin_markers(tokens, normalized_address)
    )

    # Strategy 2: Positional heuristic extraction
    # After removing numbers, noise, and known admin hierarchy,
    # remaining tokens in specific positions are locality candidates
    candidates.extend(
        _extract_by_position(tokens, known_state, known_district)
    )

    # Strategy 3: Known district as candidate (always include if provided)
    if known_district:
        candidates.append(GeographicCandidate(
            text=known_district.upper(),
            entity_type="district",
            position=-1,
            method="api_field",
            confidence="HIGH",
        ))

    # Strategy 4: Known pincode as geographic signal
    if known_pincode:
        candidates.append(GeographicCandidate(
            text=known_pincode,
            entity_type="pincode",
            position=-1,
            method="api_field",
            confidence="HIGH",
        ))

    # Deduplicate by (text, entity_type) keeping highest confidence
    seen = set()
    unique_candidates = []
    for c in candidates:
        key = (c.text, c.entity_type)
        if key not in seen:
            seen.add(key)
            unique_candidates.append(c)

    return unique_candidates


def _extract_by_admin_markers(
    tokens: list[str],
    full_address: str,
) -> list[GeographicCandidate]:
    """
    Strategy 1: Find administrative markers and extract the token
    immediately following them as a locality candidate.

    Example: "VILLAGE RAJPALLY" -> candidate("RAJPALLY", type="village")
    Example: "MANDAL NARSAPUR" -> candidate("NARSAPUR", type="mandal")
    """
    candidates = []

    for i, token in enumerate(tokens):
        # Check single-token markers
        if token in _ADMIN_MARKERS and i + 1 < len(tokens):
            next_token = tokens[i + 1]
            if not _is_noise_or_number(next_token):
                entity_type = _ADMIN_MARKERS[token]
                # Position in original address
                pos = full_address.find(next_token)
                candidates.append(GeographicCandidate(
                    text=next_token,
                    entity_type=entity_type,
                    position=pos if pos >= 0 else i + 1,
                    method="admin_marker",
                    confidence="MEDIUM",
                ))

        # Check two-token markers (e.g., "GRAM PANCHAYAT")
        if i + 2 < len(tokens):
            two_token = f"{token} {tokens[i + 1]}"
            if two_token in _ADMIN_MARKERS:
                next_token = tokens[i + 2]
                if not _is_noise_or_number(next_token):
                    entity_type = _ADMIN_MARKERS[two_token]
                    pos = full_address.find(next_token)
                    candidates.append(GeographicCandidate(
                        text=next_token,
                        entity_type=entity_type,
                        position=pos if pos >= 0 else i + 2,
                        method="admin_marker",
                        confidence="MEDIUM",
                    ))

    return candidates


def _extract_by_position(
    tokens: list[str],
    known_state: str,
    known_district: str,
) -> list[GeographicCandidate]:
    """
    Strategy 2: Positional heuristic.

    After filtering out numbers, noise tokens, known state/district,
    and administrative markers, the remaining alpha tokens are
    potential locality names. Earlier tokens (closer to start of address)
    tend to be more local (hamlet/village), later tokens tend to be
    broader administrative divisions.

    Returns candidates with lower confidence than marker-based extraction.
    """
    candidates = []
    known_upper = {
        known_state.upper(),
        known_district.upper(),
    }
    # Remove empty strings from known set
    known_upper.discard("")

    # Filter tokens to potential place names
    place_tokens = []
    for i, token in enumerate(tokens):
        if _is_noise_or_number(token):
            continue
        if token in _ADMIN_MARKERS:
            continue
        if token in known_upper:
            continue
        if len(token) < 2:
            # Single character tokens (except directional prefixes)
            # are not standalone place names
            continue
        place_tokens.append((i, token))

    # Assign types based on position in filtered list
    for idx, (original_pos, token) in enumerate(place_tokens):
        # Heuristic: earlier tokens are more likely local,
        # later tokens are broader administrative units
        if idx < len(place_tokens) // 2 + 1:
            entity_type = "locality"  # Generic — could be village/hamlet/ward
        else:
            entity_type = "locality"  # Still generic at extraction stage

        candidates.append(GeographicCandidate(
            text=token,
            entity_type=entity_type,
            position=original_pos,
            method="positional_heuristic",
            confidence="LOW",
        ))

    return candidates


def _is_noise_or_number(token: str) -> bool:
    """Check if a token is noise or a number pattern."""
    if token in _NOISE_TOKENS:
        return True
    for pattern in _NUMBER_PATTERNS:
        if pattern.match(token):
            return True
    return False
