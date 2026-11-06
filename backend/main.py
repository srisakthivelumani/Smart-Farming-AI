"""
FastAPI application entry point.

Mounts all API routers and registers exception handlers.
Run with:  uvicorn main:app --reload --port 8000
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import (
    ExternalAPIUnavailableError,
    GraniteNotConfiguredError,
    GraniteUnavailableError,
    external_api_unavailable_handler,
    granite_not_configured_handler,
    granite_unavailable_handler,
)
from app.api import chat, granite, health, knowledge
from app.api import chat, crop, granite, health, knowledge, mandi, pest, soil, weather
# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Settings ──────────────────────────────────────────────────────────────────
settings = get_settings()

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered Smart Farming Assistant for Indian farmers. "
        "Uses IBM Granite (ibm-watsonx-ai) via RAG for agricultural advice."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
app.add_exception_handler(GraniteUnavailableError, granite_unavailable_handler)
app.add_exception_handler(GraniteNotConfiguredError, granite_not_configured_handler)
app.add_exception_handler(ExternalAPIUnavailableError, external_api_unavailable_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
# Phase 1 — foundation
app.include_router(health.router, prefix="/api")
app.include_router(granite.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(weather.router, prefix="/api")
app.include_router(crop.router, prefix="/api")
app.include_router(soil.router, prefix="/api")
app.include_router(pest.router, prefix="/api")
app.include_router(mandi.router, prefix="/api")
# Phase 2+ routers will be added here as each phase is implemented:
# app.include_router(chat.router,     prefix="/api")
# app.include_router(crop.router,     prefix="/api")
# app.include_router(weather.router,  prefix="/api")
# app.include_router(soil.router,     prefix="/api")
# app.include_router(pest.router,     prefix="/api")
# app.include_router(mandi.router,    prefix="/api")
# app.include_router(knowledge.router,prefix="/api")

logger.info(
    "%s v%s starting | granite_configured=%s | model=%s",
    settings.app_name,
    settings.app_version,
    settings.granite_is_configured,
    settings.granite_model_id,
)
