
import logging
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

RESOURCE_URL = (
    "https://api.data.gov.in/resource/"
    "9ef84268-d588-465a-a308-a864a43d0070"
)


class MandiPriceService:

    async def get_prices(
        self,
        commodity: str,
        state: str,
        district: str,
    ) -> dict:

        api_key = os.getenv("DATAGOV_API_KEY")

        if not api_key:
            return {
                "data_status": "UNAVAILABLE",
                "message": "data.gov.in API key is not configured.",
                "records": [],
            }

        params = {
            "api-key": api_key,
            "format": "json",
            "limit": 100,
            "sort[arrival_date]": "desc",
        }

        if commodity:
            params["filters[commodity]"] = commodity

        if state:
            params["filters[state.keyword]"] = state

        if district:
            params["filters[district]"] = district

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    RESOURCE_URL,
                    params=params,
                )
                response.raise_for_status()
                payload = response.json()

            records = payload.get("records", [])

            return {
                "data_status": "LIVE",
                "message": (
                    "Market records retrieved from data.gov.in."
                    if records
                    else "No matching market records were returned."
                ),
                "total": payload.get("total", len(records)),
                "records": records,
            }

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Mandi API HTTP error: status=%s response=%s",
                exc.response.status_code,
                exc.response.text[:500],
            )
            return {
                "data_status": "UNAVAILABLE",
                "message": (
                    f"Government API returned HTTP "
                    f"{exc.response.status_code}."
                ),
                "records": [],
            }

        except httpx.RequestError as exc:
            logger.error(
                "Mandi API connection error: %s",
                type(exc).__name__,
            )
            return {
                "data_status": "UNAVAILABLE",
                "message": "Could not connect to the government market data service.",
                "records": [],
            }

        except ValueError:
            logger.exception("Mandi API returned invalid JSON.")
            return {
                "data_status": "UNAVAILABLE",
                "message": "Government API returned an invalid response.",
                "records": [],
            }
