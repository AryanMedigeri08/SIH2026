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

import logging
import time
import uuid

# Reconfigure stdout/stderr for Unicode and emojis on Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


class SafeStreamHandler(logging.StreamHandler):
    """Console stream handler that safely handles Unicode/emoji encoding on all platforms."""
    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            try:
                msg = self.format(record)
                safe_msg = msg.encode("ascii", errors="replace").decode("ascii")
                self.stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)
        except Exception:
            self.handleError(record)


def configure_application_logging():
    """Configures explicit StreamHandler on 'udyam_saathi' namespace and root logger."""
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    console_handler.setFormatter(formatter)

    # 1. Attach directly to 'udyam_saathi' namespace (all app loggers descend from here)
    app_logger = logging.getLogger("udyam_saathi")
    app_logger.setLevel(logging.INFO)
    app_logger.handlers = [console_handler]
    app_logger.propagate = False

    # 2. Attach to root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [console_handler]

    # Suppress noisy external library logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("hpack").setLevel(logging.WARNING)


# Configure logging immediately on module import
configure_application_logging()

logger = logging.getLogger("udyam_saathi.api")

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings, validate_production_config
from app.database import db_manager
from app.models.schemas import HealthStatus
from app.routers import (
    locations_router,
    financial_router,
    feasibility_router,
    projects_router,
    data_sources_router,
    auth_router,
    translation_router,
    chat_router,
    market_intelligence_router,
    onboarding_router,
)
from app.core.telemetry import TelemetryMiddleware
from inference import ViabilityModelLoader


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure logging handlers are active across Uvicorn worker reload
    configure_application_logging()

    # Startup
    logger.info("=" * 80)
    logger.info("🚀 Udyam Saathi (उद्यम साथी) REST API Backend Starting...")
    logger.info("📡 Environment: Port 8000 | Docs: /docs | Health: /api/v2/health")
    
    # Safe production config audit
    cfg_report = validate_production_config()
    logger.info(f"⚙️ Configuration Audit: Status={cfg_report['status']} | Modes={cfg_report['modes']}")
    if cfg_report["warnings"]:
        for w in cfg_report["warnings"]:
            logger.info(f"ℹ️ Config notice: {w}")
    if cfg_report["missing_critical"]:
        for m in cfg_report["missing_critical"]:
            logger.error(f"❌ CRITICAL CONFIG MISSING: {m}")

    await db_manager.initialize()
    logger.info("💾 Database & In-Memory Fallback Subsystem Initialized.")
    # Preload ML model & SHAP Explainer into singleton memory
    loader = ViabilityModelLoader()
    model = loader.get_model()
    if model is not None:
        loader.get_explainer()
        loader.get_metadata()
        logger.info("🤖 Supervised XGBoost Viability Classifier & TreeSHAP Explainer Loaded.")
    else:
        logger.warning("⚠️ ML Model binary not found. Deterministic rule-based fallback active.")
    logger.info("=" * 80)

    yield
    # Shutdown
    logger.info("🛑 Udyam Saathi Backend Shutting Down...")
    await db_manager.close()
    logger.info("✅ Database connections closed cleanly.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Udyam Saathi (उद्यम साथी) — AI-Powered Rural & Semi-Urban Enterprise Feasibility & Bank Credit Advisory REST API.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V2_STR}/openapi.json",
    lifespan=lifespan,
)

# Correlation ID, Tracing & Latency Middleware (Gates 20, 21, 24)
app.add_middleware(TelemetryMiddleware)

# Configure CORS Middleware (Explicit origins with credentials support)
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
app.include_router(auth_router, prefix=settings.API_V2_STR)
app.include_router(locations_router, prefix=settings.API_V2_STR)
app.include_router(financial_router, prefix=settings.API_V2_STR)
app.include_router(feasibility_router, prefix=settings.API_V2_STR)
app.include_router(projects_router, prefix=settings.API_V2_STR)
app.include_router(data_sources_router, prefix=settings.API_V2_STR)
app.include_router(translation_router, prefix=settings.API_V2_STR)
app.include_router(chat_router, prefix=f"{settings.API_V2_STR}/chat", tags=["AI Chatbot & Groq Advisor"])
app.include_router(onboarding_router, prefix=f"{settings.API_V2_STR}/chat", tags=["Conversational Onboarding"])
app.include_router(onboarding_router, prefix=settings.API_V2_STR, tags=["Conversational Onboarding"])
app.include_router(market_intelligence_router, prefix=settings.API_V2_STR)
app.include_router(market_intelligence_router, prefix="")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
