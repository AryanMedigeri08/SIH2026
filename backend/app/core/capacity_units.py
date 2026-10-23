"""Legacy unit helpers. The deterministic capacity parser is temporarily disabled."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass


def canonical_unit(value: str) -> str:
    unit = (value or "units").lower().strip()
    aliases = {
        "kg": "kg", "kgs": "kg", "kilogram": "kg", "kilograms": "kg",
        "ton": "kg", "tons": "kg", "tonne": "kg", "tonnes": "kg", "mt": "kg",
        "g": "kg", "gram": "kg", "grams": "kg", "quintal": "kg", "quintals": "kg",
        "ml": "litres", "millilitre": "litres", "millilitres": "litres",
        "l": "litres", "liter": "litres", "liters": "litres", "litre": "litres", "litres": "litres",
        "piece": "pieces", "pieces": "pieces", "garment": "pieces", "garments": "pieces",
        "job": "jobs", "jobs": "jobs", "service": "jobs", "service jobs": "jobs",
        "unit": "units", "units": "units",
    }
    return aliases.get(unit, unit)


def unit_scale(value: str) -> float:
    unit = (value or "").lower().strip()
    if unit in {"ton", "tons", "tonne", "tonnes", "mt"}:
        return 1000
    if unit in {"quintal", "quintals"}:
        return 100
    if unit in {"g", "gram", "grams", "ml", "millilitre", "millilitres"}:
        return .001
    return 1


@dataclass
class Capacity:
    quantity: float
    unit: str
    period: str
    monthly_quantity: float | None
    basis: str

    def to_dict(self) -> dict:
        return asdict(self)


def parse_capacity(text: str, hours_per_day: float = 8, days_per_month: float = 25) -> Capacity:
    # Deterministic parser temporarily disabled at the user's request.
    # Kept commented below so it can be restored without losing its logic.
    return Capacity(0, "units", "unknown", None, "Deterministic parser disabled; capacity is interpreted by the LLM")
    # text = str(text or "").lower().replace(",", "")
    # match = re.search(r"(\d+(?:\.\d+)?)\s*([a-z]+)?", text)
    # if not match:
    #     return Capacity(0, "units", "unknown", None, "Operating throughput requires an estimate")
    # quantity = float(match[1])
    # raw_unit = match[2] or "units"
    # unit = canonical_unit(raw_unit)
    # quantity *= unit_scale(raw_unit)
    # periods = (("minute", r"(?:/|per\s+)\s*(?:min(?:ute)?s?)\b", 60 * hours_per_day * days_per_month),
    #            ("hour", r"(?:/|per\s+)\s*(?:h|hr|hrs|hours?)\b", hours_per_day * days_per_month),
    #            ("day", r"(?:/|per\s+)\s*(?:d|days?)\b", days_per_month),
    #            ("month", r"(?:/|per\s+)\s*(?:mo|months?)\b", 1),
    #            ("year", r"(?:/|per\s+)\s*(?:yr|years?)\b", 1 / 12))
    # # Only inspect the main capacity, not a second rate inside parentheses.
    # main = text.split("(")[0]
    # for period, pattern, multiplier in periods:
    #     if re.search(pattern, main):
    #         return Capacity(quantity, unit, period, round(quantity * multiplier, 4),
    #                         f"{hours_per_day:g} operating hours/day; {days_per_month:g} days/month")
    # kind = "batch" if "batch" in main else "stock" if "capacity" in main else "unknown"
    # return Capacity(quantity, unit, kind, None, "Batch frequency or inventory turnover requires an estimate")
