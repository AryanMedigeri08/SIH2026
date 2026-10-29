"""Versioned catalogue candidates and deterministic capacity/budget selection."""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

CATALOGUE_PATH = Path(__file__).resolve().parents[1] / "data/msme_machinery_dataset.json"
UNIT_MAP = {
    "tonnes": ("kg", 1000), "ton": ("kg", 1000), "mt": ("kg", 1000),
    "kg": ("kg", 1), "kilograms": ("kg", 1), "g": ("kg", .001),
    "litres": ("litre", 1), "liters": ("litre", 1), "l": ("litre", 1),
    "litre": ("litre", 1), "ml": ("litre", .001),
}


def canonical_unit(unit):
    key = unit.strip().lower()
    return UNIT_MAP.get(key, (key, 1))


@lru_cache(maxsize=1)
def catalogue():
    raw = CATALOGUE_PATH.read_bytes()
    rows = json.loads(raw)
    result = []
    for row in rows:
        item = {**row, "profile_id": hashlib.sha256(row["business_name"].encode()).hexdigest()[:12]}
        result.append(item)
    return result, hashlib.sha256(raw).hexdigest()


def candidates(idea, sector, limit=5):
    rows, version = catalogue()
    tokens = set(re.findall(r"[a-z]{3,}", idea.lower())) - {
        "business", "unit", "enterprise", "want", "start", "small", "making", "processing", "manufacturing",
    }
    ranked = []
    for row in rows:
        terms = set(re.findall(r"[a-z]{3,}", " ".join(
            [row["business_name"], *row.get("search_keywords", [])]).lower()))
        score = len(tokens & terms)
        if score:
            ranked.append((score, row))
    selected = sorted(ranked, key=lambda pair: (-pair[0], pair[1]["profile_id"]))[:limit]
    return [{k: row[k] for k in (
        "profile_id", "business_name", "capacity_reference", "capacity_variants", "machinery_list", "variant_pricing"
    )} for _, row in selected], version


def monthly_input_capacity(variant, days, hours, availability):
    """Use structured capacity only. A stock capacity becomes stock-unit-days."""
    cap = variant["capacity"]
    _, factor = canonical_unit(cap["unit"])
    value = float(cap["quantity"]) * factor
    period = cap["period"]
    if period == "hour":
        value *= days * hours
    elif period == "day":
        value *= days * hours / 8  # explicit catalogue reference-shift assumption
    elif period == "month":
        value *= days / 26 * hours / 8
    elif period == "stock" and cap["capacity_kind"] == "storage":
        value *= days
    else:
        raise ValueError("Unsupported catalogue capacity period")
    return value * availability


def select_equipment(products, options, days, hours, availability, budget):
    """Choose affordable configurations; shared profiles have one capacity pool."""
    lookup = {row["profile_id"]: row for row in options}
    grouped = {}
    for product in products:
        if product.profile_id:
            if product.profile_id not in lookup:
                raise ValueError("Unknown machinery profile ID")
            grouped.setdefault(product.profile_id, []).append(product)
    variants = {pid: sorted(lookup[pid]["capacity_variants"], key=lambda v: v["total_machinery_cost_inr"])
                for pid in grouped}
    minima = sum(v[0]["total_machinery_cost_inr"] for v in variants.values())
    selected, spent = {}, 0
    warnings = []
    if minima > budget:
        warnings.append("Minimum complete machinery configurations exceed the equipment budget; production is zero until funded or outsourced.")
        return selected, warnings
    remaining_minima = minima
    for pid in sorted(grouped):
        row = lookup[pid]
        cheapest = variants[pid][0]["total_machinery_cost_inr"]
        remaining_minima -= cheapest
        allowed = [v for v in variants[pid] if v["total_machinery_cost_inr"] <= budget - spent - remaining_minima]
        members = grouped[pid]
        required = [sum(p.demand("base", m) / p.output_per_input.value for p in members) for m in range(12)]
        sufficient = [v for v in allowed if all(
            monthly_input_capacity(v, days[m], hours, availability) >= required[m] for m in range(12))]
        choice = sufficient[0] if sufficient else max(allowed, key=lambda v: v["capacity"]["quantity"])
        spent += choice["total_machinery_cost_inr"]
        selected[pid] = {
            "profile_id": pid, "business_name": row["business_name"], **choice,
            "monthly_input_capacity": [monthly_input_capacity(choice, d, hours, availability) for d in days],
            "canonical_capacity_unit": canonical_unit(choice["capacity"]["unit"])[0],
            "reference_shift_hours": 8, "reference_month_days": 26,
            "technical_suitability": "requires_supplier_confirmation",
        }
        if not sufficient:
            warnings.append(f"{row['business_name']}: affordable capacity is below base demand in some months; sales are capped.")
    if selected:
        warnings.append("Catalogue and scaled equipment costs are indicative estimates, not supplier quotations. Process suitability, power and installation require confirmation.")
    return selected, warnings
