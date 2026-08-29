"""
chat.py — REST API Router for Persistent Groq Chatbot & Enterprise Advisor.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
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
    language: Optional[str] = Field(default="en", description="Target response language code (en, hi, mr, ta, te, kn, bn, gu, ml, pa)")


class ChatCompletionResponse(BaseModel):
    message: Dict[str, str]
    reply: str
    model: str
    sources: List[str] = Field(default_factory=list, description="Verified data sources used for response")
    is_fallback: bool
    latency_ms: float
    timestamp: Optional[str] = None


@router.post(
    "",
    response_model=ChatCompletionResponse,
    summary="Send message to Groq AI Advisor with active enterprise grounding",
)
@router.post(
    "/",
    response_model=ChatCompletionResponse,
    include_in_schema=False,
)
async def create_chat_completion(payload: ChatCompletionRequest):
    """
    Submits user messages to Groq Cloud LLM with active enterprise telemetry grounding and guardrail screening.
    """
    try:
        raw_messages = [{"role": m.role, "content": m.content} for m in payload.messages]
        result = chat_service.generate_chat_response(
            messages=raw_messages,
            context=payload.context,
            language=payload.language or "en",
        )
        
        # Ensure reply, sources, and timestamp are explicitly populated for all client SDK formats
        content = result.get("message", {}).get("content", "")
        result["reply"] = content
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        if "sources" not in result:
            result["sources"] = []
        
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
