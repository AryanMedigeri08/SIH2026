"""
projects.py — REST API Router for User Projects State Persistence, Multi-Business Management & Status Evaluation.
"""

from __future__ import annotations
import uuid
import logging
from typing import Optional, Any
from fastapi import APIRouter, Query, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.database import db_manager
from app.models.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectModel,
    BusinessStatus,
    compute_business_status,
    UserInput,
)
from app.routers.feasibility import _run_pipeline
from app.core.auth_dependency import get_current_user, AuthenticatedUser
from dpr_generator import BankDPRDocument, dpr_to_printable_markdown, dpr_to_html

logger = logging.getLogger("udyam_saathi.projects")
router = APIRouter(prefix="/projects", tags=["Project State Persistence & Multi-Business Management"])


def _project_dict_to_user_input(p: dict[str, Any]) -> UserInput:
    """Helper to convert project dict into UserInput for pipeline execution."""
    return UserInput(
        enterprise_name=p.get("business_name") or p.get("enterprise_name", "Enterprise"),
        business_category=p.get("business_category", "manufacturing"),
        sector=p.get("sector", "general"),
        promoter_name=p.get("promoter_name", "Enterprise Promoter"),
        promoter_category=p.get("promoter_category", "general"),
        gender=p.get("gender", "Unspecified"),
        state_name=p.get("state_name", "West Bengal"),
        district_name=p.get("district_name", "Bankura"),
        block_name=p.get("block_name", "Joypur"),
        village_name=p.get("village_name", "Joypur"),
        is_rural=p.get("is_rural", True),
        project_cost=float(p.get("investment_amount") or p.get("project_cost", 500000.0)),
        annual_turnover_estimate=float(p.get("annual_turnover_estimate", 600000.0)),
        tenure_years=float(p.get("tenure_years", 5.0)),
        moratorium_months=int(p.get("moratorium_months", 6)),
        language=p.get("language", "en"),
        additional_business_details=p.get("additional_business_details"),
        monthly_net_operating_income_override=p.get("monthly_net_operating_income_override"),
    )


@router.post("", response_model=ProjectModel, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Creates a new persistent project record belonging to the authenticated user.
    If `auto_analyze=True`, immediately executes the feasibility pipeline, persists analysis result,
    and returns the fully analyzed ProjectModel with status.
    """
    project_dict = {
        "user_id": current_user.uid,
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
        "additional_business_details": project_in.additional_business_details,
        "monthly_net_operating_income_override": project_in.monthly_net_operating_income_override,
        "status": "draft",
        "analysis_result": None,
    }
    record = await db_manager.create_project(project_dict)

    if project_in.auto_analyze:
        user_input = _project_dict_to_user_input(record)
        report, dpr_doc = await _run_pipeline(user_input)
        analysis_payload = {
            "report": report.model_dump(mode="json"),
            "dpr": dpr_doc.to_dict(),
        }
        updated = await db_manager.update_project_analysis(record["project_id"], analysis_payload)
        if updated:
            record = updated

    return ProjectModel(**record)


@router.post("/create-and-analyze", response_model=ProjectModel, status_code=status.HTTP_201_CREATED)
async def create_and_analyze_project(
    project_in: ProjectCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Atomic creation and analysis endpoint:
    1. Persists the project draft under current_user.uid.
    2. Runs the statutory 4-tier feasibility appraisal pipeline.
    3. Persists full JSONB analysis result and Bank DPR document.
    4. Computes data-driven BusinessStatus (healthy | reconsideration | critical).
    5. Returns the complete ProjectModel.
    """
    project_dict = {
        "user_id": current_user.uid,
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
        "additional_business_details": project_in.additional_business_details,
        "monthly_net_operating_income_override": project_in.monthly_net_operating_income_override,
        "status": "draft",
        "analysis_result": None,
    }
    record = await db_manager.create_project(project_dict)

    user_input = _project_dict_to_user_input(record)
    report, dpr_doc = await _run_pipeline(user_input)

    analysis_payload = {
        "report": report.model_dump(mode="json"),
        "dpr": dpr_doc.to_dict(),
    }

    updated = await db_manager.update_project_analysis(record["project_id"], analysis_payload)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to persist analysis result.")

    return ProjectModel(**updated)


@router.get("", response_model=list[ProjectModel])
async def list_user_projects(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Lists all persistent business records belonging to the authenticated user.
    Each business includes its isolated data, analysis result, and computed BusinessStatus.
    """
    projects = await db_manager.list_projects(user_id=current_user.uid)
    return [ProjectModel(**p) for p in projects]


@router.get("/{project_id}", response_model=ProjectModel)
async def get_project_details(
    project_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Retrieves a single business record by ID with strict ownership verification (IDOR protection).
    """
    project = await db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Business '{project_id}' not found.")

    if project.get("user_id") != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to access this business record.",
        )

    return ProjectModel(**project)


@router.get("/{project_id}/status", response_model=BusinessStatus)
async def get_project_status(
    project_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Retrieves the institutional health, solvency, and viability status for a business.
    """
    project = await db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Business '{project_id}' not found.")

    if project.get("user_id") != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to access this business record.",
        )

    return compute_business_status(project.get("analysis_result"))


@router.post("/{project_id}/analyze", response_model=ProjectModel)
async def analyze_and_persist_project(
    project_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Runs the full feasibility pipeline for an existing project draft, updates project status,
    persists full JSONB analysis result and DPR, and returns the updated project model.
    """
    project = await db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Business '{project_id}' not found.")

    if project.get("user_id") != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to analyze this business record.",
        )

    user_input = _project_dict_to_user_input(project)
    report, dpr_doc = await _run_pipeline(user_input)

    analysis_payload = {
        "report": report.model_dump(mode="json"),
        "dpr": dpr_doc.to_dict(),
    }

    updated = await db_manager.update_project_analysis(project_id, analysis_payload)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update project analysis state.")

    return ProjectModel(**updated)


@router.patch("/{project_id}", response_model=ProjectModel)
@router.put("/{project_id}", response_model=ProjectModel)
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Updates enterprise parameters of an existing business with ownership verification.
    """
    project = await db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Business '{project_id}' not found.")

    if project.get("user_id") != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to modify this business record.",
        )

    update_data = project_in.model_dump(exclude_unset=True)
    if not update_data:
        return ProjectModel(**project)

    merged = {**project, **update_data}
    record = await db_manager.create_project(merged)
    return ProjectModel(**record)


@router.get("/{project_id}/dpr")
async def get_project_dpr(
    project_id: str,
    format: str = Query("json", description="Output format: json | markdown | html"),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Retrieves official 7-Section Bank DPR for a project with ownership verification."""
    project = await db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Business '{project_id}' not found.")

    if project.get("user_id") != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to access this project's DPR.",
        )

    analysis = project.get("analysis_result")
    if not analysis:
        # Run analysis on the fly
        await analyze_and_persist_project(project_id, current_user=current_user)
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


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
async def delete_project(
    project_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Deletes a business record owned by the authenticated user."""
    project = await db_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Business '{project_id}' not found.")

    if project.get("user_id") != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to delete this business record.",
        )

    await db_manager.delete_project(project_id, user_id=current_user.uid)
    return {"status": "success", "message": f"Business '{project_id}' deleted successfully."}
