"""
normalization.py — Address & Text Normalization for UDYAM Records.

Phase 5 of the implementation plan.

Operations:
    - Unicode normalization (NFKD)
    - Case normalization (uppercase)
    - Whitespace normalization (collapse multiple spaces)
    - Punctuation normalization (standardize separators)
    - Safe abbreviation expansion
    - Preservation of meaningful geographic tokens

CRITICAL: Do NOT aggressively remove geographic information.
    Example: "S KONDAPUR" must NOT become "KONDAPUR" automatically
    because similar names can represent distinct places.
"""

from __future__ import annotations
import re
import unicodedata


# Safe abbreviation expansions that do not risk losing geographic specificity
_SAFE_ABBREVIATIONS = {
    r'\bVILL\b': 'VILLAGE',
    r'\bVILL\.': 'VILLAGE',
    r'\bDIST\b': 'DISTRICT',
    r'\bDIST\.': 'DISTRICT',
    r'\bTAL\b': 'TALUKA',
    r'\bTAL\.': 'TALUKA',
    r'\bTEH\b': 'TEHSIL',
    r'\bTEH\.': 'TEHSIL',
    r'\bMDL\b': 'MANDAL',
    r'\bMDL\.': 'MANDAL',
    r'\bGP\b': 'GRAM PANCHAYAT',
    r'\bG\.P\.': 'GRAM PANCHAYAT',
    r'\bPO\b': 'POST OFFICE',
    r'\bP\.O\.': 'POST OFFICE',
    r'\bPS\b': 'POLICE STATION',
    r'\bP\.S\.': 'POLICE STATION',
    r'\bBLK\b': 'BLOCK',
    r'\bBLK\.': 'BLOCK',
    r'\bRD\b': 'ROAD',
    r'\bRD\.': 'ROAD',
    r'\bST\b': 'STREET',
    r'\bST\.': 'STREET',
    r'\bNR\b': 'NEAR',
    r'\bNR\.': 'NEAR',
    r'\bOPP\b': 'OPPOSITE',
    r'\bOPP\.': 'OPPOSITE',
    r'\bINDL\b': 'INDUSTRIAL',
    r'\bINDL\.': 'INDUSTRIAL',
}


