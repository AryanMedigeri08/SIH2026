"""
market_intelligence.py — FastAPI Router for UDYAM Village Market Intelligence.

Exposes Phase 33 API endpoints:
    - POST /api/v2/market-analysis — Full village intelligence & competitor pipeline
    - GET /api/v2/market-analysis/categories — Available business ontology categories
    - GET /api/v2/market-analysis/health — UDYAM API connectivity & cache status
"""

from __future__ import annotations
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query

from app.models.schemas import MarketAnalysisRequest, MarketAnalysisResponse
from app.core.udyam.pipeline import VillageIntelligencePipeline
from app.core.udyam.activities.categories import BUSINESS_CATEGORIES
from app.core.udyam.client import UdyamClient

logger = logging.getLogger("udyam_saathi.market_intelligence")

router = APIRouter(
    prefix="/market-analysis",
    tags=["UDYAM Village Intelligence & Competitor Analysis"],
)

# Shared pipeline instance
_pipeline: Optional[VillageIntelligencePipeline] = None


def get_pipeline() -> VillageIntelligencePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = VillageIntelligencePipeline()
    return _pipeline


@router.post(
    "",
    response_model=MarketAnalysisResponse,
    summary="Execute full UDYAM Village Intelligence & Market Analysis",
    description="""
    Given an Indian village/locality and an optional proposed business category,
    retrieves official UDYAM enterprise records, normalizes addresses, resolves
    geographic locations without fabricating coordinates, calculates distance-based
    market zones (<=5km, 5-10km), classifies potential competitors and suppliers,
    and returns comprehensive market intelligence with explicit limitations.
    """,
)
async def analyze_market(req: MarketAnalysisRequest) -> MarketAnalysisResponse:
    try:
        pipeline = get_pipeline()
        result = await pipeline.analyze(
            state=req.state.strip(),
            district=req.district.strip(),
            village=req.village.strip() if req.village else "",
            target_lat=req.target_lat,
            target_lon=req.target_lon,
            radius_km=req.radius_km,
            core_radius_km=req.core_radius_km,
            business_category=req.business_category.strip() if req.business_category else "",
            pincode=req.pincode.strip() if req.pincode else None,
            max_records=req.max_records,
        )
        return MarketAnalysisResponse(**result.to_dict())

    except ValueError as e:
        logger.warning(f"Validation error in market analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error executing market analysis pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Market analysis pipeline failed: {str(e)}",
        )


@router.get(
    "/categories",
    summary="List supported business category ontology",
    description="Returns all standard business categories used for MSME classification and competitor/supplier pairing.",
)
async def list_business_categories():
    categories = [
        {
            "code": code,
            "label": meta["label"],
            "description": meta["description"],
        }
        for code, meta in sorted(BUSINESS_CATEGORIES.items(), key=lambda x: x[1]["label"])
    ]
    return {
        "count": len(categories),
        "categories": categories,
    }


