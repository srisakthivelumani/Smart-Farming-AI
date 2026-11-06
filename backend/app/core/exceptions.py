"""
Custom application exceptions and FastAPI exception handlers.
"""
from fastapi import Request
from fastapi.responses import JSONResponse


class GraniteUnavailableError(Exception):
    """
    Raised when IBM Granite inference fails for any reason.
    The original IBM SDK error message is always preserved and surfaced —
    the application will NEVER silently fall back to another model.
    """

    def __init__(self, message: str, ibm_error: str | None = None):
        self.message = message
        self.ibm_error = ibm_error
        super().__init__(message)


class GraniteNotConfiguredError(Exception):
    """
    Raised when Granite credentials (API key or project ID) are missing from
    the environment. Indicates setup is incomplete — not a transient error.
    """


class ExternalAPIUnavailableError(Exception):
    """
    Raised when a third-party API (weather, mandi) is unreachable or returns
    an error. The application will display an explicit 'data unavailable'
    message rather than fabricating data.
    """

    def __init__(self, service: str, detail: str):
        self.service = service
        self.detail = detail
        super().__init__(f"{service}: {detail}")


class DocumentProcessingError(Exception):
    """Raised when a document cannot be parsed or chunked."""


# ── FastAPI exception handlers ────────────────────────────────────────────────

async def granite_unavailable_handler(
    request: Request, exc: GraniteUnavailableError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": "granite_unavailable",
            "message": exc.message,
            "ibm_error": exc.ibm_error,
            "suggestion": (
                "Check that WATSONX_API_KEY and WATSONX_PROJECT_ID are set correctly "
                "and that the model is available in your IBM Cloud account. "
                "Call GET /api/granite/test for a detailed connection report."
            ),
        },
    )


async def granite_not_configured_handler(
    request: Request, exc: GraniteNotConfiguredError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": "granite_not_configured",
            "message": str(exc),
            "suggestion": (
                "Set WATSONX_API_KEY and WATSONX_PROJECT_ID in your .env file. "
                "See .env.example for the full list of required variables."
            ),
        },
    )


async def external_api_unavailable_handler(
    request: Request, exc: ExternalAPIUnavailableError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": "external_api_unavailable",
            "service": exc.service,
            "message": exc.detail,
            "note": "Live data is unavailable. No fabricated data will be returned.",
        },
    )
