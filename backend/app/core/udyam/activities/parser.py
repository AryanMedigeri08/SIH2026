"""
parser.py — UDYAM Activities Field Parser.

Phase 17 of the implementation plan.

The `Activities` field in the UDYAM API is a JSON-encoded string
that may contain multiple activity records. Each enterprise can have
multiple activities.

IMPORTANT DISTINCTIONS:
    - enterprise count != activity count
    - One enterprise with multiple activities remains ONE enterprise
      and MULTIPLE activity rows

Stores:
    - nic_code (raw)
    - nic_description_raw
    - activity_description
    - normalized_category (Phase 19+)
    - category_confidence
    - validation_source
"""

from __future__ import annotations
import json
import re
import logging
from typing import Optional
from ..models import ActivityRecord

logger = logging.getLogger("udyam_saathi.activities")


def parse_activities(raw_activities: str) -> list[ActivityRecord]:
    """
    Parse the Activities field from a UDYAM API record.

    The field is typically a JSON-encoded string containing one or more
    activity entries with NIC codes and descriptions.

    Handles multiple known formats:
        - JSON array of objects
        - JSON object with numbered keys
        - Comma-separated NIC descriptions
        - Plain text descriptions

    Returns:
        List of ActivityRecord objects. Empty list if parsing fails.
    """
    if not raw_activities or not raw_activities.strip():
        return []

    raw = raw_activities.strip()

    # Strategy 1: Try JSON parsing
    activities = _try_json_parse(raw)
    if activities:
        return activities

    # Strategy 2: Try as a semicolon or pipe-separated list
    activities = _try_delimited_parse(raw, ";")
    if activities:
        return activities
    activities = _try_delimited_parse(raw, "|")
    if activities:
        return activities

    # Strategy 3: Try as a single activity description
    return _parse_single_activity(raw)


def _try_json_parse(raw: str) -> list[ActivityRecord]:
    """
    Attempt to parse Activities as JSON.
    Handles arrays of objects, single objects, and nested structures.
    """
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # Try fixing common JSON issues (single quotes, trailing commas)
        try:
            fixed = raw.replace("'", '"')
            fixed = re.sub(r',\s*}', '}', fixed)
            fixed = re.sub(r',\s*]', ']', fixed)
            data = json.loads(fixed)
        except (json.JSONDecodeError, ValueError):
            return []

    records = []

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                records.extend(_extract_from_dict(item))
            elif isinstance(item, str):
                records.extend(_parse_single_activity(item))
    elif isinstance(data, dict):
        records.extend(_extract_from_dict(data))
    elif isinstance(data, str):
        records.extend(_parse_single_activity(data))

    return records


def _extract_from_dict(d: dict) -> list[ActivityRecord]:
    """
    Extract activity records from a dictionary.
    Handles various key naming conventions observed in the UDYAM data.
    """
    records = []

    # Common key patterns for NIC code
    nic_keys = [
        "nic5digitid", "nic4digitid", "nic2digitid",
        "nic_2_digit", "nic_code", "nic", "nic_code",
        "nic_4_digit", "nic_5_digit", "nic5digit", "nic4digit", "nic2digit",
    ]
    # Common key patterns for activity description
    desc_keys = [
        "activity", "description", "activity_description",
        "nic_description", "name",
    ]

    nic_code = ""
    description = ""

    # Case-insensitive key lookup
    d_lower = {str(k).lower(): v for k, v in d.items()}

    # Find NIC code
    for key in nic_keys:
        if key in d_lower and d_lower[key] is not None:
            nic_code = str(d_lower[key]).strip()
            break

    # Find description
    for key in desc_keys:
        if key in d_lower and d_lower[key] is not None:
            description = str(d_lower[key]).strip()
            break

    # If we found at least something, create a record
    if nic_code or description:
        rec = ActivityRecord(
            nic_code=nic_code,
            nic_description_raw=description,
            activity_description=description,
            normalized_category="UNKNOWN",
            category_confidence="UNKNOWN",
        )
        try:
            from .categories import enrich_activity_record
            rec = enrich_activity_record(rec)
        except Exception:
            pass
        records.append(rec)
    else:
        # Try treating all values as descriptions
        for key, value in d.items():
            val = str(value).strip()
            if val and len(val) > 2:
                # Check if value looks like a NIC code
                if re.match(r'^\d{2,5}$', val):
                    nic_code = val
                else:
                    rec = ActivityRecord(
                        nic_code="",
                        nic_description_raw=val,
                        activity_description=val,
                        normalized_category="UNKNOWN",
                        category_confidence="UNKNOWN",
                    )
                    try:
                        from .categories import enrich_activity_record
                        rec = enrich_activity_record(rec)
                    except Exception:
                        pass
                    records.append(rec)

    return records


def _try_delimited_parse(raw: str, delimiter: str) -> list[ActivityRecord]:
    """
    Try parsing as a delimited list of activities.
    """
    parts = raw.split(delimiter)
    if len(parts) <= 1:
        return []

    records = []
    for part in parts:
        part = part.strip()
        if part:
            records.extend(_parse_single_activity(part))

    return records if records else []


def _parse_single_activity(text: str) -> list[ActivityRecord]:
    """
    Parse a single activity text string.
    Attempts to extract NIC code if present as a prefix.
    """
    text = text.strip()
    if not text:
        return []

    nic_code = ""
    description = text

    # Try to extract NIC code from common patterns
    # Pattern: "10 - Manufacture of food products"
    # Pattern: "1050 - Dairy Products"
    # Pattern: "NIC-10: Food Products"
    nic_patterns = [
        re.compile(r'^(\d{2,5})\s*[-:]\s*(.+)$'),
        re.compile(r'^NIC\s*[-:]?\s*(\d{2,5})\s*[-:]?\s*(.+)$', re.IGNORECASE),
        re.compile(r'^(\d{2,5})\s+(.+)$'),  # Just number followed by text
    ]

    for pattern in nic_patterns:
        match = pattern.match(text)
        if match:
            nic_code = match.group(1).strip()
            description = match.group(2).strip()
            break

    return [ActivityRecord(
        nic_code=nic_code,
        nic_description_raw=text,
        activity_description=description,
        normalized_category="UNKNOWN",
        category_confidence="UNKNOWN",
    )]
