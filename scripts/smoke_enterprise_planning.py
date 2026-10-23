"""Synthetic planning smoke check. Pass --live to exercise configured LLM providers."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.main import app  # Application import paths.
from app.core.chat_service import chat_service
from app.core.business_interpreter import interpret_business_idea
from app.core.machinery_variants import select_machinery_capacity
from app.core.enterprise_assumptions import estimate_operations, calculate_operations
from app.core.llm_financials import calculate_report_finance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--details", action="store_true", help="Print synthetic calculation inputs and results")
    parser.add_argument("--sizing-only", action="store_true", help="Exercise only catchment-led machinery selection")
    args = parser.parse_args()
    call = chat_service._call_llm_chat_completion if args.live else None
    idea = "A small paneer manufacturing business selling to households in a rural village"
    interpretation = interpret_business_idea(idea, None if args.sizing_only else call)
    evidence = {
        "idea": idea, "sector": interpretation["sector"],
        "business_category": interpretation["business_category"], "project_cost": 500000,
        "households": 1000, "machinery_profile": interpretation["machinery_plan"],
        "amenities": {"power_supply_hours_per_day": 12, "provenance": "synthetic_smoke_fixture"},
        "cpi": {"annual_pct": 5, "source": "synthetic_smoke_fixture"},
        "evidence_type": "synthetic_test_data",
    }
    plan = select_machinery_capacity(interpretation["machinery_plan"], evidence, call)
    evidence["machinery_profile"] = plan
    if args.sizing_only:
        print(json.dumps({"selected_variant": plan.get("selected_capacity_variant_id"),
            "capacity": plan.get("typical_capacity"), "equipment_cost_inr": plan.get("total_machinery_cost_inr"),
            "selection": plan.get("capacity_selection"), "funding_gap_inr": plan.get("equipment_funding_gap_inr")}, ensure_ascii=True))
        if args.live and plan.get("capacity_selection", {}).get("source") != "llm_capacity_selection":
            raise SystemExit("Indicative sizing works, but live LLM selection did not complete.")
        return
    assumptions = estimate_operations(evidence, call)
    operations = calculate_operations(assumptions)
    capacity = assumptions["capacity"]
    finance = calculate_report_finance(operations, {
        "project_cost": 500000, "loan_principal": 300000, "annual_rate_pct": 10,
        "tenure_years": 7, "moratorium_months": 6, "sector": interpretation["sector"],
        "cpi_pct": 5, "subsidy_amount": 100000, "promoter_margin": 100000,
    }, call)
    print(json.dumps({"interpretation_source": interpretation["interpretation_source"],
        "category": interpretation["business_category"], "type": interpretation["business_type"],
        "machines": len(interpretation["machinery_plan"]["machinery_list"]),
        "assumptions_source": assumptions["source_summary"], "model": assumptions["model"],
        "selling_price_inr": operations["selling_price_inr"], "output_unit": operations["output_unit"],
        "annual_sales": operations["annual_sales"], "capacity_source": capacity["source"],
        "operating_calculation_source": operations["calculation_source"],
        "financial_calculation_source": finance["source"], "financial_model": finance["model"],
        "dscr": finance["result"].dscr.dscr}, ensure_ascii=True))
    if args.details:
        print(json.dumps({"capacity": assumptions["capacity"], "values": assumptions["values"],
            "calculations": {key: value for key, value in operations.items() if key != "assumptions"},
            "first_year": finance["result"].projections[0].model_dump()}, ensure_ascii=True))
    if args.live and (interpretation["interpretation_source"] != "llm_interpreted" or
                     capacity["source"] != "llm_calculated" or operations["calculation_source"] != "llm_calculated" or
                     finance["source"] != "llm_calculated"):
        raise SystemExit("Fallback report works, but a live LLM calculation step did not complete.")


if __name__ == "__main__":
    main()
