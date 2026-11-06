import logging

from fastapi import APIRouter, HTTPException

from app.core.dependencies import GraniteServiceDep
from app.models.crop import CropRecommendationRequest
from app.services.crop_service import CropRecommendationService
from app.core.exceptions import GraniteUnavailableError, GraniteNotConfiguredError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crop-recommend", tags=["Crop Recommendation"])


@router.post("", summary="Get AI-powered crop recommendations")
def recommend_crops(
    request: CropRecommendationRequest,
    granite_service: GraniteServiceDep,
):
    try:
        service = CropRecommendationService(granite_service)
        return service.recommend_crops(request)

    except (GraniteUnavailableError, GraniteNotConfiguredError):
        logger.exception("IBM Granite is unavailable.")
        raise HTTPException(
            status_code=503,
            detail="Crop recommendation service is currently unavailable."
        )

    except Exception:
        logger.exception("Crop recommendation failed.")
        raise HTTPException(
            status_code=502,
            detail="Unable to generate crop recommendations."
        )