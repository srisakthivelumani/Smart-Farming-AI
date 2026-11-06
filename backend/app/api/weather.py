
"""
Weather API — provides live weather information.
GET /api/weather/{location}
"""

import logging

from fastapi import APIRouter, HTTPException

from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["Weather"])

weather_service = WeatherService()


@router.get("/{location}", summary="Get live weather for a location")
async def get_weather(location: str):
    try:
        return await weather_service.get_weather(location)

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    except RuntimeError as exc:
        logger.exception("Weather service unavailable.")
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
