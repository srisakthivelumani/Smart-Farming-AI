
"""
Weather service — retrieves live weather from OpenWeatherMap.
"""

import logging
import time
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(self):
        self.settings = get_settings()
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}

    async def get_weather(self, location: str) -> dict[str, Any]:
        location = location.strip()

        if not location:
            raise ValueError("Location cannot be empty.")

        if not self.settings.openweather_api_key:
            raise RuntimeError("OpenWeatherMap API key is not configured.")

        cache_key = location.lower()
        now = time.monotonic()

        cached = self._cache.get(cache_key)

        if cached:
            cached_time, cached_data = cached

            if now - cached_time < self.settings.weather_cache_ttl_seconds:
                return {**cached_data, "data_status": "CACHED"}

        url = f"{self.settings.openweather_base_url}/weather"

        params = {
            "q": location,
            "appid": self.settings.openweather_api_key,
            "units": "metric",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)

            if response.status_code == 404:
                raise ValueError(f"Location not found: {location}")

            if response.status_code == 401:
                raise RuntimeError("OpenWeatherMap API key is invalid or inactive.")

            response.raise_for_status()
            data = response.json()

            result = {
                "location": data["name"],
                "country": data["sys"]["country"],
                "temperature_c": data["main"]["temp"],
                "feels_like_c": data["main"]["feels_like"],
                "humidity_percent": data["main"]["humidity"],
                "pressure_hpa": data["main"]["pressure"],
                "weather": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "wind_speed_mps": data["wind"]["speed"],
                "cloudiness_percent": data["clouds"]["all"],
                "data_status": "LIVE",
            }

            self._cache[cache_key] = (now, result)

            return result

        except (ValueError, RuntimeError):
            raise

        except httpx.HTTPError as exc:
            logger.exception("OpenWeatherMap request failed.")
            raise RuntimeError("Unable to retrieve live weather data.") from exc

        except (KeyError, IndexError, TypeError) as exc:
            logger.exception("Unexpected OpenWeatherMap response format.")
            raise RuntimeError("Invalid weather data received from provider.") from exc
