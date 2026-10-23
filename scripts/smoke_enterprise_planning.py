"""Synthetic planning smoke check. Pass --live to exercise configured LLM providers."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.main import app  # Application import paths.
from app.core.chat_service import chat_service
from app.core.business_interpreter import interpret_business_idea
from app.core.enterprise_assumptions import estimate_operations, calculate_operations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    call = chat_service._call_llm_chat_completion if args.live else None
    idea = "A small paneer manufacturing business selling to households in a rural village"
    interpretation = interpret_business_idea(idea, call)
    assumptions = estimate_operations({
        "idea": idea, "sector": interpretation["sector"],
        "business_category": interpretation["business_category"], "project_cost": 500000,
        "households": 1000, "machinery_profile": interpretation["machinery_plan"],
        "amenities": {"power_supply_hours_per_day": 12, "provenance": "synthetic_smoke_fixture"},
        "cpi": {"annual_pct": 5, "source": "synthetic_smoke_fixture"},
        "evidence_type": "synthetic_test_data",
    }, call)
    operations = calculate_operations(assumptions)
    print(json.dumps({"interpretation_source": interpretation["interpretation_source"],
        "category": interpretation["business_category"], "type": interpretation["business_type"],
        "machines": len(interpretation["machinery_plan"]["machinery_list"]),
        "assumptions_source": assumptions["source_summary"], "model": assumptions["model"],
        "selling_price_inr": operations["selling_price_inr"], "output_unit": operations["output_unit"],
        "annual_sales": operations["annual_sales"]}, ensure_ascii=True))
    if args.live and (interpretation["interpretation_source"] != "llm_interpreted" or "llm_estimate" not in assumptions["field_sources"].values()):
        raise SystemExit("Planning fallback works, but the live LLM did not complete both steps.")


if __name__ == "__main__":
    main()
