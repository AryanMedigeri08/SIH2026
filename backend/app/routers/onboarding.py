"""
onboarding.py — Conversational Onboarding API Router for Mira.

Processes natural language input from Mira's chat interface and extracts
structured wizard fields using Sarvam LLM, with ODOP benchmarking intelligence (0-100 score).
Replaces the 7-step wizard with an intelligent conversational flow.
"""

from __future__ import annotations
import json
import logging
import re
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
    "state_name",           # auto-resolved from GPS or selected in menu
    "district_name",        # auto-resolved from GPS or selected in menu
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


def clean_for_bhashini_tts(text: str, lang: str = "hi") -> str:
    """
    Cleans text for Bhashini TTS:
    - Converts symbols like ₹ and % to spoken vernacular words.
    - Strips punctuation that Bhashini literally says out loud ('question mark', 'colon', 'slash', etc.).
    - Leaves plain, natural, human speech sentences.
    """
    if not text:
        return ""

    t = text
    if lang == "hi":
        t = re.sub(r'₹\s*(\d+(?:\.\d+)?)', r'\1 रुपये', t)
        t = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'\1 प्रतिशत', t)
        t = t.replace('/', ' या ')
    elif lang == "mr":
        t = re.sub(r'₹\s*(\d+(?:\.\d+)?)', r'\1 रुपये', t)
        t = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'\1 टक्के', t)
        t = t.replace('/', ' किंवा ')
    else:
        t = re.sub(r'₹\s*(\d+(?:\.\d+)?)', r'\1 rupees', t)
        t = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'\1 percent', t)
        t = t.replace('/', ' or ')

    # Strip markdown syntax
    t = re.sub(r'\*\*(.*?)\*\*', r'\1', t)
    t = re.sub(r'[*#_`~]', ' ', t)

    # Format bullet numbers like '1.' and '2.' so Bhashini doesn't say 'one dot'
    if lang == "hi":
        t = re.sub(r'(?:^|\s)1\.\s*', ' पहला विकल्प ', t)
        t = re.sub(r'(?:^|\s)2\.\s*', ' दूसरा विकल्प ', t)
    elif lang == "mr":
        t = re.sub(r'(?:^|\s)1\.\s*', ' पहिला पर्याय ', t)
        t = re.sub(r'(?:^|\s)2\.\s*', ' दुसरा पर्याय ', t)
    else:
        t = re.sub(r'(?:^|\s)1\.\s*', ' Option 1 ', t)
        t = re.sub(r'(?:^|\s)2\.\s*', ' Option 2 ', t)

    # Remove symbols that Bhashini vocally pronounces awkwardly
    for sym in ['?', ':', ';', '(', ')', '[', ']', '{', '}', '"', "'", '!', '@', '#', '$', '^', '&', '*', '+', '=', '<', '>', '|', '\\']:
        t = t.replace(sym, ' ')

    t = t.replace('-', ' ')
    t = t.replace(',', ' ')
    t = re.sub(r'\s+', ' ', t).strip()

    # Bhashini ULCA handles up to 1800 characters smoothly without audio truncation
    if len(t) > 1800:
        sentences = t.split('. ')
        chosen = []
        curr_len = 0
        for s in sentences:
            if curr_len + len(s) + 2 <= 1800:
                chosen.append(s)
                curr_len += len(s) + 2
            else:
                break
        t = '. '.join(chosen) if chosen else t[:1800]

    return t


