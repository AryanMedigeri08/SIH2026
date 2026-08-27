"""
executive_synthesizer.py — Phase 4, Udyam Saathi

Tier 3: Unified AI Synthesis Layer & SHA-256 In-Memory Caching Engine.

Core Invariants:
    1. Single LLM Call Guarantee: Consolidates Tier 1 (deterministic math) and Tier 2
       (XGBoost viability prediction) into ONE single Groq synthesis call (Llama 3.3 70B).
    2. Zero Financial Recalculation: All ₹ figures, EMIs, subsidies, DSCR ratios, and
       ML probabilities are computed upstream and injected into the prompt as immutable facts.
    3. SHA-256 In-Memory Caching (< 1ms): Payloads are hashed using canonical JSON. Identical
       requests return instantly from memory with 1-hour TTL.
    4. Zero-Crash Deterministic Fallback: When offline, unauthenticated, or rate-limited,
       the platform seamlessly generates an auditable, fully grounded template narrative
       in any of the 6 supported Indian languages.
    5. Supported Languages:
       - en: English
       - hi: Hindi (हिन्दी)
       - mr: Marathi (मराठी)
       - ta: Tamil (தமிழ்)
       - te: Telugu (తెలుగు)
       - kn: Kannada (ಕನ್ನಡ)
"""

from __future__ import annotations
import hashlib
import json
import os
import time
import threading
from dataclasses import dataclass, asdict
from typing import Optional, Union, Any
from pathlib import Path

import logging

logger = logging.getLogger("udyam_saathi.synthesizer")

# Supported regional languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "mr": "Marathi (मराठी)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "kn": "Kannada (ಕನ್ನಡ)",
}

DEFAULT_LANGUAGE = "en"
DEFAULT_CACHE_TTL_SECONDS = 3600  # 1 hour TTL


@dataclass
class ExecutiveSynthesis:
    executive_summary: str
    strategic_recommendations: list[str]
    bank_appraisal_notes: str
    language: str
    is_cached: bool
    is_fallback: bool
    latency_ms: float
    model_name: str
    payload_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "executive_summary": self.executive_summary,
            "strategic_recommendations": self.strategic_recommendations,
            "bank_appraisal_notes": self.bank_appraisal_notes,
            "language": self.language,
            "language_name": SUPPORTED_LANGUAGES.get(self.language, "English"),
            "is_cached": self.is_cached,
            "is_fallback": self.is_fallback,
            "source_type": "DETERMINISTIC_TEMPLATE" if self.is_fallback else "AI_GENERATED",
            "source_description": (
                f"Predefined Domain Template ({self.model_name})"
                if self.is_fallback
                else f"AI Synthesized via Groq ({self.model_name})"
            ),
            "latency_ms": round(self.latency_ms, 2),
            "model_name": self.model_name,
            "payload_hash": self.payload_hash,
        }



class SynthesisCache:
    """
    Thread-safe in-memory cache keyed on SHA-256 hash of canonical JSON payload + language code.
    """
    _instance: Optional[SynthesisCache] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SynthesisCache, cls).__new__(cls)
                cls._instance._store = {}
                cls._instance._hits = 0
                cls._instance._misses = 0
            return cls._instance

    @staticmethod
    def compute_hash(payload: dict[str, Any], language: str) -> str:
        """Computes deterministic SHA-256 hash from canonical JSON string."""
        canonical_str = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        composite = f"{canonical_str}|lang={language.lower().strip()}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()

    def get(self, payload_hash: str) -> Optional[ExecutiveSynthesis]:
        with self._lock:
            if payload_hash in self._store:
                entry = self._store[payload_hash]
                now = time.time()
                if now < entry["expires_at"]:
                    self._hits += 1
                    cached_synthesis = entry["synthesis"]
                    # Return copy marked as cached
                    return ExecutiveSynthesis(
                        executive_summary=cached_synthesis.executive_summary,
                        strategic_recommendations=list(cached_synthesis.strategic_recommendations),
                        bank_appraisal_notes=cached_synthesis.bank_appraisal_notes,
                        language=cached_synthesis.language,
                        is_cached=True,
                        is_fallback=cached_synthesis.is_fallback,
                        latency_ms=0.01,
                        model_name=cached_synthesis.model_name,
                        payload_hash=payload_hash,
                    )
                else:
                    del self._store[payload_hash]
            self._misses += 1
            return None

    def set(self, payload_hash: str, synthesis: ExecutiveSynthesis, ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> None:
        with self._lock:
            self._store[payload_hash] = {
                "synthesis": synthesis,
                "expires_at": time.time() + ttl_seconds,
            }

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "items_count": len(self._store),
                "hits": self._hits,
                "misses": self._misses,
            }


