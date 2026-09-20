"""
categories.py — Business Category Ontology & NIC Mapping.

Phase 19-20 of the implementation plan.

Provides:
    - Data-driven, extensible business category ontology
    - NIC code -> business category mapping hierarchy:
        NIC code -> official NIC meaning -> normalized category -> user intent
    - Retains original NIC information (never replaces raw values)

IMPORTANT:
    - Do not freeze the final ontology before inspecting activity distributions
      across multiple districts/states
    - The ontology should be data-driven and extensible
    - If the semantic mapping is uncertain: normalized_category = UNKNOWN
    - Do not invent a category from a suspicious label
"""

from __future__ import annotations
from typing import Optional
from ..models import ActivityRecord


# Initial extensible category ontology (Phase 19)
# These are starting categories — will be refined after cross-state data inspection
BUSINESS_CATEGORIES = {
    "FOOD_RETAIL": {
        "label": "Food & Grocery Retail",
        "description": "Retail sale of food items, grocery stores, kirana shops",
    },
    "GENERAL_RETAIL": {
        "label": "General Retail Trade",
        "description": "Non-food retail, hardware, stationery, electronics",
    },
    "TAILORING": {
        "label": "Tailoring & Garments",
        "description": "Custom tailoring, garment manufacturing, alterations",
    },
    "DAIRY": {
        "label": "Dairy & Milk Products",
        "description": "Dairy farming, milk processing, chilling, ghee, paneer",
    },
    "POULTRY": {
        "label": "Poultry Farming",
        "description": "Poultry rearing, egg production, hatcheries",
    },
    "GOAT_SHEEP": {
        "label": "Goat & Sheep Rearing",
        "description": "Goat farming, sheep rearing, wool",
    },
    "TRANSPORT": {
        "label": "Transport Services",
        "description": "Goods transport, passenger transport, auto-rickshaw",
    },
    "CONSTRUCTION": {
        "label": "Construction & Building",
        "description": "Construction contracting, masonry, building materials",
    },
    "FABRICATION": {
        "label": "Metal Fabrication & Welding",
        "description": "Steel fabrication, welding, metalworks, structural steel",
    },
    "MANUFACTURING": {
        "label": "General Manufacturing",
        "description": "Manufacturing activities not covered by specific categories",
    },
    "FOOD_PROCESSING": {
        "label": "Food Processing & Agro",
        "description": "Food processing, flour milling, oil pressing, pickle making",
    },
    "SERVICES": {
        "label": "General Services",
        "description": "Service activities including repair, maintenance, consulting",
    },
    "AGRICULTURE_SUPPORT": {
        "label": "Agriculture Support Services",
        "description": "Farm equipment rental, seed supply, fertilizer, irrigation",
    },
    "BEAUTY_WELLNESS": {
        "label": "Beauty & Wellness",
        "description": "Beauty parlour, salon, spa, wellness services",
    },
    "EDUCATION_TRAINING": {
        "label": "Education & Training",
        "description": "Tuition, coaching, skill training, computer education",
    },
    "HEALTHCARE": {
        "label": "Healthcare Services",
        "description": "Medical practice, pharmacy, diagnostics, dental",
    },
    "UNKNOWN": {
        "label": "Unclassified",
        "description": "Category could not be determined with sufficient confidence",
    },
}


# NIC 2-digit code to business category mapping
# Source: NIC-2008 (National Industrial Classification)
# Only mapping codes where the correspondence is clear and defensible
NIC_2DIGIT_TO_CATEGORY = {
    "01": "AGRICULTURE_SUPPORT",  # Crop and animal production
    "02": "AGRICULTURE_SUPPORT",  # Forestry
    "03": "AGRICULTURE_SUPPORT",  # Fishing and aquaculture
    "10": "FOOD_PROCESSING",      # Manufacture of food products
    "11": "FOOD_PROCESSING",      # Manufacture of beverages
    "13": "TAILORING",            # Manufacture of textiles
    "14": "TAILORING",            # Manufacture of wearing apparel
    "15": "MANUFACTURING",        # Manufacture of leather
    "16": "MANUFACTURING",        # Manufacture of wood products
    "17": "MANUFACTURING",        # Manufacture of paper products
    "20": "MANUFACTURING",        # Manufacture of chemicals
    "22": "MANUFACTURING",        # Manufacture of rubber/plastics
    "23": "CONSTRUCTION",         # Manufacture of non-metallic minerals (cement, bricks)
    "24": "FABRICATION",          # Manufacture of basic metals
    "25": "FABRICATION",          # Manufacture of fabricated metal products
    "28": "MANUFACTURING",        # Manufacture of machinery
    "29": "TRANSPORT",            # Manufacture of motor vehicles
    "31": "MANUFACTURING",        # Manufacture of furniture
    "33": "SERVICES",             # Repair and installation of machinery
    "41": "CONSTRUCTION",         # Construction of buildings
    "42": "CONSTRUCTION",         # Civil engineering
    "43": "CONSTRUCTION",         # Specialized construction
    "45": "GENERAL_RETAIL",       # Wholesale/retail trade of motor vehicles
    "46": "GENERAL_RETAIL",       # Wholesale trade
    "47": "FOOD_RETAIL",          # Retail trade
    "49": "TRANSPORT",            # Land transport
    "50": "TRANSPORT",            # Water transport
    "56": "FOOD_PROCESSING",      # Food and beverage service activities
    "62": "SERVICES",             # Computer programming/IT
    "68": "SERVICES",             # Real estate activities
    "85": "EDUCATION_TRAINING",   # Education
    "86": "HEALTHCARE",           # Human health activities
    "95": "SERVICES",             # Repair of computers and household goods
    "96": "BEAUTY_WELLNESS",      # Other personal service activities
}

