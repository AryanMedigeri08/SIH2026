"""
projects.py — REST API Router for User Projects State Persistence & Analysis Lifecycle.
"""

from __future__ import annotations
import uuid
from typing import Optional, Any
from fastapi import APIRouter, Query, HTTPException, Header
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.database import db_manager
from app.models.schemas import ProjectCreate, ProjectUpdate, ProjectModel, UserInput
from app.routers.feasibility import _run_pipeline
from dpr_generator import BankDPRDocument, dpr_to_printable_markdown, dpr_to_html

router = APIRouter(prefix="/projects", tags=["Project State Persistence"])


@router.post("", response_model=ProjectModel, status_code=201)
async def create_project(
    project_in: ProjectCreate,
    user_id: str = Header("guest_user", alias="X-User-ID"),
):
    """Creates a new project draft record."""
    project_dict = {
        "user_id": user_id,
        "business_name": project_in.business_name,
        "business_category": project_in.business_category,
        "sector": project_in.sector,
        "investment_amount": project_in.investment_amount,
        "annual_turnover_estimate": project_in.annual_turnover_estimate,
        "state_name": project_in.state_name,
        "district_name": project_in.district_name,
        "block_name": project_in.block_name,
        "village_name": project_in.village_name,
        "promoter_name": project_in.promoter_name,
        "promoter_category": project_in.promoter_category,
        "gender": project_in.gender,
        "is_rural": project_in.is_rural,
        "tenure_years": project_in.tenure_years,
        "moratorium_months": project_in.moratorium_months,
        "language": project_in.language,
        "status": "draft",
        "analysis_result": None,
    }
    record = await db_manager.create_project(project_dict)
    return ProjectModel(**record)


@router.get("", response_model=list[ProjectModel])
async def list_user_projects(
    user_id: str = Header("guest_user", alias="X-User-ID"),
):
    """Lists all projects for the given user."""
    projects = await db_manager.list_projects(user_id=user_id)
    return [ProjectModel(**p) for p in projects]


@router.get("/{project_id}", response_model=ProjectModel)
async def get_project_details(project_id: str):
    """Retrieves single project record by ID."""
    project = await db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return ProjectModel(**project)


@router.post("/{project_id}/analyze", response_model=ProjectModel)
async def analyze_and_persist_project(project_id: str):
    """
    Runs the full feasibility pipeline for the project, updates project status to 'analyzed',
    persists full JSONB analysis result, and returns the updated project model.
    """
    project = await db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    # Convert project fields to UserInput
    user_input = UserInput(
        enterprise_name=project["business_name"],
        business_category=project["business_category"],
        sector=project["sector"],
        promoter_name=project.get("promoter_name", "Enterprise Promoter"),
        promoter_category=project.get("promoter_category", "general"),
        gender=project.get("gender", "Unspecified"),
        state_name=project["state_name"],
        district_name=project["district_name"],
        block_name=project.get("block_name", "N/A"),
        village_name=project.get("village_name", "N/A"),
        is_rural=project.get("is_rural", True),
        project_cost=project["investment_amount"],
        annual_turnover_estimate=project["annual_turnover_estimate"],
        tenure_years=project.get("tenure_years", 5.0),
        moratorium_months=project.get("moratorium_months", 6),
        language=project.get("language", "en"),
    )

    report, dpr_doc = await _run_pipeline(user_input)

    analysis_payload = {
        "report": report.model_dump(mode="json"),
        "dpr": dpr_doc.to_dict(),
    }

    updated = await db_manager.update_project_analysis(project_id, analysis_payload)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update project analysis state.")

    return ProjectModel(**updated)


@router.get("/{project_id}/dpr")
async def get_project_dpr(
    project_id: str,
    format: str = Query("json", description="Output format: json | markdown | html"),
):
    """Retrieves official 7-Section Bank DPR for a project (executing analysis if needed)."""
    project = await db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    analysis = project.get("analysis_result")
    if not analysis:
        # Run analysis on the fly
        await analyze_and_persist_project(project_id)
        project = await db_manager.get_project(project_id)
        analysis = project.get("analysis_result")

    dpr_dict = analysis["dpr"]
    dpr_doc = BankDPRDocument(**dpr_dict)

    fmt = format.lower().strip()
    if fmt == "html":
        return HTMLResponse(content=dpr_to_html(dpr_doc), media_type="text/html")
    elif fmt == "markdown":
        return PlainTextResponse(content=dpr_to_printable_markdown(dpr_doc), media_type="text/markdown")
    return dpr_dict
