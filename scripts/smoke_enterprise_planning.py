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
from app.core.project_budget import estimate_project_budget, apply_project_budget, reconcile_funding


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--details", action="store_true", help="Print synthetic calculation inputs and results")
    parser.add_argument("--sizing-only", action="store_true", help="Exercise only catchment-led machinery selection")
    parser.add_argument("--operations-only", action="store_true", help="Exercise only saleable-unit conversion and monthly sales")
    parser.add_argument("--idea", default="A small paneer manufacturing business selling to households in a rural village")
    args = parser.parse_args()
    call = chat_service._call_llm_chat_completion if args.live else None
    idea = args.idea
    interpretation = interpret_business_idea(idea, None if args.sizing_only or args.operations_only else call)
    evidence = {
        "idea": idea, "sector": interpretation["sector"],
        "business_category": interpretation["business_category"], "project_cost": 500000,
        "households": 1000, "machinery_profile": interpretation["machinery_plan"],
        "amenities": {"power_supply_hours_per_day": 12, "provenance": "synthetic_smoke_fixture"},
        "cpi": {"annual_pct": 5, "source": "synthetic_smoke_fixture"},
        "evidence_type": "synthetic_test_data",
    }
    plan = select_machinery_capacity(interpretation["machinery_plan"], evidence, None if args.operations_only else call)
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
    if args.operations_only:
        print(json.dumps({"source": operations["calculation_source"], "model": assumptions["model"],
            "conversion": assumptions.get("conversion"), "capacity": capacity,
            "pricing": assumptions.get("pricing"), "price_comparison": operations.get("price_comparison"),
            "monthly_production_capacity": operations["monthly_saleable_capacity"],
            "monthly_sales_units": operations["monthly_sales_units"], "output_unit": operations["output_unit"],
            "selling_price_inr": operations["selling_price_inr"], "monthly_gross_sales": operations["monthly_gross_sales"],
            "annual_sales": operations["annual_sales"]}, ensure_ascii=True))
        if args.live and operations["calculation_source"] != "llm_calculated":
            raise SystemExit("Fallback report works, but live monthly production/sales conversion did not validate.")
        return
    budget = estimate_project_budget(evidence, operations, llm_call=call)
    operations = apply_project_budget(operations, budget)
    funding = reconcile_funding(budget, 100000)
    finance = calculate_report_finance(operations, {
        "project_cost": budget["net_fresh_outlay"], "loan_principal": funding["loan_required"], "annual_rate_pct": 10,
        "tenure_years": 7, "moratorium_months": 6, "sector": interpretation["sector"],
        "cpi_pct": 5, "subsidy_amount": 0, "promoter_margin": funding["cash_applied"],
        "depreciable_machinery_value": budget["equipment_total"],
    }, call)
    print(json.dumps({"interpretation_source": interpretation["interpretation_source"],
        "category": interpretation["business_category"], "type": interpretation["business_type"],
        "machines": len(interpretation["machinery_plan"]["machinery_list"]),
        "assumptions_source": assumptions["source_summary"], "model": assumptions["model"],
        "selling_price_inr": operations["selling_price_inr"], "output_unit": operations["output_unit"],
        "annual_sales": operations["annual_sales"], "capacity_source": capacity["source"],
        "operating_calculation_source": operations["calculation_source"],
        "financial_calculation_source": finance["source"], "financial_model": finance["model"],
        "budget_source": budget["source"], "gross_project_cost": budget["gross_project_cost"],
        "net_fresh_outlay": budget["net_fresh_outlay"], "loan_required": funding["loan_required"],
        "dscr": finance["result"].dscr.dscr}, ensure_ascii=True))
    if args.details:
        print(json.dumps({"capacity": assumptions["capacity"], "conversion": assumptions.get("conversion"), "pricing": assumptions.get("pricing"), "values": assumptions["values"],
            "calculations": {key: value for key, value in operations.items() if key != "assumptions"},
            "first_year": finance["result"].projections[0].model_dump()}, ensure_ascii=True))
    if args.live and (interpretation["interpretation_source"] != "llm_interpreted" or
                     capacity["source"] != "llm_calculated" or operations["calculation_source"] != "llm_calculated" or
                     finance["source"] != "llm_calculated" or budget["source"] != "llm_itemized_budget"):
        raise SystemExit("Fallback report works, but a live LLM calculation step did not complete.")


if __name__ == "__main__":
    main()
