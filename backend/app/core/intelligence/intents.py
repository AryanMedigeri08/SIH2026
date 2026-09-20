"""
intents.py — Business Intent Modeling & Resolution.

Document 2, Section 5.

Translates an entrepreneur's freeform or pre-selected business ambition
into a structured intent representation with direct category anchors,
related supply-chain/complementary categories, and semantic search keywords.
"""

from __future__ import annotations
from typing import Optional
from .models import BusinessIntent

# Canonical Business Intent Catalog
INTENT_CATALOG: dict[str, BusinessIntent] = {
    "dairy": BusinessIntent(
        intent_id="dairy",
        display_name="Dairy Farming & Milk Processing",
        primary_category="DAIRY",
        direct_categories=["DAIRY"],
        related_categories=["FOOD_RETAIL", "FOOD_PROCESSING", "AGRICULTURE_SUPPORT"],
        search_keywords=["MILK", "DAIRY", "GHEE", "PANEER", "CURD", "CHILLING", "CATTLE", "BUFFALO"],
        description="Dairy animal rearing, fresh milk collection, chilling, and value-added dairy product production.",
    ),
    "kirana": BusinessIntent(
        intent_id="kirana",
        display_name="Grocery & Kirana Store",
        primary_category="FOOD_RETAIL",
        direct_categories=["FOOD_RETAIL"],
        related_categories=["GENERAL_RETAIL", "FOOD_PROCESSING", "DAIRY"],
        search_keywords=["KIRANA", "GROCERY", "PROVISION", "SUPERMARKET", "RATION", "GENERAL STORE"],
        description="Retail storefront supplying daily consumer staples, packed foods, grains, and household consumables.",
    ),
    "tailoring": BusinessIntent(
        intent_id="tailoring",
        display_name="Tailoring & Garment Manufacturing",
        primary_category="TAILORING",
        direct_categories=["TAILORING"],
        related_categories=["GENERAL_RETAIL", "MANUFACTURING"],
        search_keywords=["TAILOR", "GARMENT", "STITCHING", "BOUTIQUE", "DRESSMAKING", "EMBROIDERY", "APPAREL"],
        description="Custom stitching, apparel alteration, boutique garment production, and ready-made school/work uniforms.",
    ),
    "poultry": BusinessIntent(
        intent_id="poultry",
        display_name="Poultry Farming & Layer/Broiler Unit",
        primary_category="POULTRY",
        direct_categories=["POULTRY"],
        related_categories=["AGRICULTURE_SUPPORT", "FOOD_PROCESSING", "FOOD_RETAIL"],
        search_keywords=["POULTRY", "CHICKEN", "BROILER", "LAYER", "EGG", "HATCHERY", "BIRD FEED"],
        description="Commercial broiler meat rearing, layer egg production, and day-old chick nursery management.",
    ),
    "agro_processing": BusinessIntent(
        intent_id="agro_processing",
        display_name="Agro & Food Processing Unit (Flour / Dal / Oil Mill)",
        primary_category="FOOD_PROCESSING",
        direct_categories=["FOOD_PROCESSING"],
        related_categories=["FOOD_RETAIL", "AGRICULTURE_SUPPORT", "DAIRY"],
        search_keywords=["FLOUR MILL", "ATTA", "CHAKKI", "OIL MILL", "DAL MILL", "RICE MILL", "SPICE", "FOOD PROCESSING"],
        description="Post-harvest agro value addition, grain milling, mustard/groundnut oil expelling, and spice packaging.",
    ),
    "fabrication": BusinessIntent(
        intent_id="fabrication",
        display_name="Steel & Metal Fabrication Workshop",
        primary_category="FABRICATION",
        direct_categories=["FABRICATION"],
        related_categories=["CONSTRUCTION", "MANUFACTURING", "SERVICES"],
        search_keywords=["FABRICATION", "WELDING", "GRILL", "SHUTTER", "STEEL", "IRON", "ALUMINIUM", "GATE"],
        description="Structural steel fabrication, welding, window grills, rolling shutters, and agricultural implement repair.",
    ),
    "mobile_repair": BusinessIntent(
        intent_id="mobile_repair",
        display_name="Mobile Sales & Electronics Repair Center",
        primary_category="SERVICES",
        direct_categories=["SERVICES", "GENERAL_RETAIL"],
        related_categories=["GENERAL_RETAIL"],
        search_keywords=["MOBILE", "PHONE", "ELECTRONICS", "REPAIR", "ACCESSORIES", "CHARGER", "SMARTPHONE"],
        description="Handset repair, screen replacement, gadget accessories sales, and digital recharge services.",
    ),
    "beauty_salon": BusinessIntent(
        intent_id="beauty_salon",
        display_name="Beauty Parlour & Grooming Salon",
        primary_category="BEAUTY_WELLNESS",
        direct_categories=["BEAUTY_WELLNESS"],
        related_categories=["GENERAL_RETAIL"],
        search_keywords=["BEAUTY", "PARLOUR", "PARLOR", "SALON", "HAIRCUT", "MEHNDI", "MAKEUP", "BRIDAL"],
        description="Women's and men's personal grooming, skincare, bridal styling, and haircare services.",
    ),
    "transport": BusinessIntent(
        intent_id="transport",
        display_name="Rural Goods & Passenger Transport",
        primary_category="TRANSPORT",
        direct_categories=["TRANSPORT"],
        related_categories=["SERVICES"],
        search_keywords=["TRANSPORT", "GOODS", "AUTO", "RICKSHAW", "TEMPO", "TRUCK", "LOGISTICS", "CARRIER"],
        description="Last-mile agricultural freight carriage, mini-truck logistics, and rural passenger feeder transit.",
    ),
    "construction": BusinessIntent(
        intent_id="construction",
        display_name="Building Materials & Masonry Contracting",
        primary_category="CONSTRUCTION",
        direct_categories=["CONSTRUCTION"],
        related_categories=["FABRICATION", "MANUFACTURING"],
        search_keywords=["BRICK", "CEMENT", "SAND", "GRAVEL", "BUILDING", "CONSTRUCTION", "CONTRACTOR", "BLOCK"],
        description="Cement brick/block making, aggregate supply, sand retailing, and rural housing civil construction.",
    ),
}


def resolve_business_intent(user_input: str) -> BusinessIntent:
    """
    Resolve a user query or intent code into a structured BusinessIntent.
    Supports exact code match, keyword substring, and category fallback.
    """
    clean_input = user_input.lower().strip() if user_input else "general"

    # 1. Exact intent_id match
    if clean_input in INTENT_CATALOG:
        return INTENT_CATALOG[clean_input]

    # 2. Check keywords & display names
    for intent_id, intent in INTENT_CATALOG.items():
        if clean_input in intent.display_name.lower():
            return intent
        if clean_input in intent.primary_category.lower():
            return intent
        for kw in intent.search_keywords:
            if kw.lower() in clean_input or clean_input in kw.lower():
                return intent

    # 3. Fallback: Generic business intent mapped to uppercase category
    cat_code = clean_input.upper().replace(" ", "_")
    return BusinessIntent(
        intent_id=clean_input,
        display_name=user_input.title(),
        primary_category=cat_code,
        direct_categories=[cat_code],
        related_categories=["SERVICES", "GENERAL_RETAIL"],
        search_keywords=[clean_input.upper()],
        description=f"Commercial enterprise operating in {user_input}.",
    )


def list_all_intents() -> list[dict]:
    """Return all available predefined business intents for UI menus."""
    return [intent.to_dict() for intent in INTENT_CATALOG.values()]
