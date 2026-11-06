"""
Health check endpoint.
GET /api/health — lightweight liveness probe; no external calls.
"""
import platform
import sys

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Application health check")
async def health_check() -> JSONResponse:
    settings = get_settings()
    return JSONResponse(
        content={
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
            "python": sys.version.split()[0],
            "platform": platform.system(),
            "granite": {
                "configured": settings.granite_is_configured,
                "model_id": settings.granite_model_id,
                "endpoint": settings.watsonx_url,
                "note": (
                    "configured=true means credentials are present in environment. "
                    "Call GET /api/granite/test for a real inference verification."
                ),
            },
            "external_apis": {
                "openweather": bool(settings.openweather_api_key),
                "datagov": bool(settings.datagov_api_key),
            },
        }
    )
