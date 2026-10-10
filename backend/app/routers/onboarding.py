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
    from app.core.business_interpreter import interpret_business_idea
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
    from backend.app.core.business_interpreter import interpret_business_idea
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
    input_source: str = Field("text", description="text, voice, or confirmed business idea")
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
    odop_intro: Optional[Dict[str, Any]] = None
    message: Optional[Dict[str, str]] = None


def _machinery_profile_for_fields(fields: dict) -> Optional[dict]:
    """Reuse the business idea's vetted plan through all later onboarding steps."""
    plan = fields.get("machinery_plan")
    if isinstance(plan, dict):
        profile_name = plan.get("business_name")
        if not profile_name:
            return None  # Retail or an idea absent from the plant catalogue.
        base = next((item for item in load_machinery_dataset() if item["business_name"] == profile_name), None)
        if base:
            allowed = {machine["machine_name"] for machine in plan.get("machinery_list", [])}
            return {**base, "machinery_list": [machine for machine in base["machinery_list"] if machine["machine_name"] in allowed]}
    return find_matching_machinery_profile(
        fields.get("business_idea") or fields.get("additional_business_details") or fields.get("enterprise_name", ""),
        fields.get("sector"),
    )


# ── Field Extraction System Prompt ───────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are Mira, an intelligent MSME underwriting and onboarding AI for Indian entrepreneurs.
Your task is to accurately extract structured business information from the user's natural language message across Hindi, English, Marathi, and Hinglish.

CRITICAL INSTRUCTION: Respond ONLY with a valid JSON object. No explanation, no markdown text outside JSON.

FIELDS TO EXTRACT IF PRESENT:
1. "enterprise_name": string or null
   - Extract ONLY if the user explicitly mentions a business or shop name (e.g., "Sharma Dairy", "Shree Ganesh Bakery", "M/s Aryan Fabricators", "Royal Tailors").
   - If the user only describes their activity (e.g., "bakery shuru karni hai", "lathe machine lagani hai", "kapde ki dukan"), do NOT make up an enterprise name; set to null.

2. "business_category": "manufacturing" or "service"
   - "manufacturing": Any physical production, processing, baking, stitching, milling, packaging, fabrication, crafting, or assembling (e.g., bakery, dairy products, garment making, flour mill, spice grinding, welding/lathe, pottery, papad, handicrafts).
   - "service": Repair shops, garages, salons/beauty parlour, mobile/bike repair, photocopy/xerox, retail/kirana store, maintenance.

3. "sector": exactly ONE of:
   - "dairy": Milk processing, curd, paneer, ghee, ice cream, kulfi, dairy farming, cattle feed, dairy booths.
   - "food_processing": Atta chakki, flour mill, oil expeller, spice/masala grinding, bakery, biscuits, cake, namkeen, papad, pickle/achar, sauce/ketchup, fruit pulp/juice, honey, fish/prawn/marine processing, food dehydration, pulses/dal mill.
   - "apparel": Tailoring, stitching, garment manufacturing, boutique, textile printing, embroidery, readymade garments, uniforms, fashion design, cloth manufacturing.
   - "repair": Mobile/smartphone repair, two-wheeler/bike garage, automobile mechanic, laptop/computer repair, electrical/electronic appliance repair, motor winding.
   - "fabrication": Welding workshop, iron gates/grills, aluminum fabrication, steel furniture, lathe machine, sheet metal, hardware fabrication.
   - "artisan_trades": Terracotta, clay pottery, Dokra/brass craft, handloom weaving, carpet, bamboo craft, wood carving, leather footwear/chappal, handicrafts.
   - "general": Kirana/grocery shop, hardware store, stationary/cyber cafe, beauty salon, event services, general trading or retail.

4. "promoter_category": exactly ONE of:
   - "general": General category, open, samanya, Brahmin, Rajput, Maratha, Jain, Baniya, etc.
   - "obc": Other Backward Class, pichhda varg, Yadav, Kurmi, Patel, Gupta, Maurya, Mali, etc.
   - "sc": Scheduled Caste, anushuchit jati, Dalit, Mahar, Chamar, Valmiki, etc.
   - "st": Scheduled Tribe, anushuchit janjati, Adivasi, Gond, Bhil, Santhal, Meena, etc.
   - "women": Woman entrepreneur, mahila, female founder.
   - "women_shg": Self Help Group, SHG, bachat gat, mahila samooh.

5. "promoter_equity": number in INR (e.g. 250000)
   - The user's OWN savings, self-investment, or cash equity contribution ("mere paas 2.5 lakh hai", "apna 50 hazar lagaunga", "khud ka 1 lakh", "savings 2 lakh", "250k khud ka").
   - Understand all Indian numerical patterns:
     * Lakhs: "2.5 lakh" / "2.5L" / "2.5 lac" -> 250000, "1 lakh" -> 100000, "10 lakh" -> 1000000
     * Fractions: "डेढ़ लाख" / "dedh lakh" / "दीड लाख" -> 150000, "ढाई लाख" / "dhai lakh" / "अडीच लाख" -> 250000, "सवा लाख" / "sawa lakh" -> 125000, "पौने दो लाख" -> 175000, "साढ़े तीन लाख" -> 350000
     * Thousands: "50k" / "50 thousand" / "50 हजार" / "50000" -> 50000, "25k" -> 25000, "75 hazar" -> 75000
     * Bare numbers on equity inquiry: "2.5" means 250000, "2" means 200000, "5" means 500000, "50" means 50000.

6. "project_cost": number in INR (e.g. 500000)
   - ONLY extract if the user explicitly states the TOTAL project outlay or plant setup cost ("kul kharch 10 lakh hoga", "total project cost 8 lakh", "poora setup 5 lakh me hoga").
   - Do NOT confuse project_cost with promoter_equity (savings).

7. "additional_business_details": string or null
   - Extra details mentioned such as specific machines ("have 2 sewing machines", "lathe machine", "mixer"), capacity, target market, or products.

8. "owned_machinery_mentioned": boolean (true if user mentions already having some machine or equipment).

NEVER extract annual_turnover_estimate or sales figures.
Return ONLY valid JSON like: {"sector": "food_processing", "business_category": "manufacturing", "promoter_equity": 250000}
"""

CONVERSATION_SYSTEM_PROMPT_TEMPLATE = """You are Mira, a warm, energetic, and encouraging personal business advisor for Indian entrepreneurs.
You speak {language_name} naturally, affectionately, and respectfully (always using जी / Ji).

PERSONA & INTERACTION GUIDELINES:
1. TALK LIKE A REAL CARING HUMAN: Talk like an experienced, supportive elder sister or mentor (दीदी / मार्गदर्शक) sitting with the entrepreneur having tea. Never sound like a robot, generic AI, or clerk.
2. GROUNDED ENCOURAGEMENT: Acknowledge the specific product or service the user actually described. Never claim demand, profitability, subsidy eligibility, or that an unclear idea is excellent without evidence. If speech may have been mistranscribed or the activity is unclear, ask one precise confirmation question before proceeding.
3. NO REPETITION: Never repeat the same greeting or phrase every turn. Adapt directly to what the user just said.
4. DO NOT ASK FOR CONFIRMED LOCATION: Location is already confirmed as {location_info}. Never ask state or district!
5. DO NOT ASK FOR ANNUAL SALES / TURNOVER: Never ask for annual turnover or sales projections. That is calculated by the backend feasibility engine.
6. HANDLE USER QUESTIONS EMPATHETICALLY:
    - If the user asks about subsidy, bank loan, or ODOP, answer with conditions and uncertainty; never promise a grant or loan before eligibility and bank review.
    - If the user expresses anxiety ("mere paas paise kam hai"), explain the relevant financing options without guaranteeing approval.
7. ONE CLEAR QUESTION AT A TIME: After warm acknowledgement, ask for the single next missing piece of information.
8. CONCISE & LIVELY: Keep your response within 2-3 sweet, clear sentences.

CURRENT ENTREPRENEUR STATUS:
- Name: {user_name}
- Location: {location_info}
- District Verified ODOP Product: {district_odop_product}
- Applicable Government Scheme: {district_scheme_name}
- Information Gathered So Far:
{collected_info}

