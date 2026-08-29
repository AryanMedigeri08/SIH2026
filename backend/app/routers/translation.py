"""
translation.py — REST API Router for Google Cloud Translation & Multilingual Services.
"""

from __future__ import annotations
from typing import Optional, Any, Union, List, Dict
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

try:
    from app.core.translation_service import translation_service, SUPPORTED_LANGUAGES
except ImportError:
    from backend.app.core.translation_service import translation_service, SUPPORTED_LANGUAGES

router = APIRouter(prefix="/translate", tags=["Translation & Localization"])


class TranslationRequest(BaseModel):
    text: str = Field(..., description="Source text to translate", min_length=1)
    target_language: str = Field(..., description="Target ISO 639-1 language code (e.g. 'hi', 'mr', 'ta', 'te', 'kn', 'en')")
    source_language: Optional[str] = Field("en", description="Source ISO 639-1 language code or 'auto'")
    format: Optional[str] = Field("text", description="'text' or 'html'")


class TranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    provider: str


class BatchTranslationRequest(BaseModel):
    texts: list[str] = Field(..., description="Array of strings to translate")
    target_language: str = Field(..., description="Target ISO 639-1 language code")
    source_language: Optional[str] = Field("en", description="Source language code")


class DictionaryTranslationRequest(BaseModel):
    dictionary: dict[str, str] = Field(..., description="Key-value dictionary of UI / domain strings")
    target_language: str = Field(..., description="Target ISO 639-1 language code")
    source_language: Optional[str] = Field("en", description="Source language code")


@router.post("", response_model=TranslationResponse)
async def translate_single_text(request: TranslationRequest):
    """
    Translates a single text string into target Indian language using Google Cloud Translation API.
    """
    try:
        res = await translation_service.translate_text(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language or "en",
            format_type=request.format or "text",
        )
        return TranslationResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation service error: {str(e)}"
        )


@router.post("/batch", response_model=list[TranslationResponse])
async def translate_batch_texts(request: BatchTranslationRequest):
    """
    Translates an array of strings in batch.
    """
    try:
        results = await translation_service.translate_batch(
            texts=request.texts,
            target_language=request.target_language,
            source_language=request.source_language or "en",
        )
        return [TranslationResponse(**r) for r in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch translation error: {str(e)}"
        )


@router.post("/dictionary", response_model=dict[str, str])
async def translate_ui_dictionary(request: DictionaryTranslationRequest):
    """
    Translates a key-value dictionary of UI labels or report attributes.
    """
    try:
        return await translation_service.translate_dictionary(
            data_dict=request.dictionary,
            target_language=request.target_language,
            source_language=request.source_language or "en",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dictionary translation error: {str(e)}"
        )


@router.get("/languages")
async def get_supported_languages():
    """
    Returns the supported Indian languages and Google Cloud Translation engine status.
    """
    return {
        "status": "active",
        "default_language": "en",
        "supported_languages": list(SUPPORTED_LANGUAGES.values()),
        "providers": ["google_cloud_sdk", "google_cloud_rest", "persistent_cache", "domain_dictionary"],
    }
