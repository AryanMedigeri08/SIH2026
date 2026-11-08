"""Persist an accepted appraisal exactly once; never call an evaluator/provider."""
import uuid

from fastapi import HTTPException

from app.database import db_manager
from app.models.schemas import ProjectModel


async def save_selected_plan(owner: str, draft_id: str, selection: dict):
    evaluation = selection["evaluation"]
    inputs = selection["initial_data"]
    report = evaluation["report"]
    if inputs["available_margin_capital"] != report["input_parameters"]["available_margin_capital"]:
        raise HTTPException(409, "The contribution differs from this appraisal. Compare plans again.")
    # Stable across retries and workers. The client cannot supply a project ID.
    project_id = "proj_" + uuid.uuid5(uuid.NAMESPACE_URL, f"planning:{owner}:{draft_id}:{selection['proposal_id']}").hex
    existing = await db_manager.get_project(project_id)
    if existing and existing["user_id"] != owner:
        raise HTTPException(404, "Business not found.")
    payload = {
        "report": report, "dpr": evaluation["dpr"],
        "planning_selection": {"draft_id": draft_id, "proposal_id": selection["proposal_id"]},
    }
    # A retry also repairs a report save that failed after project persistence.
    await db_manager.save_feasibility_report(report["report_id"], payload, owner)
    if existing:
        return ProjectModel(**existing)
    record = await db_manager.create_project({
        **inputs, "project_id": project_id, "user_id": owner,
        "business_name": inputs["enterprise_name"], "investment_amount": inputs["project_cost"],
        "status": "analyzed", "analysis_result": payload,
    })
    return ProjectModel(**record)
