"""Read-only recalculation of a saved report; never saves or overwrites reports/projects."""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.main import app  # Configure application import paths.
from app.config import settings
from app.models.schemas import UserInput
from app.routers import feasibility


async def run(report_id: str, live: bool, budget_only: bool = False):
    import asyncpg
    pool = await asyncpg.create_pool(settings.DATABASE_URL.strip(), min_size=1, max_size=3, timeout=10)
    previous = feasibility.db_manager.pool
    feasibility.db_manager.pool = pool
    try:
        row = await pool.fetchrow("SELECT report_payload FROM feasibility_reports WHERE report_id = $1", report_id)
        if row is None:
            raise SystemExit("Report not found")
        saved = row["report_payload"]
        saved = json.loads(saved) if isinstance(saved, str) else saved
        if budget_only:
            from app.core.project_budget import estimate_project_budget
            f, inp = saved["financial_analysis"], saved["input_parameters"]
            operations = {**f["operating_model"], "assumptions": f["planning_assumptions"]}
            evidence = {**f["planning_assumptions"]["evidence"],
                "machinery_profile": inp.get("machinery_plan") or f["planning_assumptions"]["evidence"].get("machinery_profile") or {}}
            budget = estimate_project_budget(evidence, operations, inp.get("owned_machinery_value", 0),
                inp.get("owned_machines"), feasibility.chat_service._call_llm_chat_completion if live else None)
            print(json.dumps({"check": "budget only; historical operating inputs held fixed", "budget": budget}, ensure_ascii=True))
            return
        if not live:
            def offline(**kwargs):
                raise RuntimeError("Read-only offline recalculation")
            feasibility.chat_service._call_llm_chat_completion = offline
            from app.core.executive_synthesizer import ExecutiveSynthesis
            feasibility.generate_executive_synthesis = lambda *args, **kwargs: ExecutiveSynthesis(
                "Read-only calculation check", ["Review indicative assumptions"],
                "Indicative offline costs", "en", False, True, 0, "offline", "offline")
        report, dpr = await feasibility._run_pipeline(UserInput.model_validate(saved["input_parameters"]))
        f = report.financial_analysis
        budget = f["project_budget"]
        print(json.dumps({"saved_report_id": report_id, "persisted": False,
            "previous_dscr": saved["financial_analysis"]["dscr"]["dscr"],
            "annual_sales": f["gross_annual_sales"], "monthly_sales_units": f["operating_model"]["monthly_sales_units"],
            "average_selling_price": f["operating_model"]["selling_price_inr"],
            "saleable_unit": f["operating_model"].get("saleable_unit_definition"),
            "equipment_total": budget["equipment_total"], "owned_credit": budget["owned_machinery_credit"],
            "gross_project_cost": budget["gross_project_cost"], "net_fresh_outlay": budget["net_fresh_outlay"],
            "monthly_fixed_cost": budget["monthly_fixed_cost"], "budget_source": budget["source"],
            "loan_principal": f["loan_principal"], "monthly_emi": f["amortization"]["monthly_emi"],
            "year_one_dscr": f["dscr"]["dscr"], "full_repayment_year": f["first_full_repayment_year"],
            "average_dscr": f["average_dscr"], "operating_source": f["operating_model"]["calculation_source"],
            "financial_source": f["financial_calculation_source"],
            "finance_balanced": dpr.section_2_capital_outlay_and_finance["means_of_finance"]["reconciliation_balanced"]}, ensure_ascii=True))
    finally:
        feasibility.db_manager.pool = previous
        await pool.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_id")
    parser.add_argument("--live", action="store_true", help="Use configured LLM providers; default exercises indicative fallbacks")
    parser.add_argument("--budget-only", action="store_true", help="Validate just the itemized budget with historical operating inputs held fixed")
    args = parser.parse_args()
    asyncio.run(run(args.report_id, args.live, args.budget_only))