STILL NEEDED:
{missing_fields}
"""

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "mr": "Marathi",
    "te": "Telugu", "ta": "Tamil", "kn": "Kannada",
}


def _business_idea_clarification(idea: str, language: str, interpretation: dict, from_voice: bool) -> str:
    """Ask about the user's actual idea before a guessed transcript becomes business data."""
    language_name = LANGUAGE_NAMES.get(language, "English")
    sector = interpretation.get("sector")
    category = interpretation.get("business_category")
    unclear_activity = sector == "general"
    tailoring_terms = ("tailor", "alteration", "सिलाई", "दर्जी", "शिवण")
    explicit_garment_production = ("garment", "uniform", "factory", "manufactur", "production", "उत्पादन")
    tailoring_service = sector == "apparel" and any(term in idea.lower() for term in tailoring_terms) and not any(term in idea.lower() for term in explicit_garment_production)
    goods_activity = sector in {"dairy", "food_processing", "apparel", "fabrication", "artisan_trades"} and not tailoring_service
    try:
        content, _, _ = chat_service._call_llm_chat_completion(
            messages=[
                {"role": "system", "content": (
                    f"You are Mira. Reply only in {language_name}. The user described a business idea, "
                    "but its transcription or meaning needs confirmation. Paraphrase only what was actually "
                    "heard; do not invent a product, praise an unverified idea, assert market demand, "
                    "or proceed to ODOP. Ask ONE short question based on the actual ambiguity. "
                    "If speech recognition may be wrong, quote what was heard and invite correction. "
                    "If the activity is unclear, ask what product or service they mean. "
                    "Only ask make-versus-sell if this is a physical product and that distinction is missing; "
                    "do not ask a tailoring or repair service whether they will manufacture the service. "
                    "Do not follow a fixed script or ask multiple unrelated questions."
                )},
                {"role": "user", "content": json.dumps({
                    "heard": idea,
                    "source": "speech recognition" if from_voice else "typed answer",
                    "tentative_sector": sector,
                    "tentative_activity": category,
                    "unclear_activity": unclear_activity,
                    "physical_goods": goods_activity,
                }, ensure_ascii=False)},
            ],
            temperature=0.2,
            max_tokens=130,
            timeout_s=8.0,
        )
        if content and content.strip() and not re.search(r"\b(great idea|wonderful idea|excellent idea|strong market demand)\b|बहुत अच्छा विचार|खूप छान कल्पना", content, re.I):
            return content.strip()[:600]
    except Exception:
        pass
    if unclear_activity:
        if language == "hi":
            return f"मैंने ‘{idea}’ सुना। क्या आप अपना उत्पाद या सेवा थोड़ा स्पष्ट करेंगे? अगर मैंने गलत सुना है तो सही शब्द बता दें।"
        if language == "mr":
            return f"मला ‘{idea}’ असे ऐकू आले. तुम्ही कोणते उत्पादन किंवा सेवा देणार आहात ते स्पष्ट कराल का? चुकले असल्यास दुरुस्त करा."
        return f"I heard ‘{idea}’. What product or service did you mean? Please correct the wording if I misheard you."
    if not goods_activity or category == "service":
        if language == "hi":
            return f"मैंने ‘{idea}’ सुना। क्या मैंने आपका व्यवसाय सही समझा? गलत हो तो कृपया सुधार दें।"
        if language == "mr":
            return f"मला ‘{idea}’ असे ऐकू आले. मी तुमचा व्यवसाय बरोबर समजले का? चुकले असल्यास दुरुस्त करा."
        return f"I heard ‘{idea}’. Is that the business you mean? Please correct me if I misheard it."
    if language == "hi":
        return f"मैंने ‘{idea}’ सुना। क्या यही आपका विचार है, और आप इसे बनाएँगे या तैयार माल बेचेंगे? गलत सुना हो तो सुधार दें।"
    if language == "mr":
        return f"मी तुमची कल्पना ‘{idea}’ अशी ऐकली. हे बरोबर आहे का? तुम्ही ते तयार करणार की तयार माल विकणार? चूक असल्यास कृपया दुरुस्त करा."
    return f"I heard ‘{idea}’. Is that the business you mean, and will you make the product or sell finished goods? Please correct me if I heard it wrong."


# ── Core Processing Logic ────────────────────────────────────────────────────

def _normalize_devanagari_numerals(text: str) -> str:
    """Converts Devanagari numerals (०-९) to standard ASCII digits (0-9)."""
    dev_digits = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
    for d, a in dev_digits.items():
        text = text.replace(d, a)
    return text


def _extract_promoter_equity(text: str, is_equity_step: bool = False) -> Optional[float]:
    """
    Robustly extracts promoter's equity/savings capital from arbitrary user input in
    English, Hindi, Marathi, and Hinglish across all colloquial phrases, abbreviations,
    currency notations, Devanagari digits, and bare numbers.
    """
    if not text:
        return None
    t = _normalize_devanagari_numerals(text.lower().strip())

    # 1. Colloquial Hindi / Marathi / Hinglish fractional terms and number words
    phrase_map = {
        # 1.5 Lakh = 150000
        "डेढ़ लाख": 150000.0, "दीड लाख": 150000.0, "dedh lakh": 150000.0, "dhed lakh": 150000.0, "dedh lac": 150000.0,
        "1 and half lakh": 150000.0, "one and half lakh": 150000.0, "one and a half lakh": 150000.0,
        # 2.5 Lakh = 250000
        "ढाई लाख": 250000.0, "अडीच लाख": 250000.0, "dhai lakh": 250000.0, "dhai lac": 250000.0, "dhay lakh": 250000.0,
        "two and half lakh": 250000.0, "two and a half lakh": 250000.0,
        # 1.25 Lakh = 125000
        "सवा लाख": 125000.0, "sawa lakh": 125000.0, "sawa lac": 125000.0,
        # 2.25 Lakh = 225000
        "सवा दो लाख": 225000.0, "sawa do lakh": 225000.0,
        # 1.75 Lakh = 175000
        "पौने दो लाख": 175000.0, "paune do lakh": 175000.0,
        # 2.75 Lakh = 275000
        "पौने तीन लाख": 275000.0, "paune teen lakh": 275000.0,
        # 3.5 Lakh = 350000
        "साढ़े तीन लाख": 350000.0, "sadhe teen lakh": 350000.0,
        # 4.5 Lakh = 450000
        "साढ़े चार लाख": 450000.0, "sadhe char lakh": 450000.0,
        # 50,000
        "आधा लाख": 50000.0, "adha lakh": 50000.0, "aadha lakh": 50000.0, "half lakh": 50000.0,
        # Number words (Lakhs)
        "एक लाख": 100000.0, "दोन लाख": 200000.0, "दो लाख": 200000.0, "तीन लाख": 300000.0,
        "चार लाख": 400000.0, "पांच लाख": 500000.0, "पाच लाख": 500000.0, "छह लाख": 600000.0,
        "सात लाख": 700000.0, "आठ लाख": 800000.0, "नौ लाख": 900000.0, "दस लाख": 1000000.0,
        "one lakh": 100000.0, "two lakh": 200000.0, "two lakhs": 200000.0, "three lakh": 300000.0,
        "three lakhs": 300000.0, "four lakh": 400000.0, "four lakhs": 400000.0, "five lakh": 500000.0,
        "five lakhs": 500000.0, "ten lakh": 1000000.0, "ten lakhs": 1000000.0,
        "ek lakh": 100000.0, "do lakh": 200000.0, "teen lakh": 300000.0, "char lakh": 400000.0, "panch lakh": 500000.0,
        # Thousands
        "दस हजार": 10000.0, "बीस हजार": 20000.0, "तीस हजार": 30000.0, "चालीस हजार": 40000.0,
        "पचास हजार": 50000.0, "साठ हजार": 60000.0, "सत्तर हजार": 70000.0, "अस्सी हजार": 80000.0,
        "नब्बे हजार": 90000.0,
        "पन्नास हजार": 50000.0, "वीस हजार": 20000.0, "तीस हजार": 30000.0, "चाळीस हजार": 40000.0,
        "ऐंशी हजार": 80000.0, "नव्वद हजार": 90000.0,
        "ten thousand": 10000.0, "twenty thousand": 20000.0, "thirty thousand": 30000.0,
        "forty thousand": 40000.0, "fifty thousand": 50000.0, "sixty thousand": 60000.0,
        "seventy thousand": 70000.0, "eighty thousand": 80000.0, "ninety thousand": 90000.0,
        "pachas hazar": 50000.0, "bees hazar": 20000.0, "assi hazar": 80000.0,
    }
    for phrase, val in phrase_map.items():
        if phrase in t:
            return val

    # 2. Crores
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:cr\b|crore|crores|करोड़)', t)
    if m:
        return float(m.group(1)) * 10000000.0

    # 3. Lakhs / Lacs / L (e.g. 1.5L, 2L, 2.5 L, 10 Lakh, 1.5 lac, 0.5L)
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?|लाख|l\b)', t)
    if m:
        return float(m.group(1)) * 100000.0

    # 4. Thousands / K (e.g. 50k, 100 k, 75 thousand, 50 hazar, 50 हजार)
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:k\b|thousands?|hazar\b|hazār\b|hajar\b|हज़ार|हजार|हज़ार)', t)
    if m:
        return float(m.group(1)) * 1000.0

    # 5. Standard numbers with commas/currency (e.g. ₹1,50,000, 50,000/-, rs 50000, 100000)
    clean_num = re.sub(r'[₹$]|(?:rs\.?|inr|रुपये|रुपए|rupees)\s*', '', t)
    m = re.search(r'\b(\d{1,3}(?:,\d{2,3})+|\d{4,})\b', clean_num)
    if m:
        val = float(m.group(1).replace(',', ''))
        if val >= 1000:
            return val

    # 6. Bare numbers or standalone decimals e.g. '1.5', '2', '2.5', '5', '1'
    bare_match = re.search(r'^\s*(?:about|around|approx|mere\s*paas|i\s*have|only|budget|saving[s]?)?\s*(\d+(?:\.\d+)?)\s*(?:rs|rupees|रुपये)?\s*$', t)
    if bare_match:
        n = float(bare_match.group(1))
        # If user entered 1, 2, 1.5, 2.5 (< 50) on promoter equity step, interpret as Lakhs
        if n < 50 and (is_equity_step or n <= 25):
            return n * 100000.0
        elif n >= 1000:
            return n

    # 7. Embedded standalone number in message
    all_nums = re.findall(r'\b\d+\b', t.replace(',', ''))
    for num_str in all_nums:
        n = float(num_str)
        if n >= 1000:
            return n

    return None


