import logging

from app.services.granite_service import GraniteService
from app.models.pest import PestAdvisoryRequest

logger = logging.getLogger(__name__)


class PestAdvisoryService:

    def __init__(self, granite_service: GraniteService):
        self.granite_service = granite_service

    def generate_advisory(self, request: PestAdvisoryRequest) -> dict:

        prompt = f"""
You are an agricultural pest and disease advisory assistant.

Farmer observations:

Crop: {request.crop}
Symptoms: {request.symptoms}
Affected plant part: {request.affected_part}
Duration: {request.duration}
Location: {request.location}

Provide:
1. Possible causes (do not claim a confirmed diagnosis).
2. Signs the farmer should inspect.
3. Safe immediate management practices.
4. Preventive measures.
5. When to consult an agricultural expert.

Do not invent a diagnosis.
Do not recommend unverified pesticide doses or chemical mixtures.
Prioritize integrated pest management (IPM).
Use simple English.
Clearly state that field inspection is required for confirmation.
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