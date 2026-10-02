"""
onboarding.py — Conversational Onboarding API Router.

Processes natural language input from MIRA's chat interface and extracts
structured wizard fields using Sarvam LLM, with ODOP alignment intelligence.
Replaces the 7-step wizard with an intelligent conversational Q&A flow.
"""

from __future__ import annotations
import json
import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
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
# Note: annual_turnover_estimate is automatically computed by the backend based
# on capital investment and sector velocity ratios. It is NEVER asked from the user.
REQUIRED_FIELDS = [
    "enterprise_name",
    "business_category",    # manufacturing | service (auto-inferred from sector)
    "sector",               # dairy, food_processing, repair, apparel, etc.
    "promoter_category",    # general | sc | st | obc | women | women_shg
    "state_name",           # auto-resolved from GPS during registration
    "district_name",        # auto-resolved from GPS during registration
    "project_cost",         # user specifies e.g. 2 lakh
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

# ── Reverse Geocoding from SQLite Locality Master ─────────────────────────────
_LOCALITY_DB_PATH = Path(__file__).resolve().parent.parent / "core" / "data" / "locality_master.sqlite3"


def reverse_geocode_coords(lat: float, lon: float) -> Optional[dict[str, str]]:
    """Resolves GPS latitude and longitude to state, district, and locality using locality_master.sqlite3."""
    try:
        if not _LOCALITY_DB_PATH.exists():
            return None
        conn = sqlite3.connect(str(_LOCALITY_DB_PATH))
        cur = conn.cursor()
        cur.execute("""
            SELECT state, district, office_name
            FROM pincode_localities
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY ((latitude - ?)*(latitude - ?)*1.5 + (longitude - ?)*(longitude - ?)) ASC
            LIMIT 1
        """, (lat, lat, lon, lon))
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "state_name": row[0],
                "district_name": row[1],
                "locality_name": row[2],
            }
    except Exception as e:
        logger.warning("Reverse geocode error for coords (%s, %s): %s", lat, lon, e)
    return None


