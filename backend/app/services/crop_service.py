import logging

from app.services.granite_service import GraniteService
from app.models.crop import CropRecommendationRequest

logger = logging.getLogger(__name__)


class CropRecommendationService:

    def __init__(self, granite_service: GraniteService):
        self.granite_service = granite_service

    def recommend_crops(
        self,
        request: CropRecommendationRequest
    ) -> dict:

        prompt = f"""
You are an agricultural assistant helping farmers.

Analyze the following farming conditions:

Location: {request.location}
Nitrogen (N): {request.nitrogen}
Phosphorus (P): {request.phosphorus}
Potassium (K): {request.potassium}
Temperature: {request.temperature} °C
Humidity: {request.humidity} %
Soil pH: {request.ph}
Rainfall: {request.rainfall} mm

Recommend three potentially suitable crops.

For each crop:
1. Give the crop name.
2. Explain why it may suit these conditions.
3. Mention one important cultivation consideration.

Use simple English.
Do not invent soil test results or guarantee crop success.
Mention that the recommendation requires local agricultural verification.

Format the answer clearly using numbered points.
"""

        response = self.granite_service.generate(
            prompt,
            max_new_tokens=500,
            temperature=0.2
        )

        return {
            "location": request.location,
            "recommendation": response.generated_text,
            "model_id": response.model_id,
            "latency_seconds": response.latency_seconds,
        }