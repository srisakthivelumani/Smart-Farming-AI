import logging

from fastapi import APIRouter, HTTPException

from app.core.dependencies import GraniteServiceDep
from app.core.exceptions import (
    GraniteUnavailableError,
    GraniteNotConfiguredError,
)
from app.models.soil import SoilAdvisoryRequest
from app.services.soil_service import SoilAdvisoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/soil-advisory", tags=["Soil Advisory"])


@router.post("", summary="Get AI-powered soil advisory")
def get_soil_advisory(
    request: SoilAdvisoryRequest,
    granite_service: GraniteServiceDep,
):
    try:
        service = SoilAdvisoryService(granite_service)
        return service.generate_advisory(request)

    except (GraniteUnavailableError, GraniteNotConfiguredError):
        logger.exception("IBM Granite is unavailable.")
        raise HTTPException(
            status_code=503,
            detail="Soil advisory service is currently unavailable.",
        )

    except Exception:
        logger.exception("Soil advisory request failed.")
        raise HTTPException(
            status_code=502,
            detail="Unable to generate soil advisory.",
        )