@router.get(
    "/health",
    summary="Check UDYAM intelligence service status and cache statistics",
)
async def udyam_health():
    try:
        pipeline = get_pipeline()
        stats = pipeline.gazetteer.get_statistics()
        cache_dir = pipeline.client.cache_dir
        cached_files_count = len(list(cache_dir.glob("**/*.json"))) if cache_dir.exists() else 0

        return {
            "status": "ready",
            "api_key_configured": bool(pipeline.client.api_key),
            "cache_dir": str(cache_dir),
            "cached_responses": cached_files_count,
            "gazetteer_statistics": stats,
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# Document 2: Opportunity Engine Endpoints
# ---------------------------------------------------------------------------
from app.models.schemas import (
    OpportunityAnalysisRequest,
    OpportunityAnalysisResponse,
    MultiCategoryCompareRequest,
    MultiCategoryCompareResponse,
)
from app.core.intelligence.engine import MarketOpportunityEngine
from app.core.intelligence.intents import list_all_intents
from app.core.adapters.registry import list_all_sources

_opportunity_engine: Optional[MarketOpportunityEngine] = None


def get_opportunity_engine() -> MarketOpportunityEngine:
    global _opportunity_engine
    if _opportunity_engine is None:
        _opportunity_engine = MarketOpportunityEngine(udyam_pipeline=get_pipeline())
    return _opportunity_engine


@router.post(
    "/opportunity",
    response_model=OpportunityAnalysisResponse,
    summary="Full MSME Market Intelligence & Opportunity Analysis (Document 2)",
    description="""
    Executes Document 2's end-to-end intelligence layer:
    - 5-class competitor relevance categorization
    - Supply concentration & distance metrics
    - Independent government demand/amenities indicators (Census, Antyodaya, ODOP)
    - Transparent opportunity score & guardrails
    - Explainability evidence object with positive drivers and limitations
    - Radius sensitivity & uncertainty stress testing
    """,
)
async def analyze_opportunity(req: OpportunityAnalysisRequest) -> OpportunityAnalysisResponse:
    try:
        engine = get_opportunity_engine()
        report = await engine.analyze_opportunity(
            state=req.state.strip(),
            district=req.district.strip(),
            village=req.village.strip() if req.village else "",
            target_lat=req.target_lat,
            target_lon=req.target_lon,
            business_intent=req.business_intent.strip(),
            radius_km=req.radius_km,
            core_radius_km=req.core_radius_km,
            pincode=req.pincode.strip() if req.pincode else None,
            max_records=req.max_records,
            base_population_2011=req.base_population_2011,
            snapshot_id=req.snapshot_id,
        )
        return OpportunityAnalysisResponse(**report.to_dict())
    except ValueError as e:
        logger.warning(f"Validation error in opportunity analysis: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Opportunity engine error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/compare",
    response_model=MultiCategoryCompareResponse,
    summary="Multi-category comparative opportunity evaluation",
    description="Compares multiple enterprise categories side-by-side for the same village location.",
)
async def compare_categories(req: MultiCategoryCompareRequest) -> MultiCategoryCompareResponse:
    try:
        engine = get_opportunity_engine()
        comps = await engine.compare_categories(
            state=req.state.strip(),
            district=req.district.strip(),
            village=req.village.strip() if req.village else "",
            target_lat=req.target_lat,
            target_lon=req.target_lon,
            categories=req.categories,
            radius_km=req.radius_km,
            max_records=req.max_records,
        )
        return MultiCategoryCompareResponse(
            state=req.state.strip(),
            district=req.district.strip(),
            village=req.village.strip() if req.village else "",
            comparisons=comps,
            count=len(comps),
        )
    except Exception as e:
        logger.error(f"Multi-category comparison error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/intents",
    summary="List predefined business intents and category anchors",
)
async def list_business_intents():
    intents = list_all_intents()
    return {"count": len(intents), "intents": intents}


@router.get(
    "/sources",
    summary="List government data sources and lineage metadata",
)
async def list_sources():
    sources = list_all_sources()
    return {"count": len(sources), "sources": sources}


# ---------------------------------------------------------------------------
# Document 5: Ecosystem Graph / Map Endpoints
# ---------------------------------------------------------------------------
from app.models.schemas import EcosystemGraphRequest, EcosystemGraphResponse
from app.core.intelligence.ecosystem_graph import (
    EcosystemGraphAdapter,
    validate_ecosystem_graph_request,
)

_graph_adapter: Optional[EcosystemGraphAdapter] = None


def get_graph_adapter() -> EcosystemGraphAdapter:
    global _graph_adapter
    if _graph_adapter is None:
        _graph_adapter = EcosystemGraphAdapter(
            opportunity_engine=get_opportunity_engine(),
        )
    return _graph_adapter


@router.post(
    "/ecosystem-graph",
    response_model=EcosystemGraphResponse,
    summary="Interactive Business Ecosystem Intelligence Graph (Document 5)",
    description="""
    Generates a versioned ecosystem graph data contract for dual-projection
    (Geographic + Topological) visualization. Consumes the existing validated
    MarketOpportunityEngine output and transforms it into graph nodes, derived
    edges, spatial catchments, temporal metadata, and provenance warnings.

    This endpoint is a READ-MODEL — it does NOT duplicate UDYAM ingestion or
    redefine market-intelligence scoring semantics.
    """,
)
async def generate_ecosystem_graph(req: EcosystemGraphRequest) -> EcosystemGraphResponse:
    # Validate input parameters
    errors = validate_ecosystem_graph_request(
        target_lat=req.target_lat,
        target_lon=req.target_lon,
        radius_km=req.radius_km,
    )
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ecosystem graph request: {'; '.join(errors)}",
        )

    try:
        adapter = get_graph_adapter()
        graph = await adapter.build_graph(
            state=req.state.strip(),
            district=req.district.strip(),
            village=req.village.strip() if req.village else "",
            target_lat=req.target_lat,
            target_lon=req.target_lon,
            business_intent=req.business_intent.strip(),
            radius_km=req.radius_km,
            visualization_radius_km=req.visualization_radius_km,
            pincode=req.pincode.strip() if req.pincode else None,
            max_records=req.max_records,
            snapshot_id=req.snapshot_id,
        )
        return EcosystemGraphResponse(**graph)
    except ValueError as e:
        logger.warning(f"Validation error in ecosystem graph: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Ecosystem graph generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ecosystem graph generation failed: {str(e)}",
        )

