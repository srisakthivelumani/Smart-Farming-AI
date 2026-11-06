import logging

from app.services.granite_service import GraniteService
from app.models.soil import SoilAdvisoryRequest

logger = logging.getLogger(__name__)


class SoilAdvisoryService:

    def __init__(self, granite_service: GraniteService):
        self.granite_service = granite_service

    def generate_advisory(
        self,
        request: SoilAdvisoryRequest
    ) -> dict:

        prompt = f"""
You are an agricultural soil advisory assistant.

Analyze the following soil information:

Location: {request.location}
Soil type: {request.soil_type}
Current crop: {request.crop}

Nitrogen (N): {request.nitrogen}
Phosphorus (P): {request.phosphorus}
Potassium (K): {request.potassium}
Soil pH: {request.ph}

Provide a soil health advisory covering:

1. General interpretation of the supplied soil values.
2. Potential nutrient deficiencies or imbalances.
3. Soil pH management considerations.
4. Organic soil improvement practices.
5. Recommendations for further soil testing.

Use simple English.
Do not invent missing soil measurements.
Do not prescribe exact fertilizer quantities without sufficient soil
test information and locally applicable recommendations.
Mention that farmers should verify advice with local agricultural experts.

Format the response using clear headings and numbered points.
"""

        response = self.granite_service.generate(
            prompt,
            max_new_tokens=500,
            temperature=0.2
        )

        return {
            "location": request.location,
            "advisory": response.generated_text,
            "model_id": response.model_id,
            "latency_seconds": response.latency_seconds,
        }