def _llm_extract_equity_amount(text: str) -> Optional[float]:
    """Uses LLM to parse complex conversational Hindi/English sentences for equity amount."""
    if not text or len(text.strip()) < 2:
        return None
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "Extract the numerical monetary amount in Indian Rupees (INR) from the user statement "
                    "about their business investment capital, promoter equity, or savings. "
                    "Respond with ONLY the plain integer number in INR (e.g. 50000, 100000, 250000) or 'null' if none."
                ),
            },
            {"role": "user", "content": text},
        ]
        content, _, _ = chat_service._call_llm_chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=30,
            timeout_s=6.0,
        )
        if content:
            nums = re.findall(r'\d+', content.replace(',', ''))
            if nums:
                val = float(nums[0])
                if val >= 1000:
                    return val
    except Exception as e:
        logger.warning("LLM equity extraction fallback notice: %s", e)
    return None


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

    curr_eq = existing_fields.get("promoter_equity")
    if (curr_eq is None or float(curr_eq or 0) < 5000) and "project_cost" not in existing_fields:
        eq_val = _extract_promoter_equity(text)
        if eq_val and eq_val >= 5000:
            extracted["promoter_equity"] = eq_val

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
                # Purge invalid, zero, or negative promoter_equity from LLM
                if "promoter_equity" in data:
                    try:
                        eq_num = float(data["promoter_equity"])
                        if eq_num < 5000:
                            data.pop("promoter_equity", None)
                    except (ValueError, TypeError):
                        data.pop("promoter_equity", None)
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

    odop_info = find_district_odop(state_name, district_name) or {}
    district_odop_product = odop_info.get("official_odop_product") or "District MSME Specialty"
    district_scheme_name = odop_info.get("scheme_name") or "PMEGP / ODOP Scheme"

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
        district_odop_product=district_odop_product,
        district_scheme_name=district_scheme_name,
        collected_info=collected_info,
        missing_fields=missing_info,
    )

    llm_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages[-6:]:
        llm_messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        content, _, _ = chat_service._call_llm_chat_completion(
            messages=llm_messages,
            temperature=0.85,
            max_tokens=380,
            timeout_s=12.0,
        )
        if content and content.strip():
            return content.strip()
    except Exception as e:
        logger.error("Mira response generation failed: %s", e)

    # A failed LLM call must not pretend to understand an unclear answer.
    if language == "hi":
        return f"{user_name} जी, मैं आपकी बात सही समझना चाहती हूँ। कृपया अपने उत्पाद या सेवा के बारे में थोड़ा और बताइए।"
    if language == "mr":
        return f"{user_name} जी, मला तुमची कल्पना नीट समजून घ्यायची आहे. कृपया तुमच्या उत्पादन किंवा सेवेबद्दल थोडे अधिक सांगा."
    return f"{user_name} Ji, I want to be sure I understand. Could you tell me a little more about the product or service you have in mind?"


# ── ODOP 100-Point Fixed Benchmarking System Prompt ───────────────────────────
ODOP_BENCHMARK_SYSTEM_PROMPT = """You are an expert MSME Cluster & ODOP Underwriting Evaluator for the Government of India's One District One Product (ODOP) initiative.

CRITICAL MANDATE:
You are provided with the EXACT official ODOP product, category, and government scheme directly from the Government ODOP Registry.
DO NOT hallucinate, guess, or substitute a different ODOP product or scheme. Rely STRICTLY on the statutory parameters provided in the user prompt.

### 100-POINT STATUTORY BENCHMARKING CRITERIA:

1. Pillar 1: Sector Overlap & Value-Addition Synergy (0 to 50 points)
   - 40 to 50 pts: Direct processing, manufacturing, or primary value-addition with the district ODOP produce (e.g. Tomato -> Ketchup/Purée, Milk -> Ice Cream/Paneer/Ghee, Cotton/Silk -> Garments, Turmeric -> Extraction/Powder, Brass/Metal -> Artware, Fish -> Processing/Cold Chain).
   - 25 to 39 pts: Allied processing, packaging, cold chain, tooling, or complementary machinery servicing the local district cluster.
   - 0 to 24 pts: Unrelated services, retail, or disconnected trades with no supply chain overlap (e.g. mobile repair, beauty salon, hardware store).

2. Pillar 2: Local Sourcing & Catchment Feasibility (0 to 25 points)
   - 18 to 25 pts: The district possesses established raw material catchment, artisan clusters, mandis, or Common Facility Centers (CFC) for this ODOP commodity. Raw materials can be procured locally at lower freight cost.
   - 10 to 17 pts: Partial local catchment; secondary processing or inter-district transit sourcing needed.
   - 0 to 9 pts: Infeasible local sourcing; the venture does not utilize local district raw materials.

3. Pillar 3: Statutory Government Scheme Qualification (0 to 25 points)
   - 20 to 25 pts: Fully qualifies under the applicable government scheme (e.g., PMFME 35% subsidy for food processing, PMMSY 40%-60% for fisheries, or PMEGP 25%-35% for artisan/manufacturing clusters), Common Facility Center (CFC) access, and priority GeM onboarding.
   - 12 to 19 pts: Partial cluster incentive; eligible under allied MSME schemes.
   - 0 to 11 pts: Standard credit schemes only (general MUDRA / MSME loan).

### SCORING & RECOMMENDATION RULES:
- alignment_score = pillar_1_score + pillar_2_score + pillar_3_score (clamped between 15 and 98).
- If alignment_score >= 65:
  * verdict_key: "recommended"
  * verdict_title: "उत्कृष्ट तालमेल (Highly Recommended)"
  * mira_recommendation: "Mira Recommends: Excellent ODOP Synergy for Government Subsidy"
- If alignment_score is 50 to 64:
  * verdict_key: "viable"
  * verdict_title: "सकारात्मक तालमेल (Viable Synergy)"
  * mira_recommendation: "Mira Recommends: Viable Strategic Opportunity"
- If alignment_score < 50:
  * verdict_key: "not_recommended"
  * verdict_title: "कम तालमेल (Standard MSME Recommended)"
  * mira_recommendation: "Mira Recommends: Continue with Standard Business Model"

### OUTPUT FORMAT:
You MUST respond with valid JSON ONLY. No markdown wrappers, no conversational commentary.
{
  "pillar_1_score": <int 0-50>,
  "pillar_2_score": <int 0-25>,
  "pillar_3_score": <int 0-25>,
  "alignment_score": <int 15-98>,
  "verdict_key": "recommended" | "viable" | "not_recommended",
  "verdict_title": "<Localized title in English or Hindi>",
  "mira_recommendation": "<Concise recommendation statement citing the applicable scheme>",
  "verdict_spoken": "<One or two clean spoken sentences in the requested language giving Mira's verdict>",
  "product_innovation_title": "<Title for Pillar 1>",
  "product_innovation_desc": "<Detailed strategic idea description for Pillar 1>",
  "local_sourcing_title": "<Title for Pillar 2>",
  "local_sourcing_desc": "<Detailed description for Pillar 2>",
  "financial_incentives_title": "<Title for Pillar 3 citing the exact scheme>",
  "financial_incentives_desc": "<Detailed description for Pillar 3 citing the exact scheme>"
}
"""


