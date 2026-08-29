"""
translation_service.py — Enterprise Google Cloud Translation Engine & Multilingual Synthesis Agent.
Supports Google Cloud Translation API (v2/v3), Service Account auth, API Key REST fallback,
high-speed persistent caching, and deterministic institutional domain dictionary fallback.
"""

from __future__ import annotations
import os
import json
import logging
import hashlib
import sqlite3
from typing import Optional, Any, Union, Dict, List
from pathlib import Path

import httpx

try:
    from app.config import settings
except ImportError:
    from backend.app.config import settings

logger = logging.getLogger("udyam_saathi.translation")

# Supported Indian Languages + English
SUPPORTED_LANGUAGES = {
    "en": {"code": "en", "name": "English", "native": "English"},
    "hi": {"code": "hi", "name": "Hindi", "native": "हिन्दी"},
    "mr": {"code": "mr", "name": "Marathi", "native": "मराठी"},
    "ta": {"code": "ta", "name": "Tamil", "native": "தமிழ்"},
    "te": {"code": "te", "name": "Telugu", "native": "తెలుగు"},
    "kn": {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ"},
}

# Institutional Banking & Credit Domain Dictionary
CORE_DOMAIN_TERMS: dict[str, dict[str, str]] = {
    "dashboard": {"en": "Dashboard", "hi": "डैशबोर्ड", "mr": "डॅशबोर्ड", "ta": "டாஷ்போர்டு", "te": "డ్యాష్‌బోర్డ్", "kn": "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್"},
    "overview": {"en": "Overview & Synthesis", "hi": "अवलोकन और सार", "mr": "आढावा आणि सारांश", "ta": "கண்ணோட்டம் மற்றும் சுருக்கம்", "te": "అవలోకనం మరియు సారాంశం", "kn": "ಅವಲೋಕನ ಮತ್ತು ಸಾರಾಂಶ"},
    "viability": {"en": "ML Viability", "hi": "एमएल व्यवहार्यता", "mr": "एमएल व्यवहार्यता", "ta": "ML செயல்திறன்", "te": "ML సాధ్యత", "kn": "ML ಕಾರ್ಯಸಾಧ್ಯತೆ"},
    "market": {"en": "Market & Demand", "hi": "बाज़ार और मांग", "mr": "बाजार आणि मागणी", "ta": "சந்தை மற்றும் தேவை", "te": "మార్కెట్ మరియు డిమాండ్", "kn": "ಮಾರುಕಟ್ಟೆ ಮತ್ತು ಬೇಡಿಕೆ"},
    "schemes": {"en": "Government Schemes", "hi": "सरकारी योजनाएँ", "mr": "सरकारी योजना", "ta": "அரசுத் திட்டங்கள்", "te": "ప్రభుత్వ పథకాలు", "kn": "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು"},
    "financials": {"en": "Financials & Cash Flow", "hi": "वित्त और नकदी प्रवाह", "mr": "आर्थिक व रोख प्रवाह", "ta": "நிதி மற்றும் பணப்புழக்கம்", "te": "ఆర్థికాలు మరియు నగదు ప్రవాహం", "kn": "ಹಣಕಾಸು ಮತ್ತು ನಗದು ಹರಿವು"},
    "risk": {"en": "Risk Assessment", "hi": "जोखिम मूल्यांकन", "mr": "जोखीम मूल्यांकन", "ta": "இடர் மதிப்பீடு", "te": "ప్రమాద అంచనా", "kn": "ಅಪಾಯ ಮೌಲ್ಯಮಾಪನ"},
    "swot": {"en": "SWOT Analysis", "hi": "SWOT विश्लेषण", "mr": "SWOT विश्लेषण", "ta": "SWOT பகுப்பாய்வு", "te": "SWOT విశ్లేషణ", "kn": "SWOT ವಿಶ್ಲೇಷಣೆ"},
    "dpr": {"en": "Bank DPR & Documents", "hi": "बैंक डीपीआर और दस्तावेज़", "mr": "बँक डीपीआर आणि दस्तऐवज", "ta": "வங்கி DPR ஆவணங்கள்", "te": "బ్యాంక్ DPR పత్రాలు", "kn": "ಬ್ಯಾಂಕ್ DPR ದಾಖಲೆಗಳು"},
    "calculator": {"en": "Loan Calculator", "hi": "ऋण कैलकुलेटर", "mr": "कर्ज गणक", "ta": "கடன் கணிப்பான்", "te": "రుణ కాలిక్యులేటర్", "kn": "ಸಾಲದ ಕ್ಯಾಲ್ಕುಲೇಟರ್"},
    "dataSources": {"en": "Data Sources", "hi": "डेटा स्रोत", "mr": "डेटा स्रोत", "ta": "தரவு ஆதாரங்கள்", "te": "డేటా మూలాలు", "kn": "ಡೇಟಾ ಮೂಲಗಳು"},
    "newEnterprise": {"en": "New Enterprise", "hi": "नया उद्यम", "mr": "नवीन उद्योग", "ta": "புதிய நிறுவனம்", "te": "కొత్త సంస్థ", "kn": "ಹೊಸ ಉದ್ಯಮ"},
    "logout": {"en": "Logout", "hi": "लॉग आउट", "mr": "लॉग आउट", "ta": "வெளியேறு", "te": "లాగ్ అవుట్", "kn": "ಲಾಗ್ ಔಟ್"},
    "login": {"en": "Login", "hi": "लॉग इन", "mr": "लॉग इन", "ta": "உள்நுழை", "te": "లాగ్ ఇన్", "kn": "ಲಾಗ್ ಇನ್"},
    "register": {"en": "Register", "hi": "पंजीकरण", "mr": "नोंदणी", "ta": "பதிவு", "te": "నమోదు", "kn": "ನೋಂದಣಿ"},
    "language": {"en": "Language", "hi": "भाषा", "mr": "भाषा", "ta": "மொழி", "te": "భాష", "kn": "ಭಾಷೆ"},
    "yourEnterprises": {"en": "Your Enterprises", "hi": "आपके उद्यम", "mr": "तुमचे उद्योग", "ta": "உங்கள் நிறுவனங்கள்", "te": "మీ సంస్థలు", "kn": "ನಿಮ್ಮ ಉದ್ಯಮಗಳು"},
    "activeEnterprise": {"en": "Active Enterprise", "hi": "सक्रिय उद्यम", "mr": "सक्रिय उद्योग", "ta": "செயலில் உள்ள நிறுவனம்", "te": "క్రియాశీల సంస్థ", "kn": "ಸಕ್ರಿಯ ಉದ್ಯಮ"},
    "createEnterprise": {"en": "Create & Analyze New Enterprise", "hi": "नया उद्यम बनाएँ और विश्लेषण करें", "mr": "नवीन उद्योग तयार करा व विश्लेषण करा", "ta": "புதிய நிறுவனத்தை உருவாக்கி பகுப்பாய்வு செய்க", "te": "కొత్త సంస్థను సృష్టించి విశ్లేషించండి", "kn": "ಹೊಸ ಉದ್ಯಮವನ್ನು ರಚಿಸಿ ಮತ್ತು ವಿಶ್ಲೇಷಿಸಿ"},
    "createAccount": {"en": "Create Entrepreneur Account", "hi": "उद्यमी खाता बनाएँ", "mr": "उद्योजक खाते तयार करा", "ta": "தொழில்முனைவோர் கணக்கை உருவாக்கவும்", "te": "వ్యవస్థాపక ఖాతాను సృష్టించండి", "kn": "ಉದ್ಯಮಿ ಖಾತೆ ರಚಿಸಿ"},
    "signIn": {"en": "Sign In", "hi": "लॉग इन", "mr": "लॉग इन", "ta": "உள்நுழை", "te": "లాగ్ ఇన్", "kn": "ಲಾಗ್ ಇನ್"},
    "appraisalLanguage": {"en": "Credit Appraisal Language", "hi": "क्रेडिट मूल्यांकन भाषा", "mr": "पत मूल्यांकन भाषा", "ta": "கடன் மதிப்பீட்டு மொழி", "te": "క్రెడిట్ మదింపు భాష", "kn": "ಸಾಲ ಮೌಲ್ಯಮಾಪನ ಭಾಷೆ"},
}


class TranslationService:
    """
    Singleton translation agent coordinating:
    1. Google Cloud Translation API via service credentials
    2. Google Cloud Translation REST API fallback
    3. SQLite Persistent Caching layer
    4. Deterministic Institutional Multi-Lingual Fallback
    """
    _instance: Optional[TranslationService] = None

    def __init__(self):
        self._memory_cache: dict[str, str] = {}
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        self._gcp_client = None
        self._init_sqlite_cache()
        self._init_gcp_client()

    @classmethod
    def get_instance(cls) -> TranslationService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_sqlite_cache(self):
        """Initializes a durable SQLite translation cache table."""
        try:
            cache_path = Path(__file__).resolve().parent.parent / "data" / "translation_cache.sqlite3"
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._sqlite_conn = sqlite3.connect(str(cache_path), check_same_thread=False)
            self._sqlite_conn.execute("""
                CREATE TABLE IF NOT EXISTS translation_cache (
                    cache_key TEXT PRIMARY KEY,
                    source_lang TEXT,
                    target_lang TEXT,
                    source_text TEXT,
                    translated_text TEXT,
                    provider TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self._sqlite_conn.execute("CREATE INDEX IF NOT EXISTS idx_target_lang ON translation_cache(target_lang);")
            self._sqlite_conn.commit()
            logger.info("✅ Persistent Translation Cache Initialized at %s", cache_path)
        except Exception as e:
            logger.warning("Could not initialize SQLite translation cache: %s", e)

    def _init_gcp_client(self):
        """Initializes the official Google Cloud Translation SDK client if credentials exist."""
        try:
            from google.cloud import translate_v2 as translate
            # Check for candidate service account credentials
            path_str = getattr(settings, "FIREBASE_SERVICE_ACCOUNT_PATH", None) or os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "serviceAccountKey.json"
            raw_path = Path(path_str) if path_str else None
            candidates = [
                raw_path,
                Path.cwd() / raw_path if raw_path else None,
                Path(__file__).resolve().parent.parent.parent.parent / "serviceAccountKey.json",
                Path(__file__).resolve().parent.parent.parent / "serviceAccountKey.json",
                Path.cwd() / "serviceAccountKey.json",
            ]
            cred_file = None
            for c in candidates:
                if c and c.exists() and c.is_file():
                    cred_file = str(c.resolve())
                    break

            if cred_file:
                self._gcp_client = translate.Client.from_service_account_json(cred_file)
                logger.info("🌐 Google Cloud Translation SDK Client initialized with: %s", cred_file)
            else:
                api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
                if api_key:
                    self._gcp_client = translate.Client(api_key=api_key)
                    logger.info("🌐 Google Cloud Translation SDK Client initialized with API Key.")
        except Exception as e:
            logger.info("ℹ️ Google Cloud Translation SDK deferred to REST / Fallback mode: %s", e)

    def _cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        h = hashlib.sha256(f"{source_lang}:{target_lang}:{text.strip()}".encode("utf-8")).hexdigest()
        return h

    def _get_cached_translation(self, cache_key: str) -> Optional[str]:
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]
        if self._sqlite_conn:
            try:
                cur = self._sqlite_conn.cursor()
                row = cur.execute("SELECT translated_text FROM translation_cache WHERE cache_key = ?", (cache_key,)).fetchone()
                if row and row[0]:
                    self._memory_cache[cache_key] = row[0]
                    return row[0]
            except Exception:
                pass
        return None

    def _save_cached_translation(self, cache_key: str, source_lang: str, target_lang: str, source_text: str, translated_text: str, provider: str):
        self._memory_cache[cache_key] = translated_text
        if self._sqlite_conn:
            try:
                self._sqlite_conn.execute(
                    "INSERT OR REPLACE INTO translation_cache (cache_key, source_lang, target_lang, source_text, translated_text, provider) VALUES (?, ?, ?, ?, ?, ?)",
                    (cache_key, source_lang, target_lang, source_text, translated_text, provider)
                )
                self._sqlite_conn.commit()
            except Exception as e:
                logger.warning("Could not write translation to SQLite cache: %s", e)

    async def translate_text(
        self,
        text: str,
        target_language: str = "hi",
        source_language: str = "en",
        format_type: str = "text",
    ) -> dict[str, Any]:
        """
        Translates a single text string into target Indian language.
        Returns dict with: translated_text, source_language, target_language, provider.
        """
        if not text or not text.strip():
            return {
                "translated_text": text,
                "source_language": source_language,
                "target_language": target_language,
                "provider": "noop"
            }

        target_lang = target_language.lower().strip()
        src_lang = source_language.lower().strip() if source_language else "en"

        # Identity return
        if target_lang == src_lang:
            return {
                "translated_text": text,
                "source_language": src_lang,
                "target_language": target_lang,
                "provider": "identity"
            }

        clean_text = text.strip()
        ckey = self._cache_key(clean_text, src_lang, target_lang)

        # 1. Check Cache
        cached = self._get_cached_translation(ckey)
        if cached:
            return {
                "translated_text": cached,
                "source_language": src_lang,
                "target_language": target_lang,
                "provider": "cache"
            }

        # 2. Check Static Domain Dictionary for single term lookups
        lookup_key = clean_text.lower()
        if lookup_key in CORE_DOMAIN_TERMS and target_lang in CORE_DOMAIN_TERMS[lookup_key]:
            dict_translation = CORE_DOMAIN_TERMS[lookup_key][target_lang]
            self._save_cached_translation(ckey, src_lang, target_lang, clean_text, dict_translation, "domain_dictionary")
            return {
                "translated_text": dict_translation,
                "source_language": src_lang,
                "target_language": target_lang,
                "provider": "domain_dictionary"
            }

        # 3. Try Google Cloud Translation SDK
        if self._gcp_client:
            try:
                result = self._gcp_client.translate(
                    clean_text,
                    target_language=target_lang,
                    source_language=src_lang if src_lang != "auto" else None,
                    format_=format_type,
                )
                translated_str = result.get("translatedText", clean_text)
                detected_src = result.get("detectedSourceLanguage", src_lang)
                self._save_cached_translation(ckey, detected_src, target_lang, clean_text, translated_str, "google_cloud_sdk")
                return {
                    "translated_text": translated_str,
                    "source_language": detected_src,
                    "target_language": target_lang,
                    "provider": "google_cloud_sdk"
                }
            except Exception as gcp_err:
                logger.warning("Google Cloud Translation SDK call failed (%s); trying REST fallback.", gcp_err)

        # 4. Try Google Cloud Translation REST API (v2)
        api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
        if api_key:
            try:
                url = "https://translation.googleapis.com/language/translate/v2"
                payload = {
                    "q": clean_text,
                    "target": target_lang,
                    "source": src_lang if src_lang != "auto" else None,
                    "format": format_type,
                    "key": api_key,
                }
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        translations = data.get("data", {}).get("translations", [])
                        if translations:
                            translated_str = translations[0].get("translatedText", clean_text)
                            detected_src = translations[0].get("detectedSourceLanguage", src_lang)
                            self._save_cached_translation(ckey, detected_src, target_lang, clean_text, translated_str, "google_cloud_rest")
                            return {
                                "translated_text": translated_str,
                                "source_language": detected_src,
                                "target_language": target_lang,
                                "provider": "google_cloud_rest"
                            }
            except Exception as rest_err:
                logger.warning("Google Cloud Translation REST API failed: %s", rest_err)

        # 5. Deterministic AI / Dictionary Fallback
        fallback_str = self._apply_domain_substitutions(clean_text, target_lang)
        self._save_cached_translation(ckey, src_lang, target_lang, clean_text, fallback_str, "deterministic_fallback")
        return {
            "translated_text": fallback_str,
            "source_language": src_lang,
            "target_language": target_lang,
            "provider": "deterministic_fallback"
        }

    async def translate_batch(
        self,
        texts: list[str],
        target_language: str = "hi",
        source_language: str = "en",
    ) -> list[dict[str, Any]]:
        """Batch translation for arrays of strings."""
        results = []
        for t in texts:
            res = await self.translate_text(t, target_language=target_language, source_language=source_language)
            results.append(res)
        return results

    async def translate_dictionary(
        self,
        data_dict: dict[str, str],
        target_language: str = "hi",
        source_language: str = "en",
    ) -> dict[str, str]:
        """Translates all string values in a dictionary."""
        translated = {}
        for k, v in data_dict.items():
            if isinstance(v, str):
                res = await self.translate_text(v, target_language=target_language, source_language=source_language)
                translated[k] = res["translated_text"]
            else:
                translated[k] = v
        return translated

    def _apply_domain_substitutions(self, text: str, target_lang: str) -> str:
        """Applies high-accuracy Indian language institutional banking substitutions."""
        res = text
        for term, translations in CORE_DOMAIN_TERMS.items():
            if target_lang in translations and translations["en"] in res:
                res = res.replace(translations["en"], translations[target_lang])
        return res


# Global singleton
translation_service = TranslationService.get_instance()
