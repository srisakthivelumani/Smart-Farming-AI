"""
FastAPI dependency injection providers.
Services are instantiated once at startup and reused across requests.
"""
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings


# ── Settings dependency ───────────────────────────────────────────────────────

SettingsDep = Annotated[Settings, Depends(get_settings)]


# ── Granite service dependency ────────────────────────────────────────────────
# Imported here to avoid circular imports; the service module is the
# single authoritative place that initialises the IBM SDK client.

@lru_cache(maxsize=1)
def _get_granite_service():
    """
    Return a cached singleton GraniteService.
    Import is deferred so the SDK is only loaded when the service is first used,
    giving a clear startup error if ibm-watsonx-ai is not installed.
    """
    from app.services.granite_service import GraniteService
    return GraniteService(settings=get_settings())


def get_granite_service():
    return _get_granite_service()


GraniteServiceDep = Annotated[object, Depends(get_granite_service)]
# RAG service dependency

@lru_cache(maxsize=1)
def _get_rag_service():
    from app.services.rag.rag_service import RAGService

    service = RAGService(
        granite_service=get_granite_service(),
        settings=get_settings()
    )

    try:
        service.load_index()
    except FileNotFoundError:
        pass

    return service


def get_rag_service():
    return _get_rag_service()


RAGServiceDep = Annotated[object, Depends(get_rag_service)]