def _compute_deterministic_benchmark(
    sector: str,
    user_business: str,
    state: str,
    district: str,
    odop_product: str,
    category: str,
    scheme_name: str,
    subsidy_summary: str,
    subsidy_pct: int,
    key_benefits: list[str],
    target_sectors: list[str],
    raw_material_available: bool,
    cfc_available: bool,
    pmfme_eligible: bool,
    language: str = "hi",
) -> dict[str, Any]:
    sector_norm = (sector or "general").lower().strip()
    idea_norm = (user_business or "").lower().strip()
    odop_lower = (odop_product or "").lower()
    cat_lower = (category or "").lower()
    sector_clean = sector.replace("_", " ").title()

    # Pillar 1: Sector Overlap & Value-Addition (0 to 50 pts)
    p1 = 0
    if sector_norm in target_sectors:
        p1 = 49
    elif any(kw in idea_norm for kw in ["ice cream", "kulfi", "sweet", "dessert", "bakery", "snack", "juice", "jam", "chocolat", "sauce", "ketchup", "puree", "pasta", "flour", "oil"]) and any(kw in (odop_lower + " " + cat_lower) for kw in ["millet", "fruit", "dairy", "milk", "grain", "mango", "orange", "banana", "tomato", "chilli", "spice", "pulses", "rice"]):
        p1 = 48
    elif sector_norm in ("dairy", "food_processing") and any(s in target_sectors for s in ("dairy", "food_processing", "agriculture")):
        p1 = 44
    elif sector_norm in ("repair", "fabrication") and any(kw in (odop_lower + " " + cat_lower) for kw in ["machinery", "engineering", "steel", "tools", "hardware", "metal", "brass"]):
        p1 = 42
    elif sector_norm in ("apparel", "artisan_trades") and any(kw in (odop_lower + " " + cat_lower) for kw in ["textile", "garment", "silk", "cotton", "handloom", "carpet", "pottery", "craft", "wood"]):
        p1 = 47
    elif sector_norm in ("service", "repair", "general"):
        p1 = 18
    else:
        p1 = 14

    # Pillar 2: Local Sourcing & Catchment Feasibility (0 to 25 pts)
    p2 = 0
    if raw_material_available and cfc_available:
        p2 = 24
    elif raw_material_available:
        p2 = 20
    elif cfc_available:
        p2 = 16
    else:
        p2 = 11
    if sector_norm in ("repair", "service", "general") and p1 < 25:
        p2 = min(p2, 8)

    # Pillar 3: Statutory Government Scheme Qualification (0 to 25 pts)
    p3 = 0
    if p1 >= 30:
        p3 = 24
    elif p1 >= 20:
        p3 = 18
    else:
        p3 = 9
    if sector_norm in ("repair", "service", "general") and p1 < 25:
        p3 = 7

    score = max(15, min(98, p1 + p2 + p3))

    if score >= 65:
        verdict_key = "recommended"
        verdict_title = "उत्कृष्ट तालमेल (Highly Recommended)"
        mira_rec = f"Mira Recommends: Excellent ODOP Synergy for {subsidy_summary} Subsidy"
        if language == "hi":
            verdict_spoken = f"मुझे आपके व्यवसाय का {district} के {odop_product} के साथ बहुत सुंदर तालमेल मिला है और इसका स्कोर {score} आया है। मेरी सलाह है कि आप इसे ज़रूर अपनाएँ ताकि आपको {scheme_name} में {subsidy_summary} सरकारी सब्सिडी मिल सके।"
        elif language == "mr":
            verdict_spoken = f"मला तुमच्या व्यवसायाचा {district} च्या {odop_product} सोबत अतिशय सुंदर मेळ मिळाला आहे आणि याचा स्कोअर {score} आला आहे. {scheme_name} मधून {subsidy_summary} सरकारी सबसिडीसाठी तुम्ही हा पर्याय नक्की निवडावा."
        else:
            verdict_spoken = f"I found an excellent strategic synergy between your venture and {district}'s {odop_product} with an alignment score of {score} out of 100. My sincere recommendation is to align with ODOP to unlock {subsidy_summary} subsidy under {scheme_name}."
    elif score >= 50:
        verdict_key = "viable"
        verdict_title = "सकारात्मक तालमेल (Viable Synergy)"
        mira_rec = "Mira Recommends: Viable Strategic Opportunity"
        if language == "hi":
            verdict_spoken = f"आपके व्यवसाय का ODOP के साथ स्कोर {score} है। यह एक अच्छा अतिरिक्त विकल्प है जिसे आप {subsidy_summary} सब्सिडी के लिए जोड़ सकते हैं या अपने मूल विचार के साथ भी बढ़ सकते हैं।"
        elif language == "mr":
            verdict_spoken = f"तुमच्या व्यवसायाचा ODOP सोबत स्कोअर {score} आला आहे. {subsidy_summary} सबसिडी मिळवण्यासाठी तुम्ही हा पर्याय जोडू शकता किंवा मूळ कल्पनेनेही पुढे जाऊ शकता."
        else:
            verdict_spoken = f"Your venture has a viable strategic synergy score of {score} out of 100 with ODOP. It provides a rewarding opportunity for {subsidy_summary} capital subsidy under {scheme_name}, though proceeding with your original model is also viable."
    else:
        verdict_key = "not_recommended"
        verdict_title = "कम तालमेल (Standard MSME Recommended)"
        mira_rec = "Mira Recommends: Continue with Standard Business Model"
        if language == "hi":
            verdict_spoken = f"मैं आपसे बिल्कुल सच कहूँगी, आपके इस विचार के लिए जबरदस्ती {odop_product} जोड़ना सही नहीं रहेगा। आपका स्कोर {score} है। मेरी सलाह है कि आप अपने मूल विचार के साथ ही PMEGP और मुद्रा लोन का लाभ लें।"
        elif language == "mr":
            verdict_spoken = f"मी तुमच्याशी अगदी खरे बोलेन, या व्यवसायासाठी जबरदस्तीने {odop_product} जोडणे योग्य ठरणार नाही. तुमचा स्कोअर {score} आहे. तुम्ही तुमच्या मूळ कल्पनेसह PMEGP आणि मुद्रा कर्ज योजनांचा लाभ घ्यावा."
        else:
            verdict_spoken = f"I will be completely honest with you. Forced alignment with {odop_product} does not suit your business model, and the alignment score is only {score} out of 100. My sincere recommendation is to proceed with your original business model under standard PMEGP and Mudra loan schemes."

    if sector_norm in ("dairy", "food_processing"):
        innov_title = f"Product Innovation ({odop_product}-Infused {sector_clean})"
        innov_desc = f"Introduce a premium, quality-tested product line utilizing {district}'s {odop_product}, targeting high-margin regional retail and institutional corridors."
    elif sector_norm in ("apparel", "artisan_trades"):
        innov_title = f"Design & Craft Innovation ({odop_product} Cluster)"
        innov_desc = f"Incorporate {district}'s indigenous {odop_product} techniques, materials, or provenance into modern product lines, unlocking premium domestic and GeM corridors."
    elif sector_norm in ("repair", "fabrication", "service"):
        innov_title = f"Cluster Tooling & Equipment Support ({odop_product})"
        innov_desc = f"Expand your {sector_clean} operations to provide specialized repair, maintenance, fabrication, or tooling support for enterprises in {district}'s {odop_product} cluster."
    else:
        innov_title = f"Product Innovation ({odop_product} Integration)"
        innov_desc = f"Introduce a specialized product line utilizing or servicing {odop_product}, achieving regional differentiation and government cluster priority."

    source_title = f"Local Sourcing & Catchment Advantage ({district})"
    source_desc = f"Procure raw materials directly from registered producer clusters, mandis, or artisans in {district}, eliminating intermediary markups and ensuring dependable supply."

    fin_title = f"Financial Incentives ({scheme_name})"
    fin_desc = f"Aligning with {odop_product} qualifies your enterprise for {subsidy_summary} credit-linked capital subsidy under {scheme_name}, along with priority GeM onboarding and Common Facility Center (CFC) access."

    what_is_odop = (
        f"Under the Government of India's One District One Product (ODOP) initiative, "
        f"**{odop_product}** ({category}) is designated for **{district}** to develop local "
        f"manufacturing and artisan clusters. By aligning your business with this ODOP mandate, you qualify for "
        f"**{subsidy_summary} capital subsidy under {scheme_name}**, priority GeM government procurement, "
        f"and cluster Common Facility Center (CFC) access."
    )

    resolved_benefits = key_benefits if key_benefits else [
        f"{subsidy_summary} Credit-Linked Capital Subsidy under {scheme_name}",
        "Priority Seller Onboarding on GeM Government Portal without Tender Turnover Criteria",
        "Access to District Cluster Common Facility Centers (CFC)",
        "Premium Price Advantage with Certified ODOP Regional Branding",
    ]

    return {
        "what_is_odop": what_is_odop,
        "user_business": f"{user_business} ({sector_clean})",
        "district_odop": odop_product,
        "primary_odop_product": odop_product,
        "district": district,
        "state": state,
        "alignment_score": score,
        "scheme_name": scheme_name,
        "subsidy_summary": subsidy_summary,
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
        "key_benefits": resolved_benefits,
        "odop_product": odop_product,
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
        odop_product = odop_data.get("official_odop_product") or odop_data.get("odop_product") or "District Specialty Produce"
        category = odop_data.get("category") or "MSME Cluster"
        scheme_name = odop_data.get("scheme_name") or "PMEGP & ODOP Cluster Scheme"
        subsidy_summary = odop_data.get("subsidy_summary") or "25%–35%"
        subsidy_pct = odop_data.get("subsidy_pct") or 35
        key_benefits = odop_data.get("key_benefits") or []
        target_sectors = [s.lower() for s in odop_data.get("matching_sectors", [])]
        raw_mat = bool(odop_data.get("raw_material_availability", True))
        cfc_avail = bool(odop_data.get("cfc_available", False))
        pmfme_elig = bool(odop_data.get("pmfme_eligible", False))

        # Baseline deterministic benchmark evaluation
        baseline = _compute_deterministic_benchmark(
            sector=sector,
            user_business=user_business,
            state=state,
            district=district,
            odop_product=odop_product,
            category=category,
            scheme_name=scheme_name,
            subsidy_summary=subsidy_summary,
            subsidy_pct=subsidy_pct,
            key_benefits=key_benefits,
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
            f"- Official District ODOP Product: {odop_product}\n"
            f"- Category: {category}\n"
            f"- Applicable Government Scheme: {scheme_name} ({subsidy_summary})\n"
            f"- Target Cluster Sectors: {', '.join(target_sectors) if target_sectors else 'Allied MSME / Processing'}\n"
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

        if action == "chat_only":
            missing = [field for field in REQUIRED_FIELDS if not merged_fields.get(field)]
            reply = _generate_mira_response(
                [{"role": message.role, "content": message.content} for message in payload.messages],
                payload.user_name, payload.language, merged_fields, missing,
            )
            return OnboardingResponse(
                reply=reply,
                tts_text=clean_for_bhashini_tts(reply, payload.language),
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="split_screen",
                all_fields_collected=True,
                message={"role": "assistant", "content": reply},
            )

        # Never promote a possibly misheard business into the enterprise record.
        # The confirmation turn uses the pending transcript, not a generic "yes".
        confirmed_idea = action == "confirm_business_idea"
        if confirmed_idea:
            pending_idea = str(existing_fields.get("pending_business_idea") or "").strip()
            if not pending_idea:
                raise HTTPException(status_code=400, detail="No business idea is awaiting confirmation")
            last_user_msg = pending_idea
            action = "business_idea"

        # A business idea is interpreted once, immediately after location. The
        # selected catalogue equipment stays private until the investment turn.
        if action == "business_idea":
            interpretation = interpret_business_idea(
                last_user_msg, chat_service._call_llm_chat_completion,
            )
            uncertain_idea = interpretation["sector"] == "general" and not interpretation["matched_machinery_profile"]
            if not confirmed_idea and (payload.input_source == "voice" or uncertain_idea):
                reply = _business_idea_clarification(
                    last_user_msg, payload.language, interpretation, payload.input_source == "voice"
                )
                return OnboardingResponse(
                    reply=reply,
                    tts_text=clean_for_bhashini_tts(reply, payload.language),
                    extracted_fields={"pending_business_idea": last_user_msg},
                    next_step=payload.conversation_step + 1,
                    next_phase="business_idea_confirmation",
                    all_fields_collected=False,
                    message={"role": "assistant", "content": reply},
                )
            new_fields.update(interpretation)
            new_fields["additional_business_details"] = last_user_msg
            new_fields["pending_business_idea"] = None
            merged_fields.update(new_fields)

        # ── Action: Check ODOP Alignment (User clicked "Let's Check") ─────────
        if action == "check_odop_alignment":
            new_fields["odop_checked"] = True
            merged_fields["odop_checked"] = True

            user_biz = merged_fields.get("additional_business_details") or merged_fields.get("enterprise_name") or f"{merged_fields.get('sector', 'MSME')} Business"
            odop_synergy = _generate_odop_synergy(
                user_business=user_biz,
                sector=merged_fields.get("sector", "general"),
                state=existing_fields.get("state_name") or state_name,
                district=existing_fields.get("district_name") or district_name,
                language=payload.language,
            )

            p_crop = odop_synergy.get("primary_odop_product", "District Product") if odop_synergy else "District Product"
            score_val = odop_synergy.get("alignment_score", 50) if odop_synergy else 50
            mira_verdict = odop_synergy.get("verdict_spoken") or ""
            sub_sum = odop_synergy.get("subsidy_summary", "25%–35%") if odop_synergy else "25%–35%"
            sch_title = odop_synergy.get("scheme_name", "Government Subsidy") if odop_synergy else "Government Subsidy"

            if payload.language == "hi":
                reply = (
                    f"अरे वाह {payload.user_name} जी! मैंने आपके व्यवसाय का {district_name} ज़िले के आधिकारिक उत्पाद {p_crop} के साथ पूरा मूल्यांकन कर लिया है। "
                    f"आपका रणनीतिक तालमेल स्कोर 100 में से **{score_val}** आया है! {mira_verdict}\n\n"
                    f"नीचे दिए गए कार्ड में आप पूरा विश्लेषण देख सकते हैं। अब आप क्या चुनना चाहेंगे:\n"
                    f"1. ODOP तालमेल दर्ज करें (योजना पात्रता अलग से जाँची जाएगी)\n"
                    f"2. अपना मूल विचार रखें"
                )
            elif payload.language == "mr":
                reply = (
                    f"अरे वा {payload.user_name} जी! मी तुमच्या व्यवसायाचे {district_name} जिल्ह्याच्या मुख्य उत्पादन {p_crop} सोबत सखोल मूल्यांकन केले आहे. "
                    f"तुमचा रणनीतिक तालमेल स्कोअर 100 पैकी **{score_val}** आला आहे! {mira_verdict}\n\n"
                    f"खालील कार्डमध्ये संपूर्ण विश्लेषण दिले आहे. आता मला सांगा आपण काय निवडू इच्छिता:\n"
                    f"1. ODOP शी जोडा ({sub_sum} सबसिडी)\n"
                    f"2. माझी मूळ कल्पना ठेवा"
                )
            else:
                reply = (
                    f"Wonderful {payload.user_name} Ji! I have analyzed the strategic synergy between your enterprise and {district_name}'s designated ODOP produce {p_crop}. "
                    f"Your alignment synergy score is **{score_val} out of 100**! {mira_verdict}\n\n"
                    f"You can review the strategic evaluation in the card below. Please select how you would like to proceed:\n"
                    f"1. Align with ODOP strategy (scheme eligibility requires review)\n"
                    f"2. Keep my original idea"
                )

            new_fields["odop_score"] = score_val
            new_fields["odop_product"] = p_crop
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
                message={"role": "assistant", "content": reply},
            )

        # ── Action: Skip ODOP Alignment (User clicked "Will go with my idea") ───
        if action == "skip_odop_alignment":
            new_fields["odop_decision"] = "keep_original"
            new_fields["odop_synergy_aligned"] = False
            merged_fields["odop_decision"] = "keep_original"
            merged_fields["odop_synergy_aligned"] = False

            if payload.language == "hi":
                reply = (
                    f"बहुत बढ़िया {payload.user_name} जी! मुझे आपका आत्मविश्वास बहुत पसंद आया। "
                    f"हम आपके मूल व्यवसाय मॉडल के साथ PMEGP और मुद्रा लोन योजनाओं के तहत आगे बढ़ेंगे।\n\n"
                    f"अब कृपया मुझे अपने उद्यम का नाम और अपनी जाति श्रेणी बताइए ताकि मैं आपकी पूरी रिपोर्ट तैयार कर सकूँ।"
                )
            elif payload.language == "mr":
                reply = (
                    f"खूप छान {payload.user_name} जी! तुमचा आत्मविश्वास मला आवडला. "
                    f"आपण तुमच्या मूळ मॉडेलसह PMEGP आणि मुद्रा कर्ज योजनांअंतर्गत पुढे जाऊ.\n\n"
                    f"आता कृपया तुमच्या उद्योगाचे नाव आणि जात श्रेणी सांगा म्हणजे मी तुमचा अहवाल तयार करू शकेन."
                )
            else:
                reply = (
                    f"Wonderful {payload.user_name} Ji! I admire your conviction. "
                    f"We will proceed with your original model under PMEGP and MUDRA schemes.\n\n"
                    f"Now, could you please share your enterprise name and your caste category so I can prepare your complete report?"
                )

            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="enterprise_info",
                all_fields_collected=False,
                message={"role": "assistant", "content": reply},
            )

        # ── Action: Enterprise Name + Caste Category Submission ────────────────
        if action == "submit_enterprise_info":
            ent_name = existing_fields.get("enterprise_name") or payload.user_name + "'s Enterprise"
            prom_cat = existing_fields.get("promoter_category") or "general"
            new_fields["enterprise_name"] = ent_name
            new_fields["promoter_category"] = prom_cat
            merged_fields["enterprise_name"] = ent_name
            merged_fields["promoter_category"] = prom_cat

            if payload.language == "hi":
                reply = (
                    f"बहुत खूब {payload.user_name} जी! आपके उद्यम का नाम **{ent_name}** और श्रेणी **{prom_cat.upper()}** सुरक्षित कर ली गई है। "
                    f"अब बस मुझे बताइए कि इस उद्यम को शुरू करने के लिए आपके पास अपनी खुद की कितनी प्रमोटर इक्विटी "
                    f"यानी आपकी अपनी बचत या पूँजी तैयार है? जैसे ₹50,000, ₹1 लाख या ₹2 लाख?"
                )
            elif payload.language == "mr":
                reply = (
                    f"अतिशय छान {payload.user_name} जी! तुमच्या उद्योगाचे नाव **{ent_name}** आणि श्रेणी **{prom_cat.upper()}** सुरक्षित केली आहे. "
                    f"आता मला सांगा की हा व्यवसाय सुरू करण्यासाठी तुमच्याकडे स्वतःचे किती प्रमोटर इक्विटी भांडवल "
                    f"किंवा स्वतःची बचत तयार आहे? जसे ₹50,000, ₹1 लाख किंवा ₹2 लाख?"
                )
            else:
                reply = (
                    f"Wonderful {payload.user_name} Ji! Your enterprise name **{ent_name}** and category **{prom_cat.upper()}** have been saved. "
                    f"Now, could you please share how much promoter equity (your own personal savings or capital) "
                    f"you have ready to invest? For example, ₹50,000, ₹1 Lakh, or ₹2 Lakhs?"
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

        # ── Action: Owned Machinery Selection from Interactive Dropdown / Checklist ──
        if action in ("select_owned_machinery", "confirm_machinery"):
            matched_mach = _machinery_profile_for_fields(merged_fields)
            if matched_mach:
                m_name = matched_mach.get("business_name")
                new_fields["matched_machinery_profile"] = m_name
                merged_fields["matched_machinery_profile"] = m_name

            chosen_items = payload.selected_machines or []
            confirmed_owned: List[Dict[str, Any]] = []

            if chosen_items:
                profile_machines = matched_mach.get("machinery_list", []) if matched_mach else []
                selected_names = set()
                for item in chosen_items:
                    name = item.get("machine_name", "") if isinstance(item, dict) else str(item)
                    machine = next((pm for pm in profile_machines if pm.get("machine_name", "").lower() == name.lower()), None)
                    if machine and machine["machine_name"] not in selected_names:
                        confirmed_owned.append(dict(machine))
                        selected_names.add(machine["machine_name"])

            total_owned_val = sum(m.get("estimated_cost_inr", 0) for m in confirmed_owned)
            new_fields["owned_machines"] = confirmed_owned
            new_fields["owned_machinery_value"] = total_owned_val
            new_fields["machinery_selection_confirmed"] = True
            merged_fields["owned_machines"] = confirmed_owned
            merged_fields["owned_machinery_value"] = total_owned_val
            merged_fields["machinery_selection_confirmed"] = True

            # Outlay recalculation with equity and credited owned machinery
            emi_saved = 0.0
            eq_val = float(merged_fields.get("promoter_equity", 100000.0))
            outlay_calc = calculate_tiered_capital_outlay(
                promoter_equity=eq_val,
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

            # Statutory Banking parameters
            bank_params = compute_statutory_banking_parameters(
                sector=merged_fields.get("sector", "general"),
                business_category=merged_fields.get("business_category", "manufacturing"),
                project_cost=merged_fields["project_cost"],
                is_rural=bool(merged_fields.get("is_rural", True)),
                matched_profile=matched_mach,
            )
            for k, v in bank_params.items():
                new_fields[k] = v
                merged_fields[k] = v

            # Calculate intelligent turnover
            try:
                turnover_res = calculate_intelligent_turnover(
                    project_cost=float(merged_fields["project_cost"]),
                    sector=merged_fields.get("sector", "general"),
                    business_category=merged_fields.get("business_category", "manufacturing"),
                    expected_monthly_units=merged_fields.get("expected_monthly_units"),
                    matched_profile=matched_mach,
                )
                new_fields["annual_turnover_estimate"] = turnover_res["projected_turnover"]
                merged_fields["annual_turnover_estimate"] = turnover_res["projected_turnover"]
            except Exception as e:
                logger.warning("Intelligent turnover error: %s", e)

            mach_names_list = [m["machine_name"] for m in confirmed_owned]
            mach_names_str = ", ".join(mach_names_list) if mach_names_list else "आपकी मशीनें"

            applicable_mach_payload = {
                "business_name": matched_mach.get("business_name") if matched_mach else None,
                "category": matched_mach.get("category") if matched_mach else None,
                "industry_sector": matched_mach.get("industry_sector") if matched_mach else None,
                "typical_capacity": matched_mach.get("typical_capacity") if matched_mach else None,
                "total_machinery_cost_inr": matched_mach.get("total_machinery_cost_inr") if matched_mach else None,
                "machinery_list": matched_mach.get("machinery_list", []) if matched_mach else [],
            } if matched_mach else (merged_fields.get("machinery_plan") or {"business_name": None, "machinery_list": [], "total_machinery_cost_inr": 0})

            if total_owned_val > 0:
                owned_lead_hi = f"बहुत खूब {payload.user_name} जी! आपने {mach_names_str} चुना है (मूल्य ₹{int(total_owned_val):,})। हमने इसे आपके आवश्यक बैंक लोन में से घटा दिया है, जिससे आपकी मासिक EMI में लगभग ₹{int(emi_saved):,} रुपये की बचत होगी! "
                owned_lead_mr = f"अतिशय छान {payload.user_name} जी! तुम्ही {mach_names_str} निवडले आहे (मूल्य ₹{int(total_owned_val):,}). आम्ही हे तुमच्या आवश्यक बँक कर्जातून वजा केले आहे! "
                owned_lead_en = f"Excellent {payload.user_name} Ji! You have selected {mach_names_str} (valued at ₹{int(total_owned_val):,}). We have credited this against your bank loan, saving you approximately ₹{int(emi_saved):,} per month in EMI! "
            else:
                owned_lead_hi = f"बहुत अच्छा {payload.user_name} जी! मैंने नोट कर लिया है कि आपको सभी नए उपकरणों की आवश्यकता होगी। "
                owned_lead_mr = f"खूप छान {payload.user_name} जी! मी नोंदवून घेतले आहे की तुम्हाला सर्व नवीन यंत्रसामग्रीची आवश्यकता असेल. "
                owned_lead_en = f"Got it {payload.user_name} Ji! I have noted that you will need all fresh equipment. "

            if payload.language == "hi":
                reply = (
                    f"{owned_lead_hi}"
                    f"अरे वाह {payload.user_name} जी! बहुत-बहुत बधाई! आपकी सभी जानकारियाँ पूरी तरह से सुरक्षित हो गई हैं। "
                    f"मैंने आपके लिए पूरा वित्तीय व व्यवसाय सारांश फॉर्म तैयार कर दिया है। "
                    f"आप दाईं ओर इसे देख सकते हैं और कोई भी विवरण संपादित कर सकते हैं। इसके बाद नीचे दिए गए बटन से अपनी बैंक-स्तरीय व्यवहार्यता रिपोर्ट तैयार करें!"
                )
            elif payload.language == "mr":
                reply = (
                    f"{owned_lead_mr}"
                    f"अरे वा {payload.user_name} जी! तुमचे मनापासून अभिनंदन! तुमची संपूर्ण माहिती सुरक्षित झाली आहे. "
                    f"मी तुमच्यासाठी संपूर्ण प्रकल्प फॉर्म तयार केला आहे. "
                    f"उजव्या बाजूला तुम्ही तो पाहू शकता आणि दुरुस्ती करू शकता. त्यानंतर खालील बटणावरून तुमचा व्यवहार्यता अहवाल तयार करा!"
                )
            else:
                reply = (
                    f"{owned_lead_en}"
                    f"Congratulations {payload.user_name} Ji! All your enterprise and financial details are now securely locked in. "
                    f"I have compiled your complete project summary form. "
                    f"You can review and edit any details on the right side of the screen, then click the button below to generate your bank-grade appraisal report!"
                )

            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="split_screen",
                all_fields_collected=True,
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
            matched_mach = _machinery_profile_for_fields(merged_fields)
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

            odop_info = find_district_odop(state_name, district_name) or {}
            odop_prod = (
                existing_fields.get("odop_product")
                or existing_fields.get("primary_odop_product")
                or odop_info.get("official_odop_product")
                or odop_info.get("odop_product")
                or "District Product"
            )
            if "(" in odop_prod:
                odop_prod = odop_prod.split("(")[0].strip()

            scheme_title = odop_info.get("scheme_name", "PMEGP / ODOP Scheme")
            sub_summary = odop_info.get("subsidy_summary", "25%–35%")

            new_fields["odop_product"] = odop_prod
            merged_fields["odop_product"] = odop_prod

            if align_with_odop:
                synergy_note = f"ODOP Cluster Synergy: Aligned with {odop_prod} under {scheme_title} ({sub_summary})."
                existing_notes = merged_fields.get("additional_business_details", "")
                if synergy_note not in existing_notes:
                    merged_fields["additional_business_details"] = f"{existing_notes} | {synergy_note}".strip(" |")
                    new_fields["additional_business_details"] = merged_fields["additional_business_details"]

            # ── After ODOP decision → Ask for Enterprise Name + Caste Category ──
            if payload.language == "hi":
                if align_with_odop:
                    lead = (
                        f"बहुत ही शानदार और समझदारी भरा निर्णय {payload.user_name} जी! "
                        f"हमने आपके व्यवसाय को {district_name} के ODOP उत्पाद {odop_prod} के साथ जोड़ दिया है, "
                        f"जिससे {scheme_title} की पात्रता जाँचने का अवसर मिल सकता है; सब्सिडी की गारंटी नहीं है। "
                    )
                else:
                    lead = (
                        f"बहुत बढ़िया {payload.user_name} जी! मुझे आपका आत्मविश्वास बहुत पसंद आया। "
                        f"हम आपके मूल व्यवसाय मॉडल के साथ PMEGP और मुद्रा लोन के तहत आगे बढ़ेंगे। "
                    )
                reply = (
                    f"{lead}"
                    f"अब कृपया मुझे अपने उद्यम का नाम और अपनी जाति श्रेणी बताइए ताकि मैं आपकी पूरी रिपोर्ट तैयार कर सकूँ। "
                    f"नीचे दिए गए फॉर्म में अपनी जानकारी भर दीजिए।"
                )
            elif payload.language == "mr":
                if align_with_odop:
                    lead = (
                        f"अतिशय हुशारीचा निर्णय {payload.user_name} जी! "
                        f"आम्ही तुमचा व्यवसाय {district_name} च्या {odop_prod} शी जोडला आहे, "
                        f"त्यामुळे {scheme_title} योजनेची पात्रता तपासता येईल; अनुदानाची हमी नाही. "
                    )
                else:
                    lead = (
                        f"खूप छान {payload.user_name} जी! तुमचा आत्मविश्वास मला आवडला. "
                        f"आपण तुमच्या मूळ मॉडेलसह PMEGP आणि मुद्रा कर्जाअंतर्गत पुढे जाऊ. "
                    )
                reply = (
                    f"{lead}"
                    f"आता कृपया तुमच्या उद्योगाचे नाव आणि तुमची जात श्रेणी सांगा म्हणजे मी तुमचा अहवाल तयार करू शकेन. "
                    f"खालील फॉर्ममध्ये तुमची माहिती भरा."
                )
            else:
                if align_with_odop:
                    lead = (
                        f"A brilliant decision {payload.user_name} Ji! "
                        f"We have aligned your enterprise with {district_name}'s ODOP product {odop_prod}, "
                        f"so we can check eligibility for {scheme_title}; any subsidy remains subject to scheme rules. "
                    )
                else:
                    lead = (
                        f"Wonderful {payload.user_name} Ji! I admire your conviction. "
                        f"We will proceed with your original model under PMEGP and MUDRA schemes. "
                    )
                reply = (
                    f"{lead}"
                    f"Now, could you please share your enterprise name and your caste category so I can prepare your complete report? "
                    f"Please fill in the form below."
                )

            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="enterprise_info",
                all_fields_collected=False,
                odop_alignment=None,
                odop_comparison=None,
                message={"role": "assistant", "content": reply},
            )

        # Extract fields from text
        keyword_fields = {} if action == "business_idea" else _extract_fields_from_text(last_user_msg, existing_fields)
        llm_fields = {} if action == "business_idea" else _llm_extract_fields(last_user_msg)

        for key in set(list(keyword_fields.keys()) + list(llm_fields.keys())):
            if key not in existing_fields and key not in new_fields:
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
        curr_eq = existing_fields.get("promoter_equity")
        if curr_eq is None or float(curr_eq or 0) < 5000:
            is_equity_turn = (
                payload.current_action == "promoter_equity"
                or existing_fields.get("odop_decision") is not None
                or payload.conversation_step >= 4
            )
            eq_val = _extract_promoter_equity(last_user_msg, is_equity_step=is_equity_turn)
            if not eq_val and is_equity_turn:
                eq_val = _llm_extract_equity_amount(last_user_msg)
            if eq_val and eq_val >= 5000:
                new_fields["promoter_equity"] = eq_val
                merged_fields["promoter_equity"] = eq_val

        # ── Match MSME Machinery Profile & Detect Owned Equipment ───────────
        matched_machinery = None
        if "sector" in merged_fields:
            biz_query = f"{merged_fields.get('enterprise_name', '')} {merged_fields.get('additional_business_details', '')} {last_user_msg}"
            matched_machinery = _machinery_profile_for_fields(merged_fields)
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

        # ── Step 3: Business idea provided -> Introduce ODOP & Prompt to check alignment ──
        if "sector" in merged_fields and not existing_fields.get("odop_intro_presented"):
            odop_info = find_district_odop(state_name, district_name) or {}
            odop_prod = odop_info.get("official_odop_product") or odop_info.get("odop_product") or "स्थानीय विशेष उत्पाद"
            if "(" in odop_prod:
                odop_prod = odop_prod.split("(")[0].strip()

            scheme_title = odop_info.get("scheme_name", "PMEGP / ODOP योजना")
            sub_summary = odop_info.get("subsidy_summary", "25% से 35%")

            biz_desc = merged_fields.get("additional_business_details") or merged_fields.get("enterprise_name") or f"{merged_fields['sector'].replace('_', ' ').title()}"
            if merged_fields.get("business_category") == "service":
                retail_terms = ("shop", "store", "retail", "sell", "dukan", "dukkan", "dukaan", "दुकान", "बेचना", "बिक्री")
                is_retail = any(term in biz_desc.lower() for term in retail_terms)
                activity_hi = "तैयार माल बेचने" if is_retail else "सेवा देने"
                activity_en = "selling finished goods" if is_retail else "providing a service"
            else:
                activity_hi = "उत्पादन करने"
                activity_en = "making the product"

            if payload.language == "hi":
                reply = (
                    f"{payload.user_name} जी, मैंने आपकी बात **{biz_desc}** के रूप में समझी है और योजना में **{activity_hi}** का मॉडल रखा है। अगर यह अलग है, तो कृपया मुझे सुधार दें।\n\n"
                    f"आगे बढ़ने से पहले एक बहुत महत्वपूर्ण जानकारी: भारत सरकार की **ODOP (एक ज़िला एक उत्पाद)** पहल के तहत "
                    f"ज़िले के विशेष उत्पाद से जुड़ने पर स्थानीय आपूर्ति, साझा सुविधाओं और **{scheme_title}** जैसी योजनाओं की पात्रता की जाँच की जा सकती है। {sub_summary} एक योजना सीमा है, स्वचालित लाभ नहीं।\n\n"
                    f"आपके ज़िले **{district_name}** का आधिकारिक ODOP उत्पाद **{odop_prod}** है।\n\n"
                    f"क्या आप चाहते हैं कि मैं आपके व्यवसाय विचार और आपके ज़िले के ODOP उत्पाद के बीच तालमेल और {sub_summary} सब्सिडी की संभावना की जाँच करूँ?"
                )
            elif payload.language == "mr":
                reply = (
                    f"{payload.user_name} जी, मी तुमचा व्यवसाय **{biz_desc}** असा समजले आहे. हा अर्थ चुकीचा असल्यास कृपया मला दुरुस्त करा.\n\n"
                    f"पुढे जाण्यापूर्वी एक अत्यंत महत्त्वाची माहिती: केंद्र शासनाच्या **ODOP (एक जिल्हा एक उत्पादन)** उपक्रमांतर्गत "
                    f"जिल्ह्याच्या विशेष उत्पादनाशी संबंध असल्यास स्थानिक पुरवठा, सामायिक सुविधा आणि **{scheme_title}** योजनेची पात्रता तपासता येते. {sub_summary} ही योजनेची मर्यादा आहे, हमखास लाभ नाही.\n\n"
                    f"तुमच्या **{district_name}** जिल्ह्याचे अधिकृत उत्पादन **{odop_prod}** हे आहे.\n\n"
                    f"तुमच्या व्यवसाय कल्पनेचा आणि जिल्ह्याच्या ODOP उत्पादनाचा ताळमेळ तपासून {sub_summary} सबसिडीची शक्यता मी तपासावी का?"
                )
            else:
                reply = (
                    f"{payload.user_name} Ji, I understood your idea as **{biz_desc}**, with a focus on **{activity_en}**. Please correct me if that is not what you intend.\n\n"
                    f"Before we proceed, here is a strategic opportunity: Under the Government's **One District One Product (ODOP)** initiative, "
                    f"a genuine link to the district product may improve local sourcing and allow an eligibility check for **{scheme_title}**. Its {sub_summary} subsidy is conditional, not automatic.\n\n"
                    f"Your district **{district_name}** has **{odop_prod}** as its official ODOP produce.\n\n"
                    f"Would you like me to check whether your **{biz_desc}** idea is a suitable fit for the district ODOP?"
                )

            new_fields["odop_intro_presented"] = True
            new_fields["district_odop_product"] = odop_prod
            merged_fields["odop_intro_presented"] = True
            merged_fields["district_odop_product"] = odop_prod

            odop_intro_payload = {
                "district": district_name,
                "state": state_name,
                "odop_product": odop_prod,
                "description": odop_info.get("description", ""),
                "scheme": scheme_title,
                "subsidy_summary": sub_summary,
                "pmfme_eligible": bool(odop_info.get("pmfme_eligible")),
                "category": odop_info.get("category", "MSME Cluster"),
            }

            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="odop_check_prompt",
                all_fields_collected=False,
                odop_intro=odop_intro_payload,
                message={"role": "assistant", "content": reply},
            )

        # ── Step 3 -> 4: Conversational response to ODOP Check Prompt ──────────
        if existing_fields.get("odop_intro_presented") and not existing_fields.get("odop_checked") and not existing_fields.get("odop_decision"):
            user_txt = last_user_msg.lower().strip()
            check_patterns = [
                r'\bcheck\b', r'\byes\b', r'हाँ', r'जाँच', r'तालमेल', r'दिखाओ', r'बताओ', r'करो',
                r'sure', r'ok', r'1\b', r'१\b', r'होय', r'तपासा', r'पहा', r'बघू', r'let\'?s\s*check'
            ]
            skip_patterns = [
                r'\bno\b', r'\bkeep\b', r'\boriginal\b', r'नहीं', r'नाही', r'मूल\s*विचार',
                r'मेरा\s*विचार', r'स्किप', r'skip', r'2\b', r'२\b', r'नको'
            ]

            if any(re.search(p, user_txt) for p in check_patterns):
                new_fields["odop_checked"] = True
                merged_fields["odop_checked"] = True

                user_biz = merged_fields.get("additional_business_details") or merged_fields.get("enterprise_name") or f"{merged_fields.get('sector', 'MSME')} Business"
                odop_synergy = _generate_odop_synergy(
                    user_business=user_biz,
                    sector=merged_fields.get("sector", "general"),
                    state=existing_fields.get("state_name") or state_name,
                    district=existing_fields.get("district_name") or district_name,
                    language=payload.language,
                )

                p_crop = odop_synergy.get("primary_odop_product", "District Product") if odop_synergy else "District Product"
                score_val = odop_synergy.get("alignment_score", 50) if odop_synergy else 50
                mira_verdict = odop_synergy.get("verdict_spoken") or ""
                if payload.language == "hi":
                    reply = (
                        f"अरे वाह {payload.user_name} जी! मैंने आपके व्यवसाय का {district_name} ज़िले के आधिकारिक उत्पाद {p_crop} के साथ पूरा मूल्यांकन कर लिया है। "
                        f"आपका रणनीतिक तालमेल स्कोर 100 में से **{score_val}** आया है! {mira_verdict}\n\n"
                        f"नीचे दिए गए कार्ड में आप पूरा विश्लेषण देख सकते हैं। अब आप क्या चुनना चाहेंगे:\n"
                        f"1. ODOP से जुड़ें (योजना पात्रता अलग से जाँची जाएगी)\n"
                        f"2. अपना मूल विचार रखें"
                    )
                elif payload.language == "mr":
                    reply = (
                        f"अरे वा {payload.user_name} जी! मी तुमच्या व्यवसायाचे {district_name} जिल्ह्याच्या मुख्य उत्पादन {p_crop} सोबत सखोल मूल्यांकन केले आहे. "
                        f"तुमचा रणनीतिक तालमेल स्कोअर 100 पैकी **{score_val}** आला आहे! {mira_verdict}\n\n"
                        f"खालील कार्डमध्ये संपूर्ण विश्लेषण दिले आहे. आता मला सांगा आपण काय निवडू इच्छिता:\n"
                        f"1. ODOP शी जोडा (योजनेची पात्रता स्वतंत्रपणे तपासावी लागेल)\n"
                        f"2. माझी मूळ कल्पना ठेवा"
                    )
                else:
                    reply = (
                        f"Wonderful {payload.user_name} Ji! I have analyzed the strategic synergy between your enterprise and {district_name}'s designated ODOP produce {p_crop}. "
                        f"Your alignment synergy score is **{score_val} out of 100**! {mira_verdict}\n\n"
                        f"You can review the strategic evaluation in the card below. Please select how you would like to proceed:\n"
                        f"1. Align with ODOP (scheme eligibility requires a separate review)\n"
                        f"2. Keep my original idea"
                    )

                new_fields["odop_score"] = score_val
                new_fields["odop_product"] = p_crop
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
                    message={"role": "assistant", "content": reply},
                )
            elif any(re.search(p, user_txt) for p in skip_patterns):
                new_fields["odop_decision"] = "keep_original"
                new_fields["odop_synergy_aligned"] = False
                merged_fields["odop_decision"] = "keep_original"
                merged_fields["odop_synergy_aligned"] = False

                if payload.language == "hi":
                    reply = (
                        f"बहुत बढ़िया {payload.user_name} जी! मुझे आपका आत्मविश्वास बहुत पसंद आया। "
                        f"हम आपके मूल व्यवसाय मॉडल के साथ PMEGP और मुद्रा लोन योजनाओं के तहत आगे बढ़ेंगे।\n\n"
                        f"अब कृपया मुझे अपने उद्यम का नाम और अपनी जाति श्रेणी बताइए ताकि मैं आपकी पूरी रिपोर्ट तैयार कर सकूँ।"
                    )
                elif payload.language == "mr":
                    reply = (
                        f"खूप छान {payload.user_name} जी! तुमचा आत्मविश्वास मला आवडला. "
                        f"आपण तुमच्या मूळ मॉडेलसह PMEGP आणि मुद्रा कर्ज योजनांअंतर्गत पुढे जाऊ.\n\n"
                        f"आता कृपया तुमच्या उद्योगाचे नाव आणि जात श्रेणी सांगा म्हणजे मी तुमचा अहवाल तयार करू शकेन."
                    )
                else:
                    reply = (
                        f"Wonderful {payload.user_name} Ji! I admire your conviction. "
                        f"We will proceed with your original model under PMEGP and MUDRA schemes.\n\n"
                        f"Now, could you please share your enterprise name and your caste category so I can prepare your complete report?"
                    )

                tts_clean = clean_for_bhashini_tts(reply, payload.language)
                return OnboardingResponse(
                    reply=reply,
                    tts_text=tts_clean,
                    extracted_fields=new_fields,
                    next_step=payload.conversation_step + 1,
                    next_phase="enterprise_info",
                    all_fields_collected=False,
                    message={"role": "assistant", "content": reply},
                )

        # ── Step 5 -> 6: Enterprise Info -> Promoter Equity prompt ────────────
        curr_eq = merged_fields.get("promoter_equity")
        has_valid_eq = curr_eq is not None and float(curr_eq or 0) >= 5000
        if existing_fields.get("odop_decision") and not has_valid_eq:
            if payload.language == "hi":
                reply = (
                    f"बहुत खूब {payload.user_name} जी! अब मुझे यह बताइए कि इस उद्यम को शुरू करने के लिए "
                    f"आपके पास अपनी खुद की कितनी पूँजी या बचत तैयार है? जैसे 50 हजार, ₹1 लाख, ₹2 लाख, या जो भी राशि आप लगाना चाहें—मुझे आसानी से अपने शब्दों में बताइए!"
                )
            elif payload.language == "mr":
                reply = (
                    f"छान {payload.user_name} जी! आता मला सांगा की हा व्यवसाय सुरू करण्यासाठी "
                    f"तुमच्याकडे स्वतःचे किती बचत भांडवल तयार आहे? जसे ₹50,000, 1 लाख, 2 लाख किंवा जी काही रक्कम तुम्ही गुंतवू इच्छिता—मला मोकळेपणाने सांगा!"
                )
            else:
                reply = (
                    f"Wonderful {payload.user_name} Ji! Now, please tell me how much promoter equity "
                    f"(your own personal savings or capital) you have ready to invest? For example, 50k, ₹1 Lakh, ₹2 Lakhs, or any amount you have in mind—tell me in your own words!"
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

        # ── Step 7: Promoter Equity provided -> Present Machinery Card ────────
        has_valid_eq_for_mach = "promoter_equity" in merged_fields and float(merged_fields.get("promoter_equity", 0)) >= 5000
        if has_valid_eq_for_mach and not existing_fields.get("machinery_selection_confirmed"):
            eq_val = float(merged_fields["promoter_equity"])
            biz_name = matched_machinery.get("business_name") if matched_machinery else (merged_fields.get("enterprise_name") or "व्यवसाय")

            if payload.language == "hi":
                reply = (
                    f"बहुत सुंदर {payload.user_name} जी! आपकी ₹{int(eq_val):,} की बचत पूँजी बिल्कुल सही है—यह आपके उद्यम की नींव मजबूत करेगी।\n\n"
                    + (f"अब मैंने आपके **{biz_name}** के लिए उपकरणों की सूची निकाली है। इनमें से जो पहले से आपके पास हैं उन्हें चुनें; अनुमानित मूल्य परियोजना लागत में गिना जाएगा।"
                       if matched_machinery else "यह खुदरा या ऐसा व्यवसाय लगता है जिसके लिए हमारे मशीनरी कैटलॉग में उत्पादन उपकरण नहीं हैं। कृपया इसकी पुष्टि करें।")
                )
            elif payload.language == "mr":
                reply = (
                    f"खूप छान {payload.user_name} जी! तुमचे ₹{int(eq_val):,} चे प्रमोटर इक्विटी भांडवल सुरक्षित नोंदवले गेले आहे.\n\n"
                    + (f"आता तुमच्या **{biz_name}** साठी संबंधित यंत्रांची यादी पाहा. तुमच्याकडे आधीपासून असलेली यंत्रे निवडा."
                       if matched_machinery else "हा किरकोळ व्यवसाय किंवा आमच्या यंत्रसामग्री सूचीबाहेरचा व्यवसाय दिसतो. उत्पादन यंत्रे नसल्यास पुढे जा.")
                )
            else:
                reply = (
                    f"Wonderful {payload.user_name} Ji! Your ₹{int(eq_val):,} investment equity is noted—it sets a solid financial foundation for your venture!\n\n"
                    + (f"I found the catalogue equipment relevant to **{biz_name}**. Select any items you already own so their estimated value can be considered in the project outlay."
                       if matched_machinery else "This appears to be retail or an idea with no production machinery in our catalogue. Please confirm that before reviewing the form.")
                )

            applicable_mach_payload = {
                "business_name": matched_machinery.get("business_name") if matched_machinery else None,
                "category": matched_machinery.get("category") if matched_machinery else None,
                "industry_sector": matched_machinery.get("industry_sector") if matched_machinery else None,
                "typical_capacity": matched_machinery.get("typical_capacity") if matched_machinery else None,
                "total_machinery_cost_inr": matched_machinery.get("total_machinery_cost_inr") if matched_machinery else None,
                "machinery_list": matched_machinery.get("machinery_list", []) if matched_machinery else [],
            } if matched_machinery else (merged_fields.get("machinery_plan") or {"business_name": None, "machinery_list": [], "total_machinery_cost_inr": 0})

            tts_clean = clean_for_bhashini_tts(reply, payload.language)
            return OnboardingResponse(
                reply=reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="machinery_selection",
                all_fields_collected=False,
                applicable_machinery=applicable_mach_payload,
                machinery_analysis={
                    "matched_profile": merged_fields.get("matched_machinery_profile"),
                    "typical_capacity": matched_machinery.get("typical_capacity") if matched_machinery else None,
                    "benchmark_machinery_cost": matched_machinery.get("total_machinery_cost_inr") if matched_machinery else None,
                },
                message={"role": "assistant", "content": reply},
            )

        # ── Step 8: Machinery confirmed -> Split Screen Form ─────────────────
        if existing_fields.get("machinery_selection_confirmed"):
            if payload.language == "hi":
                final_reply = (
                    f"अरे वाह {payload.user_name} जी! बहुत-बहुत बधाई! आपकी सभी जानकारियाँ पूरी तरह से सुरक्षित हो गई हैं। "
                    f"मैंने आपके लिए पूरा वित्तीय व व्यवसाय सारांश फॉर्म तैयार कर दिया है। "
                    f"आप दाईं ओर इसे देख सकते हैं और कोई भी विवरण संपादित कर सकते हैं। इसके बाद नीचे दिए गए बटन से अपनी बैंक-स्तरीय व्यवहार्यता रिपोर्ट तैयार करें!"
                )
            elif payload.language == "mr":
                final_reply = (
                    f"अरे वा {payload.user_name} जी! तुमचे मनापासून अभिनंदन! तुमची संपूर्ण माहिती सुरक्षित झाली आहे. "
                    f"मी तुमच्यासाठी संपूर्ण प्रकल्प फॉर्म तयार केला आहे. "
                    f"उजव्या बाजूला तुम्ही तो पाहू शकता आणि दुरुस्ती करू शकता. त्यानंतर खालील बटणावरून तुमचा व्यवहार्यता अहवाल तयार करा!"
                )
            else:
                final_reply = (
                    f"Congratulations {payload.user_name} Ji! All your enterprise and financial details are now securely locked in. "
                    f"I have compiled your complete project summary form. "
                    f"You can review and edit any details on the right side of the screen, then click the button below to generate your bank-grade appraisal report!"
                )

            tts_clean = clean_for_bhashini_tts(final_reply, payload.language)
            return OnboardingResponse(
                reply=final_reply,
                tts_text=tts_clean,
                extracted_fields=new_fields,
                next_step=payload.conversation_step + 1,
                next_phase="split_screen",
                all_fields_collected=True,
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
                message={"role": "assistant", "content": final_reply},
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