def normalize_text_basic(text: str) -> str:
    """
    Basic text normalization: Unicode NFKD, uppercase, collapse whitespace.
    Does NOT remove geographic tokens. Safe for all field types.
    """
    if not text:
        return ""
    # Unicode normalization
    text = unicodedata.normalize("NFKD", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    # Uppercase
    text = text.upper()
    # Collapse multiple whitespace to single space
    text = re.sub(r'\s+', ' ', text)
    return text


def normalize_address(address: str) -> str:
    """
    Normalize a communication address for geographic parsing.

    Operations (in order):
        1. Unicode NFKD normalization
        2. Uppercase
        3. Remove specific noise punctuation (quotes, brackets)
        4. Normalize common separators (, ; / -) to spaces
        5. Expand safe abbreviations
        6. Collapse whitespace
        7. Preserve all geographic tokens

    Does NOT remove:
        - Directional prefixes (S, N, E, W) before place names
        - Numeric house/survey/gat numbers (these carry geographic signal)
        - Any token that could be a village/locality name
    """
    if not address:
        return ""

    # Step 1-2: Unicode + uppercase
    addr = unicodedata.normalize("NFKD", address)
    addr = addr.upper()

    # Step 3: Remove noise punctuation but preserve hyphen in number ranges
    # Remove: quotes, backticks, pipes, brackets (but not the content)
    addr = re.sub(r'["\'\`\|]', ' ', addr)
    addr = re.sub(r'[\[\]\(\)\{\}]', ' ', addr)

    # Step 4: Normalize separators
    # Commas, semicolons -> space (they typically separate address components)
    addr = re.sub(r'[,;]', ' ', addr)
    # Forward slashes between numbers are meaningful (survey numbers like 3/26)
    # but between words they're separators
    addr = re.sub(r'(?<=[A-Z])\s*/\s*(?=[A-Z])', ' ', addr)

    # Step 5: Expand safe abbreviations
    for pattern, expansion in _SAFE_ABBREVIATIONS.items():
        addr = re.sub(pattern, expansion, addr)

    # Remove dots that are not part of abbreviations (already expanded)
    # But preserve dots in numbers (e.g., "17.9276")
    addr = re.sub(r'(?<![0-9])\.(?![0-9])', ' ', addr)

    # Step 6: Collapse whitespace
    addr = re.sub(r'\s+', ' ', addr).strip()

    return addr


def normalize_pincode(pincode: Any) -> str:
    """
    Normalize an Indian PIN code. Must be exactly 6 digits.
    Handles float representations from government CSV/JSON exports (e.g. '110096.0').
    Returns empty string if invalid.
    """
    if pincode is None:
        return ""
    raw = str(pincode).strip()
    if not raw:
        return ""
    if "." in raw:
        raw = raw.split(".")[0].strip()
    cleaned = re.sub(r'\D', '', raw)
    if len(cleaned) == 6:
        return cleaned
    return ""


def normalize_state(state: str) -> str:
    """
    Normalize a state name. Handles known variations.
    Returns uppercase normalized form.
    """
    if not state:
        return ""
    s = normalize_text_basic(state)

    # Known state name variations
    _STATE_ALIASES = {
        "ANDHRA PRADESH": "ANDHRA PRADESH",
        "AP": "ANDHRA PRADESH",
        "ARUNACHAL PRADESH": "ARUNACHAL PRADESH",
        "ASSAM": "ASSAM",
        "BIHAR": "BIHAR",
        "CHHATTISGARH": "CHHATTISGARH",
        "CHATTISGARH": "CHHATTISGARH",
        "DELHI": "DELHI",
        "NCT OF DELHI": "DELHI",
        "GOA": "GOA",
        "GUJARAT": "GUJARAT",
        "HARYANA": "HARYANA",
        "HIMACHAL PRADESH": "HIMACHAL PRADESH",
        "HP": "HIMACHAL PRADESH",
        "JAMMU AND KASHMIR": "JAMMU AND KASHMIR",
        "JAMMU & KASHMIR": "JAMMU AND KASHMIR",
        "J&K": "JAMMU AND KASHMIR",
        "JHARKHAND": "JHARKHAND",
        "KARNATAKA": "KARNATAKA",
        "KERALA": "KERALA",
        "MADHYA PRADESH": "MADHYA PRADESH",
        "MP": "MADHYA PRADESH",
        "MAHARASHTRA": "MAHARASHTRA",
        "MANIPUR": "MANIPUR",
        "MEGHALAYA": "MEGHALAYA",
        "MIZORAM": "MIZORAM",
        "NAGALAND": "NAGALAND",
        "ODISHA": "ODISHA",
        "ORISSA": "ODISHA",
        "PUNJAB": "PUNJAB",
        "RAJASTHAN": "RAJASTHAN",
        "SIKKIM": "SIKKIM",
        "TAMIL NADU": "TAMIL NADU",
        "TAMILNADU": "TAMIL NADU",
        "TN": "TAMIL NADU",
        "TELANGANA": "TELANGANA",
        "TRIPURA": "TRIPURA",
        "UTTAR PRADESH": "UTTAR PRADESH",
        "UP": "UTTAR PRADESH",
        "UTTARAKHAND": "UTTARAKHAND",
        "UTTARANCHAL": "UTTARAKHAND",
        "WEST BENGAL": "WEST BENGAL",
        "WB": "WEST BENGAL",
        "ANDAMAN AND NICOBAR ISLANDS": "ANDAMAN AND NICOBAR ISLANDS",
        "ANDAMAN AND NICOBAR": "ANDAMAN AND NICOBAR ISLANDS",
        "CHANDIGARH": "CHANDIGARH",
        "DADRA AND NAGAR HAVELI AND DAMAN AND DIU": "DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
        "DADRA AND NAGAR HAVELI": "DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
        "DAMAN AND DIU": "DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
        "LAKSHADWEEP": "LAKSHADWEEP",
        "PUDUCHERRY": "PUDUCHERRY",
        "PONDICHERRY": "PUDUCHERRY",
        "LADAKH": "LADAKH",
    }
    return _STATE_ALIASES.get(s, s)


def normalize_district(district: str) -> str:
    """
    Normalize a district name. Basic normalization only —
    district alias resolution requires state context and is handled
    by the geographic resolver.
    """
    return normalize_text_basic(district)


def extract_tokens(normalized_address: str) -> list[str]:
    """
    Split a normalized address into individual tokens for geographic matching.
    Preserves token order (position matters for candidate extraction).
    """
    if not normalized_address:
        return []
    # Split on whitespace
    tokens = normalized_address.split()
    # Filter out very short tokens that are unlikely to be place names
    # But preserve single characters like "S" (could be directional prefix)
    return [t for t in tokens if t]
