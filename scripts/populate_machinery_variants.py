"""Populate indicative capacity options from explicit catalogue reference data.

This is an offline catalogue authoring tool, not the runtime capacity parser.
Re-running it preserves every original reference specification and price.
"""
import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "backend/app/data/msme_machinery_dataset.json"
# Explicit reference quantities: never infer throughput from free-text specs.
# prefix, quantity, unit, period, material, capacity kind
REFERENCES = [
    ("Spice Grinding", 500, "kg", "day", "spice", "throughput"),
    ("Cold-Pressed", 200, "kg", "day", "seed", "throughput"),
    ("Mini Modern Rice", 1, "tonnes", "hour", "paddy", "throughput"),
    ("Automatic Dal", 1, "tonnes", "hour", "raw pulses", "throughput"),
    ("Commercial Semi-Automated Bakery", 300, "kg", "day", "bakery output", "throughput"),
    ("Dairy Processing", 1000, "litres", "day", "milk input", "throughput"),
    ("Fruit Juice", 500, "kg", "day", "fruit input", "throughput"),
    ("Honey Processing", 500, "kg", "day", "honey input", "throughput"),
    ("Soya Milk", 200, "kg", "day", "soya input", "throughput"),
    ("Solid Jaggery", 2, "tonnes", "day", "cane input", "throughput"),
    ("Cattle Feed", 1, "tonnes", "hour", "feed output", "throughput"),
    ("Cashew Nut", 500, "kg", "day", "raw nut input", "throughput"),
    ("Dehydrated Onion", 500, "kg", "day", "raw vegetable input", "throughput"),
    ("Commercial Atta", 1, "tonnes", "hour", "wheat input", "throughput"),
    ("Ayurvedic", 50000, "tablets", "hour", "tablet output", "throughput"),
    ("Steam Distillation", 500, "kg", "day", "herb input", "throughput"),
    ("Organic Bio-Fertilizer", 10, "tonnes", "day", "compost input", "throughput"),
    ("Detergent Powder", 1, "tonnes", "day", "detergent output", "throughput"),
    ("Corrugated Packaging", 3000, "boxes", "day", "box output", "throughput"),
    ("Biodegradable Paper Bag", 20000, "bags", "day", "bag output", "throughput"),
    ("Plastic Injection", 2000, "pieces", "hour", "moulded output", "throughput"),
    ("Non-Woven Fabric", 10000, "bags", "day", "bag output", "throughput"),
    ("Automatic Paper Cup", 30000, "cups", "day", "cup output", "throughput"),
    ("Precision CNC", 500, "components", "day", "machined components", "service"),
    ("Structural Steel", 50, "tonnes", "month", "steel input", "throughput"),
    ("Automatic Wire Nail", 1.5, "tonnes", "day", "nail output", "throughput"),
    ("Chain Link", 1, "tonnes", "day", "wire input", "throughput"),
    ("Aluminum Section", 60, "windows", "day", "window output", "throughput"),
    ("Automobile Workshop", 15, "vehicles", "day", "vehicles serviced", "service"),
    ("Readymade Garment", 300, "pieces", "day", "garment output", "throughput"),
    ("Multi-Head", 1500, "designs", "day", "embroidered designs", "throughput"),
    ("Sanitary Napkin", 3000, "pads", "hour", "pad output", "throughput"),
    ("Hydraulic Fly Ash", 15000, "bricks", "day", "brick output", "throughput"),
    ("Concrete Hollow", 2000, "blocks", "day", "block output", "throughput"),
    ("Plastic Waste", 500, "kg", "hour", "plastic input", "throughput"),
    ("Commercial Reverse", 2000, "litres", "hour", "treated water output", "throughput"),
    ("Mini Solar", 10, "tonnes", "stock", "stored produce", "storage"),
]


def populate(profiles):
    assert len(profiles) == len(REFERENCES)
    for prefix, quantity, unit, period, material, kind in REFERENCES:
        matches = [p for p in profiles if p["business_name"].startswith(prefix)]
        assert len(matches) == 1, prefix
        profile = matches[0]
        profile["capacity_reference"] = dict(quantity=quantity, unit=unit, period=period, material=material, capacity_kind=kind)
        profile["variant_pricing"] = {
            "source": "derived_catalogue_estimate",
            "basis": "Reference machine price × (0.25 + 0.75 × capacity_ratio^0.65); fixed equipment retains its price; multiple identical machines use whole quantities.",
            "fixed_cost_share": 0.25, "scaling_exponent": 0.65,
            "notice": "Indicative equipment estimates, not supplier quotations. Compact configurations and technical compatibility require supplier confirmation. Installation, premises and working capital are additional.",
        }
        variants = []
        for variant_id, factor in (("starter", .1), ("small", .25), ("medium", .5), ("reference", 1), ("expanded", 2)):
            amount = round(quantity * factor, 4)
            if unit not in {"kg", "litres", "tonnes"}:
                amount = math.ceil(amount)
            ratio = amount / quantity
            label = profile["typical_capacity"] if factor == 1 else f"{amount:g} {unit} {material}" + (" storage" if period == "stock" else f"/{period}")
            costs = []
            for machine in profile["machinery_list"]:
                name = machine["machine_name"].lower()
                ref_quantity = machine.get("quantity", 1)
                ref_price = machine["estimated_cost_inr"]
                # Instruments and single precision machines cannot simply shrink.
                fixed = any(word in name for word in ("scale", "meter", "tester", "analy", "tool kit", "toolkit", "cnc", "alignment")) and not any(word in name for word in ("chiller", "cooler", "plant", "mill"))
                scalable_vessels = any(word in name for word in ("tank", "pasteurizer", "ro plant"))
                if ref_quantity > 1 and not scalable_vessels:
                    count = max(1, math.ceil(ref_quantity * ratio))
                    price, model = ref_price, "whole_machine_quantity"
                elif fixed:
                    count, price, model = 1, ref_price, "fixed_equipment"
                else:
                    count = max(1, math.ceil(ref_quantity * ratio)) if ref_quantity > 1 else 1
                    per_machine_ratio = ratio * ref_quantity / count
                    price = round(ref_price * (.25 + .75 * per_machine_ratio ** .65) / 100) * 100
                    model = "capacity_cost_curve"
                costs.append(dict(machine_name=machine["machine_name"], quantity=count, estimated_cost_inr=price, pricing_model=model))
            variants.append({"variant_id": variant_id, "capacity": {**profile["capacity_reference"], "quantity": amount},
                "typical_capacity": label, "capacity_ratio": ratio, "machine_costs": costs,
                "total_machinery_cost_inr": sum(m["quantity"] * m["estimated_cost_inr"] for m in costs),
                "cost_source": "machinery_catalogue" if factor == 1 else "derived_catalogue_estimate"})
        profile["capacity_variants"] = variants
    return profiles


if __name__ == "__main__":
    profiles = populate(json.loads(DATA.read_text(encoding="utf-8")))
    DATA.write_text(json.dumps(profiles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Populated {len(profiles)} profiles with {sum(len(p['capacity_variants']) for p in profiles)} options")
