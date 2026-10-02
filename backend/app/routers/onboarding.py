"""
onboarding.py — Conversational Onboarding API Router.

Processes natural language input from MIRA's chat interface and extracts
structured wizard fields using Sarvam LLM, with ODOP alignment intelligence.
Replaces the 7-step wizard with an intelligent conversational Q&A flow.
"""

from __future__ import annotations
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

try:
    from app.core.chat_service import chat_service
    from app.core.odop_matcher import match_odop, find_district_odop
    from app.config import settings
except ImportError:
    from backend.app.core.chat_service import chat_service
    from backend.app.core.odop_matcher import match_odop, find_district_odop
    from backend.app.config import settings

logger = logging.getLogger("udyam_saathi.api.onboarding")

router = APIRouter()

# ── Required Fields for XGBoost Feasibility Model ────────────────────────────
REQUIRED_FIELDS = [
    "enterprise_name",
    "business_category",    # manufacturing | service
    "sector",               # dairy, food_processing, repair, apparel, etc.
    "promoter_category",    # general | sc | st | obc | women | women_shg
    "state_name",
    "district_name",
    "project_cost",
    "annual_turnover_estimate",
]

OPTIONAL_FIELDS = [
    "block_name",
    "village_name",
    "is_rural",
    "tenure_years",
    "moratorium_months",
    "expected_monthly_units",
    "infrastructure_score",
    "additional_business_details",
]

# ── Sector Name Mapping ─────────────────────────────────────────────────────
SECTOR_MAP = {
    "dairy": "dairy", "milk": "dairy", "cow": "dairy", "buffalo": "dairy",
    "दूध": "dairy", "डेयरी": "dairy", "गाय": "dairy", "भैंस": "dairy",
    "food": "food_processing", "snacks": "food_processing", "pickle": "food_processing",
    "bakery": "food_processing", "papad": "food_processing", "chips": "food_processing",
    "खाना": "food_processing", "खाद्य": "food_processing", "नमकीन": "food_processing",
    "अचार": "food_processing", "बेकरी": "food_processing",
    "repair": "repair", "mobile": "repair", "electronics": "repair", "mechanic": "repair",
    "मरम्मत": "repair", "मोबाइल": "repair", "इलेक्ट्रॉनिक्स": "repair",
    "cloth": "apparel", "apparel": "apparel", "garment": "apparel", "tailoring": "apparel",
    "कपड़े": "apparel", "सिलाई": "apparel", "दर्जी": "apparel",
    "fabrication": "fabrication", "welding": "fabrication", "steel": "fabrication",
    "वेल्डिंग": "fabrication", "लोहा": "fabrication",
    "artisan": "artisan_trades", "handicraft": "artisan_trades", "craft": "artisan_trades",
    "pottery": "artisan_trades", "weaving": "artisan_trades",
    "हस्तशिल्प": "artisan_trades", "बुनाई": "artisan_trades", "मिट्टी": "artisan_trades",
    "salon": "service", "beauty": "service", "parlour": "service",
    "shop": "general", "store": "general", "kirana": "general", "दुकान": "general",
}

CATEGORY_MAP = {
    "general": "general", "सामान्य": "general", "gen": "general",
    "obc": "obc", "other backward": "obc", "ओबीसी": "obc",
    "sc": "sc", "scheduled caste": "sc", "अनुसूचित जाति": "sc",
    "st": "st", "scheduled tribe": "st", "अनुसूचित जनजाति": "st",
    "women": "women", "woman": "women", "महिला": "women",
    "shg": "women_shg", "self help group": "women_shg", "स्वयं सहायता समूह": "women_shg",
}

BUSINESS_CATEGORY_MAP = {
    "manufacturing": "manufacturing", "production": "manufacturing", "factory": "manufacturing",
    "उत्पादन": "manufacturing", "फैक्ट्री": "manufacturing", "बनाना": "manufacturing",
    "service": "service", "shop": "service", "repair": "service", "salon": "service",
    "सेवा": "service", "दुकान": "service",
}


# ── Request / Response Models ────────────────────────────────────────────────
class OnboardingMessagePayload(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="Message text content")