# ── Sector Name Mapping ─────────────────────────────────────────────────────
SECTOR_MAP = {
    # Dairy
    "dairy": "dairy", "milk": "dairy", "cow": "dairy", "buffalo": "dairy",
    "दूध": "dairy", "डेयरी": "dairy", "गाय": "dairy", "भैंस": "dairy",
    "ice cream": "dairy", "icecream": "dairy", "कुल्फी": "dairy", "आइसक्रीम": "dairy",
    "paneer": "dairy", "पनीर": "dairy", "ghee": "dairy", "घी": "dairy", "butter": "dairy", "मक्खन": "dairy",

    # Food Processing
    "food": "food_processing", "snacks": "food_processing", "pickle": "food_processing",
    "bakery": "food_processing", "papad": "food_processing", "chips": "food_processing",
    "खाना": "food_processing", "खाद्य": "food_processing", "नमकीन": "food_processing",
    "अचार": "food_processing", "बेकरी": "food_processing", "पापड़": "food_processing",
    "restaurant": "food_processing", "hotel": "food_processing", "होटल": "food_processing",
    "cafe": "food_processing", "कैफे": "food_processing", "catering": "food_processing",
    "sweet": "food_processing", "sweets": "food_processing", "मिठाई": "food_processing",
    "millet": "food_processing", "मिलेट": "food_processing", "flour": "food_processing", "आटा": "food_processing",
    "spices": "food_processing", "masala": "food_processing", "मसाला": "food_processing",
    "juice": "food_processing", "जूस": "food_processing", "oil": "food_processing", "तेल": "food_processing",

    # Repair & Electronics
    "repair": "repair", "mobile": "repair", "electronics": "repair", "mechanic": "repair",
    "मरम्मत": "repair", "मोबाइल": "repair", "इलेक्ट्रॉनिक्स": "repair", "मैकेनिक": "repair",
    "auto": "repair", "garage": "repair", "ऑटो": "repair", "गैराज": "repair", "bike": "repair",

    # Apparel & Textiles
    "cloth": "apparel", "apparel": "apparel", "garment": "apparel", "tailoring": "apparel",
    "कपड़े": "apparel", "सिलाई": "apparel", "दर्जी": "apparel", "boutique": "apparel", "बुटीक": "apparel",
    "textile": "apparel", "कपड़ा": "apparel", "dress": "apparel",

    # Fabrication & Engineering
    "fabrication": "fabrication", "welding": "fabrication", "steel": "fabrication",
    "वेल्डिंग": "fabrication", "लोहा": "fabrication", "फ्रेब्रिकेशन": "fabrication", "iron": "fabrication",

    # Artisan & Handicrafts
    "artisan": "artisan_trades", "handicraft": "artisan_trades", "craft": "artisan_trades",
    "pottery": "artisan_trades", "weaving": "artisan_trades", "कुम्हार": "artisan_trades",
    "हस्तशिल्प": "artisan_trades", "बुनाई": "artisan_trades", "मिट्टी": "artisan_trades",

    # Services & Retail
    "salon": "service", "beauty": "service", "parlour": "service", "ब्यूटी": "service", "पार्लर": "service",
    "shop": "general", "store": "general", "kirana": "general", "दुकान": "general", "किराना": "general",
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
    current_action: Optional[str] = Field(None, description="UI action trigger (confirm_loc, change_loc, submit_loc, odop_decision)")
    user_location: Optional[Dict[str, Any]] = Field(None, description="GPS coordinates or hierarchy")


class OnboardingResponse(BaseModel):
    reply: str = Field(..., description="Mira's conversational response text")
    tts_text: Optional[str] = Field(None, description="Cleaned speech text without awkward symbols for Bhashini")
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    next_step: int = Field(0)
    next_phase: str = Field("business_idea", description="Current conversation phase")
    all_fields_collected: bool = Field(False)
    odop_alignment: Optional[Dict[str, Any]] = None
    odop_comparison: Optional[Dict[str, Any]] = None
    message: Optional[Dict[str, str]] = None


# ── Field Extraction System Prompt ───────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are Mira, an intelligent and friendly MSME advisor for Indian entrepreneurs.
Your task is to extract structured business information from the user's natural language input.

IMPORTANT: Respond ONLY with valid JSON. No explanation text.

Fields to extract if present in the text:
- enterprise_name: string (name of the business, e.g. "Sharma Dairy", "Cool Ice Cream")
- business_category: "manufacturing" or "service"
- sector: one of "dairy", "food_processing", "repair", "apparel", "fabrication", "artisan_trades", "general"
- promoter_category: one of "general", "sc", "st", "obc", "women", "women_shg"
- state_name: string (if mentioned)
- district_name: string (if mentioned)
- promoter_equity: number (the user's own investment capital/promoter's equity in INR, e.g. 1 lakh = 100000, 50 thousand = 50000)
- project_cost: number (total investment in INR if explicitly stated)
- additional_business_details: string (any extra business context)

DO NOT extract annual_turnover_estimate or gross sales.
Return JSON like: {"enterprise_name": "Sharma Ice Cream", "sector": "dairy", "promoter_equity": 100000}
Empty JSON {} is valid if no structured fields are present.
"""

CONVERSATION_SYSTEM_PROMPT_TEMPLATE = """You are Mira, a loving, sweet, polite, charming, calm, caring, and encouraging business advisor.
There is NO full form for your name, you are simply Mira. You speak {language_name} with deep warmth, respect (using जी / Ji), and encouragement.

CURRENT USER STATUS:
- Entrepreneur Name: {user_name}
- Location: {location_info}
- Information Gathered:
{collected_info}

STILL NEEDED:
{missing_fields}

CRITICAL RULES (FOLLOW STRICTLY):
1. TONE: Loving, caring, polite, charming, sweet, calm, and encouraging. Make {user_name} feel valued, excited, and confident. Never command the user to be polite or say 'प्यार से बताइए' — you be polite and respectful to them!
2. DO NOT ASK FOR LOCATION: Location is already confirmed as {location_info}. Never ask state or district!
3. DO NOT ASK FOR ANNUAL SALES / TURNOVER: Never ask for turnover, yearly sales, or gross sales. That is computed by the backend.
4. QUESTIONS TO ASK (ask only ONE at a time in very sweet, natural language):
   - If business idea is missing: Politely ask what type of business or product they want to start with lovely examples (e.g. ice cream, dairy, bakery, clothes/boutique, mobile repair).
   - If promoter's equity is missing: Praise their business idea charmingly, then politely ask how much promoter equity (their own contribution/capital) they have ready to invest.
5. LENGTH: Keep responses to 2-3 sweet, clear sentences. No long lectures.
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

    for keyword, sector_val in SECTOR_MAP.items():
        if keyword in text_lower and "sector" not in existing_fields:
            extracted["sector"] = sector_val
            break

    for keyword, cat_val in CATEGORY_MAP.items():
        if keyword in text_lower and "promoter_category" not in existing_fields:
            extracted["promoter_category"] = cat_val
            break

    for keyword, bcat_val in BUSINESS_CATEGORY_MAP.items():
        if keyword in text_lower and "business_category" not in existing_fields:
            extracted["business_category"] = bcat_val
            break

    # Promoter's Equity / investment amount
    cost_patterns = [
        (r'(?:₹|rs\.?|rupees?)\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|लाख)', lambda m: float(m.group(1)) * 100000),
        (r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|लाख)', lambda m: float(m.group(1)) * 100000),
        (r'(?:₹|rs\.?|rupees?)\s*(\d+(?:\.\d+)?)\s*(?:crore|करोड़)', lambda m: float(m.group(1)) * 10000000),
        (r'(\d+(?:\.\d+)?)\s*(?:crore|करोड़)', lambda m: float(m.group(1)) * 10000000),
        (r'(?:₹|rs\.?|rupees?)\s*(\d{4,})', lambda m: float(m.group(1))),
    ]

    if "promoter_equity" not in existing_fields and "project_cost" not in existing_fields:
        for pattern, converter in cost_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                extracted["promoter_equity"] = converter(match)
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
    """Generate Mira's conversational response using Sarvam LLM."""
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
        logger.error("Mira response generation failed: %s", e)

    # Fallback sweet responses
    if language == "hi":
        return f"नमस्ते {user_name} जी! मैं आपकी बात बहुत अच्छे से समझ रही हूँ। कृपया मुझे अपने व्यवसाय के बारे में थोड़ा और बताइए ना। 🙏"
    return f"Namaste {user_name} Ji! I understand completely. Please tell me a bit more about your business idea. 🙏"


def _generate_odop_synergy(
    user_business: str,
    sector: str,
    state: str,
    district: str,
) -> Optional[dict[str, Any]]:
    """
    Constructs a 3-pillar strategic synergy aligning the user's business with the district's ODOP,
    complete with a 0-100 Benchmarking Alignment Score.
    """
    try:
        odop_data = find_district_odop(state, district) or {}
        pmfme_item = odop_data.get("pmfme_odop_product") or odop_data.get("odop_product") or "Local Agricultural Produce"
        odop_item = odop_data.get("odop_product") or pmfme_item

        primary_crop = pmfme_item.split("(")[0].strip() if "(" in pmfme_item else pmfme_item
        sector_clean = sector.replace("_", " ").title()

        # ── Benchmarking Alignment Score (0 - 100) ───────────────────────────
        score = 0
        sector_norm = sector.lower().strip()
        idea_norm = user_business.lower().strip()
        target_sectors = [s.lower() for s in odop_data.get("matching_sectors", [])]
        odop_product_lower = odop_item.lower()
        pmfme_lower = pmfme_item.lower()

        # Pillar 1: Sector Overlap & Synergy (up to 50 pts)
        if sector_norm in target_sectors:
            score += 50
        elif any(kw in idea_norm for kw in ["ice cream", "kulfi", "sweet", "dessert", "bakery", "snack", "juice", "jam", "chocolat"]) and any(kw in (odop_product_lower + " " + pmfme_lower) for kw in ["millet", "fruit", "dairy", "milk", "grain", "mango", "orange", "banana"]):
            score += 48
        elif sector_norm in ("dairy", "food_processing") and any(s in target_sectors for s in ("dairy", "food_processing", "agriculture")):
            score += 44
        elif sector_norm in ("repair", "fabrication") and any(kw in (odop_product_lower + " " + pmfme_lower) for kw in ["machinery", "engineering", "steel", "tools", "hardware"]):
            score += 40
        elif sector_norm in ("apparel", "artisan_trades") and any(kw in (odop_product_lower + " " + pmfme_lower) for kw in ["textile", "garment", "silk", "cotton", "handloom", "carpet"]):
            score += 45
        elif sector_norm in ("service", "repair", "general"):
            score += 26
        else:
            score += 15

        # Pillar 2: Local Sourcing & Catchment Feasibility (up to 25 pts)
        if odop_data.get("raw_material_availability"):
            score += 15
        else:
            score += 10
        if odop_data.get("cfc_available"):
            score += 10
        else:
            score += 5

        # Pillar 3: PMFME 35% Scheme Subsidy Qualification (up to 25 pts)
        if odop_data.get("pmfme_eligible") or "food" in sector_norm or "dairy" in sector_norm or "millet" in (odop_product_lower + " " + pmfme_lower):
            score += 25
        elif odop_data.get("key_benefits"):
            score += 18
        else:
            score += 12

        final_score = max(20, min(96, score))

        if final_score >= 70:
            verdict_key = "recommended"
            verdict_title = "उत्कृष्ट तालमेल (Highly Recommended)"
            mira_recommendation = "Mira Recommends: Excellent ODOP Synergy for 35% Subsidy"
            verdict_spoken = f"मुझे आपके व्यवसाय का {primary_crop} के साथ बहुत सुंदर तालमेल मिला है और इसका स्कोर {final_score} आया है। मेरी दिल से सलाह है कि आप इसे ज़रूर अपनाएँ ताकि आपको 35 प्रतिशत सरकारी सब्सिडी मिल सके।"
        elif final_score >= 45:
            verdict_key = "viable"
            verdict_title = "सकारात्मक तालमेल (Viable Synergy)"
            mira_recommendation = "Mira Recommends: Viable Strategic Opportunity"
            verdict_spoken = f"आपके व्यवसाय का ODOP के साथ स्कोर {final_score} है। यह एक अच्छा अतिरिक्त विकल्प है जिसे आप सब्सिडी के लिए जोड़ सकते हैं या अपने सामान्य विचार के साथ भी बढ़ सकते हैं।"
        else:
            verdict_key = "not_recommended"
            verdict_title = "कम तालमेल (Standard MSME Recommended)"
            mira_recommendation = "Mira Recommends: Continue with Standard Business Model"
            verdict_spoken = f"मैं आपसे बिल्कुल सच कहूँगी, आपके इस विचार के लिए जबरदस्ती ODOP जोड़ना सही नहीं रहेगा। आपका स्कोर {final_score} है। मेरी सलाह है कि आप अपने मूल विचार के साथ ही PMEGP और मुद्रा लोन का लाभ लें।"

        # Tailored synergy descriptions
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

        source_title = f"Local Sourcing Advantage ({district} Farmer Clusters)"
        source_desc = (
            f"Source raw {primary_crop} directly from {district}'s local farmer clusters, FPOs, and recognized "
            f"brands, reducing procurement transit costs and fulfilling statutory ODOP cluster mandates."
        )

        fin_title = "Financial Incentives (PMFME 35% Capital Subsidy)"
        fin_desc = (
            f"Using this product formulation qualifies your enterprise for the PMFME Scheme's 35% credit-linked "
            f"capital subsidy (up to ₹10 Lakhs) on machinery and processing tools, with priority GeM portal listing."
        )

        what_is_odop = (
            f"Under the central government's One District One Product (ODOP) and PMFME initiative, "
            f"**{primary_crop}** has been designated as the key focus product for **{district}** to promote "
            f"local processing and farming clusters. By aligning your business idea with ODOP, you qualify for "
            f"a **35% capital subsidy (up to ₹10 Lakhs)** on machinery and priority government procurement."
        )

        return {
            "what_is_odop": what_is_odop,
            "user_business": f"{user_business} ({sector_clean})",
            "district_odop": f"{pmfme_item}",
            "primary_odop_product": primary_crop,
            "district": district,
            "state": state,
            "alignment_score": final_score,
            "verdict_key": verdict_key,
            "verdict_title": verdict_title,
            "mira_recommendation": mira_recommendation,
            "verdict_spoken": verdict_spoken,
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
    Mira Conversational Onboarding Endpoint.
    
    1. Handles location confirmation & menu update.
    2. Extracts structured business & equity fields using keyword matching + LLM.
    3. Auto-calculates annual turnover without asking the user.
    4. Formulates 0-100 ODOP Benchmarking Alignment and 3-pillar synergy.
    5. Cleans all speech outputs so Bhashini TTS never reads out punctuation awkwardly.
    """
    start_time = time.perf_counter()

    try:
        existing_fields = dict(payload.collected_fields)
        new_fields = {}
        action = payload.current_action

        # ── Step 0: Auto-resolve location from GPS coordinates if present ──────
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
                except Exception as geo_err:
                    logger.warning("Failed to auto-resolve user location coords: %s", geo_err)

        # Direct hierarchy injection from location menu
        if payload.user_location:
            for k in ("state_name", "district_name", "block_name", "village_name", "is_rural"):
                if payload.user_location.get(k) is not None:
                    existing_fields[k] = payload.user_location[k]
                    new_fields[k] = payload.user_location[k]

        district_name = existing_fields.get("district_name", "your area")
        state_name = existing_fields.get("state_name", "India")
        loc_str = f"{district_name}, {state_name}"

        # ── Phase-specific Handling ──────────────────────────────────────────

        # Action: User confirmed the auto-detected location
        if action == "confirm_location":
            if payload.language == "hi":
                reply = f"बहुत अच्छा लगा {payload.user_name} जी! हम {loc_str} से आपकी खूबसूरत व्यवसाय यात्रा शुरू कर रहे हैं। कृपया मुझे बताइए कि आप किस प्रकार का व्यवसाय शुरू करना चाहते हैं? जैसे कि डेयरी फार्म, आइसक्रीम पार्लर, बेकरी, कपड़ों की दुकान या मोबाइल रिपेयर?"
            elif payload.language == "mr":
                reply = f"खूप छान {payload.user_name} जी! आपण {loc_str} मधून तुमचा व्यवसाय प्रवास सुरू करत आहोत. कृपया मला सांगा की तुम्हाला कोणत्या प्रकारचा व्यवसाय सुरू करायचा आहे? जसे की डेअरी, आईस्क्रीम, बेकरी, कापड दुकान किंवा मोबाइल दुरुस्ती?"
            else:
                reply = f"Wonderful {payload.user_name} Ji! We are beginning your entrepreneurial journey in {loc_str}. Could you please tell me what type of business or product you want to start? For example, an ice cream venture, bakery, garment boutique, dairy farm, or repair center?"

            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=1,
                next_phase="business_idea",
                all_fields_collected=False,
                message={"role": "assistant", "content": reply},
            )

        # Action: User requested location change menu
        if action == "request_change_location":
            if payload.language == "hi":
                reply = f"कोई बात नहीं {payload.user_name} जी! आप जहाँ से भी अपना व्यवसाय शुरू करना चाहते हैं, कृपया नीचे दिए गए मेन्यू से अपना राज्य, ज़िला, ब्लॉक और गाँव चुन लीजिए।"
            elif payload.language == "mr":
                reply = f"काही हरकत नाही {payload.user_name} जी! तुम्हाला जिथून व्यवसाय सुरू करायचा आहे, कृपया खालील मेनूमधून तुमचे राज्य, जिल्हा, ब्लॉक आणि गाव निवडा."
            else:
                reply = f"No problem at all {payload.user_name} Ji! Please select your preferred state, district, block, and village from the menu below."

            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=1,
                next_phase="location_menu",
                all_fields_collected=False,
                message={"role": "assistant", "content": reply},
            )

        # Action: User submitted location from dropdown menu
        if action == "submit_new_location":
            if payload.language == "hi":
                reply = f"बहुत खूब {payload.user_name} जी! आपकी लोकेशन {loc_str} सफलतापूर्वक सुरक्षित कर ली गई है। कृपया मुझे बताइए कि आप किस प्रकार का व्यवसाय शुरू करना चाहते हैं? जैसे कि डेयरी, आइसक्रीम, बेकरी, कपड़े, या मोबाइल रिपेयर?"
            elif payload.language == "mr":
                reply = f"फार छान {payload.user_name} जी! तुमचे स्थान {loc_str} यशस्वीरित्या अपडेट झाले आहे. कृपया मला सांगा की तुम्हाला कोणत्या प्रकारचा व्यवसाय सुरू करायचा आहे?"
            else:
                reply = f"Excellent {payload.user_name} Ji! Your location has been confirmed as {loc_str}. Could you please tell me what kind of business or product you want to start? Like dairy, ice cream, food processing, garments, or repairs?"

            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=2,
                next_phase="business_idea",
                all_fields_collected=False,
                message={"role": "assistant", "content": reply},
            )

        # ── Regular Conversational Turns ─────────────────────────────────────
        last_user_msg = ""
        for msg in reversed(payload.messages):
            if msg.role == "user":
                last_user_msg = msg.content
                break

        if not last_user_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user message found in conversation",
            )

        # Extract fields from text
        keyword_fields = _extract_fields_from_text(last_user_msg, existing_fields)
        llm_fields = _llm_extract_fields(last_user_msg)

        for key in set(list(keyword_fields.keys()) + list(llm_fields.keys())):
            if key not in existing_fields:
                val = keyword_fields.get(key) or llm_fields.get(key)
                if val is not None:
                    new_fields[key] = val

        merged_fields = {**existing_fields, **new_fields}

        # ── Auto-Detect Sector on Business Idea turn to NEVER ask twice ─────
        if "sector" not in merged_fields and last_user_msg:
            text_l = last_user_msg.lower()
            # Check if this message was an amount, not a business idea
            is_amount_only = bool(re.search(r'^\s*(?:₹|rs\.?)?\s*\d+(?:\.\d+)?\s*(?:lakh|lac|लाख|crore|करोड़|k)?\s*$', text_l))
            if not is_amount_only:
                detected_sector = "general"
                if any(w in text_l for w in ["दूध", "डेयरी", "गाय", "भैंस", "आइसक्रीम", "dairy", "milk", "kulfi", "ice cream"]):
                    detected_sector = "dairy"
                elif any(w in text_l for w in ["खाद्य", "खाना", "food", "मसाला", "अचार", "बेकरी", "मिठाई", "जूस", "तेल", "sweet", "grain", "snack", "bakery", "restaurant", "cafe", "hotel", "होटल"]):
                    detected_sector = "food_processing"
                elif any(w in text_l for w in ["कपड़ा", "कपड़े", "सिलाई", "दर्जी", "boutique", "cloth", "garment", "apparel", "textile"]):
                    detected_sector = "apparel"
                elif any(w in text_l for w in ["गाड़ी", "मोबाइल", "मरम्मत", "repair", "service", "mechanic", "electronics", "auto"]):
                    detected_sector = "repair"
                elif any(w in text_l for w in ["लोहा", "वेल्डिंग", "fabrication", "steel", "iron"]):
                    detected_sector = "fabrication"
                elif any(w in text_l for w in ["हस्तशिल्प", "art", "craft", "wood", "pottery", "weaving"]):
                    detected_sector = "artisan_trades"
                elif any(w in text_l for w in ["salon", "beauty", "parlour", "दुकान", "किराना", "shop", "store"]):
                    detected_sector = "service"
                else:
                    detected_sector = "food_processing" if ("बनाना" in text_l or "manufacturing" in text_l or "उत्पादन" in text_l) else "general"

                new_fields["sector"] = detected_sector
                merged_fields["sector"] = detected_sector
                new_fields["additional_business_details"] = last_user_msg
                merged_fields["additional_business_details"] = last_user_msg
                clean_name = last_user_msg.strip()
                if len(clean_name) > 50:
                    clean_name = clean_name[:50] + "..."
                new_fields["enterprise_name"] = clean_name
                merged_fields["enterprise_name"] = clean_name

        # ── Auto-infer business_category ─────────────────────────────────────
        if "sector" in merged_fields and "business_category" not in merged_fields:
            if merged_fields["sector"] in ("repair", "general", "service"):
                merged_fields["business_category"] = "service"
                new_fields["business_category"] = "service"
            else:
                merged_fields["business_category"] = "manufacturing"
                new_fields["business_category"] = "manufacturing"

        # Auto-infer enterprise_name
        if "enterprise_name" not in merged_fields and "sector" in merged_fields:
            sector_label = merged_fields["sector"].replace("_", " ").title()
            merged_fields["enterprise_name"] = f"{payload.user_name}'s {sector_label} Venture"
            new_fields["enterprise_name"] = merged_fields["enterprise_name"]

        # ── Check for Promoter's Equity in message ───────────────────────────
        cost_patterns = [
            (r'(?:₹|rs\.?|rupees?)\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|लाख)', lambda m: float(m.group(1)) * 100000),
            (r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|लाख)', lambda m: float(m.group(1)) * 100000),
            (r'(?:₹|rs\.?|rupees?)\s*(\d+(?:\.\d+)?)\s*(?:crore|करोड़)', lambda m: float(m.group(1)) * 10000000),
            (r'(\d+(?:\.\d+)?)\s*(?:crore|करोड़)', lambda m: float(m.group(1)) * 10000000),
            (r'(?:₹|rs\.?|rupees?)\s*(\d{4,})', lambda m: float(m.group(1))),
        ]

        if "promoter_equity" not in existing_fields:
            for pattern, converter in cost_patterns:
                match = re.search(pattern, last_user_msg, re.IGNORECASE)
                if match:
                    eq_val = converter(match)
                    new_fields["promoter_equity"] = eq_val
                    merged_fields["promoter_equity"] = eq_val
                    # Derive project_cost assuming ~15% promoter margin in MSME lending
                    if "project_cost" not in merged_fields:
                        derived_cost = round(eq_val / 0.15, -2)
                        new_fields["project_cost"] = derived_cost
                        merged_fields["project_cost"] = derived_cost
                    break

        # Auto-calculate annual_turnover_estimate
        if "project_cost" in merged_fields and "annual_turnover_estimate" not in merged_fields:
            try:
                cost = float(merged_fields["project_cost"])
                multiplier = 2.2 if merged_fields.get("business_category") == "manufacturing" else 1.8
                merged_fields["annual_turnover_estimate"] = round(cost * multiplier, -2)
                new_fields["annual_turnover_estimate"] = merged_fields["annual_turnover_estimate"]
            except (ValueError, TypeError):
                pass

        # Determine missing fields
        missing = [f for f in REQUIRED_FIELDS if f not in merged_fields or not merged_fields[f]]

        # ── Step: Business idea just provided -> Sweet acknowledgment & Ask for Promoter's Equity ──
        if "sector" in merged_fields and "promoter_equity" not in merged_fields and "promoter_equity" not in new_fields:
            sector_label = merged_fields["sector"].replace("_", " ").title()
            if payload.language == "hi":
                reply = (
                    f"अरे वाह {payload.user_name} जी! मैंने नोट कर लिया है। सच में आपका यह व्यवसाय विचार बहुत ही सुंदर और दिलचस्प है! "
                    f"कृपया मुझे बताइए कि इस उद्यम को शुरू करने के लिए आपके पास अपनी खुद की कितनी प्रमोटर इक्विटी यानी आपकी अपनी बचत या पूँजी तैयार है? "
                    f"जैसे ₹50,000, ₹1 लाख या ₹2 लाख?"
                )
            elif payload.language == "mr":
                reply = (
                    f"अरे वा {payload.user_name} जी! मी नोंदवून घेतले आहे. तुमची ही व्यवसाय कल्पना खूपच सुंदर आणि उत्तम आहे! "
                    f"कृपया मला सांगा की हा व्यवसाय सुरू करण्यासाठी तुमच्याकडे स्वतःचे किती प्रमोटर इक्विटी भांडवल किंवा स्वतःची बचत तयार आहे? "
                    f"जसे ₹50,000, ₹1 लाख किंवा ₹2 लाख?"
                )
            else:
                reply = (
                    f"Wonderful {payload.user_name} Ji! I have noted that down. What a promising and exciting business idea! "
                    f"Could you please share how much promoter equity (your own personal capital or savings) you have ready to start? "
                    f"For example, ₹50,000, ₹1 Lakh, or ₹2 Lakhs?"
                )

            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="promoter_equity",
                all_fields_collected=False,
                message={"role": "assistant", "content": reply},
            )

        # ── Step: ODOP Alignment & Benchmarking Check ────────────────────────
        odop_synergy = None
        if "sector" in merged_fields and ("project_cost" in merged_fields or "promoter_equity" in merged_fields):
            user_biz = merged_fields.get("additional_business_details") or merged_fields.get("enterprise_name") or f"{merged_fields['sector'].replace('_', ' ').title()} Business"
            # Use verified state & district
            s_name = existing_fields.get("state_name") or state_name
            d_name = existing_fields.get("district_name") or district_name
            odop_synergy = _generate_odop_synergy(
                user_business=user_biz,
                sector=merged_fields["sector"],
                state=s_name,
                district=d_name,
            )

        # If promoter_equity was just collected, speak the ODOP intro & verdict
        if ("promoter_equity" in new_fields or "project_cost" in new_fields) and odop_synergy:
            p_crop = odop_synergy.get("primary_odop_product", "District Product")
            score_val = odop_synergy.get("alignment_score", 75)
            is_good_synergy = score_val >= 60

            biz_desc = (
                merged_fields.get("enterprise_name")
                or f"{merged_fields.get('sector', 'MSME').replace('_', ' ').title()} Business"
            )

            if payload.language == "hi":
                if is_good_synergy:
                    synergy_spoken = (
                        f"यह तालमेल आपके लिए बहुत ही फायदेमंद रहेगा क्योंकि आप अपने उत्पाद में स्थानीय {p_crop} का उपयोग करके "
                        f"सीधे 35 प्रतिशत PMFME पूंजीगत सब्सिडी और स्थानीय किसान नेटवर्क का पूरा लाभ उठा सकते हैं।"
                    )
                else:
                    synergy_spoken = (
                        f"मैं आपसे बिल्कुल सच कहूँगी, आपके इस व्यवसाय के साथ {district_name} के {p_crop} का कोई उचित तालमेल नहीं बैठ रहा है "
                        f"और इसका अलाइनमेंट स्कोर केवल {score_val} आया है। इसलिए किसी जबरदस्ती के बिना, मेरी दिल से सलाह है कि आप अपने "
                        f"मूल विचार के साथ ही आगे बढ़ें जहाँ आपको PMEGP और मुद्रा लोन का पूरा लाभ मिलेगा।"
                    )

                reply = (
                    f"अरे वाह {payload.user_name} जी! मैंने आपके व्यवसाय को बहुत ही गहराई और प्यार से समझ लिया है। "
                    f"आप {district_name} में {biz_desc} शुरू करना चाहते हैं और आपका यह अंदाज़ मुझे बहुत पसंद आया! "
                    f"क्या आप जानते हैं? सरकार की वन डिस्ट्रिक्ट वन प्रोडक्ट यानी ODOP योजना के तहत अगर आप अपने ज़िले के चयनित उत्पाद से जुड़ते हैं, "
                    f"तो मशीनरी और प्लांट पर पूरे 35 प्रतिशत की भारी सरकारी सब्सिडी मिलती है! "
                    f"और जहाँ तक मैंने आपके व्यवसाय को समझा है, आपके {district_name} ज़िले का आधिकारिक ODOP {p_crop} है और आपका व्यवसाय विचार {biz_desc} का है। "
                    f"मैंने इन दोनों को मिलाकर आपके लिए एक सुंदर रास्ता तैयार किया है, और इसका अलाइनमेंट स्कोर 100 में से {score_val} आया है! "
                    f"{synergy_spoken} "
                    f"नीचे दिए गए कार्ड में मैंने आपका पूरा विश्लेषण तैयार किया है। तो अब आप मुझे बताइए, आप क्या चुनना चाहेंगे:\n"
                    f"1. ODOP से जुड़ें\n"
                    f"2. अपना मूल विचार रखें"
                )
            elif payload.language == "mr":
                if is_good_synergy:
                    synergy_spoken_mr = (
                        f"हा मेळ तुमच्यासाठी अत्यंत फायदेशीर ठरेल! कारण तुम्ही स्थानिक {p_crop} चा वापर करून थेट 35 टक्के सरकारी सबसिडी "
                        f"आणि स्थानिक शेतकरी क्लस्टरचा पूर्ण लाभ घेऊ शकता."
                    )
                else:
                    synergy_spoken_mr = (
                        f"मी तुमच्याशी अगदी खरे बोलेन, तुमच्या या व्यवसायाचा {district_name} च्या {p_crop} सोबत कोणताही थेट मेळ बसत नाही "
                        f"आणि याचा स्कोअर फक्त {score_val} आला आहे. म्हणूनच जबरदस्ती न करता, तुम्ही तुमच्या मूळ कल्पनेसह पुढे जावे हा माझा सल्ला आहे."
                    )

                reply = (
                    f"अरे वा {payload.user_name} जी! मी तुमचा व्यवसाय अतिशय प्रेमाने आणि काळजीपूर्वक समजून घेतला आहे. "
                    f"तुम्ही {district_name} मध्ये {biz_desc} सुरू करू इच्छिता आणि तुमची ही कल्पना मला मनापासून आवडली! "
                    f"तुम्हाला माहिती आहे का? शासनाच्या एक जिल्हा एक उत्पादन म्हणजेच ODOP योजनेअंतर्गत स्थानिक उत्पादनाशी जोडल्यास यंत्रसामग्रीवर तब्बल 35 टक्के सबसिडी मिळते! "
                    f"मला समजले त्यानुसार तुमच्या {district_name} जिल्ह्याचे मुख्य उत्पादन {p_crop} आहे आणि तुमची कल्पना {biz_desc} ची आहे. "
                    f"मी या दोघांचा अतिशय सुंदर मेळ घातला असून त्याचा स्कोअर 100 पैकी {score_val} आला आहे! "
                    f"{synergy_spoken_mr} "
                    f"आता मला सांगा, तुम्हाला कोणता पर्याय निवडायला आवडेल:\n"
                    f"1. ODOP शी जोडा\n"
                    f"2. माझी मूळ कल्पना ठेवा"
                )
            else:
                if is_good_synergy:
                    synergy_spoken_en = (
                        f"This alignment is wonderfully beneficial for you! By integrating {district_name}'s local {p_crop} into your venture, "
                        f"you qualify for the 35 percent PMFME capital grant up to 10 lakh rupees and direct farmer sourcing."
                    )
                else:
                    synergy_spoken_en = (
                        f"I will be completely honest with you my dear friend. Forced alignment with {district_name}'s {p_crop} does not make practical sense "
                        f"for your venture, and its alignment score is only {score_val} out of 100. My sincere recommendation is to proudly proceed with your "
                        f"original business model under standard PMEGP and Mudra loan schemes."
                    )

                reply = (
                    f"Oh wonderful {payload.user_name} Ji! I have understood your business venture deeply and lovingly. "
                    f"You wish to establish {biz_desc} in {district_name}, and I truly admire your dedication! "
                    f"Did you know? Under the government's One District One Product ODOP initiative, enterprises aligned with their district's designated product get a massive 35 percent capital subsidy on machinery! "
                    f"From what I have understood, your district {district_name} has {p_crop} as its official ODOP, while your business idea is {biz_desc}. "
                    f"I tried aligning both for you, and here is your strategic match with an alignment score of {score_val} out of 100! "
                    f"{synergy_spoken_en} "
                    f"I have presented your complete alignment match in the card below. Now please tell me what you would love to choose:\n"
                    f"1. Align with ODOP\n"
                    f"2. Keep my idea"
                )

            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="odop_alignment",
                all_fields_collected=len(missing) == 0,
                odop_alignment=odop_synergy,
                odop_comparison=odop_synergy,
                message={"role": "assistant", "content": reply},
            )

        # General MIRA conversational response fallback
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

        all_collected = len(missing) == 0
        tts_clean = clean_for_bhashini_tts(mira_reply, payload.language)

        return OnboardingResponse(
            reply=mira_reply,
            tts_text=tts_clean,
            extracted_fields=new_fields,
            next_step=payload.conversation_step + 1,
            next_phase="completed" if all_collected else "chatting",
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
