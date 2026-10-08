"""Ground onboarding business intent in the local MSME machinery catalogue.

The catalogue contains plant profiles, not retail inventory. A shop that sells a
product must therefore never inherit a manufacturing plant merely because its
product name matches a catalogue keyword.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from .machinery_matcher import load_machinery_dataset


_PRODUCT_ALIASES = {
    "paneer": ("paneer", "पनीर"),
    "ghee": ("ghee", "घी"),
    "milk": ("milk", "दूध", "दुध"),
    "curd": ("curd", "dahi", "दही"),
    "spice": ("spice", "masala", "मसाला"),
    "bakery": ("bakery", "बेकरी"),
    "tofu": ("tofu", "soya paneer", "सोया पनीर"),
}
_RETAIL = ("shop", "store", "retail", "sell", "selling", "dukan", "dukkan", "dukaan", "दुकान", "बेचना", "बिक्री")
_PRODUCTION = ("make", "making", "manufacture", "produce", "processing", "factory", "plant", "unit", "banana", "banane", "बनाना", "बनाने", "निर्माण", "उत्पादन", "प्रोसेस")
_SECTOR_WORDS = {
    "dairy": ("paneer", "पनीर", "ghee", "घी", "milk", "दूध", "curd", "दही", "dairy", "डेयरी", "cheese", "ice cream", "आइसक्रीम"),
    "food_processing": ("spice", "masala", "मसाला", "bakery", "बेकरी", "oil", "तेल", "flour", "आटा", "juice", "जूस", "pickle", "अचार"),
    "apparel": ("garment", "tailor", "कपड़", "सिलाई", "boutique"),
    "repair": ("repair", "मरम्मत", "mechanic", "garage", "रिपेयर"),
    "fabrication": ("welding", "वेल्डिंग", "fabrication", "lathe"),
    "artisan_trades": ("pottery", "मिट्टी", "handicraft", "हस्तशिल्प"),
}


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _products(text: str) -> set[str]:
    return {name for name, aliases in _PRODUCT_ALIASES.items() if _has_any(text, aliases)}


def _candidates(text: str, sector: str) -> list[dict[str, Any]]:
    """Retrieve a small candidate set by catalogue keywords before any LLM call."""
    query_products = _products(text)
    ranked = []
    for profile in load_machinery_dataset():
        keywords = profile.get("search_keywords", [])
        haystack = " ".join((profile.get("business_name", ""), profile.get("where_used_application", ""), *keywords)).lower()
        score = sum(10 for product in query_products if product in haystack)
        score += sum(6 for keyword in keywords if len(keyword) > 3 and keyword.lower() in text)
        score += sum(2 for word in re.findall(r"[a-z]{4,}", text) if word in haystack)
        if sector == "dairy" and "dairy processing" in profile.get("business_name", "").lower():
            score += 8
        if score:
            ranked.append((score, profile))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [profile for _, profile in ranked[:3]]


def _relevant_machines(profile: dict[str, Any], idea: str) -> list[dict[str, Any]]:
    machines = profile.get("machinery_list", [])
    products = _products(idea)
    if not products or len(products) > 1:
        return machines
    product = next(iter(products))
    if product not in {"paneer", "ghee", "curd", "milk"} or "dairy processing" not in profile.get("business_name", "").lower():
        return machines
    # Shared milk handling, chilling, testing and packing equipment applies to
    # every dairy product. Product-specific vats/boilers must match the idea.
    product_terms = {"paneer": ("paneer", "cheese"), "ghee": ("ghee", "cream separator"), "curd": ("curd", "dahi"), "milk": ()}[product]
    all_product_terms = ("paneer", "cheese", "ghee", "cream separator", "curd", "dahi")
    return [machine for machine in machines if not _has_any(machine["machine_name"].lower(), all_product_terms) or _has_any(machine["machine_name"].lower(), product_terms)]


def interpret_business_idea(
    idea: str,
    llm_call: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Classify intent and return only catalogue-backed equipment and prices.

    The LLM sees at most three retrieved catalogue candidates. Its classification
    is validated and all machine names and costs are taken from the JSON dataset.
    """
    text = idea.strip().lower()
    sector = next((name for name, terms in _SECTOR_WORDS.items() if _has_any(text, terms)), "general")
    retail = _has_any(text, _RETAIL) and not _has_any(text, _PRODUCTION)
    category = "service" if retail or sector == "repair" or sector == "general" else "manufacturing"
    candidates = _candidates(text, sector)
    selected = None if retail else (candidates[0] if candidates else None)
    llm_machine_names = None

    if llm_call:
        prompt_candidates = [{
            "business_name": candidate["business_name"],
            "search_keywords": candidate.get("search_keywords", []),
            "machinery": [{"name": m["machine_name"], "cost_inr": m.get("estimated_cost_inr", 0)} for m in candidate.get("machinery_list", [])],
        } for candidate in candidates]
        try:
            content, _, _ = llm_call(
                messages=[
                    {"role": "system", "content": "Classify this Indian MSME idea. Return JSON only: sector (dairy, food_processing, apparel, repair, fabrication, artisan_trades, general), business_category (manufacturing or service), profile_name (exact candidate name or null), machine_names (exact candidate machine names relevant to the user's PRODUCT, not unrelated products). Retail shops that only sell finished goods have no manufacturing profile. Use only supplied candidate names and costs. Never invent equipment or prices."},
                    {"role": "user", "content": json.dumps({"idea": idea, "catalogue_candidates": prompt_candidates}, ensure_ascii=False)},
                ], temperature=0.1, max_tokens=280, timeout_s=8.0,
            )
            parsed = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip()) if content else {}
            if parsed.get("sector") in (*_SECTOR_WORDS.keys(), "general") and (sector == "general" or parsed["sector"] == sector):
                sector = parsed["sector"]
            if parsed.get("business_category") in ("manufacturing", "service") and not _has_any(text, _PRODUCTION):
                category = parsed["business_category"]
            if not retail and category == "manufacturing":
                selected = next((candidate for candidate in candidates if candidate["business_name"] == parsed.get("profile_name")), selected)
                if isinstance(parsed.get("machine_names"), list):
                    llm_machine_names = set(parsed["machine_names"])
        except Exception:
            pass  # Deterministic retrieval remains available when the LLM fails.

    if retail:
        category = "service"
        selected = None
    if category != "manufacturing":
        selected = None
    machines = _relevant_machines(selected, text) if selected else []
    if llm_machine_names:
        filtered = [m for m in machines if m["machine_name"] in llm_machine_names]
        if filtered:
            machines = filtered
    return {
        "business_idea": idea.strip(),
        "sector": sector,
        "business_category": category,
        "matched_machinery_profile": selected["business_name"] if selected else None,
        "machinery_plan": {
            "business_name": selected["business_name"] if selected else None,
            "category": selected.get("category") if selected else None,
            "industry_sector": selected.get("industry_sector") if selected else None,
            "typical_capacity": selected.get("typical_capacity") if selected else None,
            "total_machinery_cost_inr": sum(m.get("estimated_cost_inr", 0) * m.get("quantity", 1) for m in machines),
            "machinery_list": machines,
        },
    }