# More specific 3-4 digit NIC mappings where 2-digit is too broad
NIC_SPECIFIC_TO_CATEGORY = {
    "0141": "DAIRY",              # Raising of cattle and buffaloes (dairy)
    "0143": "GOAT_SHEEP",         # Raising of horses and other equines
    "0144": "GOAT_SHEEP",         # Raising of sheep and goats
    "0145": "GOAT_SHEEP",         # Raising of swine/pigs
    "0146": "POULTRY",            # Raising of poultry
    "1050": "DAIRY",              # Manufacture of dairy products
    "105": "DAIRY",               # Dairy products
    "251": "FABRICATION",         # Manufacture of structural metal products
    "106": "FOOD_PROCESSING",     # Manufacture of grain mill products
    "107": "FOOD_PROCESSING",     # Manufacture of bakery products
    "141": "TAILORING",           # Manufacture of wearing apparel
    "4711": "FOOD_RETAIL",        # Retail sale in non-specialized stores (food)
    "4719": "GENERAL_RETAIL",     # Other retail in non-specialized stores
    "472": "FOOD_RETAIL",         # Retail sale of food, beverages in specialized stores
    "475": "GENERAL_RETAIL",      # Retail sale of other household equipment
    "476": "GENERAL_RETAIL",      # Retail sale of cultural and recreation goods (stationery, books)
    "4761": "GENERAL_RETAIL",     # Retail sale of books, newspapers, stationery
    "477": "GENERAL_RETAIL",      # Retail sale of other goods
    "4771": "GENERAL_RETAIL",     # Retail sale of clothing
    "4773": "HEALTHCARE",         # Dispensing chemist (pharmacy)
    "478": "FOOD_RETAIL",         # Retail sale via stalls and markets
    "479": "GENERAL_RETAIL",      # Retail sale not in stores
    "9602": "BEAUTY_WELLNESS",    # Hairdressing and other beauty treatment
}


# Keyword-based category inference for activity descriptions
# Only use when NIC code is missing or unmappable
# These must be conservative — only match when confidence is reasonable
_KEYWORD_RULES = [
    (["DAIRY", "MILK", "GHEE", "PANEER", "CURD", "CHEESE", "CREAMERY"], "DAIRY"),
    (["POULTRY", "CHICKEN", "EGG", "HATCHERY", "BROILER"], "POULTRY"),
    (["GOAT", "SHEEP", "MUTTON", "WOOL"], "GOAT_SHEEP"),
    (["TAILOR", "GARMENT", "STITCH", "BOUTIQUE", "APPAREL", "READYMADE"], "TAILORING"),
    (["FABRICAT", "WELD", "STEEL", "METAL", "IRON", "ALUMINIUM"], "FABRICATION"),
    (["FLOUR", "MILL", "ATTA", "CHAKKI", "OIL MILL", "RICE MILL", "DAL MILL"], "FOOD_PROCESSING"),
    (["GROCERY", "KIRANA", "PROVISION", "GENERAL STORE"], "FOOD_RETAIL"),
    (["HARDWARE", "ELECTRIC", "STATIONAR", "MOBILE", "COMPUTER"], "GENERAL_RETAIL"),
    (["TRANSPORT", "TRUCK", "AUTO", "RICKSHAW", "TAXI", "LOGISTICS"], "TRANSPORT"),
    (["CONSTRUCT", "BUILDING", "MASON", "BRICK", "CEMENT", "CONCRETE"], "CONSTRUCTION"),
    (["SALON", "PARLOUR", "PARLOR", "BEAUTY", "BARBER", "MEHNDI"], "BEAUTY_WELLNESS"),
    (["SCHOOL", "TUITION", "COACHING", "TRAINING", "EDUCATION"], "EDUCATION_TRAINING"),
    (["MEDICAL", "CLINIC", "HOSPITAL", "PHARMACY", "DOCTOR", "DENTAL"], "HEALTHCARE"),
    (["REPAIR", "SERVICE", "MAINTENANCE", "WORKSHOP"], "SERVICES"),
    (["FARM", "SEED", "FERTILIZ", "PESTICIDE", "TRACTOR", "IRRIGATION"], "AGRICULTURE_SUPPORT"),
]