class OnboardingRequest(BaseModel):
    messages: List[OnboardingMessagePayload] = Field(..., min_length=1)
    language: str = Field("hi", description="Selected language code")
    user_name: str = Field("Entrepreneur", description="User's display name")
    collected_fields: Dict[str, Any] = Field(default_factory=dict, description="Already collected wizard fields")
    conversation_step: int = Field(0, description="Current conversation step index")
    user_location: Optional[Dict[str, Any]] = Field(None, description="GPS coordinates {latitude, longitude}")


class OnboardingResponse(BaseModel):
    reply: str = Field(..., description="MIRA's conversational response text")
    extracted_fields: Dict[str, Any] = Field(default_factory=dict, description="Fields extracted from user's latest message")
    next_step: int = Field(0, description="Updated conversation step")
    all_fields_collected: bool = Field(False, description="True if all required fields are filled")
    odop_alignment: Optional[Dict[str, Any]] = Field(None, description="ODOP comparison data when applicable")
    odop_comparison: Optional[Dict[str, Any]] = Field(None, description="ODOP pros/cons comparison for UI cards")
    message: Optional[Dict[str, str]] = None


# ── Field Extraction System Prompt ───────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are MIRA, a friendly rural business advisor for Indian MSME entrepreneurs.
Your task is to extract structured business information from the user's natural language input.

IMPORTANT: Respond ONLY with valid JSON. No explanation text.

Extract the following fields from the user's message. Return ONLY fields that can be confidently determined from the text.
Do NOT infer or guess fields that are not mentioned.

Fields to extract:
- enterprise_name: string (name of the business, e.g. "Sharma Dairy Farm")
- business_category: "manufacturing" or "service"  
- sector: one of "dairy", "food_processing", "repair", "apparel", "fabrication", "artisan_trades", "general"
- promoter_category: one of "general", "sc", "st", "obc", "women", "women_shg"
- state_name: string (Indian state name)
- district_name: string (district name)
- block_name: string (block/tehsil)
- village_name: string (village)
- project_cost: number (total investment in INR, convert lakhs/crores to absolute value)
- annual_turnover_estimate: number (estimated yearly revenue in INR)
- is_rural: boolean
- additional_business_details: string (any extra business context)

Examples of conversion:
- "2 lakh" = 200000, "5 lakh" = 500000, "1 crore" = 10000000
- "2 लाख" = 200000, "5 लाख" = 500000

Return JSON like: {"enterprise_name": "value", "sector": "dairy", "project_cost": 500000}
Only include fields you are CONFIDENT about from the user's text. Empty JSON {} is valid if nothing can be extracted.
"""


CONVERSATION_SYSTEM_PROMPT_TEMPLATE = """You are MIRA (MSME Intelligent Rural Advisor), a very sweet, warm, understanding, and empathetic business advisor.
You speak {language_name} fluently with proper human emotion. You are helping {user_name} start their business journey.

Your tone should be:
- Very sweet and appealing, like a caring elder sister/advisor
- Consoling and understanding when the user seems confused
- Encouraging and motivating
- Use simple language that rural entrepreneurs can understand
- Mix Hindi/regional words naturally for warmth

CURRENT COLLECTED INFORMATION:
{collected_info}

MISSING FIELDS (still needed):
{missing_fields}

