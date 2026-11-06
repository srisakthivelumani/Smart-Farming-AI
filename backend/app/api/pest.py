import logging

from fastapi import APIRouter, HTTPException

from app.core.dependencies import GraniteServiceDep
from app.core.exceptions import (
    GraniteUnavailableError,
    GraniteNotConfiguredError,
)
from app.models.pest import PestAdvisoryRequest
from app.services.pest_service import PestAdvisoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pest-advisory", tags=["Pest Advisory"])


@router.post("")
def get_pest_advisory(
    request: PestAdvisoryRequest,
    granite_service: GraniteServiceDep,
):
    try:
        service = PestAdvisoryService(granite_service)
        return service.generate_advisory(request)

    except (GraniteUnavailableError, GraniteNotConfiguredError):
        logger.exception("Granite unavailable.")
        raise HTTPException(
            status_code=503,
            detail="Pest advisory service unavailable."
        )

    except Exception:
        logger.exception("Pest advisory failed.")
        raise HTTPException(
            status_code=502,
            detail="Unable to generate pest advisory."
        )