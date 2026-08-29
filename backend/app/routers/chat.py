"""
chat.py — REST API Router for Persistent Groq Chatbot & Enterprise Advisor.
"""

from __future__ import annotations
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

try:
    from app.core.chat_service import chat_service
except ImportError:
    from backend.app.core.chat_service import chat_service

logger = logging.getLogger("udyam_saathi.api.chat")

router = APIRouter()


class ChatMessagePayload(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="Message text content")


class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessagePayload] = Field(..., min_length=1, description="List of chat messages in conversation")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Active enterprise and report telemetry context")
    language: Optional[str] = Field(default="en", description="Target response language code (en, hi, mr, ta, te, kn)")


class ChatCompletionResponse(BaseModel):
    message: Dict[str, str]
    model: str
    is_fallback: bool
    latency_ms: float


@router.post(
    "",
    response_model=ChatCompletionResponse,
    summary="Send message to Groq AI Advisor with active enterprise grounding",
)
async def create_chat_completion(payload: ChatCompletionRequest):
    """
    Submits user messages to Groq Cloud LLM with active enterprise telemetry grounding.
    """
    try:
        raw_messages = [{"role": m.role, "content": m.content} for m in payload.messages]
        result = chat_service.generate_chat_response(
            messages=raw_messages,
            context=payload.context,
            language=payload.language or "en",
        )
        return result
    except Exception as e:
        logger.error("Chat completion error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chatbot failed to process message: {str(e)}",
        )


@router.get(
    "/health",
    summary="Check Chatbot engine status",
)
async def get_chat_health():
    """Returns active model and provider status for chatbot."""
    api_key = chat_service._get_api_key()
    return {
        "status": "ready" if api_key else "fallback_ready",
        "provider": "groq" if api_key else "deterministic_fallback",
        "has_dedicated_key": bool(chat_service._get_api_key()),
    }