YOUR TASK:
1. Acknowledge what the user just told you warmly
2. If the user mentioned business details, confirm what you understood
3. Ask about the NEXT missing piece of information naturally (don't ask all at once)
4. If the user seems confused about costs/investment, help them think through it
5. Keep responses SHORT and conversational (3-5 sentences max)
6. If all required information is collected, congratulate them and say you'll generate their report

FIELD PRIORITIES (ask in this order):
1. Business idea / sector (what they want to do)
2. Investment amount (project cost)
3. Location (state, district)  
4. Promoter category (general/SC/ST/OBC/women)
5. Expected revenue/turnover
6. Enterprise name (can be auto-generated)

IMPORTANT: Never use technical terms. Say "kitna paisa lagana hai" instead of "project cost".
Say "aap kahan se hain" instead of "state_name". Be natural!
"""

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "mr": "Marathi",
    "te": "Telugu", "ta": "Tamil", "kn": "Kannada",
}


# ── Core Processing Logic ────────────────────────────────────────────────────

def _extract_fields_from_text(text: str, existing_fields: dict) -> dict:
    """
    Uses keyword matching to rapidly extract obvious fields.
    Falls back to LLM extraction for complex inputs.
    """
    extracted = {}
    text_lower = text.lower()
    text_words = set(text_lower.split())

    # --- Sector detection ---
    for keyword, sector_val in SECTOR_MAP.items():
        if keyword in text_lower and "sector" not in existing_fields:
            extracted["sector"] = sector_val
            break

    # --- Category detection ---
    for keyword, cat_val in CATEGORY_MAP.items():
        if keyword in text_lower and "promoter_category" not in existing_fields:
            extracted["promoter_category"] = cat_val
            break

    # --- Business category ---
    for keyword, bcat_val in BUSINESS_CATEGORY_MAP.items():
        if keyword in text_lower and "business_category" not in existing_fields:
            extracted["business_category"] = bcat_val
            break

    # --- Investment / project cost ---
    import re
    # Match patterns like "2 lakh", "₹5 lakh", "2लाख", "10 lacs", "1 crore"
    cost_patterns = [
        (r'(?:₹|rs\.?|rupees?)\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|लाख)', lambda m: float(m.group(1)) * 100000),
        (r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|लाख)', lambda m: float(m.group(1)) * 100000),
        (r'(?:₹|rs\.?|rupees?)\s*(\d+(?:\.\d+)?)\s*(?:crore|करोड़)', lambda m: float(m.group(1)) * 10000000),
        (r'(\d+(?:\.\d+)?)\s*(?:crore|करोड़)', lambda m: float(m.group(1)) * 10000000),
        (r'(?:₹|rs\.?|rupees?)\s*(\d{4,})', lambda m: float(m.group(1))),
    ]

    if "project_cost" not in existing_fields:
        for pattern, converter in cost_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                extracted["project_cost"] = converter(match)
                # Estimate turnover as 2x project cost if not set
                if "annual_turnover_estimate" not in existing_fields:
                    extracted["annual_turnover_estimate"] = extracted["project_cost"] * 2
                break

    # --- Location (basic keyword matching) ---
    # Common Indian state names
    STATES = {
        "karnataka": "Karnataka", "कर्नाटक": "Karnataka",
        "maharashtra": "Maharashtra", "महाराष्ट्र": "Maharashtra",
        "rajasthan": "Rajasthan", "राजस्थान": "Rajasthan",
        "uttar pradesh": "Uttar Pradesh", "उत्तर प्रदेश": "Uttar Pradesh",
        "madhya pradesh": "Madhya Pradesh", "मध्य प्रदेश": "Madhya Pradesh",
        "west bengal": "West Bengal", "पश्चिम बंगाल": "West Bengal",
        "tamil nadu": "Tamil Nadu", "तमिलनाडु": "Tamil Nadu",
        "andhra pradesh": "Andhra Pradesh",
        "telangana": "Telangana", "तेलंगाना": "Telangana",
        "gujarat": "Gujarat", "गुजरात": "Gujarat",
        "bihar": "Bihar", "बिहार": "Bihar",
        "odisha": "Odisha", "ओडिशा": "Odisha",
        "kerala": "Kerala", "केरल": "Kerala",
        "punjab": "Punjab", "पंजाब": "Punjab",
        "haryana": "Haryana", "हरियाणा": "Haryana",
        "jharkhand": "Jharkhand", "झारखंड": "Jharkhand",
        "chhattisgarh": "Chhattisgarh", "छत्तीसगढ़": "Chhattisgarh",
        "assam": "Assam", "असम": "Assam",
        "goa": "Goa", "गोवा": "Goa",
        "uttarakhand": "Uttarakhand", "उत्तराखंड": "Uttarakhand",
        "himachal pradesh": "Himachal Pradesh", "हिमाचल प्रदेश": "Himachal Pradesh",
        "delhi": "Delhi", "दिल्ली": "Delhi",
    }
    if "state_name" not in existing_fields:
        for keyword, state_val in STATES.items():
            if keyword in text_lower:
                extracted["state_name"] = state_val
                break

    # --- Rural/Urban detection ---
    if "is_rural" not in existing_fields:
        if any(w in text_lower for w in ("rural", "village", "gram", "gaon", "गाँव", "ग्राम", "ग्रामीण")):
            extracted["is_rural"] = True
        elif any(w in text_lower for w in ("urban", "city", "town", "शहर", "नगर")):
            extracted["is_rural"] = False

    return extracted


def _llm_extract_fields(text: str) -> dict:
    """Use the Sarvam LLM to extract structured fields from natural language."""
    try:
        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ]
        content, _, _ = chat_service._call_llm_chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=256,
            timeout_s=10.0,
        )
        if content:
            # Parse JSON from the response
            content_clean = content.strip()
            if content_clean.startswith("```"):
                # Strip markdown code fence
                content_clean = content_clean.split("```")[1]
                if content_clean.startswith("json"):
                    content_clean = content_clean[4:]
            return json.loads(content_clean)
    except Exception as e:
        logger.warning("LLM field extraction failed: %s", e)
    return {}


def _generate_mira_response(
    messages: list,
    user_name: str,
    language: str,
    collected_fields: dict,
    missing_fields: list,
) -> str:
    """Generate MIRA's conversational response using Sarvam LLM."""
    lang_name = LANGUAGE_NAMES.get(language, "Hindi")

    collected_info = "\n".join(
        f"- {k.replace('_', ' ').title()}: {v}"
        for k, v in collected_fields.items()
        if v is not None
    ) or "Nothing collected yet"

    missing_info = "\n".join(
        f"- {f.replace('_', ' ').title()}"
        for f in missing_fields
    ) or "All required fields collected!"

    system_prompt = CONVERSATION_SYSTEM_PROMPT_TEMPLATE.format(
        language_name=lang_name,
        user_name=user_name,
        collected_info=collected_info,
        missing_fields=missing_info,
    )

    llm_messages = [{"role": "system", "content": system_prompt}]
    # Include recent conversation history (last 6 messages)
    for msg in messages[-6:]:
        llm_messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        content, _, model = chat_service._call_llm_chat_completion(
            messages=llm_messages,
            temperature=0.6,
            max_tokens=300,
            timeout_s=15.0,
        )
        if content and content.strip():
            return content.strip()
    except Exception as e:
        logger.error("MIRA response generation failed: %s", e)

    # Fallback response
    if language == "hi":
        return "मैं समझ गई! कृपया मुझे और बताएँ ताकि मैं आपकी बेहतर मदद कर सकूँ। 🙏"
    return "I understand! Please tell me more so I can help you better. 🙏"


def _check_odop_alignment(collected_fields: dict) -> Optional[dict]:
    """Check ODOP alignment when both state and district are known."""
    state = collected_fields.get("state_name")
    district = collected_fields.get("district_name")
    sector = collected_fields.get("sector")

    if not (state and district and sector):
        return None

    try:
        odop_data = find_district_odop(state, district)
        if not odop_data:
            return None

        odop_product = odop_data.get("odop_product", "District Product")
        target_sectors = [s.lower() for s in odop_data.get("matching_sectors", [])]
        is_aligned = sector.lower() in target_sectors

        if is_aligned:
            return None  # Already aligned, no need to show comparison

        # Build comparison data for the UI cards
        return {
            "user_business": f"{sector.replace('_', ' ').title()} Business",
            "odop_product": odop_product,
            "district": district,
            "state": state,
            "without_odop_pros": [
                "You can pursue your original idea",
                "Standard PMEGP/MUDRA schemes available",
                f"Existing demand in {district}",
            ],
            "without_odop_cons": [
                "No ODOP cluster benefits",
                "Standard subsidy rates only",
                "No priority GeM listing",
            ],
            "with_odop_pros": [
                f"35% capital subsidy for {odop_product}",
                "Priority GeM seller corridor",
                "ODOP seal price premium (15-18%)",
                "Cluster common facility access",
            ],
            "with_odop_cons": [
                f"Must pivot to {odop_product} sector",
                "May need new skills/training",
            ],
        }
    except Exception as e:
        logger.warning("ODOP alignment check failed: %s", e)
        return None


# ── API Endpoint ─────────────────────────────────────────────────────────────

@router.post(
    "/onboarding",
    response_model=OnboardingResponse,
    summary="Process conversational onboarding input and extract wizard fields",
)
@router.post(
    "/onboarding/",
    response_model=OnboardingResponse,
    include_in_schema=False,
)
async def process_onboarding_message(payload: OnboardingRequest):
    """
    MIRA Conversational Onboarding Endpoint.
    
    1. Receives user's natural language message from the chat interface
    2. Extracts structured wizard fields using keyword matching + LLM
    3. Generates warm, empathetic conversational response
    4. Checks ODOP alignment when location + sector are known
    5. Returns updated fields, next step, and MIRA's response
    """
    start_time = time.perf_counter()

    try:
        # Get the latest user message
        last_user_msg = ""
        for msg in reversed(payload.messages):
            if msg.role == "user":
                last_user_msg = msg.content
                break

        if not last_user_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user message found in the conversation",
            )

        logger.info(
            "🧭 [ONBOARDING] User '%s' (step %d, lang=%s): \"%s\"",
            payload.user_name,
            payload.conversation_step,
            payload.language,
            last_user_msg[:80],
        )

        # Step 1: Rapid keyword-based field extraction
        existing_fields = dict(payload.collected_fields)
        keyword_fields = _extract_fields_from_text(last_user_msg, existing_fields)

        # Step 2: LLM-based extraction for complex inputs
        llm_fields = _llm_extract_fields(last_user_msg)

        # Merge: keyword results take priority, LLM fills gaps
        new_fields = {}
        for key in set(list(keyword_fields.keys()) + list(llm_fields.keys())):
            if key not in existing_fields:
                new_fields[key] = keyword_fields.get(key) or llm_fields.get(key)

        # Merge into collected fields
        merged_fields = {**existing_fields, **new_fields}

        # Auto-fill defaults
        if "sector" in merged_fields and "business_category" not in merged_fields:
            if merged_fields["sector"] in ("repair", "general"):
                merged_fields["business_category"] = "service"
                new_fields["business_category"] = "service"
            else:
                merged_fields["business_category"] = "manufacturing"
                new_fields["business_category"] = "manufacturing"

        if "enterprise_name" not in merged_fields and "sector" in merged_fields:
            sector_label = merged_fields["sector"].replace("_", " ").title()
            merged_fields["enterprise_name"] = f"{payload.user_name}'s {sector_label} Enterprise"
            new_fields["enterprise_name"] = merged_fields["enterprise_name"]

        # Step 3: Determine missing required fields
        missing = [f for f in REQUIRED_FIELDS if f not in merged_fields or not merged_fields[f]]
        all_collected = len(missing) == 0

        # Step 4: ODOP alignment check
        odop_comparison = None
        if "state_name" in merged_fields and "district_name" in merged_fields and "sector" in merged_fields:
            odop_comparison = _check_odop_alignment(merged_fields)

        # Step 5: Generate MIRA's conversational response
        conversation_history = [
            {"role": m.role, "content": m.content}
            for m in payload.messages
        ]

        mira_reply = _generate_mira_response(
            messages=conversation_history,
            user_name=payload.user_name,
            language=payload.language,
            collected_fields=merged_fields,
            missing_fields=missing,
        )

        next_step = payload.conversation_step + 1
        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "🧭 [ONBOARDING] Extracted %d new fields | Total: %d/%d | Missing: %s | ⏱️ %dms",
            len(new_fields),
            len(merged_fields),
            len(REQUIRED_FIELDS),
            ", ".join(missing[:3]) if missing else "NONE",
            int(latency_ms),
        )

        return OnboardingResponse(
            reply=mira_reply,
            extracted_fields=new_fields,
            next_step=next_step,
            all_fields_collected=all_collected,
            odop_alignment=odop_comparison if odop_comparison else None,
            odop_comparison=odop_comparison,
            message={"role": "assistant", "content": mira_reply},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Onboarding processing error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Onboarding processing failed: {str(e)}",
        )