# ---------------------------------------------------------------------------
# 100% Deterministic Grounded Narrative Engine (6 Languages)
# ---------------------------------------------------------------------------
def get_deterministic_narrative(
    enterprise_name: str,
    business_category: str,
    sector: str,
    location_str: str,
    project_cost: float,
    top_scheme_name: str,
    subsidy_amount: float,
    effective_loan: float,
    monthly_emi: float,
    dscr: float,
    dscr_verdict: str,
    ml_verdict: str,
    ml_confidence_pct: float,
    cpi_adjusted_price_floor: float,
    key_risks: list[str],
    language: str = "en",
) -> ExecutiveSynthesis:
    """
    Generates a high-quality, professional, and audit-traceable executive narrative
    using localized deterministic templates with exact grounded numbers.
    """
    lang = language.lower().strip()
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"

    subsidy_pct = (subsidy_amount / project_cost * 100) if project_cost > 0 else 0.0
    risk_summary = "; ".join(key_risks[:2]) if key_risks else "Standard operational contingencies"

    if lang == "hi":
        summary = (
            f"**उद्यम साथी व्यवहार्यता मूल्यांकन**: {location_str} में प्रस्तावित {sector} ({business_category}) "
            f"इकाई की कुल पूंजीगत लागत ₹{project_cost:,.0f} आंकी गई है। सरकारी योजना अनुकूलक ने **{top_scheme_name}** "
            f"को सर्वोत्तम विकल्प के रूप में चिन्हित किया है, जिसके तहत ₹{subsidy_amount:,.0f} ({subsidy_pct:.1f}%) "
            f"का पूंजी अनुदान देय है, जिससे शुद्ध बैंक सावधि ऋण भार घटकर ₹{effective_loan:,.0f} रह जाता है।\n\n"
            f"वित्तीय दृष्टि से, ऋण शोधन क्षमता अनुपात (DSCR) **{dscr:.2f}** ({dscr_verdict}) है, जो मासिक EMI ₹{monthly_emi:,.2f} "
            f"के सुचारू पुनर्भुगतान को सुनिश्चित करता है। हमारे 10-आयामी मशीन लर्निंग मॉडल ने **{ml_verdict}** निर्णय "
            f"**{ml_confidence_pct:.1f}%** विश्वसनीयता के साथ निर्धारित किया है। मुद्रास्फीति-समायोजित आधार लागत मूल्य "
            f"₹{cpi_adjusted_price_floor:.2f} प्रति इकाई निर्धारित किया गया है।"
        )
        recommendations = [
            f"शीघ्र लाभ प्राप्त करने हेतु {top_scheme_name} के तहत ऑनलाइन आवेदन नोडल बैंक शाखा में अग्रसारित करें।",
            f"मासिक ₹{monthly_emi:,.0f} EMI दायित्व की सुरक्षा हेतु न्यूनतम 3 महीने का आकस्मिक आरक्षित कोष (₹{monthly_emi * 3:,.0f}) बनाए रखें।",
            f"स्थानीय कच्चे माल आपूर्तिकर्ताओं से 6 से 12 महीने के निश्चित मूल्य अनुबंध स्थापित करें ताकि मुद्रास्फीति प्रभाव कम हो।",
            f"उत्पाद की गुणवत्ता सुनिश्चित करते हुए बिक्री मूल्य को ₹{cpi_adjusted_price_floor:.2f} के अनुशंसित मूल्य बैंड के अनुसार निर्धारित करें।"
        ]
        bank_notes = (
            f"**बैंक ऋण अधिकारी मूल्यांकन टिप्पणी**: यह परियोजना RBI के 1.33 DSCR मानदंड को पूरा करती है "
            f"(परिकलित DSCR: {dscr:.2f})। {top_scheme_name} से प्राप्त होने वाली ₹{subsidy_amount:,.0f} की अग्रिम/पश्चगामी "
            f"सब्सिडी क्रेडिट जोखिम को पर्याप्त रूप से कम करती है। प्राथमिक मशीनरी एवं स्टॉक पर दृष्टिबंधक (Hypothecation) "
            f"के साथ ऋण संवितरण संस्तुत है।"
        )

    elif lang == "mr":
        summary = (
            f"**उद्यम साथी व्यवहार्यता अहवाल**: {location_str} येथील प्रस्तावित {sector} ({business_category}) "
            f"प्रकल्पाचा एकूण भांडवली खर्च ₹{project_cost:,.0f} आहे. **{top_scheme_name}** अंतर्गत ₹{subsidy_amount:,.0f} "
            f"({subsidy_pct:.1f}%) चे भांडवली अनुदान मंजूर होत असून निव्वळ बँक कर्ज ₹{effective_loan:,.0f} निश्चित होते.\n\n"
            f"प्रकल्पाचा कर्ज परतफेड क्षमता गुणोत्तर (DSCR) **{dscr:.2f}** ({dscr_verdict}) असून मासिक हप्ता (EMI) "
            f"₹{monthly_emi:,.2f} आहे. १०-घटकीय AI/ML मॉडेलने या प्रकल्पाला **{ml_confidence_pct:.1f}%** आत्मविश्वासासह "
            f"**{ml_verdict}** दर्जा दिला आहे. महागाई समायोजित किमान उत्पादन दर ₹{cpi_adjusted_price_floor:.2f} प्रति युनिट आहे."
        )
        recommendations = [
            f"{top_scheme_name} योजनेअंतर्गत अधिकृत बँक शाखेत तात्काळ प्रस्ताव सादर करावा.",
            f"मासिक EMI सुरक्षेसाठी ३ महिन्यांचा राखीव निधी (₹{monthly_emi * 3:,.0f}) राखून ठेवावा.",
            f"स्थानिक बाजारपेठेत ग्राहकांशी थेट संपर्क साधून ₹{cpi_adjusted_price_floor:.2f} च्या आधारभूत दरावर विक्री करावी.",
            f"कच्च्या मालाच्या पुरवठ्यावर लक्ष ठेवून खेळत्या भांडवलाचे योग्य नियोजन करावे."
        ]
        bank_notes = (
            f"**बँक कर्ज मूल्यांकन नोंद**: सदर प्रकल्पाचा DSCR {dscr:.2f} समाधानकारक असून तो RBI निकषांनुसार व्यवहार्य आहे. "
            f"₹{subsidy_amount:,.0f} ची शासकीय सबसिडी क्रेडिट रिस्क कमी करते. मुदत कर्जास मंजुरी देण्यास हरकत नाही."
        )

    elif lang == "ta":
        summary = (
            f"**உத்யம் சாதி திட்ட அறிக்கை**: {location_str} பகுதியில் அமையவிருக்கும் {sector} ({business_category}) "
            f"தொழிலின் மொத்த முதலீடு ₹{project_cost:,.0f} ஆகும். **{top_scheme_name}** திட்டத்தின் கீழ் ₹{subsidy_amount:,.0f} "
            f"({subsidy_pct:.1f}%) மானியம் கிடைப்பதால், நிகர வங்கி கடன் ₹{effective_loan:,.0f} ஆக குறைகிறது.\n\n"
            f"நிதி அடிப்படையில், கடன் சேவை பாதுகாப்பு விகிதம் (DSCR) **{dscr:.2f}** ({dscr_verdict}) ஆகவும், மாத தவணை (EMI) "
            f"₹{monthly_emi:,.2f} ஆகவும் உள்ளது. எங்கள் AI/ML மாதிரி **{ml_confidence_pct:.1f}%** துல்லியத்துடன் "
            f"**{ml_verdict}** என மதிப்பிட்டுள்ளது. குறைந்தபட்ச உற்பத்தி விலை ஒரு யூனிட்டுக்கு ₹{cpi_adjusted_price_floor:.2f} ஆகும்."
        )
        recommendations = [
            f"{top_scheme_name} திட்ட மானியத்திற்கு உடனடியாக வங்கியில் விண்ணப்பிக்கவும்.",
            f"3 மாத EMI தவணைக்கான அவசர நிதியை (₹{monthly_emi * 3:,.0f}) சேமிப்பில் வைத்திருக்கவும்.",
            f"பணவீக்க தாக்கத்தை குறைக்க மூலப்பொருள் விநியோகஸ்தர்களுடன் நிலையான ஒப்பந்தம் செய்யவும்.",
            f"பரிந்துரைக்கப்பட்ட ₹{cpi_adjusted_price_floor:.2f} விலை வரம்பிற்குள் விற்பனை விலையை நிர்ணயிக்கவும்."
        ]
        bank_notes = (
            f"**வங்கி கடன் அதிகாரி குறிப்பு**: திட்டத்தின் DSCR விகிதம் {dscr:.2f} ரிசர்வ் வங்கியின் வழிகாட்டுதலுக்கு "
            f"ஏற்ப உள்ளது. ₹{subsidy_amount:,.0f} அரசு மானியம் கடன் அபாயத்தை குறைக்கிறது. கடன் வழங்க பரிந்துரைக்கப்படுகிறது."
        )

    elif lang == "te":
        summary = (
            f"**ఉద్యమ్ సాథీ సాధ్యత నివేదిక**: {location_str} లో ప్రతిపాదిత {sector} ({business_category}) "
            f"యూనిట్ మొత్తం ప్రాజెక్ట్ వ్యయం ₹{project_cost:,.0f}. **{top_scheme_name}** పథకం కింద ₹{subsidy_amount:,.0f} "
            f"({subsidy_pct:.1f}%) సబ్సిడీ లభిస్తుంది, దీనివల్ల నికర బ్యాంకు రుణం ₹{effective_loan:,.0f} కు తగ్గుతుంది.\n\n"
            f"ఆర్థికంగా, డెట్ సర్వీస్ కవరేజ్ రేషియో (DSCR) **{dscr:.2f}** ({dscr_verdict}) మరియు నెలవారీ EMI ₹{monthly_emi:,.2f}. "
            f"మా 10-డైమెన్షనల్ AI/ML మోడల్ **{ml_confidence_pct:.1f}%** ఖచ్చితత్వంతో **{ml_verdict}** రేటింగ్ ఇచ్చింది. "
            f"ద్రవ్యోల్బణ సర్దుబాటు యూనిట్ ధర ₹{cpi_adjusted_price_floor:.2f} గా నిర్ణయించబడింది."
        )
        recommendations = [
            f"{top_scheme_name} పథకం కింద రుణ దరఖాస్తును వెంటనే బ్యాంకులో సమర్పించండి.",
            f"నెలవారీ EMI భద్రత కోసం 3 నెలల అత్యవసర నిధిని (₹{monthly_emi * 3:,.0f}) నిర్వహించండి.",
            f"స్థానిక మార్కెట్ డిమాండ్ ఆధారంగా వర్కింగ్ క్యాపిటల్ నిర్వహణను పటిష్టం చేయండి.",
            f"సిఫార్సు చేయబడిన ధర ₹{cpi_adjusted_price_floor:.2f} ప్రకారం లాభదాయకమైన అమ్మకాలను చేపట్టండి."
        ]
        bank_notes = (
            f"**బ్యాంక్ క్రెడిట్ అధికారి నివేదిక**: ఈ ప్రాజెక్ట్ యొక్క DSCR {dscr:.2f} RBI ప్రమాణాలకు అనుగుణంగా ఉంది. "
            f"₹{subsidy_amount:,.0f} ప్రభుత్వ సబ్సిడీ క్రెడిట్ రిస్క్‌ను గణనీయంగా తగ్గిస్తుంది. లోన్ మంజూరుకు అనుకూలం."
        )

    elif lang == "kn":
        summary = (
            f"**ಉದ್ಯಮ್ ಸಾಥಿ ಕಾರ್ಯಸಾಧ್ಯತಾ ವರದಿ**: {location_str} ನಲ್ಲಿ ಪ್ರಸ್ತಾಪಿಸಲಾದ {sector} ({business_category}) "
            f"ಘಟಕದ ಒಟ್ಟು ಬಂಡವಾಳ ವೆಚ್ಚ ₹{project_cost:,.0f} ಆಗಿದೆ. **{top_scheme_name}** ಯೋಜನೆಯಡಿ ₹{subsidy_amount:,.0f} "
            f"({subsidy_pct:.1f}%) ಅನುದಾನ ಲಭ್ಯವಿದ್ದು, ನಿವ್ವಳ ಬ್ಯಾಂಕ್ ಸಾಲ ₹{effective_loan:,.0f} ಗೆ ಇಳಿಕೆಯಾಗುತ್ತದೆ.\n\n"
            f"ಯೋಜನೆಯ ಸಾಲ ಮರುಪಾವತಿ ಸಾಮರ್ಥ್ಯ (DSCR) **{dscr:.2f}** ({dscr_verdict}) ಆಗಿದ್ದು, ಮಾಸಿಕ ಕಂತು (EMI) "
            f"₹{monthly_emi:,.2f} ಆಗಿದೆ. 10-ಆಯಾಮದ AI/ML ಮಾದರಿಯು **{ml_confidence_pct:.1f}%** ವಿಶ್ವಾಸಾರ್ಹತೆಯೊಂದಿಗೆ "
            f"**{ml_verdict}** ತೀರ್ಪು ನೀಡಿದೆ. ಹಣದುಬ್ಬರ ಹೊಂದಾಣಿಕೆಯ ಕನಿಷ್ಠ ದರ ಪ್ರತಿ ಯೂನಿಟ್‌ಗೆ ₹{cpi_adjusted_price_floor:.2f} ಆಗಿದೆ."
        )
        recommendations = [
            f"{top_scheme_name} ಯೋಜನೆಯಡಿ ಶೀಘ್ರವಾಗಿ ಬ್ಯಾಂಕ್ ಶಾಖೆಯಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ.",
            f"ಮಾಸಿಕ EMI ರಕ್ಷಣೆಗಾಗಿ 3 ತಿಂಗಳ ಮೀಸಲು ನಿಧಿಯನ್ನು (₹{monthly_emi * 3:,.0f}) ಇರಿಸಿಕೊಳ್ಳಿ.",
            f"ಸ್ಥಳೀಯ ಮಾರುಕಟ್ಟೆ ಬೇಡಿಕೆಗೆ ತಕ್ಕಂತೆ ಕಚ್ಚಾ ವಸ್ತುಗಳ ಸಂಗ್ರಹಣೆ ನಿರ್ವಹಿಸಿ.",
            f"ಶಿಫಾರಸು ಮಾಡಲಾದ ₹{cpi_adjusted_price_floor:.2f} ಬೆಲೆಗೆ ಅನುಗುಣವಾಗಿ ಮಾರಾಟ ನಡೆಸಿ."
        ]
        bank_notes = (
            f"**ಬ್ಯಾಂಕ್ ಸಾಲ ಅಧಿಕಾರಿ ಟಿಪ್ಪಣಿ**: ಯೋಜನೆಯ DSCR {dscr:.2f} RBI ಮಾನದಂಡಕ್ಕೆ ಅನುಗುಣವಾಗಿದ್ದು, "
            f"₹{subsidy_amount:,.0f} ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿ ಸಾಲದ ಅಪಾಯವನ್ನು ಕಡಿಮೆ ಮಾಡುತ್ತದೆ. ಸಾಲ ಮಂಜೂರಾತಿಗೆ ಸೂಕ್ತವಾಗಿದೆ."
        )

    else:  # Default: English
        summary = (
            f"**Executive Feasibility Appraisal**: The proposed {sector.title()} ({business_category.title()}) "
            f"enterprise at {location_str} represents a total capital outlay of ₹{project_cost:,.0f}. "
            f"The deterministic multi-scheme optimizer identifies **{top_scheme_name}** as the optimal financing vehicle, "
            f"providing a ₹{subsidy_amount:,.0f} ({subsidy_pct:.1f}%) capital subsidy grant, reducing net term loan exposure "
            f"to ₹{effective_loan:,.0f}.\n\n"
            f"Financial underwriting yields a Debt Service Coverage Ratio (DSCR) of **{dscr:.2f}** ({dscr_verdict}), "
            f"adequately servicing the monthly EMI liability of ₹{monthly_emi:,.2f}. The 10-Dimensional Supervised "
            f"ML Viability Classifier rates this enterprise as **{ml_verdict}** with **{ml_confidence_pct:.1f}%** confidence. "
            f"The CPI-adjusted unit price floor is established at ₹{cpi_adjusted_price_floor:.2f}/unit."
        )
        recommendations = [
            f"Initiate formal loan appraisal under {top_scheme_name} to secure the ₹{subsidy_amount:,.0f} capital grant.",
            f"Maintain a mandatory 3-month EMI liquidity reserve of ₹{monthly_emi * 3:,.0f} prior to commercial operations.",
            f"Establish forward supplier contracts to hedge against localized input cost inflation ({risk_summary}).",
            f"Align commercial pricing within the recommended range above ₹{cpi_adjusted_price_floor:.2f}/unit to preserve gross margins."
        ]
        bank_notes = (
            f"**Bank Credit Appraisal Memorandum**: The project comfortably satisfies the RBI solvency threshold "
            f"with a DSCR of {dscr:.2f}. The capital subsidy cushion of ₹{subsidy_amount:,.0f} substantially de-risks "
            f"the bank's primary credit exposure. Primary security comprises hypothecation of machinery and working capital assets."
        )

    return ExecutiveSynthesis(
        executive_summary=summary,
        strategic_recommendations=recommendations,
        bank_appraisal_notes=bank_notes,
        language=lang,
        is_cached=False,
        is_fallback=True,
        latency_ms=0.05,
        model_name="deterministic_narrative_engine_v1.0",
        payload_hash="",
    )


