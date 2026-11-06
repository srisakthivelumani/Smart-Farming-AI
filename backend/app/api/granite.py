"""
Granite connection test endpoint.
GET /api/granite/test — performs a real inference request and reports results.
"""
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.dependencies import get_granite_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/granite", tags=["granite"])


@router.get(
    "/test",
    summary="Test IBM Granite connectivity",
    description=(
        "Performs a real minimal inference request against IBM Granite via "
        "ibm-watsonx-ai SDK. Reports credential status, model availability, "
        "latency, token usage, and a Tamil generation quality probe. "
        "Never substitutes another LLM — if Granite is unreachable, the exact "
        "IBM error is returned."
    ),
)
async def test_granite_connection() -> JSONResponse:
    service = get_granite_service()
    result = service.test_connection()

    status_code = 200 if result.success else 503

    body = {
        "connection_test": {
            "success": result.success,
            "model_id": result.model_id,
            "endpoint": result.endpoint,
            "credentials": {
                "api_key_configured": result.api_key_configured,
                "project_id_configured": result.project_id_configured,
            },
        },
    }

    if result.success:
        body["inference_result"] = {
            "sample_response": result.sample_response,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "latency_seconds": result.latency_seconds,
            "note": (
                "Token counts above are deducted from your IBM Cloud Lite monthly "
                "allowance (300,000 tokens/month)."
            ),
        }
    else:
        body["error"] = {
            "type": result.ibm_error_type,
            "ibm_error": result.ibm_error_message,
            "action": (
                "Review the ibm_error field above for the exact IBM SDK message. "
                "Common causes: invalid API key, incorrect project ID, model not "
                "accessible on your account tier, or endpoint mismatch."
            ),
        }

    if result.tamil_test_attempted:
        body["tamil_generation_probe"] = {
            "attempted": True,
            "response": result.tamil_test_response,
            "note": result.tamil_test_note,
            "disclaimer": (
                "Granite 4 H Small does not officially advertise Tamil language support. "
                "The response above is the raw model output — evaluate quality manually "
                "before relying on Tamil generation in production."
            ),
        }
    else:
        body["tamil_generation_probe"] = {
            "attempted": False,
            "reason": "Skipped because the primary English inference test failed.",
        }

    return JSONResponse(status_code=status_code, content=body)
