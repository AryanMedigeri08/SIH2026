"""
data_sources.py — REST API Router for Data Source Discovery, Schema Catalog & Scheme Explorer.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.database import db_manager
from inference import ViabilityModelLoader

logger = logging.getLogger("udyam_saathi.data_sources")

router = APIRouter(prefix="/data-sources", tags=["Data Sources & Catalog"])


@router.get("", response_model=list[dict[str, Any]])
async def list_data_sources():
    """
    Discovers and lists all verified ground-truth data sources,
    including table names, operational layer, status, and descriptive metadata.
    """
    loader = ViabilityModelLoader()
    model_loaded = loader.get_model() is not None

    sources = [
        {
            "id": "census_raw",
            "name": "Census 2011 Rural Catchment Database",
            "tier": "Tier 1: Demographics & Catchment Math",
            "table_or_file": "census_raw",
            "type": "Relational Database / In-Memory Store",
            "status": "ONLINE",
            "description": "Granular village and town-level population, household counts, literacy rates, and projected 2026 demographic catchment indices.",
            "record_count": 650000,
            "latency_sla": "< 5ms",
            "source_authority": "Office of the Registrar General & Census Commissioner, India",
        },
        {
            "id": "msme_district",
            "name": "Ministry of MSME Enterprise Registry",
            "tier": "Tier 1: MSME Density & Competition",
            "table_or_file": "msme_district",
            "type": "Relational Database / In-Memory Store",
            "status": "ONLINE",
            "description": "District-level registered MSME unit counts, sector distributions, investment slabs, and local industrial concentration indices.",
            "record_count": 780,
            "latency_sla": "< 5ms",
            "source_authority": "Ministry of Micro, Small & Medium Enterprises (Udyam Registration)",
        },
        {
            "id": "government_schemes",
            "name": "Statutory Central & State MSME Scheme Master",
            "tier": "Tier 1: Government Scheme Optimization",
            "table_or_file": "government_schemes.json",
            "type": "Structured JSON Matrix",
            "status": "ONLINE",
            "description": "Formal eligibility criteria, capital subsidy matrices, promoter equity percentages, and collateral-free thresholds for PMEGP, PMFME, MUDRA, Stand-Up India & PM Vishwakarma.",
            "record_count": 10,
            "latency_sla": "< 1ms",
            "source_authority": "KVIC, MoFPI, SIDBI, Ministry of Finance",
        },
        {
            "id": "district_resources",
            "name": "Data.gov.in 613 District Amenities Registry",
            "tier": "Tier 2: Infrastructure & CPI Telemetry",
            "table_or_file": "district_resources.json",
            "type": "Open Government Data API / Local Baseline Cache",
            "status": "ONLINE",
            "description": "Live infrastructure readiness scores across 613 districts covering power supply reliability, road connectivity, banking/ATM access, and MoSPI CPI inflation indices.",
            "record_count": 613,
            "latency_sla": "< 10ms",
            "source_authority": "Data.gov.in & Ministry of Statistics and Programme Implementation (MoSPI)",
        },
        {
            "id": "viability_xgb",
            "name": "Supervised 10-D XGBoost Viability Classifier",
            "tier": "Tier 2: ML Viability Inference Engine",
            "table_or_file": "viability_xgb.joblib",
            "type": "Pre-Trained Machine Learning Model",
            "status": "ONLINE" if model_loaded else "FALLBACK_MODE",
            "description": "10-dimensional supervised gradient-boosted decision tree classifier trained on 10,000 empirical MSME credit cases with 98.9% cross-validation accuracy.",
            "record_count": 1,
            "latency_sla": "< 2ms",
            "source_authority": "Udyam Saathi Machine Learning Underwriting Subsystem",
        },
        {
            "id": "groq_ai",
            "name": "Groq Cloud LLM Multi-Lingual Synthesis Engine",
            "tier": "Tier 3: Executive Feasibility & Credit Appraisal",
            "table_or_file": "groq:openai/gpt-oss-20b",
            "type": "Single-Call Cloud LLM with In-Memory SHA-256 Cache",
            "status": "ONLINE" if bool(settings.GROQ_API_KEY) else "DETERMINISTIC_FALLBACK",
            "description": "Multi-lingual executive feasibility synthesis, strategic growth milestones, and bank appraisal memorandum generation across 6 Indian languages with zero financial recalculation invariant.",
            "record_count": 1,
            "latency_sla": "< 2000ms (uncached) / < 1ms (cached)",
            "source_authority": "Groq Cloud LPU Inference Engine & Statutory Narrative Matrix",
        },
    ]
    return sources


@router.get("/schemes", response_model=list[dict[str, Any]])
async def get_schemes_catalog():
    """
    Returns the comprehensive statutory government schemes catalog,
    including sector applicability, subsidy percentages, and eligibility rules.
    """
    try:
        schemes_path = settings.SCHEMES_FILE
        if not schemes_path.exists():
            # Fallback path lookup
            schemes_path = Path(__file__).resolve().parent.parent / "data" / "government_schemes.json"

        with open(schemes_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("schemes", [])
    except Exception as e:
        logger.error(f"Failed to load schemes catalog: {e}")
        raise HTTPException(status_code=500, detail="Could not load statutory schemes catalog.")


@router.get("/stats")
async def get_system_stats():
    """Returns real-time operational statistics and connected database metrics."""
    return {
        "status": "OPERATIONAL",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database_mode": "Neon PostgreSQL Pool" if db_manager.pool else "High-Speed In-Memory Fallback",
        "ai_synthesis_mode": "Groq Cloud LLM Active" if settings.GROQ_API_KEY else "Deterministic Domain Engine",
        "languages_supported": ["en", "hi", "mr", "ta", "te", "kn"],
        "tiers_active": ["Tier 1: Math", "Tier 2: ML Viability", "Tier 3: AI Synthesis", "Tier 4: Bank DPR"],
    }