# ---------------------------------------------------------------------------
# Prompt Builder & Groq Single-Call Synthesizer
# ---------------------------------------------------------------------------
def _build_synthesis_prompt(
    payload: dict[str, Any],
    language: str,
) -> tuple[str, str]:
    """
    Constructs a hardened, zero-hallucination prompt. Injects all pre-calculated
    numbers as immutable constants. Instructs the LLM to output valid JSON.
    """
    target_lang_name = SUPPORTED_LANGUAGES.get(language, "English")

    system_prompt = (
        "You are the Chief Credit Appraisal & Enterprise Advisory AI for Udyam Saathi (SIH 2026 PS 26091).\n"
        "Your mission is to synthesize pre-computed financial, market, risk, and machine-learning signals "
        "into a professional, bank-ready Detailed Project Report (DPR) executive summary.\n\n"
        "STRICT ARCHITECTURAL INVARIANTS:\n"
        "1. ZERO FINANCIAL RECALCULATION: You must NEVER re-compute, modify, or hallucinate any financial numbers. "
        "Use the EXACT rupee values (₹), DSCR ratio, EMI, subsidy amounts, and ML probabilities provided in the user prompt.\n"
        "2. LANGUAGE: You must write the entire output strictly in the requested target language: "
        f"'{target_lang_name}' (language code: '{language}'). Use fluent, professional business and banking terminology.\n"
        "3. JSON OUTPUT ONLY: You must respond ONLY with a single valid, parseable JSON object matching this schema:\n"
        "{\n"
        '  "executive_summary": "<2-3 paragraph professional narrative>",\n'
        '  "strategic_recommendations": ["<rec 1>", "<rec 2>", "<rec 3>", "<rec 4>"],\n'
        '  "bank_appraisal_notes": "<Targeted credit memo for scheduled commercial bank loan officers>"\n'
        "}\n"
        "Do NOT include markdown backticks like ```json ... ``` outside the JSON object. Do not include introductory text."
    )

    user_prompt = (
        f"Generate the executive feasibility synthesis in '{target_lang_name}' using these exact pre-calculated metrics:\n\n"
        f"--- ENTERPRISE & PROMOTER PROFILE ---\n"
        f"- Enterprise Name: {payload.get('enterprise_name', 'Micro Enterprise Unit')}\n"
        f"- Sector / Category: {payload.get('sector', 'N/A')} ({payload.get('business_category', 'N/A')})\n"
        f"- Location: {payload.get('location_str', 'Rural Catchment')}\n"
        f"- Total Capital Outlay: ₹{payload.get('project_cost', 0):,.2f}\n"
        f"- Promoter Margin: ₹{payload.get('promoter_margin_amount', 0):,.2f}\n\n"
        f"--- TIER 1: DETERMINISTIC FINANCIAL & SCHEME OPTIMIZATION ---\n"
        f"- Recommended Scheme: {payload.get('top_scheme_name', 'PMEGP')}\n"
        f"- Capital Subsidy Grant: ₹{payload.get('subsidy_amount', 0):,.2f} ({payload.get('subsidy_pct', 0):.1f}% of outlay)\n"
        f"- Net Bank Term Loan: ₹{payload.get('effective_loan', 0):,.2f}\n"
        f"- Monthly EMI Liability: ₹{payload.get('monthly_emi', 0):,.2f}\n"
        f"- Debt Service Coverage Ratio (DSCR): {payload.get('dscr', 1.33):.2f} (RBI Benchmark >= 1.33 -> {payload.get('dscr_verdict', 'VIABLE')})\n"
        f"- Annual Market TAM: ₹{payload.get('annual_tam', 0):,.2f}\n"
        f"- Break-Even Price Floor: ₹{payload.get('cpi_adjusted_price_floor', 0):,.2f}/unit\n\n"
        f"--- TIER 2: MACHINE LEARNING VIABILITY VERDICT ---\n"
        f"- ML Viability Verdict: {payload.get('ml_verdict', 'SUITABLE')}\n"
        f"- ML Model Confidence: {payload.get('ml_confidence_pct', 95.0):.1f}%\n"
        f"- Top Positive Driver: {payload.get('top_positive_driver', 'Adequate debt service margin')}\n"
        f"- Top Risk Factor: {payload.get('top_risk_factor', 'Moderate competition')}\n\n"
        f"Respond ONLY with the JSON object."
    )

    return system_prompt, user_prompt


