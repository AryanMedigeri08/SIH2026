"""
backend/app/routers/__init__.py
"""
from .locations import router as locations_router
from .financial import router as financial_router
from .feasibility import router as feasibility_router
from .projects import router as projects_router
from .data_sources import router as data_sources_router
from .auth import router as auth_router
from .translation import router as translation_router
from .chat import router as chat_router
from .market_intelligence import router as market_intelligence_router
from .onboarding import router as onboarding_router

