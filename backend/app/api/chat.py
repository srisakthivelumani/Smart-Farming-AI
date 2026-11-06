"""
Chat API — RAG-powered agricultural assistant.
POST /api/chat
"""

import logging

from fastapi import APIRouter, HTTPException

from app.core.dependencies import RAGServiceDep
from app.models.chat import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    summary="Ask the Smart Farming AI assistant",
    description="Answers agricultural questions using RAG and IBM Granite.",
)
async def chat(
    request: ChatRequest,
    rag_service: RAGServiceDep,
):
    try:
        result = rag_service.ask_question(
            query=request.question,
            language=request.language,
        )

        return {
            "question": request.question,
            "language": request.language,
            "answer": result["answer"],
            "sources": result["sources"],
            "context_used": result["context_used"],
            "model_id": result["model_id"],
            "latency_seconds": result["latency_seconds"],
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except RuntimeError as exc:
        logger.exception("RAG service is not ready.")
        raise HTTPException(
            status_code=503,
            detail="Agricultural knowledge service is not ready.",
        ) from exc

    except Exception as exc:
        logger.exception("Chat request failed.")
        raise HTTPException(
            status_code=502,
            detail="Failed to generate an agricultural answer.",
        ) from exc