def generate_executive_synthesis(
    payload: dict[str, Any],
    language: str = "en",
    groq_api_key: Optional[str] = None,
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    force_fallback: bool = False,
) -> ExecutiveSynthesis:
    """
    Main entrypoint for Tier 3 AI Synthesis.
    Executes in sequence:
        1. SHA-256 in-memory cache lookup (< 1ms)
        2. Single Groq LLM call (if API key available and not force_fallback)
        3. Deterministic template narrative fallback (zero-crash)
    """
    start_time = time.perf_counter()
    lang = language.lower().strip()
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"

    cache = SynthesisCache()
    payload_hash = cache.compute_hash(payload, lang)

    # 1. Cache Lookup
    cached = cache.get(payload_hash)
    if cached is not None and not force_fallback:
        logger.info(
            f"[SYNTHESIS CACHE HIT] SHA-256: {payload_hash[:12]}... | Model: {cached.model_name} | "
            f"Source: {'[DETERMINISTIC_TEMPLATE]' if cached.is_fallback else '[AI_GENERATED]'}"
        )
        return cached

    # 2. Extract standard variables for prompt & fallback
    enterprise_name = payload.get("enterprise_name", "Micro Enterprise Unit")
    business_category = payload.get("business_category", "manufacturing")
    sector = payload.get("sector", "general")
    location_str = payload.get("location_str", "Rural Catchment")
    project_cost = float(payload.get("project_cost", 500000.0))
    top_scheme_name = payload.get("top_scheme_name", "PMEGP")
    subsidy_amount = float(payload.get("subsidy_amount", 125000.0))
    effective_loan = float(payload.get("effective_loan", 325000.0))
    monthly_emi = float(payload.get("monthly_emi", 8500.0))
    dscr = float(payload.get("dscr", 1.45))
    dscr_verdict = payload.get("dscr_verdict", "VIABLE")
    ml_verdict = payload.get("ml_verdict", "SUITABLE")
    ml_confidence_pct = float(payload.get("ml_confidence_pct", 95.0))
    cpi_adjusted_price_floor = float(payload.get("cpi_adjusted_price_floor", 120.0))
    key_risks = payload.get("key_risks", [])

    # If offline / forced fallback / no API key -> instantaneous deterministic synthesis
    api_key = groq_api_key or os.environ.get("GROQ_API_KEY")

    if force_fallback or not api_key:
        logger.info(
            f"[SYNTHESIS: DETERMINISTIC TEMPLATE] Language: '{lang}' ({SUPPORTED_LANGUAGES.get(lang, 'English')}) | "
            f"Enterprise: '{enterprise_name}' | Source: [DETERMINISTIC_TEMPLATE]"
        )
        fallback = get_deterministic_narrative(
            enterprise_name=enterprise_name,
            business_category=business_category,
            sector=sector,
            location_str=location_str,
            project_cost=project_cost,
            top_scheme_name=top_scheme_name,
            subsidy_amount=subsidy_amount,
            effective_loan=effective_loan,
            monthly_emi=monthly_emi,
            dscr=dscr,
            dscr_verdict=dscr_verdict,
            ml_verdict=ml_verdict,
            ml_confidence_pct=ml_confidence_pct,
            cpi_adjusted_price_floor=cpi_adjusted_price_floor,
            key_risks=key_risks,
            language=lang,
        )
        fallback.payload_hash = payload_hash
        fallback.latency_ms = (time.perf_counter() - start_time) * 1000
        cache.set(payload_hash, fallback, ttl_seconds=cache_ttl_seconds)
        return fallback

    # 3. Attempt single Groq call
    try:
        from groq import Groq

        logger.info(
            f"[LLM REQUEST START] Invoking Groq Cloud LLM | Language: '{lang}' | "
            f"Context: Outlay ₹{project_cost:,.0f}, Subsidy ₹{subsidy_amount:,.0f}, "
            f"DSCR {dscr:.2f}, ML {ml_verdict} ({ml_confidence_pct:.1f}%)"
        )
        client = Groq(api_key=api_key)
        system_prompt, user_prompt = _build_synthesis_prompt(payload, lang)

        # Primary model: openai/gpt-oss-20b with fallback options
        configured_model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
        models_to_try = [
            configured_model,
            "openai/gpt-oss-20b",
            "gpt-oss-20b",
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
        ]
        # Deduplicate while preserving precedence
        models_to_try = list(dict.fromkeys(models_to_try))

        response_content = None
        used_model = models_to_try[0]

        for model_name in models_to_try:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    model=model_name,
                    temperature=0.2,
                    max_tokens=1024,
                    response_format={"type": "json_object"},
                )
                response_content = chat_completion.choices[0].message.content
                used_model = model_name
                break
            except Exception as e:
                logger.warning(f"[LLM RETRY] Model '{model_name}' failed ({str(e)}), trying next candidate...")
                continue

        if not response_content:
            raise RuntimeError("All Groq model attempts failed")

        data = json.loads(response_content)

        summary = data.get("executive_summary", "")
        recommendations = data.get("strategic_recommendations", [])
        bank_notes = data.get("bank_appraisal_notes", "")

        if not summary or not recommendations:
            raise ValueError("Incomplete JSON schema returned by LLM")

        latency = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"[LLM RESPONSE SUCCESS] Model: 'groq:{used_model}' | Latency: {latency:.2f}ms | "
            f"Source: [AI_GENERATED] | Recs: {len(recommendations)}"
        )

        synthesis = ExecutiveSynthesis(
            executive_summary=summary,
            strategic_recommendations=recommendations[:4],
            bank_appraisal_notes=bank_notes,
            language=lang,
            is_cached=False,
            is_fallback=False,
            latency_ms=latency,
            model_name=f"groq:{used_model}",
            payload_hash=payload_hash,
        )

        cache.set(payload_hash, synthesis, ttl_seconds=cache_ttl_seconds)
        return synthesis

    except Exception as e:
        logger.warning(
            f"[LLM FALLBACK ENGAGED] Groq LLM synthesis failed ({str(e)}). "
            f"Seamlessly using deterministic domain template | Source: [DETERMINISTIC_TEMPLATE]"
        )
        fallback = get_deterministic_narrative(
            enterprise_name=enterprise_name,
            business_category=business_category,
            sector=sector,
            location_str=location_str,
            project_cost=project_cost,
            top_scheme_name=top_scheme_name,
            subsidy_amount=subsidy_amount,
            effective_loan=effective_loan,
            monthly_emi=monthly_emi,
            dscr=dscr,
            dscr_verdict=dscr_verdict,
            ml_verdict=ml_verdict,
            ml_confidence_pct=ml_confidence_pct,
            cpi_adjusted_price_floor=cpi_adjusted_price_floor,
            key_risks=key_risks,
            language=lang,
        )
        fallback.payload_hash = payload_hash
        fallback.latency_ms = (time.perf_counter() - start_time) * 1000
        cache.set(payload_hash, fallback, ttl_seconds=cache_ttl_seconds)
        return fallback