# ── Sector Name Mapping ─────────────────────────────────────────────────────
SECTOR_MAP = {
    "dairy": "dairy", "milk": "dairy", "cow": "dairy", "buffalo": "dairy",
    "दूध": "dairy", "डेयरी": "dairy", "गाय": "dairy", "भैंस": "dairy",
    "food": "food_processing", "snacks": "food_processing", "pickle": "food_processing",
    "bakery": "food_processing", "papad": "food_processing", "chips": "food_processing",
    "ice cream": "dairy", "icecream": "dairy", "कुल्फी": "dairy", "आइसक्रीम": "dairy",
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
    odop_alignment: Optional[Dict[str, Any]] = Field(None, description="ODOP comparison & synergy data")
    odop_comparison: Optional[Dict[str, Any]] = Field(None, description="ODOP synergy alignment details for UI cards")
    message: Optional[Dict[str, str]] = None


# ── Field Extraction System Prompt ───────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are MIRA, an intelligent MSME advisor for Indian entrepreneurs.
Your task is to extract structured business information from the user's natural language input.

IMPORTANT: Respond ONLY with valid JSON. No explanation text.

Fields to extract if present in the text:
- enterprise_name: string (name of the business, e.g. "Sharma Dairy", "Cool Ice Cream")
- business_category: "manufacturing" or "service"
- sector: one of "dairy", "food_processing", "repair", "apparel", "fabrication", "artisan_trades", "general"
- promoter_category: one of "general", "sc", "st", "obc", "women", "women_shg"
- state_name: string (if mentioned)
- district_name: string (if mentioned)
- project_cost: number (total investment in INR, convert lakhs/crores to absolute value: e.g. 2 lakh = 200000)
- additional_business_details: string (any extra business context)

DO NOT extract annual_turnover_estimate or gross sales.
Return JSON like: {"enterprise_name": "Sharma Ice Cream", "sector": "dairy", "project_cost": 300000}
Empty JSON {} is valid if no structured fields are present.
"""

CONVERSATION_SYSTEM_PROMPT_TEMPLATE = """You are MIRA (MSME Intelligent Rural Advisor), a very sweet, warm, understanding, and empathetic business advisor.
You speak {language_name} fluently with natural human warmth and respect (ji / जी). You are helping {user_name} start their business journey.

CURRENT ENTERPRISE STATUS:
- Entrepreneur: {user_name}
- Verified Location: {location_info}
- Information Gathered So Far:
{collected_info}

STILL NEEDED TO COMPLETE APPRAISAL:
{missing_fields}

CRITICAL OPERATIONAL RULES (FOLLOW STRICTLY):
1. LOCATION IS ALREADY VERIFIED: The user's location is ALREADY KNOWN from registration GPS as {location_info}. DO NOT ASK the user where they are from, what district they are in, or what state they belong to! If you mention location, warmly acknowledge it (e.g., "बहुत खुशी की बात है कि आप {district_name}, {state_name} में व्यवसाय शुरू कर रहे हैं").
2. DO NOT ASK FOR ANNUAL SALES / TURNOVER: NEVER ask the user for their "annual turnover", "gross sales", "yearly income", or "expected revenue". That is a banking figure calculated automatically on the server.
3. REMAINING QUESTIONS TO ASK (ask only ONE at a time in natural, simple language):
   - If business idea is missing: Ask what kind of business or product they want to start (e.g. dairy, ice cream, food processing, clothes/tailoring, mobile repair, grocery).
   - If investment is missing: Ask how much capital/money they have to invest (e.g., ₹2 लाख, ₹5 लाख).
   - If category is missing: Ask which social category they belong to (General, OBC, SC, ST, or Women Entrepreneur).
4. TONE & STYLE:
   - Very warm, encouraging, respectful, like a supportive elder sister.
   - Keep answers short and clear: 2 to 4 sentences maximum.
   - If all required fields are collected, warmly congratulate {user_name} and tell them their feasibility report and ODOP alignment are ready!
"""

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "mr": "Marathi",
    "te": "Telugu", "ta": "Tamil", "kn": "Kannada",
}


# ── Core Processing Logic ────────────────────────────────────────────────────

def _extract_fields_from_text(text: str, existing_fields: dict) -> dict:
    """Uses keyword matching to rapidly extract obvious fields."""
    extracted = {}
    text_lower = text.lower()

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
                break

    return extracted


def _llm_extract_fields(user_text: str) -> dict:
    """Uses Sarvam LLM for structured field extraction from natural language."""
    try:
        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract fields from this user message: \"{user_text}\""},
        ]
        content, _, _ = chat_service._call_llm_chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=256,
            timeout_s=8.0,
        )
        if content:
            content_clean = content.strip()
            if content_clean.startswith("```"):
                content_clean = content_clean.split("```")[1]
                if content_clean.startswith("json"):
                    content_clean = content_clean[4:]
            data = json.loads(content_clean)
            if isinstance(data, dict):
                # Never extract annual_turnover_estimate from LLM
                data.pop("annual_turnover_estimate", None)
                data.pop("turnover", None)
                return data
    except Exception as e:
        logger.warning("LLM field extraction notice: %s", e)
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

    district_name = collected_fields.get("district_name", "your area")
    state_name = collected_fields.get("state_name", "India")
    location_info = f"{district_name}, {state_name}"

    collected_info = "\n".join(
        f"- {k.replace('_', ' ').title()}: {v}"
        for k, v in collected_fields.items()
        if v is not None and k not in ("latitude", "longitude")
    ) or "None yet"

    missing_info = "\n".join(
        f"- {f.replace('_', ' ').title()}"
        for f in missing_fields
    ) or "All required fields gathered!"

    system_prompt = CONVERSATION_SYSTEM_PROMPT_TEMPLATE.format(
        language_name=lang_name,
        user_name=user_name,
        location_info=location_info,
        district_name=district_name,
        state_name=state_name,
        collected_info=collected_info,
        missing_fields=missing_info,
    )

    llm_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages[-6:]:
        llm_messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        content, _, _ = chat_service._call_llm_chat_completion(
            messages=llm_messages,
            temperature=0.3,
            max_tokens=300,
            timeout_s=12.0,
        )
        if content and content.strip():
            return content.strip()
    except Exception as e:
        logger.error("MIRA response generation failed: %s", e)

    # Fallback response
    if language == "hi":
        return f"नमस्ते {user_name} जी! मैं आपकी बात समझ गई। कृपया मुझे अपने व्यवसाय के बारे में थोड़ा और बताएँ। 🙏"
    return f"Namaste {user_name} Ji! I understand. Please tell me a bit more about your business idea. 🙏"


def _generate_odop_synergy(
    user_business: str,
    sector: str,
    state: str,
    district: str,
) -> Optional[dict[str, Any]]:
    """
    Constructs a 3-pillar strategic synergy aligning the user's business with the district's ODOP.
    Does NOT change or replace the user's idea; instead enriches it for 35% PMFME subsidy eligibility.
    """
    try:
        odop_data = find_district_odop(state, district) or {}
        pmfme_item = odop_data.get("pmfme_odop_product") or odop_data.get("odop_product") or "Local Agricultural Produce"
        odop_item = odop_data.get("odop_product") or pmfme_item

        primary_crop = pmfme_item.split("(")[0].strip() if "(" in pmfme_item else pmfme_item

        # Tailored synergy descriptions based on sector
        sector_clean = sector.replace("_", " ").title()
        
        # Product Innovation Pillar
        if sector in ("dairy", "food_processing"):
            innov_title = f"Product Innovation ({primary_crop}-Infused {sector_clean})"
            innov_desc = (
                f"Introduce a premium, health-conscious line of products made with a {primary_crop} base "
                f"(e.g., lactose-free or fortified options) or incorporating {primary_crop} malted flavors "
                f"and crunchy mix-ins, targeting high-margin urban and local retail markets."
            )
        elif sector in ("apparel", "artisan_trades"):
            innov_title = f"Design Innovation (Local {primary_crop} & Craft Blend)"
            innov_desc = (
                f"Incorporate {district}'s indigenous {primary_crop} or traditional artisan patterns into "
                f"modern apparel and lifestyle products, unlocking premium export and boutique retail corridors."
            )
        elif sector in ("repair", "fabrication", "service"):
            innov_title = f"Service Expansion (Agri-Cluster & Equipment Support)"
            innov_desc = (
                f"Expand your {sector_clean} operations to provide specialized repair, maintenance, and tooling "
                f"for machinery used by local {primary_crop} farmers and processing units in {district}."
            )
        else:
            innov_title = f"Product Innovation ({primary_crop} Integration)"
            innov_desc = (
                f"Introduce an innovative product line utilizing {primary_crop}, enhancing product differentiation "
                f"and qualifying for government cluster incentives."
            )

        # Local Sourcing Advantage Pillar
        source_title = f"Local Sourcing Advantage ({district} Farmer Clusters)"
        source_desc = (
            f"Source raw {primary_crop} directly from {district}'s local farmer clusters, FPOs, and recognized "
            f"brands, reducing procurement transit costs and fulfilling statutory ODOP cluster mandates."
        )

        # Financial Incentives Pillar
        fin_title = "Financial Incentives (PMFME 35% Capital Subsidy)"
        fin_desc = (
            f"Using this product formulation qualifies your enterprise for the PMFME Scheme's 35% credit-linked "
            f"capital subsidy (up to ₹10 Lakhs) on machinery and processing tools, with priority GeM portal listing."
        )

        return {
            "what_is_odop": (
                f"Under the central government's One District One Product (ODOP) and PMFME initiative, "
                f"**{primary_crop}** has been designated as the key focus product for **{district}** to promote "
                f"local processing and farming clusters. By aligning your business idea with ODOP, you qualify for "
                f"a **35% capital subsidy (up to ₹10 Lakhs)** on machinery and priority government procurement."
            ),
            "user_business": f"{user_business} ({sector_clean})",
            "district_odop": f"{pmfme_item}",
            "primary_odop_product": primary_crop,
            "district": district,
            "state": state,
            "synergy_pillars": {
                "product_innovation": {
                    "title": innov_title,
                    "description": innov_desc,
                },
                "local_sourcing": {
                    "title": source_title,
                    "description": source_desc,
                },
                "financial_incentives": {
                    "title": fin_title,
                    "description": fin_desc,
                },
            },
            "key_benefits": [
                "35% Credit-Linked Capital Subsidy on Machinery (PMFME)",
                "Priority Seller Onboarding on GeM Government Portal",
                "Access to District Cluster Common Facility Centers (CFC)",
                "Premium Price Advantage with Certified ODOP Regional Branding",
            ],
            # Backward compatibility flags for UI
            "odop_product": pmfme_item,
        }
    except Exception as e:
        logger.warning("ODOP synergy generation error: %s", e)
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
    
    1. Pre-resolves state & district from user GPS coordinates automatically.
    2. Extracts structured wizard fields using keyword matching + LLM.
    3. Auto-calculates annual turnover without interrogating the user.
    4. Generates warm, empathetic conversational response.
    5. Formulates 3-pillar ODOP strategic synergy without changing user's idea.
    """
    start_time = time.perf_counter()

    try:
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

        existing_fields = dict(payload.collected_fields)
        new_fields = {}

        # ── Step 0: Auto-resolve location from GPS coordinates ───────────────
        if payload.user_location and payload.user_location.get("latitude") and payload.user_location.get("longitude"):
            if "state_name" not in existing_fields or "district_name" not in existing_fields:
                try:
                    lat = float(payload.user_location["latitude"])
                    lon = float(payload.user_location["longitude"])
                    geo = reverse_geocode_coords(lat, lon)
                    if geo:
                        if "state_name" not in existing_fields:
                            existing_fields["state_name"] = geo["state_name"]
                            new_fields["state_name"] = geo["state_name"]
                        if "district_name" not in existing_fields:
                            existing_fields["district_name"] = geo["district_name"]
                            new_fields["district_name"] = geo["district_name"]
                        logger.info(
                            "📍 [ONBOARDING GPS] Auto-resolved coords (%.4f, %.4f) -> %s, %s",
                            lat, lon, geo["district_name"], geo["state_name"]
                        )
                except Exception as geo_err:
                    logger.warning("Failed to auto-resolve user location coords: %s", geo_err)

        # ── Step 1: Rapid keyword-based field extraction ─────────────────────
        keyword_fields = _extract_fields_from_text(last_user_msg, existing_fields)

        # ── Step 2: LLM-based extraction for natural language inputs ────────
        llm_fields = _llm_extract_fields(last_user_msg)

        # Merge extracted fields
        for key in set(list(keyword_fields.keys()) + list(llm_fields.keys())):
            if key not in existing_fields:
                val = keyword_fields.get(key) or llm_fields.get(key)
                if val is not None:
                    new_fields[key] = val

        merged_fields = {**existing_fields, **new_fields}

        # ── Step 3: Auto-derive dependent fields without asking user ──────────
        # 3a. Auto-infer business_category (manufacturing vs service)
        if "sector" in merged_fields and "business_category" not in merged_fields:
            if merged_fields["sector"] in ("repair", "general", "service"):
                merged_fields["business_category"] = "service"
                new_fields["business_category"] = "service"
            else:
                merged_fields["business_category"] = "manufacturing"
                new_fields["business_category"] = "manufacturing"

        # 3b. Auto-infer enterprise_name if not provided
        if "enterprise_name" not in merged_fields and "sector" in merged_fields:
            sector_label = merged_fields["sector"].replace("_", " ").title()
            merged_fields["enterprise_name"] = f"{payload.user_name}'s {sector_label} Venture"
            new_fields["enterprise_name"] = merged_fields["enterprise_name"]

        # 3c. Auto-calculate annual_turnover_estimate based on project_cost
        if "project_cost" in merged_fields and "annual_turnover_estimate" not in merged_fields:
            try:
                cost = float(merged_fields["project_cost"])
                multiplier = 2.2 if merged_fields.get("business_category") == "manufacturing" else 1.8
                merged_fields["annual_turnover_estimate"] = round(cost * multiplier, -2)
                new_fields["annual_turnover_estimate"] = merged_fields["annual_turnover_estimate"]
            except (ValueError, TypeError):
                pass

        # ── Step 4: Determine missing required fields ─────────────────────────
        missing = [f for f in REQUIRED_FIELDS if f not in merged_fields or not merged_fields[f]]
        all_collected = len(missing) == 0

        # ── Step 5: ODOP Strategic Synergy Generation ─────────────────────────
        odop_synergy = None
        if "state_name" in merged_fields and "district_name" in merged_fields and "sector" in merged_fields:
            user_biz = merged_fields.get("enterprise_name") or f"{merged_fields['sector'].replace('_', ' ').title()} Business"
            odop_synergy = _generate_odop_synergy(
                user_business=user_biz,
                sector=merged_fields["sector"],
                state=merged_fields["state_name"],
                district=merged_fields["district_name"],
            )

        # ── Step 6: Generate MIRA's conversational response ───────────────────
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
            ", ".join(missing[:3]) if missing else "NONE (ALL READY)",
            int(latency_ms),
        )

        return OnboardingResponse(
            reply=mira_reply,
            extracted_fields=new_fields,
            next_step=next_step,
            all_fields_collected=all_collected,
            odop_alignment=odop_synergy,
            odop_comparison=odop_synergy,
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
