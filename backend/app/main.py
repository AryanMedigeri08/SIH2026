"""
main.py — Udyam Saathi FastAPI REST Backend Application Entrypoint.
"""

from __future__ import annotations
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

# Add project root, backend, and core directories to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent
CORE_DIR = Path(__file__).resolve().parent / "core"
for p in (str(CORE_DIR), str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import db_manager
from app.models.schemas import HealthStatus
from app.routers import locations_router, financial_router, feasibility_router, projects_router
from inference import ViabilityModelLoader


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db_manager.initialize()
    # Preload ML model into singleton memory
    loader = ViabilityModelLoader()
    loader.get_model()
    yield
    # Shutdown
    await db_manager.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Udyam Saathi (उद्यम साथी) — SIH 2026 AI-Powered Rural & Semi-Urban Enterprise Feasibility & Bank Credit Advisory REST API.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V2_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Welcome to Udyam Saathi (उद्यम साथी) REST API v2",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": f"{settings.API_V2_STR}/health",
    }


@app.get("/health", response_model=HealthStatus, tags=["System"])
@app.get(f"{settings.API_V2_STR}/health", response_model=HealthStatus, tags=["System"])
async def health_check():
    """Returns overall health, database status, ML classifier status, and uptime."""
    loader = ViabilityModelLoader()
    model_loaded = loader.get_model() is not None

    return HealthStatus(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        database_connected=db_manager.pool is not None,
        ai_synthesizer_active=True,
        ml_classifier_loaded=model_loaded,
    )


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": request.url.path,
        },
    )


# Mount API v2 Routers
app.include_router(locations_router, prefix=settings.API_V2_STR)
app.include_router(financial_router, prefix=settings.API_V2_STR)
app.include_router(feasibility_router, prefix=settings.API_V2_STR)
app.include_router(projects_router, prefix=settings.API_V2_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
