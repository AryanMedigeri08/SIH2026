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
    from app.core.machinery_matcher import (
        find_matching_machinery_profile,
        detect_owned_machinery,
        calculate_tiered_capital_outlay,
        compute_statutory_banking_parameters,
        calculate_intelligent_turnover,
        load_machinery_dataset,
    )
    from app.config import settings
except ImportError:
    from backend.app.core.chat_service import chat_service
    from backend.app.core.odop_matcher import match_odop, find_district_odop
    from backend.app.core.machinery_matcher import (
        find_matching_machinery_profile,
        detect_owned_machinery,
        calculate_tiered_capital_outlay,
        compute_statutory_banking_parameters,
        calculate_intelligent_turnover,
        load_machinery_dataset,
    )
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
    "project_cost",         # user specifies or derived from promoter equity
]

OPTIONAL_FIELDS = [
    "block_name",
    "village_name",
    "is_rural",
    "promoter_equity",
    "gross_project_cost",
    "owned_machinery_value",
    "owned_machines",
    "machinery_selection_confirmed",
    "promoter_margin_pct",
    "tenure_years",
    "moratorium_months",
    "expected_monthly_units",
    "infrastructure_score",
    "capacity_unit_label",
    "tenure_reason",
    "moratorium_reason",
    "infra_reason",
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
    current_action: Optional[str] = Field(None, description="UI action trigger (confirm_loc, change_loc, submit_loc, odop_decision, select_owned_machinery)")
    odop_decision: Optional[str] = Field(None, description="User's ODOP decision: 'align' or 'keep_original'")
    user_location: Optional[Dict[str, Any]] = Field(None, description="GPS coordinates or hierarchy")
    selected_machines: Optional[List[Any]] = Field(None, description="List of owned machine items or names selected from dropdown/checklist")


class OnboardingResponse(BaseModel):
    reply: str = Field(..., description="Mira's conversational response text")
    tts_text: Optional[str] = Field(None, description="Cleaned speech text without awkward symbols for Bhashini")
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    next_step: int = Field(0)
    next_phase: str = Field("business_idea", description="Current conversation phase")
    all_fields_collected: bool = Field(False)
    odop_alignment: Optional[Dict[str, Any]] = None
    odop_comparison: Optional[Dict[str, Any]] = None
    machinery_analysis: Optional[Dict[str, Any]] = None
    banking_parameters: Optional[Dict[str, Any]] = None
    applicable_machinery: Optional[Dict[str, Any]] = None
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


# ── ODOP 100-Point Fixed Benchmarking System Prompt ───────────────────────────
ODOP_BENCHMARK_SYSTEM_PROMPT = """You are an expert MSME and Agro-Industrial Benchmarking Evaluator for the Government of India's One District One Product (ODOP) and MoFPI PMFME Scheme.

Your task is to evaluate the strategic alignment between an entrepreneur's proposed business venture and the statutory ODOP product of their district using a strictly calibrated 100-point fixed statutory benchmark.

### 100-POINT STATUTORY BENCHMARKING CRITERIA:

1. Pillar 1: Sector Overlap & Value-Addition Synergy (0 to 50 points)
   - 40 to 50 pts: Direct processing or primary value-addition with the district ODOP produce (e.g. Tomato -> Ketchup/Paste/Purée, Milk -> Ice Cream/Paneer/Ghee, Cotton -> Garments/Apparel, Turmeric -> Extraction/Powder, Mango -> Pulp/Pickle).
   - 25 to 39 pts: Allied food processing, cold chain, packaging, or complementary machinery/equipment servicing local ODOP clusters.
   - 0 to 24 pts: Unrelated services, retail, or disconnected trades with no raw material or process overlap (e.g. mobile repair, beauty salon, hardware store).

2. Pillar 2: Local Sourcing & Catchment Feasibility (0 to 25 points)
   - 18 to 25 pts: The district possesses established farmer clusters, FPOs, APMC mandis, or Common Facility Centers (CFC) for this ODOP commodity. Raw materials can be procured locally at lower freight cost.
   - 10 to 17 pts: Partial local catchment; secondary processing or inter-district transit sourcing needed.
   - 0 to 9 pts: Infeasible local sourcing; the venture does not utilize agricultural or indigenous district raw materials.

3. Pillar 3: PMFME 35% Scheme Subsidy Qualification (0 to 25 points)
   - 20 to 25 pts: Fully qualifies for MoFPI PMFME credit-linked capital subsidy (35% up to ₹10 Lakhs) on plant and machinery, Common Facility Center (CFC) access, and priority GeM onboarding.
   - 12 to 19 pts: Partial cluster incentive; eligible under allied MSME schemes (PMEGP 15-35%).
   - 0 to 11 pts: Ineligible under PMFME (must rely solely on general PMEGP/MUDRA schemes).

### SCORING & RECOMMENDATION RULES:
- alignment_score = pillar_1_score + pillar_2_score + pillar_3_score (clamped between 15 and 98).
- If alignment_score >= 65:
  * verdict_key: "recommended"
  * verdict_title: "उत्कृष्ट तालमेल (Highly Recommended)"
  * mira_recommendation: "Mira Recommends: Excellent ODOP Synergy for 35% Subsidy"
  * recommendation logic: Enthusiastically recommend aligning with ODOP to capture the 35% PMFME capital subsidy (up to ₹10 Lakhs) and local farmer procurement.
- If alignment_score is 50 to 64:
  * verdict_key: "viable"
  * verdict_title: "सकारात्मक तालमेल (Viable Synergy)"
  * mira_recommendation: "Mira Recommends: Viable Strategic Opportunity"
  * recommendation logic: Viable strategic opportunity if the entrepreneur wants to add a district product line for subsidy, but also viable to keep the original plan.
- If alignment_score < 50:
  * verdict_key: "not_recommended"
  * verdict_title: "कम तालमेल (Standard MSME Recommended)"
  * mira_recommendation: "Mira Recommends: Continue with Standard Business Model"
  * recommendation logic: Honestly advise against forced alignment. Sincere recommendation to proudly proceed with the original business model under standard PMEGP/MUDRA schemes.

### OUTPUT FORMAT:
You MUST respond with valid JSON ONLY. No markdown wrappers, no conversational commentary.
{
  "pillar_1_score": <int 0-50>,
  "pillar_2_score": <int 0-25>,
  "pillar_3_score": <int 0-25>,
  "alignment_score": <int 15-98>,
  "verdict_key": "recommended" | "viable" | "not_recommended",
  "verdict_title": "<Localized title in English or Hindi>",
  "mira_recommendation": "<Concise recommendation statement>",
  "verdict_spoken": "<One or two clean spoken sentences in the requested language giving Mira's verdict>",
  "product_innovation_title": "<Title for Pillar 1>",
  "product_innovation_desc": "<Detailed strategic idea description for Pillar 1>",
  "local_sourcing_title": "<Title for Pillar 2>",
  "local_sourcing_desc": "<Detailed description for Pillar 2>",
  "financial_incentives_title": "<Title for Pillar 3>",
  "financial_incentives_desc": "<Detailed description for Pillar 3>"
}
"""


def _compute_deterministic_benchmark(
    sector: str,
    user_business: str,
    state: str,
    district: str,
    odop_product: str,
    pmfme_item: str,
    target_sectors: list[str],
    raw_material_available: bool,
    cfc_available: bool,
    pmfme_eligible: bool,
    language: str = "hi",
) -> dict[str, Any]:
    sector_norm = (sector or "general").lower().strip()
    idea_norm = (user_business or "").lower().strip()
    odop_lower = (odop_product or "").lower()
    pmfme_lower = (pmfme_item or "").lower()
    primary_crop = pmfme_item.split("(")[0].strip() if "(" in pmfme_item else pmfme_item
    sector_clean = sector.replace("_", " ").title()

    # Pillar 1: Sector Overlap & Value-Addition (0 to 50 pts)
    p1 = 0
    if sector_norm in target_sectors:
        p1 = 49
    elif any(kw in idea_norm for kw in ["ice cream", "kulfi", "sweet", "dessert", "bakery", "snack", "juice", "jam", "chocolat", "sauce", "ketchup", "puree", "pasta", "flour", "oil"]) and any(kw in (odop_lower + " " + pmfme_lower) for kw in ["millet", "fruit", "dairy", "milk", "grain", "mango", "orange", "banana", "tomato", "chilli", "spice", "pulses", "rice"]):
        p1 = 48
    elif sector_norm in ("dairy", "food_processing") and any(s in target_sectors for s in ("dairy", "food_processing", "agriculture")):
        p1 = 44
    elif sector_norm in ("repair", "fabrication") and any(kw in (odop_lower + " " + pmfme_lower) for kw in ["machinery", "engineering", "steel", "tools", "hardware"]):
        p1 = 38
    elif sector_norm in ("apparel", "artisan_trades") and any(kw in (odop_lower + " " + pmfme_lower) for kw in ["textile", "garment", "silk", "cotton", "handloom", "carpet"]):
        p1 = 45
    elif sector_norm in ("service", "repair", "general"):
        p1 = 18
    else:
        p1 = 12

    # Pillar 2: Local Sourcing & Catchment Feasibility (0 to 25 pts)
    p2 = 0
    if raw_material_available and cfc_available:
        p2 = 24
    elif raw_material_available:
        p2 = 20
    elif cfc_available:
        p2 = 15
    else:
        p2 = 10
    if sector_norm in ("repair", "service", "general") and p1 < 25:
        p2 = min(p2, 8)

    # Pillar 3: PMFME 35% Scheme Subsidy Qualification (0 to 25 pts)
    p3 = 0
    if pmfme_eligible and (p1 >= 30 or "food" in sector_norm or "dairy" in sector_norm):
        p3 = 24
    elif pmfme_eligible:
        p3 = 16
    else:
        p3 = 8
    if sector_norm in ("repair", "service", "general") and p1 < 25:
        p3 = 7

    score = max(15, min(98, p1 + p2 + p3))

    if score >= 65:
        verdict_key = "recommended"
        verdict_title = "उत्कृष्ट तालमेल (Highly Recommended)"
        mira_rec = "Mira Recommends: Excellent ODOP Synergy for 35% Subsidy"
        if language == "hi":
            verdict_spoken = f"मुझे आपके व्यवसाय का {primary_crop} के साथ बहुत सुंदर तालमेल मिला है और इसका स्कोर {score} आया है। मेरी दिल से सलाह है कि आप इसे ज़रूर अपनाएँ ताकि आपको 35 प्रतिशत सरकारी सब्सिडी मिल सके।"
        elif language == "mr":
            verdict_spoken = f"मला तुमच्या व्यवसायाचा {primary_crop} सोबत अतिशय सुंदर मेळ मिळाला आहे आणि याचा स्कोअर {score} आला आहे. 35 टक्के सरकारी सबसिडीसाठी तुम्ही हा पर्याय नक्की निवडावा असा माझा सल्ला आहे."
        else:
            verdict_spoken = f"I found an excellent strategic synergy between your venture and {primary_crop} with an alignment score of {score} out of 100. My sincere recommendation is to align with ODOP to unlock the 35 percent capital subsidy."
    elif score >= 50:
        verdict_key = "viable"
        verdict_title = "सकारात्मक तालमेल (Viable Synergy)"
        mira_rec = "Mira Recommends: Viable Strategic Opportunity"
        if language == "hi":
            verdict_spoken = f"आपके व्यवसाय का ODOP के साथ स्कोर {score} है। यह एक अच्छा अतिरिक्त विकल्प है जिसे आप सब्सिडी के लिए जोड़ सकते हैं या अपने मूल विचार के साथ भी बढ़ सकते हैं।"
        elif language == "mr":
            verdict_spoken = f"तुमच्या व्यवसायाचा ODOP सोबत स्कोअर {score} आला आहे. सबसिडी मिळवण्यासाठी तुम्ही हा पर्याय जोडू शकता किंवा मूळ कल्पनेनेही पुढे जाऊ शकता."
        else:
            verdict_spoken = f"Your venture has a viable strategic synergy score of {score} out of 100 with ODOP. It provides a rewarding opportunity for capital subsidy, though proceeding with your original model is also viable."
    else:
        verdict_key = "not_recommended"
        verdict_title = "कम तालमेल (Standard MSME Recommended)"
        mira_rec = "Mira Recommends: Continue with Standard Business Model"
        if language == "hi":
            verdict_spoken = f"मैं आपसे बिल्कुल सच कहूँगी, आपके इस विचार के लिए जबरदस्ती ODOP जोड़ना सही नहीं रहेगा। आपका स्कोर {score} है। मेरी सलाह है कि आप अपने मूल विचार के साथ ही PMEGP और मुद्रा लोन का लाभ लें।"
        elif language == "mr":
            verdict_spoken = f"मी तुमच्याशी अगदी खरे बोलेन, या व्यवसायासाठी जबरदस्तीने ODOP जोडणे योग्य ठरणार नाही. तुमचा स्कोअर {score} आहे. तुम्ही तुमच्या मूळ कल्पनेसह PMEGP आणि मुद्रा कर्ज योजनांचा लाभ घ्यावा."
        else:
            verdict_spoken = f"I will be completely honest with you. Forced alignment with {primary_crop} does not suit your business model, and the alignment score is only {score} out of 100. My sincere recommendation is to proceed with your original business model under standard PMEGP and Mudra loan schemes."

    if sector_norm in ("dairy", "food_processing"):
        innov_title = f"Product Innovation ({primary_crop}-Infused {sector_clean})"
        innov_desc = f"Introduce a premium, health-conscious line of products made with a {primary_crop} base or incorporating {primary_crop} malted flavors and mix-ins, targeting high-margin regional retail corridors."
    elif sector_norm in ("apparel", "artisan_trades"):
        innov_title = f"Design Innovation (Local {primary_crop} & Craft Blend)"
        innov_desc = f"Incorporate {district}'s indigenous {primary_crop} fibers or traditional motifs into modern apparel and lifestyle lines, unlocking premium export corridors."
    elif sector_norm in ("repair", "fabrication", "service"):
        innov_title = f"Service Expansion (Agri-Cluster Tooling & Equipment Support)"
        innov_desc = f"Expand your {sector_clean} operations to provide specialized repair, maintenance, and tooling support for machinery used by {primary_crop} processing units in {district}."
    else:
        innov_title = f"Product Innovation ({primary_crop} Integration)"
        innov_desc = f"Introduce a specialized product line utilizing {primary_crop}, achieving regional differentiation and government cluster priority."

    source_title = f"Local Sourcing Advantage ({district} Farmer Clusters)"
    source_desc = f"Procure raw {primary_crop} directly from registered FPOs and APMC mandis in {district}, eliminating intermediary markups and ensuring freshness."

    fin_title = "Financial Incentives (PMFME 35% Capital Subsidy)"
    fin_desc = f"Aligning with {primary_crop} qualifies your enterprise for the MoFPI PMFME 35% credit-linked capital subsidy up to ₹10 Lakhs on plant and machinery, along with priority GeM onboarding."

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
        "alignment_score": score,
        "pillar_scores": {
            "pillar_1_sector_overlap": p1,
            "pillar_2_local_sourcing": p2,
            "pillar_3_subsidy_qualification": p3,
        },
        "verdict_key": verdict_key,
        "verdict_title": verdict_title,
        "mira_recommendation": mira_rec,
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


def _generate_odop_synergy(
    user_business: str,
    sector: str,
    state: str,
    district: str,
    language: str = "hi",
) -> Optional[dict[str, Any]]:
    """
    Constructs a 3-pillar strategic synergy aligning the user's business with the district's ODOP,
    scored 0-100 against fixed statutory benchmarks evaluated by LLM with deterministic fallback.
    """
    try:
        odop_data = find_district_odop(state, district) or {}
        pmfme_item = odop_data.get("pmfme_odop_product") or odop_data.get("odop_product") or "Local Agricultural Produce"
        odop_item = odop_data.get("odop_product") or pmfme_item
        primary_crop = pmfme_item.split("(")[0].strip() if "(" in pmfme_item else pmfme_item
        target_sectors = [s.lower() for s in odop_data.get("matching_sectors", [])]
        raw_mat = bool(odop_data.get("raw_material_availability", True))
        cfc_avail = bool(odop_data.get("cfc_available", False))
        pmfme_elig = bool(odop_data.get("pmfme_eligible", True))

        # Baseline deterministic benchmark evaluation
        baseline = _compute_deterministic_benchmark(
            sector=sector,
            user_business=user_business,
            state=state,
            district=district,
            odop_product=odop_item,
            pmfme_item=pmfme_item,
            target_sectors=target_sectors,
            raw_material_available=raw_mat,
            cfc_available=cfc_avail,
            pmfme_eligible=pmfme_elig,
            language=language,
        )

        # Call LLM to evaluate the entrepreneur's nuances against the fixed benchmark
        eval_prompt = (
            f"Evaluate strategic alignment for:\n"
            f"- Proposed Business: {user_business}\n"
            f"- Sector: {sector}\n"
            f"- Location: {district}, {state}\n"
            f"- District ODOP Product: {pmfme_item} ({primary_crop})\n"
            f"- Target Cluster Sectors: {', '.join(target_sectors) if target_sectors else 'Agro / Processing'}\n"
            f"- PMFME Scheme Eligible: {pmfme_elig}\n"
            f"- CFC Available: {cfc_avail}\n"
            f"- Raw Material Abundance in District: {raw_mat}\n"
            f"- User Preferred Language: {language}\n"
        )

        llm_messages = [
            {"role": "system", "content": ODOP_BENCHMARK_SYSTEM_PROMPT},
            {"role": "user", "content": eval_prompt},
        ]

        try:
            content, _, _ = chat_service._call_llm_chat_completion(
                messages=llm_messages,
                temperature=0.1,
                max_tokens=550,
                timeout_s=10.0,
            )
            if content and content.strip():
                clean_json_str = content.strip()
                if "```json" in clean_json_str:
                    clean_json_str = clean_json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_json_str:
                    clean_json_str = clean_json_str.split("```")[1].split("```")[0].strip()

                parsed = json.loads(clean_json_str)

                p1 = int(parsed.get("pillar_1_score", baseline["pillar_scores"]["pillar_1_sector_overlap"]))
                p2 = int(parsed.get("pillar_2_score", baseline["pillar_scores"]["pillar_2_local_sourcing"]))
                p3 = int(parsed.get("pillar_3_score", baseline["pillar_scores"]["pillar_3_subsidy_qualification"]))

                # Clamp to statutory limits
                p1 = max(0, min(50, p1))
                p2 = max(0, min(25, p2))
                p3 = max(0, min(25, p3))
                final_score = max(15, min(98, p1 + p2 + p3))

                verdict_key = "recommended" if final_score >= 65 else ("viable" if final_score >= 50 else "not_recommended")

                baseline["alignment_score"] = final_score
                baseline["pillar_scores"] = {
                    "pillar_1_sector_overlap": p1,
                    "pillar_2_local_sourcing": p2,
                    "pillar_3_subsidy_qualification": p3,
                }
                baseline["verdict_key"] = verdict_key

                if parsed.get("verdict_title"):
                    baseline["verdict_title"] = parsed["verdict_title"]
                if parsed.get("mira_recommendation"):
                    baseline["mira_recommendation"] = parsed["mira_recommendation"]
                if parsed.get("verdict_spoken"):
                    baseline["verdict_spoken"] = parsed["verdict_spoken"]

                if parsed.get("product_innovation_title") and parsed.get("product_innovation_desc"):
                    baseline["synergy_pillars"]["product_innovation"] = {
                        "title": parsed["product_innovation_title"],
                        "description": parsed["product_innovation_desc"],
                    }
                if parsed.get("local_sourcing_title") and parsed.get("local_sourcing_desc"):
                    baseline["synergy_pillars"]["local_sourcing"] = {
                        "title": parsed["local_sourcing_title"],
                        "description": parsed["local_sourcing_desc"],
                    }
                if parsed.get("financial_incentives_title") and parsed.get("financial_incentives_desc"):
                    baseline["synergy_pillars"]["financial_incentives"] = {
                        "title": parsed["financial_incentives_title"],
                        "description": parsed["financial_incentives_desc"],
                    }
        except Exception as llm_err:
            logger.warning("LLM ODOP benchmark scoring fallback used due to: %s", llm_err)

        return baseline
    except Exception as e:
        logger.error("ODOP synergy generation error: %s", e, exc_info=True)
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

        if not last_user_msg and action not in ("odop_decision", "select_owned_machinery"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user message found in conversation",
            )

        merged_fields = {**existing_fields, **new_fields}

        # ── Action: Owned Machinery Selection from Interactive Dropdown / Checklist ──
        if action == "select_owned_machinery":
            biz_query = (
                merged_fields.get("additional_business_details")
                or merged_fields.get("enterprise_name")
                or last_user_msg
            )
            matched_mach = find_matching_machinery_profile(
                biz_query,
                merged_fields.get("sector"),
            )
            if matched_mach:
                m_name = matched_mach.get("business_name")
                new_fields["matched_machinery_profile"] = m_name
                merged_fields["matched_machinery_profile"] = m_name

            chosen_items = payload.selected_machines or []
            confirmed_owned: List[Dict[str, Any]] = []

            if chosen_items:
                profile_machines = matched_mach.get("machinery_list", []) if matched_mach else []
                for item in chosen_items:
                    if isinstance(item, dict):
                        m_name = item.get("machine_name", "")
                        m_cost = float(item.get("estimated_cost_inr", 0))
                        m_specs = item.get("technical_specs", "")
                        m_hp = float(item.get("power_hp", 0))
                    else:
                        m_name = str(item)
                        m_cost = 0.0
                        m_specs = ""
                        m_hp = 0.0

                    for pm in profile_machines:
                        if pm.get("machine_name", "").lower() == m_name.lower():
                            if m_cost == 0:
                                m_cost = float(pm.get("estimated_cost_inr", 0))
                            if not m_specs:
                                m_specs = pm.get("technical_specs", "")
                            if m_hp == 0:
                                m_hp = float(pm.get("power_hp", 0))
                            break

                    confirmed_owned.append({
                        "machine_name": m_name,
                        "estimated_cost_inr": m_cost,
                        "technical_specs": m_specs,
                        "power_hp": m_hp,
                    })

            total_owned_val = sum(m.get("estimated_cost_inr", 0) for m in confirmed_owned)
            new_fields["owned_machines"] = confirmed_owned
            new_fields["owned_machinery_value"] = total_owned_val
            new_fields["machinery_selection_confirmed"] = True
            merged_fields["owned_machines"] = confirmed_owned
            merged_fields["owned_machinery_value"] = total_owned_val
            merged_fields["machinery_selection_confirmed"] = True

            # Outlay recalculation if equity is present
            emi_saved = 0.0
            if "promoter_equity" in merged_fields:
                outlay_calc = calculate_tiered_capital_outlay(
                    promoter_equity=float(merged_fields["promoter_equity"]),
                    owned_machinery_value=total_owned_val,
                    explicit_project_cost=existing_fields.get("explicit_project_cost"),
                )
                new_fields["gross_project_cost"] = outlay_calc["gross_project_cost"]
                new_fields["project_cost"] = outlay_calc["net_project_cost"]
                new_fields["promoter_margin_pct"] = outlay_calc["promoter_margin_pct"]
                new_fields["estimated_monthly_emi_saved"] = outlay_calc["estimated_monthly_emi_saved_inr"]
                new_fields["estimated_interest_saved"] = outlay_calc["estimated_interest_saved_inr"]
                new_fields["outlay_tier_name"] = outlay_calc["tier_name"]
                merged_fields.update({
                    "gross_project_cost": outlay_calc["gross_project_cost"],
                    "project_cost": outlay_calc["net_project_cost"],
                    "promoter_margin_pct": outlay_calc["promoter_margin_pct"],
                    "estimated_monthly_emi_saved": outlay_calc["estimated_monthly_emi_saved_inr"],
                    "estimated_interest_saved": outlay_calc["estimated_interest_saved_inr"],
                    "outlay_tier_name": outlay_calc["tier_name"],
                })
                emi_saved = outlay_calc["estimated_monthly_emi_saved_inr"]

            # Banking parameters
            if "sector" in merged_fields and "project_cost" in merged_fields:
                bank_params = compute_statutory_banking_parameters(
                    sector=merged_fields["sector"],
                    business_category=merged_fields.get("business_category", "manufacturing"),
                    project_cost=merged_fields["project_cost"],
                    is_rural=bool(merged_fields.get("is_rural", True)),
                    matched_profile=matched_mach,
                )
                for k, v in bank_params.items():
                    new_fields[k] = v
                    merged_fields[k] = v

            mach_names_list = [m["machine_name"] for m in confirmed_owned]
            mach_names_str = ", ".join(mach_names_list) if mach_names_list else "आपकी मशीनें"

            applicable_mach_payload = {
                "business_name": matched_mach.get("business_name") if matched_mach else None,
                "category": matched_mach.get("category") if matched_mach else None,
                "industry_sector": matched_mach.get("industry_sector") if matched_mach else None,
                "typical_capacity": matched_mach.get("typical_capacity") if matched_mach else None,
                "total_machinery_cost_inr": matched_mach.get("total_machinery_cost_inr") if matched_mach else None,
                "machinery_list": matched_mach.get("machinery_list", []) if matched_mach else [],
            } if matched_mach else None

            # Case A: Promoter equity not yet known
            if "promoter_equity" not in merged_fields:
                if total_owned_val > 0:
                    if payload.language == "hi":
                        reply = (
                            f"बहुत खूब {payload.user_name} जी! आपने {mach_names_str} चुना है, जिसकी कुल अनुमानित कीमत लगभग ₹{int(total_owned_val):,} है। "
                            f"हमने इसे इन-काइंड एसेट मानकर आपके आवश्यक बैंक लोन में से घटा दिया है, जिससे आपको कम लोन लेना पड़ेगा! "
                            f"अब कृपया मुझे बताइए कि इस उद्यम को शुरू करने के लिए आपके पास अपनी खुद की कितनी प्रमोटर इक्विटी यानी आपकी अपनी बचत या पूँजी तैयार है? "
                            f"जैसे ₹50,000, ₹1 लाख या ₹2 लाख?"
                        )
                    elif payload.language == "mr":
                        reply = (
                            f"अतिशय छान {payload.user_name} जी! तुम्ही {mach_names_str} निवडले आहे, ज्याचे मूल्य सुमारे ₹{int(total_owned_val):,} आहे. "
                            f"आम्ही हे तुमच्या आवश्यक बँक कर्जातून वजा केले आहे! "
                            f"आता कृपया मला सांगा की हा व्यवसाय सुरू करण्यासाठी तुमच्याकडे स्वतःचे किती प्रमोटर इक्विटी भांडवल किंवा स्वतःची बचत तयार आहे? "
                            f"जसे ₹50,000, ₹1 लाख किंवा ₹2 लाख?"
                        )
                    else:
                        reply = (
                            f"Excellent {payload.user_name} Ji! You have selected {mach_names_str} valued at approximately ₹{int(total_owned_val):,}. "
                            f"We have credited this as an in-kind promoter contribution, reducing your required bank loan! "
                            f"Now please share how much promoter equity (your own personal savings or capital) you have ready to invest? "
                            f"For example, ₹50,000, ₹1 Lakh, or ₹2 Lakhs?"
                        )
                else:
                    if payload.language == "hi":
                        reply = (
                            f"बहुत अच्छा {payload.user_name} जी! मैंने नोट कर लिया है कि आपको सभी नए उपकरणों की आवश्यकता होगी। "
                            f"हम पूरा प्रोजेक्ट नए आधुनिक प्लांट व मशीनरी के आधार पर तैयार कर रहे हैं। "
                            f"अब कृपया मुझे बताइए कि इस उद्यम को शुरू करने के लिए आपके पास अपनी खुद की कितनी प्रमोटर इक्विटी यानी आपकी अपनी बचत या पूँजी तैयार है? "
                            f"जैसे ₹50,000, ₹1 लाख या ₹2 लाख?"
                        )
                    elif payload.language == "mr":
                        reply = (
                            f"खूप छान {payload.user_name} जी! मी नोंदवून घेतले आहे की तुम्हाला सर्व नवीन यंत्रसामग्रीची आवश्यकता असेल. "
                            f"आपण नवीन उपकरणांनुसार प्रकल्प तयार करत आहोत. "
                            f"आता कृपया मला सांगा की हा व्यवसाय सुरू करण्यासाठी तुमच्याकडे स्वतःचे किती प्रमोटर इक्विटी भांडवल किंवा स्वतःची बचत तयार आहे? "
                            f"जसे ₹50,000, ₹1 लाख किंवा ₹2 लाख?"
                        )
                    else:
                        reply = (
                            f"Understood {payload.user_name} Ji! I have noted that you will be acquiring all new machinery. "
                            f"We are planning your project outlay for brand new equipment. "
                            f"Now please tell me how much promoter equity (your own personal savings or capital) you have ready to start? "
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
                    applicable_machinery=applicable_mach_payload,
                    machinery_analysis={
                        "matched_profile": merged_fields.get("matched_machinery_profile"),
                        "owned_machines": confirmed_owned,
                        "owned_machinery_value": total_owned_val,
                        "gross_project_cost": merged_fields.get("gross_project_cost"),
                        "net_project_cost": merged_fields.get("project_cost"),
                        "promoter_margin_pct": merged_fields.get("promoter_margin_pct"),
                        "monthly_emi_saved": emi_saved,
                    },
                    banking_parameters={
                        "tenure_years": merged_fields.get("tenure_years"),
                        "moratorium_months": merged_fields.get("moratorium_months"),
                        "infrastructure_score": merged_fields.get("infrastructure_score"),
                        "expected_monthly_units": merged_fields.get("expected_monthly_units"),
                        "capacity_unit_label": merged_fields.get("capacity_unit_label"),
                        "tenure_reason": merged_fields.get("tenure_reason"),
                        "moratorium_reason": merged_fields.get("moratorium_reason"),
                    } if "tenure_years" in merged_fields else None,
                    message={"role": "assistant", "content": reply},
                )

            # Case B: Promoter equity is already known -> Present ODOP synergy benchmarking!
            odop_synergy = _generate_odop_synergy(
                user_business=merged_fields.get("additional_business_details") or merged_fields.get("enterprise_name") or f"{merged_fields.get('sector', 'MSME')} Business",
                sector=merged_fields["sector"],
                state=existing_fields.get("state_name") or state_name,
                district=existing_fields.get("district_name") or district_name,
                language=payload.language,
            )

            p_crop = odop_synergy.get("primary_odop_product", "District Product")
            score_val = odop_synergy.get("alignment_score", 75)
            is_good_synergy = score_val >= 60
            biz_desc = merged_fields.get("enterprise_name") or f"{merged_fields.get('sector', 'MSME').replace('_', ' ').title()} Business"

            if payload.language == "hi":
                owned_lead = (
                    f"बहुत खूब {payload.user_name} जी! आपने {mach_names_str} चुना है (कीमत ₹{int(total_owned_val):,})। "
                    f"हमने इसे आपके आवश्यक बैंक लोन में से घटा दिया है, जिससे आपकी मासिक EMI में लगभग ₹{int(emi_saved):,} रुपये की बचत होगी! "
                    if total_owned_val > 0 else
                    f"बहुत अच्छा {payload.user_name} जी! मैंने नोट कर लिया है कि आपको सभी नए उपकरणों की आवश्यकता होगी। "
                )
                synergy_spoken = (
                    odop_synergy.get("verdict_spoken")
                    or (
                        f"यह तालमेल आपके लिए बहुत ही फायदेमंद रहेगा क्योंकि आप अपने उत्पाद में स्थानीय {p_crop} का उपयोग करके "
                        f"सीधे 35 प्रतिशत PMFME पूंजीगत सब्सिडी का पूरा लाभ उठा सकते हैं।"
                        if is_good_synergy else
                        f"मेरी दिल से सलाह है कि आप अपने मूल विचार के साथ ही आगे बढ़ें जहाँ आपको PMEGP और मुद्रा लोन का पूरा लाभ मिलेगा।"
                    )
                )
                reply = (
                    f"{owned_lead}"
                    f"क्या आप जानते हैं? सरकार की ODOP योजना के तहत अगर आप अपने ज़िले के चयनित उत्पाद से जुड़ते हैं, "
                    f"तो मशीनरी पर पूरे 35 प्रतिशत की भारी सरकारी सब्सिडी मिलती है! "
                    f"आपके {district_name} ज़िले का आधिकारिक ODOP {p_crop} है और आपका व्यवसाय विचार {biz_desc} का है। "
                    f"मैंने इन दोनों को मिलाकर आपके लिए रणनीतिक तालमेल तैयार किया है, और इसका अलाइनमेंट स्कोर 100 में से {score_val} आया है! "
                    f"{synergy_spoken} "
                    f"नीचे दिए गए कार्ड में मैंने आपका पूरा विश्लेषण तैयार किया है। तो अब आप मुझे बताइए, आप क्या चुनना चाहेंगे:\n"
                    f"1. ODOP से जुड़ें\n"
                    f"2. अपना मूल विचार रखें"
                )
            elif payload.language == "mr":
                owned_lead_mr = (
                    f"अतिशय छान {payload.user_name} जी! तुम्ही {mach_names_str} निवडले आहे (मूल्य ₹{int(total_owned_val):,}). "
                    f"आम्ही हे तुमच्या आवश्यक बँक कर्जातून वजा केले आहे, ज्यामुळे दरमहा EMI मध्ये सुमारे ₹{int(emi_saved):,} ची बचत होईल! "
                    if total_owned_val > 0 else
                    f"खूप छान {payload.user_name} जी! मी नोंदवून घेतले आहे की तुम्हाला सर्व नवीन यंत्रसामग्रीची आवश्यकता असेल. "
                )
                synergy_spoken_mr = (
                    odop_synergy.get("verdict_spoken")
                    or (
                        f"हा मेळ तुमच्यासाठी अत्यंत फायदेशीर ठरेल! कारण तुम्ही स्थानिक {p_crop} चा वापर करून थेट 35 टक्के सबसिडी मिळवू शकता."
                        if is_good_synergy else
                        f"तुम्ही तुमच्या मूळ कल्पनेसह पुढे जावे हा माझा सल्ला आहे."
                    )
                )
                reply = (
                    f"{owned_lead_mr}"
                    f"शासनाच्या ODOP योजनेअंतर्गत स्थानिक उत्पादनाशी जोडल्यास यंत्रसामग्रीवर तब्बल 35 टक्के सबसिडी मिळते! "
                    f"तुमच्या {district_name} जिल्ह्याचे मुख्य उत्पादन {p_crop} आहे आणि तुमची कल्पना {biz_desc} ची आहे. "
                    f"मी या दोघांचा रणनीतिक मेळ घातला असून त्याचा स्कोअर 100 पैकी {score_val} आला आहे! "
                    f"{synergy_spoken_mr} "
                    f"आता मला सांगा, तुम्हाला कोणता पर्याय निवडायला आवडेल:\n"
                    f"1. ODOP शी जोडा\n"
                    f"2. माझी मूळ कल्पना ठेवा"
                )
            else:
                owned_lead_en = (
                    f"Excellent {payload.user_name} Ji! You have selected {mach_names_str} (valued at approximately ₹{int(total_owned_val):,}). "
                    f"We have credited this as an in-kind promoter contribution, saving you approximately ₹{int(emi_saved):,} per month in EMI! "
                    if total_owned_val > 0 else
                    f"Got it {payload.user_name} Ji! I have noted that you will be acquiring all fresh equipment. "
                )
                synergy_spoken_en = (
                    odop_synergy.get("verdict_spoken")
                    or (
                        f"This alignment is wonderfully beneficial for you! By integrating {district_name}'s local {p_crop}, you qualify for 35 percent PMFME grant."
                        if is_good_synergy else
                        f"My sincere recommendation is to proudly proceed with your original business model under PMEGP or Mudra."
                    )
                )
                reply = (
                    f"{owned_lead_en}"
                    f"Under the government's One District One Product (ODOP) initiative, aligning with your district's designated product unlocks a 35 percent capital subsidy on machinery! "
                    f"Your district {district_name} focuses on {p_crop}, and your enterprise is {biz_desc}. "
                    f"I have benchmarked your alignment synergy at {score_val} out of 100! "
                    f"{synergy_spoken_en} "
                    f"I have presented your complete alignment match in the card below. Now please tell me what you would love to choose:\n"
                    f"1. Align with ODOP\n"
                    f"2. Keep my idea"
                )

            new_fields["odop_alignment_presented"] = True
            new_fields["odop_product"] = p_crop
            new_fields["odop_score"] = score_val
            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="odop_alignment",
                all_fields_collected=False,
                odop_alignment=odop_synergy,
                odop_comparison=odop_synergy,
                applicable_machinery=applicable_mach_payload,
                machinery_analysis={
                    "matched_profile": merged_fields.get("matched_machinery_profile"),
                    "owned_machines": confirmed_owned,
                    "owned_machinery_value": total_owned_val,
                    "gross_project_cost": merged_fields.get("gross_project_cost"),
                    "net_project_cost": merged_fields.get("project_cost"),
                    "promoter_margin_pct": merged_fields.get("promoter_margin_pct"),
                    "monthly_emi_saved": emi_saved,
                },
                banking_parameters={
                    "tenure_years": merged_fields.get("tenure_years"),
                    "moratorium_months": merged_fields.get("moratorium_months"),
                    "infrastructure_score": merged_fields.get("infrastructure_score"),
                    "expected_monthly_units": merged_fields.get("expected_monthly_units"),
                    "capacity_unit_label": merged_fields.get("capacity_unit_label"),
                    "tenure_reason": merged_fields.get("tenure_reason"),
                    "moratorium_reason": merged_fields.get("moratorium_reason"),
                },
                message={"role": "assistant", "content": reply},
            )

        # ── Action / Turn: User made ODOP Alignment Decision ──────────────────
        is_odop_action = action == "odop_decision" or payload.odop_decision is not None
        odop_pending = (
            existing_fields.get("odop_alignment_presented") is True
            or (
                existing_fields.get("odop_decision") is None
                and ("promoter_equity" in existing_fields or "project_cost" in existing_fields)
                and "sector" in existing_fields
            )
        )

        user_text_clean = last_user_msg.strip().lower() if last_user_msg else ""
        decision_choice = None

        if payload.odop_decision in ("align", "keep_original"):
            decision_choice = payload.odop_decision
        elif is_odop_action:
            decision_choice = "align" if (payload.odop_decision == "align" or "align" in user_text_clean) else "keep_original"
        elif odop_pending and user_text_clean:
            align_patterns = [
                r'^\s*1\b', r'^\s*१\b', r'\bodop\b', r'\balign\b',
                r'जुड़ें', r'जोड़ें', r'जोड़ा', r'पहला', r'सब्सिडी',
                r'subsidy', r'option\s*1', r'choice\s*1', r'35\s*%',
                r'हाँ', r'yes', r'होय', r'हॉ', r'स्वीकार'
            ]
            keep_patterns = [
                r'^\s*2\b', r'^\s*२\b', r'\bkeep\b', r'\boriginal\b',
                r'मूल\s*विचार', r'मेरा\s*विचार', r'दूसरा', r'option\s*2',
                r'choice\s*2', r'नहीं', r'no', r'नाही', r'ना'
            ]
            if any(re.search(p, user_text_clean, re.IGNORECASE) for p in align_patterns):
                decision_choice = "align"
            elif any(re.search(p, user_text_clean, re.IGNORECASE) for p in keep_patterns):
                decision_choice = "keep_original"

        if decision_choice:
            align_with_odop = (decision_choice == "align")
            new_fields["odop_decision"] = decision_choice
            new_fields["odop_synergy_aligned"] = align_with_odop
            merged_fields["odop_decision"] = decision_choice
            merged_fields["odop_synergy_aligned"] = align_with_odop

            # Ensure all banking & outlay parameters are finalized and present
            matched_mach = find_matching_machinery_profile(
                merged_fields.get("additional_business_details") or merged_fields.get("enterprise_name", ""),
                merged_fields.get("sector"),
            )
            bank_params = compute_statutory_banking_parameters(
                sector=merged_fields.get("sector", "general"),
                business_category=merged_fields.get("business_category", "manufacturing"),
                project_cost=merged_fields.get("project_cost", 500000.0),
                is_rural=bool(merged_fields.get("is_rural", True)),
                matched_profile=matched_mach,
            )
            for k, v in bank_params.items():
                if k not in existing_fields:
                    new_fields[k] = v
                    merged_fields[k] = v

            odop_prod = (
                existing_fields.get("odop_product")
                or existing_fields.get("primary_odop_product")
            )
            if not odop_prod or odop_prod == "District Product":
                odop_info = find_district_odop(state_name, district_name) or {}
                odop_prod = odop_info.get("pmfme_odop_product") or odop_info.get("odop_product") or "ODOP Produce"
                if "(" in odop_prod:
                    odop_prod = odop_prod.split("(")[0].strip()

            new_fields["odop_product"] = odop_prod
            merged_fields["odop_product"] = odop_prod

            if align_with_odop:
                synergy_note = f"ODOP Cluster Synergy: Aligned with {odop_prod} under MoFPI PMFME 35% Scheme."
                existing_notes = merged_fields.get("additional_business_details", "")
                if synergy_note not in existing_notes:
                    merged_fields["additional_business_details"] = f"{existing_notes} | {synergy_note}".strip(" |")
                    new_fields["additional_business_details"] = merged_fields["additional_business_details"]

            if payload.language == "hi":
                if align_with_odop:
                    reply = (
                        f"बहुत ही शानदार और समझदारी भरा निर्णय {payload.user_name} जी! "
                        f"हमने आपके व्यवसाय को {district_name} के आधिकारिक ODOP उत्पाद {odop_prod} के साथ रणनीतिक रूप से जोड़ दिया है। "
                        f"इससे आपको मशीनरी पर पूरे 35 प्रतिशत की भारी PMFME सरकारी सब्सिडी और GeM पोर्टल पर सरकारी खरीद में प्राथमिकता मिलेगी। "
                        f"आपकी सभी जानकारियाँ पूरी तरह से सुरक्षित कर ली गई हैं। अब मैं आपके लिए पूरी बैंक-स्तरीय व्यवहार्यता और वित्तीय मूल्यांकन रिपोर्ट तैयार कर रही हूँ!"
                    )
                else:
                    reply = (
                        f"बहुत बढ़िया {payload.user_name} जी! मुझे अपने मूल विचार पर आपका यह आत्मविश्वास और स्पष्टता बहुत पसंद आई। "
                        f"हम आपके इसी मूल व्यवसाय मॉडल के साथ आगे बढ़ेंगे जहाँ आपको सरकार की PMEGP और मुद्रा ऋण योजनाओं का पूरा लाभ मिलेगा। "
                        f"आपकी सभी जानकारियाँ पूरी तरह से सुरक्षित कर ली गई हैं। अब मैं आपके लिए पूरी बैंक-स्तरीय व्यवहार्यता और वित्तीय मूल्यांकन रिपोर्ट तैयार कर रही हूँ!"
                    )
            elif payload.language == "mr":
                if align_with_odop:
                    reply = (
                        f"अतिशय हुशारीचा आणि उत्तम निर्णय {payload.user_name} जी! "
                        f"आम्ही तुमचा व्यवसाय {district_name} च्या {odop_prod} शी रणनीतिकदृष्ट्या जोडला आहे. "
                        f"यामुळे तुम्हाला यंत्रसामग्रीवर तब्बल 35 टक्के PMFME सरकारी सबसिडी आणि GeM पोर्टलवर प्राधान्य मिळेल. "
                        f"तुमची संपूर्ण माहिती सुरक्षित झाली असून आता मी तुमचा सर्वसमावेशक प्रकल्प व्यवहार्यता अहवाल तयार करत आहे!"
                    )
                else:
                    reply = (
                        f"खूप छान {payload.user_name} जी! तुमच्या मूळ कल्पनेवरील तुमचा हा आत्मविश्वास मला मनापासून आवडला. "
                        f"आपण तुमच्या याच मूळ व्यवसाय मॉडेलसह पुढे जाऊ जिथे तुम्हाला PMEGP आणि मुद्रा कर्ज योजनांचे सर्व लाभ मिळतील. "
                        f"तुमची संपूर्ण माहिती सुरक्षित झाली असून आता मी तुमचा सर्वसमावेशक प्रकल्प व्यवहार्यता अहवाल तयार करत आहे!"
                    )
            else:
                if align_with_odop:
                    reply = (
                        f"A truly brilliant and forward-thinking decision {payload.user_name} Ji! "
                        f"We have strategically aligned your enterprise with {district_name}'s official ODOP focus product {odop_prod}. "
                        f"This unlocks the 35 percent PMFME capital subsidy up to 10 lakh rupees on machinery and priority GeM onboarding. "
                        f"All your business details are now locked in. I am compiling your bank-grade feasibility and financial appraisal report!"
                    )
                else:
                    reply = (
                        f"Wonderful {payload.user_name} Ji! I admire your conviction and clarity in staying true to your original business vision. "
                        f"We will proudly proceed with your original model, fully backed by standard PMEGP and MUDRA credit schemes. "
                        f"All your business details are now locked in. I am compiling your bank-grade feasibility and financial appraisal report!"
                    )

            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="processing",
                all_fields_collected=True,
                odop_alignment=None,
                odop_comparison=None,
                machinery_analysis={
                    "matched_profile": merged_fields.get("matched_machinery_profile"),
                    "owned_machines": merged_fields.get("owned_machines", []),
                    "owned_machinery_value": merged_fields.get("owned_machinery_value", 0.0),
                    "gross_project_cost": merged_fields.get("gross_project_cost"),
                    "net_project_cost": merged_fields.get("project_cost"),
                    "promoter_margin_pct": merged_fields.get("promoter_margin_pct"),
                    "monthly_emi_saved": merged_fields.get("estimated_monthly_emi_saved", 0.0),
                },
                banking_parameters={
                    "tenure_years": merged_fields.get("tenure_years"),
                    "moratorium_months": merged_fields.get("moratorium_months"),
                    "infrastructure_score": merged_fields.get("infrastructure_score"),
                    "expected_monthly_units": merged_fields.get("expected_monthly_units"),
                    "capacity_unit_label": merged_fields.get("capacity_unit_label"),
                    "tenure_reason": merged_fields.get("tenure_reason"),
                    "moratorium_reason": merged_fields.get("moratorium_reason"),
                },
                message={"role": "assistant", "content": reply},
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
                    break

        # ── Match MSME Machinery Profile & Detect Owned Equipment ───────────
        matched_machinery = None
        if "sector" in merged_fields:
            biz_query = f"{merged_fields.get('enterprise_name', '')} {merged_fields.get('additional_business_details', '')} {last_user_msg}"
            matched_machinery = find_matching_machinery_profile(biz_query, merged_fields["sector"])
            if matched_machinery:
                m_name = matched_machinery.get("business_name")
                new_fields["matched_machinery_profile"] = m_name
                merged_fields["matched_machinery_profile"] = m_name

        # Detect owned machinery from user message
        if last_user_msg:
            detected_machines, detected_val = detect_owned_machinery(last_user_msg, matched_machinery)
            if detected_machines:
                existing_owned = list(merged_fields.get("owned_machines", []))
                existing_names = {m["machine_name"] for m in existing_owned}
                for dm in detected_machines:
                    if dm["machine_name"] not in existing_names:
                        existing_owned.append(dm)
                        existing_names.add(dm["machine_name"])
                total_val = sum(m.get("estimated_cost_inr", 0) for m in existing_owned)
                new_fields["owned_machines"] = existing_owned
                new_fields["owned_machinery_value"] = total_val
                merged_fields["owned_machines"] = existing_owned
                merged_fields["owned_machinery_value"] = total_val

        # ── Tiered MSME Outlay Optimization from Promoter Equity ─────────────
        if "promoter_equity" in merged_fields:
            eq_val = float(merged_fields["promoter_equity"])
            owned_val = float(merged_fields.get("owned_machinery_value", 0.0))
            outlay_calc = calculate_tiered_capital_outlay(
                promoter_equity=eq_val,
                owned_machinery_value=owned_val,
                explicit_project_cost=existing_fields.get("explicit_project_cost"),
            )
            new_fields["gross_project_cost"] = outlay_calc["gross_project_cost"]
            new_fields["project_cost"] = outlay_calc["net_project_cost"]
            new_fields["promoter_margin_pct"] = outlay_calc["promoter_margin_pct"]
            new_fields["estimated_monthly_emi_saved"] = outlay_calc["estimated_monthly_emi_saved_inr"]
            new_fields["estimated_interest_saved"] = outlay_calc["estimated_interest_saved_inr"]
            new_fields["outlay_tier_name"] = outlay_calc["tier_name"]
            merged_fields.update({
                "gross_project_cost": outlay_calc["gross_project_cost"],
                "project_cost": outlay_calc["net_project_cost"],
                "promoter_margin_pct": outlay_calc["promoter_margin_pct"],
                "estimated_monthly_emi_saved": outlay_calc["estimated_monthly_emi_saved_inr"],
                "estimated_interest_saved": outlay_calc["estimated_interest_saved_inr"],
                "outlay_tier_name": outlay_calc["tier_name"],
            })

        # ── Dynamic Statutory Banking Policies ───────────────────────────────
        # Tenure, moratorium, infrastructure score, expected monthly units
        if "sector" in merged_fields and "project_cost" in merged_fields:
            bank_params = compute_statutory_banking_parameters(
                sector=merged_fields["sector"],
                business_category=merged_fields.get("business_category", "manufacturing"),
                project_cost=merged_fields["project_cost"],
                is_rural=bool(merged_fields.get("is_rural", True)),
                matched_profile=matched_machinery,
            )
            for k, v in bank_params.items():
                if k not in existing_fields:
                    new_fields[k] = v
                    merged_fields[k] = v

        # Auto-calculate annual_turnover_estimate intelligently
        if "project_cost" in merged_fields and "annual_turnover_estimate" not in merged_fields:
            try:
                cost = float(merged_fields["project_cost"])
                sector = merged_fields.get("sector", "general")
                cat = merged_fields.get("business_category", "manufacturing")
                expected_units = merged_fields.get("expected_monthly_units")

                turnover_res = calculate_intelligent_turnover(
                    project_cost=cost,
                    sector=sector,
                    business_category=cat,
                    expected_monthly_units=expected_units,
                    matched_profile=matched_machinery,
                )
                merged_fields["annual_turnover_estimate"] = turnover_res["projected_turnover"]
                new_fields["annual_turnover_estimate"] = merged_fields["annual_turnover_estimate"]
                logger.info(
                    "Intelligent Turnover Calculation: ₹%s | Basis: %s",
                    turnover_res["projected_turnover"],
                    turnover_res.get("derivation_basis", "Triangulated"),
                )
            except (ValueError, TypeError) as e:
                logger.warning("Intelligent turnover calculation error: %s", e)

        # Determine missing fields
        missing = [f for f in REQUIRED_FIELDS if f not in merged_fields or not merged_fields[f]]

        # ── Step: Business idea just provided -> Sweet acknowledgment & Ask for Promoter's Equity ──
        if "sector" in merged_fields and "promoter_equity" not in merged_fields and "promoter_equity" not in new_fields:
            sector_label = merged_fields["sector"].replace("_", " ").title()
            if payload.language == "hi":
                reply = (
                    f"अरे वाह {payload.user_name} जी! मैंने नोट कर लिया है। सच में आपका यह व्यवसाय विचार बहुत ही सुंदर और दिलचस्प है! "
                    f"मैंने नीचे आपके व्यवसाय के लिए आवश्यक प्रमुख मानक मशीनों की सूची तैयार कर दी है। "
                    f"यदि इनमें से कोई मशीन या औजार आपके पास पहले से उपलब्ध है, तो नीचे सूची या ड्रॉपडाउन से चुन लें—हम उसका मूल्य सीधे आपके कुल खर्च में से घटा देंगे जिससे आपका बैंक लोन और मासिक किस्त (EMI) बहुत कम हो जाएगी! "
                    f"साथ ही कृपया मुझे बताइए कि इस उद्यम को शुरू करने के लिए आपके पास अपनी खुद की कितनी प्रमोटर इक्विटी यानी आपकी अपनी बचत या पूँजी तैयार है? जैसे ₹50,000, ₹1 लाख या ₹2 लाख?"
                )
            elif payload.language == "mr":
                reply = (
                    f"अरे वा {payload.user_name} जी! मी नोंदवून घेतले आहे. तुमची ही व्यवसाय कल्पना खूपच सुंदर आणि उत्तम आहे! "
                    f"मी खाली तुमच्या व्यवसायासाठी आवश्यक असणाऱ्या मुख्य यंत्रसामग्रीची यादी दिली आहे. "
                    f"यापैकी कोणतीही यंत्रसामग्री तुमच्याकडे आधीपासून असल्यास, खालील यादीतून किंवा ड्रॉपडाउनमधून ती निवडा—आम्ही त्याचे मूल्य थेट तुमच्या खर्चातून वजा करू ज्यामुळे तुमचे बँक कर्ज आणि दरमहा EMI खूप कमी होईल! "
                    f"तसेच कृपया मला सांगा की हा व्यवसाय सुरू करण्यासाठी तुमच्याकडे स्वतःचे किती प्रमोटर इक्विटी भांडवल किंवा स्वतःची बचत तयार आहे? जसे ₹50,000, ₹1 लाख किंवा ₹2 लाख?"
                )
            else:
                reply = (
                    f"Wonderful {payload.user_name} Ji! I have noted that down. What a promising and exciting business idea! "
                    f"I have listed the standard plant & machinery required for your enterprise below. "
                    f"If you already happen to own any of these machines, simply select them from the dropdown or checklist below—we will credit their valuation directly against your capital outlay, lowering your required bank loan and monthly EMI! "
                    f"Also, could you please share how much promoter equity (your own personal savings or capital) you have ready to start? For example, ₹50,000, ₹1 Lakh, or ₹2 Lakhs?"
                )

            applicable_mach_payload = {
                "business_name": matched_machinery.get("business_name") if matched_machinery else None,
                "category": matched_machinery.get("category") if matched_machinery else None,
                "industry_sector": matched_machinery.get("industry_sector") if matched_machinery else None,
                "typical_capacity": matched_machinery.get("typical_capacity") if matched_machinery else None,
                "total_machinery_cost_inr": matched_machinery.get("total_machinery_cost_inr") if matched_machinery else None,
                "machinery_list": matched_machinery.get("machinery_list", []) if matched_machinery else [],
            } if matched_machinery else None

            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="promoter_equity",
                all_fields_collected=False,
                applicable_machinery=applicable_mach_payload,
                machinery_analysis={
                    "matched_profile": merged_fields.get("matched_machinery_profile"),
                    "typical_capacity": matched_machinery.get("typical_capacity") if matched_machinery else None,
                    "benchmark_machinery_cost": matched_machinery.get("total_machinery_cost_inr") if matched_machinery else None,
                },
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
                language=payload.language,
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

            owned_val = float(merged_fields.get("owned_machinery_value", 0.0))
            emi_saved = float(merged_fields.get("estimated_monthly_emi_saved", 0.0))
            mach_list = merged_fields.get("owned_machines", [])
            mach_names = ", ".join(m.get("machine_name", "") for m in mach_list) if mach_list else "आपकी मशीनें"

            if payload.language == "hi":
                owned_speech = (
                    f"साथ ही, मुझे यह जानकर बहुत खुशी हुई कि आपके पास पहले से {mach_names} उपलब्ध है जिसकी अनुमानित कीमत लगभग ₹{int(owned_val):,} है। "
                    f"हमने इसे इन-काइंड एसेट के रूप में आपके आवश्यक बैंक लोन में से घटा दिया है, जिससे आपको बैंक से कम कर्ज लेना पड़ेगा और आपकी हर महीने की EMI में लगभग ₹{int(emi_saved):,} रुपये की भारी बचत होगी! "
                    if owned_val > 0 else ""
                )
                if is_good_synergy:
                    synergy_spoken = (
                        odop_synergy.get("verdict_spoken")
                        or (
                            f"यह तालमेल आपके लिए बहुत ही फायदेमंद रहेगा क्योंकि आप अपने उत्पाद में स्थानीय {p_crop} का उपयोग करके "
                            f"सीधे 35 प्रतिशत PMFME पूंजीगत सब्सिडी और स्थानीय किसान नेटवर्क का पूरा लाभ उठा सकते हैं।"
                        )
                    )
                else:
                    synergy_spoken = (
                        odop_synergy.get("verdict_spoken")
                        or (
                            f"मैं आपसे बिल्कुल सच कहूँगी, आपके इस व्यवसाय के साथ {district_name} के {p_crop} का कोई उचित तालमेल नहीं बैठ रहा है "
                            f"और इसका अलाइनमेंट स्कोर केवल {score_val} आया है। इसलिए किसी जबरदस्ती के बिना, मेरी दिल से सलाह है कि आप अपने "
                            f"मूल विचार के साथ ही आगे बढ़ें जहाँ आपको PMEGP और मुद्रा लोन का पूरा लाभ मिलेगा।"
                        )
                    )

                reply = (
                    f"अरे वाह {payload.user_name} जी! मैंने आपके व्यवसाय को बहुत ही गहराई और प्यार से समझ लिया है। "
                    f"आप {district_name} में {biz_desc} शुरू करना चाहते हैं और आपका यह अंदाज़ मुझे बहुत पसंद आया! "
                    f"{owned_speech}"
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
                owned_speech_mr = (
                    f"तसेच, तुमच्याकडे आधीपासून {mach_names} उपलब्ध आहे ज्याचे मूल्य सुमारे ₹{int(owned_val):,} आहे हे पाहून मला खूप आनंद झाला! "
                    f"आम्ही हे इन-काइंड ॲसेट म्हणून वजा केले आहे, ज्यामुळे तुमचे बँक कर्ज कमी होईल आणि दरमहा EMI मध्ये सुमारे ₹{int(emi_saved):,} ची बचत होईल! "
                    if owned_val > 0 else ""
                )
                if is_good_synergy:
                    synergy_spoken_mr = (
                        odop_synergy.get("verdict_spoken")
                        or (
                            f"हा मेळ तुमच्यासाठी अत्यंत फायदेशीर ठरेल! कारण तुम्ही स्थानिक {p_crop} चा वापर करून थेट 35 टक्के सरकारी सबसिडी "
                            f"आणि स्थानिक शेतकरी क्लस्टरचा पूर्ण लाभ घेऊ शकता."
                        )
                    )
                else:
                    synergy_spoken_mr = (
                        odop_synergy.get("verdict_spoken")
                        or (
                            f"मी तुमच्याशी अगदी खरे बोलेन, तुमच्या या व्यवसायाचा {district_name} च्या {p_crop} सोबत कोणताही थेट मेळ बसत नाही "
                            f"आणि याचा स्कोअर फक्त {score_val} आला आहे. म्हणूनच जबरदस्ती न करता, तुम्ही तुमच्या मूळ कल्पनेसह पुढे जावे हा माझा सल्ला आहे."
                        )
                    )

                reply = (
                    f"अरे वा {payload.user_name} जी! मी तुमचा व्यवसाय अतिशय प्रेमाने आणि काळजीपूर्वक समजून घेतला आहे. "
                    f"तुम्ही {district_name} मध्ये {biz_desc} सुरू करू इच्छिता आणि तुमची ही कल्पना मला मनापासून आवडली! "
                    f"{owned_speech_mr}"
                    f"तुम्हाला माहिती आहे का? शासनाच्या एक जिल्हा एक उत्पादन म्हणजेच ODOP योजनेअंतर्गत स्थानिक उत्पादनाशी जोडल्यास यंत्रसामग्रीवर तब्बल 35 टक्के सबसिडी मिळते! "
                    f"मला समजले त्यानुसार तुमच्या {district_name} जिल्ह्याचे मुख्य उत्पादन {p_crop} आहे आणि तुमची कल्पना {biz_desc} ची आहे. "
                    f"मी या दोघांचा अतिशय सुंदर मेळ घातला असून त्याचा स्कोअर 100 पैकी {score_val} आला आहे! "
                    f"{synergy_spoken_mr} "
                    f"आता मला सांगा, तुम्हाला कोणता पर्याय निवडायला आवडेल:\n"
                    f"1. ODOP शी जोडा\n"
                    f"2. माझी मूळ कल्पना ठेवा"
                )
            else:
                owned_speech_en = (
                    f"Additionally, I am thrilled that you already own {mach_names} valued at approximately ₹{int(owned_val):,}! "
                    f"We have credited this as an in-kind promoter asset contribution, deducting it from your fresh bank loan requirement and saving you approximately ₹{int(emi_saved):,} per month in EMI! "
                    if owned_val > 0 else ""
                )
                if is_good_synergy:
                    synergy_spoken_en = (
                        odop_synergy.get("verdict_spoken")
                        or (
                            f"This alignment is wonderfully beneficial for you! By integrating {district_name}'s local {p_crop} into your venture, "
                            f"you qualify for the 35 percent PMFME capital grant up to 10 lakh rupees and direct farmer sourcing."
                        )
                    )
                else:
                    synergy_spoken_en = (
                        odop_synergy.get("verdict_spoken")
                        or (
                            f"I will be completely honest with you my dear friend. Forced alignment with {district_name}'s {p_crop} does not make practical sense "
                            f"for your venture, and its alignment score is only {score_val} out of 100. My sincere recommendation is to proudly proceed with your "
                            f"original business model under standard PMEGP and Mudra loan schemes."
                        )
                    )

                reply = (
                    f"Oh wonderful {payload.user_name} Ji! I have understood your business venture deeply and lovingly. "
                    f"You wish to establish {biz_desc} in {district_name}, and I truly admire your dedication! "
                    f"{owned_speech_en}"
                    f"Did you know? Under the government's One District One Product ODOP initiative, enterprises aligned with their district's designated product get a massive 35 percent capital subsidy on machinery! "
                    f"From what I have understood, your district {district_name} has {p_crop} as its official ODOP, while your business idea is {biz_desc}. "
                    f"I tried aligning both for you, and here is your strategic match with an alignment score of {score_val} out of 100! "
                    f"{synergy_spoken_en} "
                    f"I have presented your complete alignment match in the card below. Now please tell me what you would love to choose:\n"
                    f"1. Align with ODOP\n"
                    f"2. Keep my idea"
                )

            new_fields["odop_alignment_presented"] = True
            new_fields["odop_product"] = p_crop
            new_fields["odop_score"] = score_val
            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="odop_alignment",
                all_fields_collected=False,
                odop_alignment=odop_synergy,
                odop_comparison=odop_synergy,
                applicable_machinery={
                    "business_name": matched_machinery.get("business_name") if matched_machinery else None,
                    "category": matched_machinery.get("category") if matched_machinery else None,
                    "industry_sector": matched_machinery.get("industry_sector") if matched_machinery else None,
                    "typical_capacity": matched_machinery.get("typical_capacity") if matched_machinery else None,
                    "total_machinery_cost_inr": matched_machinery.get("total_machinery_cost_inr") if matched_machinery else None,
                    "machinery_list": matched_machinery.get("machinery_list", []) if matched_machinery else [],
                } if matched_machinery else None,
                machinery_analysis={
                    "matched_profile": merged_fields.get("matched_machinery_profile"),
                    "owned_machines": merged_fields.get("owned_machines", []),
                    "owned_machinery_value": merged_fields.get("owned_machinery_value", 0.0),
                    "gross_project_cost": merged_fields.get("gross_project_cost"),
                    "net_project_cost": merged_fields.get("project_cost"),
                    "promoter_margin_pct": merged_fields.get("promoter_margin_pct"),
                    "monthly_emi_saved": merged_fields.get("estimated_monthly_emi_saved", 0.0),
                },
                banking_parameters={
                    "tenure_years": merged_fields.get("tenure_years"),
                    "moratorium_months": merged_fields.get("moratorium_months"),
                    "infrastructure_score": merged_fields.get("infrastructure_score"),
                    "expected_monthly_units": merged_fields.get("expected_monthly_units"),
                    "capacity_unit_label": merged_fields.get("capacity_unit_label"),
                    "tenure_reason": merged_fields.get("tenure_reason"),
                    "moratorium_reason": merged_fields.get("moratorium_reason"),
                },
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
            applicable_machinery={
                "business_name": matched_machinery.get("business_name") if matched_machinery else None,
                "category": matched_machinery.get("category") if matched_machinery else None,
                "industry_sector": matched_machinery.get("industry_sector") if matched_machinery else None,
                "typical_capacity": matched_machinery.get("typical_capacity") if matched_machinery else None,
                "total_machinery_cost_inr": matched_machinery.get("total_machinery_cost_inr") if matched_machinery else None,
                "machinery_list": matched_machinery.get("machinery_list", []) if matched_machinery else [],
            } if matched_machinery else None,
            machinery_analysis={
                "matched_profile": merged_fields.get("matched_machinery_profile"),
                "owned_machines": merged_fields.get("owned_machines", []),
                "owned_machinery_value": merged_fields.get("owned_machinery_value", 0.0),
                "gross_project_cost": merged_fields.get("gross_project_cost"),
                "net_project_cost": merged_fields.get("project_cost"),
                "promoter_margin_pct": merged_fields.get("promoter_margin_pct"),
                "monthly_emi_saved": merged_fields.get("estimated_monthly_emi_saved", 0.0),
            },
            banking_parameters={
                "tenure_years": merged_fields.get("tenure_years"),
                "moratorium_months": merged_fields.get("moratorium_months"),
                "infrastructure_score": merged_fields.get("infrastructure_score"),
                "expected_monthly_units": merged_fields.get("expected_monthly_units"),
                "capacity_unit_label": merged_fields.get("capacity_unit_label"),
                "tenure_reason": merged_fields.get("tenure_reason"),
                "moratorium_reason": merged_fields.get("moratorium_reason"),
            },
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