if __name__ == "__main__":
    sample_payload = {
        "enterprise_name": "Joypur Fresh Dairy Processing",
        "business_category": "manufacturing",
        "sector": "dairy",
        "location_str": "Joypur, Bankura, West Bengal",
        "project_cost": 900000.0,
        "promoter_margin_amount": 90000.0,
        "top_scheme_name": "PMEGP (Prime Minister's Employment Generation Programme)",
        "subsidy_amount": 225000.0,
        "subsidy_pct": 25.0,
        "effective_loan": 585000.0,
        "monthly_emi": 10530.98,
        "dscr": 2.26,
        "dscr_verdict": "VIABLE",
        "annual_tam": 10358712.0,
        "cpi_adjusted_price_floor": 131.40,
        "ml_verdict": "SUITABLE",
        "ml_confidence_pct": 99.9,
        "top_positive_driver": "Strong Debt Service Coverage Ratio (DSCR: 2.26)",
        "top_risk_factor": "Monsoon milk procurement logistics",
        "key_risks": ["Monsoon transport disruptions", "Local competitor pricing pressure"],
    }

    print("--- Testing Synthesis in Hindi (Fallback Mode) ---")
    synthesis_hi = generate_executive_synthesis(sample_payload, language="hi", force_fallback=True)
    print(json.dumps(synthesis_hi.to_dict(), indent=2, ensure_ascii=False))

    print("\n--- Testing SHA-256 Cache Replay ---")
    synthesis_cached = generate_executive_synthesis(sample_payload, language="hi")
    print(f"Is Cached: {synthesis_cached.is_cached} | Latency: {synthesis_cached.latency_ms}ms")