def map_nic_to_category(
    nic_code: str,
    activity_description: str = "",
) -> tuple[str, str, str]:
    """
    Map a NIC code and/or activity description to a business category.

    Hierarchy per Phase 20:
        NIC code -> official NIC meaning -> normalized category

    Returns:
        Tuple of (normalized_category, confidence, validation_source)

    Confidence levels:
        HIGH: Direct NIC code match in mapping table
        MEDIUM: Keyword match in activity description
        LOW: Partial or ambiguous match
        UNKNOWN: Cannot determine category
    """
    # Strategy 1: Direct specific NIC code match (3-4 digit)
    if nic_code:
        for prefix_len in [4, 3]:
            prefix = nic_code[:prefix_len]
            if prefix in NIC_SPECIFIC_TO_CATEGORY:
                return (
                    NIC_SPECIFIC_TO_CATEGORY[prefix],
                    "HIGH",
                    f"nic_specific_{prefix}",
                )

        # Strategy 2: 2-digit NIC code match
        nic_2 = nic_code[:2]
        if nic_2 in NIC_2DIGIT_TO_CATEGORY:
            return (
                NIC_2DIGIT_TO_CATEGORY[nic_2],
                "HIGH",
                f"nic_2digit_{nic_2}",
            )

    # Strategy 3: Keyword-based inference from description
    if activity_description:
        desc_upper = activity_description.upper()
        for keywords, category in _KEYWORD_RULES:
            for kw in keywords:
                if kw in desc_upper:
                    return (
                        category,
                        "MEDIUM",
                        f"keyword_match_{kw.lower()}",
                    )

    # Cannot determine
    return ("UNKNOWN", "UNKNOWN", "no_match")


def enrich_activity_record(record: ActivityRecord) -> ActivityRecord:
    """
    Enrich an ActivityRecord with normalized category mapping.
    Does NOT modify raw fields — only fills in normalized_category,
    category_confidence, and validation_source.
    """
    category, confidence, source = map_nic_to_category(
        nic_code=record.nic_code,
        activity_description=record.activity_description,
    )
    record.normalized_category = category
    record.category_confidence = confidence
    record.validation_source = source
    return record


def get_category_label(category_code: str) -> str:
    """Get the human-readable label for a category code."""
    cat = BUSINESS_CATEGORIES.get(category_code)
    if cat:
        return cat["label"]
    return category_code


def is_potential_competitor(
    category_a: str,
    category_b: str,
) -> bool:
    """
    Determine if two businesses are potential competitors
    based on their normalized categories.

    Per Phase 16: A nearby business is NOT automatically a competitor.
    It becomes a potential competitor only after category relevance
    is established.

    Pipeline: nearby_business -> relevant_business -> potential_competitor
    """
    if category_a == "UNKNOWN" or category_b == "UNKNOWN":
        return False
    return category_a == category_b


def is_potential_supply_chain(
    category_a: str,
    category_b: str,
) -> bool:
    """
    Determine if two businesses have a potential supply-chain relationship.
    Based on deterministic input-output category pairs.
    """
    # Bidirectional supply-chain pairs
    supply_chain_pairs = {
        frozenset({"DAIRY", "FOOD_RETAIL"}),
        frozenset({"DAIRY", "FOOD_PROCESSING"}),
        frozenset({"AGRICULTURE_SUPPORT", "DAIRY"}),
        frozenset({"AGRICULTURE_SUPPORT", "FOOD_PROCESSING"}),
        frozenset({"AGRICULTURE_SUPPORT", "GOAT_SHEEP"}),
        frozenset({"AGRICULTURE_SUPPORT", "POULTRY"}),
        frozenset({"FABRICATION", "CONSTRUCTION"}),
        frozenset({"MANUFACTURING", "GENERAL_RETAIL"}),
        frozenset({"FOOD_PROCESSING", "FOOD_RETAIL"}),
        frozenset({"TAILORING", "GENERAL_RETAIL"}),
    }
    pair = frozenset({category_a, category_b})
    return pair in supply_chain_pairs
