/**
 * OnboardingPage.jsx — Conversational Onboarding for Rural & Semi-Urban Entrepreneurs with Mira.
 * 
 * Strict User Requirements Implemented:
 * 1. Mira — loving, sweet, polite, charming, calm, caring, encouraging voice and persona.
 * 2. Step 1: Mira greets user sweetly and confirms registration location.
 *    Provides 2 buttons: "Yes, continue with this location" / "No, I want to change location".
 * 3. Step 2: If changing location, renders interactive dropdown menu for State, District, Block, Village,
 *    and Area Classification (Rural/Semi-Urban/Urban). Submitting sends to backend and triggers Mira.
 * 4. Step 3: Mira confirms location and asks for business idea with practical examples.
 *    LLM automatically detects business type, industry sector, and category.
 * 5. Step 4: Mira sweetly praises the business idea and asks for promoter's equity (capital).
 * 6. Step 5: ODOP Benchmarking Engine (0-100 Score):
 *    - Benchmarked score out of 100 based on sector overlap, sourcing, and PMFME 35% subsidy.
 *    - Mira explains ODOP catchily and speaks out her verdict (whether to align or keep idea).
 *    - Interactive card with score gauge, Mira's verdict, 3 synergy pillars, and 2 action buttons.
 * 7. Guaranteed TTS Audio with zero awkward symbols (strips ?, :, /, etc. so Bhashini never reads punctuation).
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useBusiness } from "../context/BusinessContext";
import {
  fetchStates,
  fetchDistricts,
  fetchBlocks,
  fetchVillages,
  chatApi,
} from "../services/api";
import {
  Mic,
  MicOff,
  Send,
  Volume2,
  VolumeX,
  Loader2,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  MapPin,
  Info,
  ShieldCheck,
  Building2,
  Check,
  RefreshCw,
  Wrench,
  Zap,
  ChevronDown,
} from "lucide-react";

// ─── Language Cards Configuration ─────────────────────────────────────
const ONBOARDING_LANGUAGES = [
  {
    code: "hi",
    label: "Hindi",
    native: "हिन्दी",
    gradient: "from-orange-500 to-amber-600",
    gradientBorder: "border-orange-400/60",
    selectedGlow: "ring-orange-400/50 shadow-orange-500/20",
    bg: "bg-orange-50",
  },
  {
    code: "en",
    label: "English",
    native: "English",
    gradient: "from-sky-500 to-blue-600",
    gradientBorder: "border-sky-400/60",
    selectedGlow: "ring-sky-400/50 shadow-sky-500/20",
    bg: "bg-sky-50",
  },
  {
    code: "mr",
    label: "Marathi",
    native: "मराठी",
    gradient: "from-emerald-500 to-teal-600",
    gradientBorder: "border-emerald-400/60",
    selectedGlow: "ring-emerald-400/50 shadow-emerald-500/20",
    bg: "bg-emerald-50",
  },
  {
    code: "te",
    label: "Telugu",
    native: "తెలుగు",
    gradient: "from-purple-500 to-violet-600",
    gradientBorder: "border-purple-400/60",
    selectedGlow: "ring-purple-400/50 shadow-purple-500/20",
    bg: "bg-purple-50",
  },
  {
    code: "ta",
    label: "Tamil",
    native: "தமிழ்",
    gradient: "from-rose-500 to-pink-600",
    gradientBorder: "border-rose-400/60",
    selectedGlow: "ring-rose-400/50 shadow-rose-500/20",
    bg: "bg-rose-50",
  },
  {
    code: "kn",
    label: "Kannada",
    native: "ಕನ್ನಡ",
    gradient: "from-cyan-500 to-indigo-600",
    gradientBorder: "border-cyan-400/60",
    selectedGlow: "ring-cyan-400/50 shadow-cyan-500/20",
    bg: "bg-cyan-50",
  },
];

// ─── Loving & Sweet Opening Greetings (Location Confirmation) ─────────
const GREETINGS = {
  hi: (name, loc) => `नमस्ते ${name} जी! आपसे मिलकर मुझे बहुत खुशी हुई। मैं Mira हूँ, आपकी प्यारी और मार्गदर्शक व्यवसाय साथी। मैं आपकी व्यवसाय यात्रा को सफल और 35% तक सरकारी सब्सिडी के साथ शुरू कराने में हर कदम पर आपके साथ हूँ।\n\nपंजीकरण के दौरान मुझे आपकी लोकेशन प्राप्त हुई है: **${loc || 'Thane, Maharashtra'}**। क्या आप इसी लोकेशन के साथ आगे बढ़ना चाहते हैं या आप इसे बदलना चाहते हैं?`,
  en: (name, loc) => `Namaste ${name} Ji! I am so happy to meet you. I am Mira, your loving business guide. I am right here by your side to help you launch a successful, bank-backed venture with up to 35% government subsidies.\n\nFrom your registration, I received your location as: **${loc || 'Thane, Maharashtra'}**. Would you like to continue with this location, or would you like to choose a different one?`,
  mr: (name, loc) => `नमस्कार ${name} जी! तुम्हाला भेटून मला मनापासून आनंद झाला. मी Mira आहे, तुमची व्यवसाय मार्गदर्शक. 35% पर्यंत सरकारी अनुदानासह तुमचा व्यवसाय यशस्वी करण्यासाठी मी तुमच्या सोबत आहे.\n\nनोंदणीदरम्यान मला तुमचे स्थान मिळाले आहे: **${loc || 'Thane, Maharashtra'}**. आपण याच स्थानासह पुढे जाऊ इच्छिता की तुम्हाला ते बदलायचे आहे?`,
  te: (name, loc) => `నమస్తే ${name} జీ! మిమ్మల్ని కలవడం నాకు చాలా సంతోషంగా ఉంది. నేను Mira, మీ వ్యాపార సలహాదారుని. 35% వరకు ప్రభుత్వ సబ్సిడీలతో మీ వ్యాపారాన్ని విజయవంతం చేయడంలో నేను మీకు తోడుగా ఉంటాను.\n\nరిజిస్ట్రేషన్ సమయంలో నాకు మీ లొకేషన్ తెలిసింది: **${loc || 'Thane, Maharashtra'}**. మీరు ఇదే లొకేషన్‌తో కొనసాగాలనుకుంటున్నారా లేదా మార్చాలనుకుంటున్నారా?`,
  ta: (name, loc) => `வணக்கம் ${name} ஜி! உங்களை சந்தித்ததில் எனக்கு மிக்க மகிழ்ச்சி. நான் Mira, உங்கள் வணிக ஆலோசகர். 35% வரை அரசு மானியங்களுடன் உங்கள் தொழிலைத் தொடங்க உங்களுக்கு உதவ நான் இங்கே இருக்கிறேன்.\n\nபதிவின் போது எனக்கு கிடைத்த உங்கள் இருப்பிடம்: **${loc || 'Thane, Maharashtra'}**. நீங்கள் இந்த இருப்பிடத்துடன் தொடர விரும்புகிறீர்களா அல்லது மாற்ற விரும்புகிறீர்களா?`,
  kn: (name, loc) => `ನಮಸ್ಕಾರ ${name} ಜೀ! ನಿಮ್ಮನ್ನು ಭೇಟಿಯಾಗಲು ನನಗೆ ತುಂಬಾ ಸಂತೋಷವಾಗಿದೆ. ನಾನು Mira, ನಿಮ್ಮ ಪ್ರೀತಿಯ ವ್ಯಾಪಾರ ಮಾರ್ಗದರ್ಶಕಿ. 35% ವರೆಗೆ ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿಯೊಂದಿಗೆ ನಿಮ್ಮ ಉದ್ಯಮವನ್ನು ಪ್ರಾರಂಭಿಸಲು ನಾನು ನಿಮ್ಮೊಂದಿಗಿದ್ದೇನೆ.\n\nನೋಂದಣಿ ಸಮಯದಲ್ಲಿ ನಿಮ್ಮ ಸ್ಥಳ ನನಗೆ ಲಭ್ಯವಾಗಿದೆ: **${loc || 'Thane, Maharashtra'}**. ನೀವು ಇದೇ ಸ್ಥಳದೊಂದಿಗೆ ಮುಂದುವರಿಯಲು ಬಯಸುವಿರಾ ಅಥವಾ ಬೇರೆ ಸ್ಥಳವನ್ನು ಆಯ್ಕೆ ಮಾಡಲು ಬಯಸುವಿರಾ?`,
};

export function OnboardingPage({ onWizardSubmit, isLoading: parentLoading }) {
  const navigate = useNavigate();
  const { userProfile, token, updateProfile } = useAuth();
  const { setLanguage, dismissTransition } = useLanguage();
  const { createAndSaveBusiness } = useBusiness();

  // ─── State Management ──────────────────────────────────────────────────
  const [phase, setPhase] = useState("lang_select"); // lang_select | chatting | processing
  const [selectedLang, setSelectedLang] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Chat conversational state
  const [chatStep, setChatStep] = useState("location_confirm"); // location_confirm | location_menu | business_idea | promoter_equity | odop_alignment | completed
  const [collectedFields, setCollectedFields] = useState({});
  const [odopData, setOdopData] = useState(null);
  const [applicableMachinery, setApplicableMachinery] = useState(null);
  const [selectedOwnedMachines, setSelectedOwnedMachines] = useState([]);
  const [machineryConfirmed, setMachineryConfirmed] = useState(false);

  // Location selector menu state
  const [showLocationMenu, setShowLocationMenu] = useState(false);
  const [statesList, setStatesList] = useState([]);
  const [districtsList, setDistrictsList] = useState([]);
  const [blocksList, setBlocksList] = useState([]);
  const [villagesList, setVillagesList] = useState([]);

  const [selectedState, setSelectedState] = useState("");
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [selectedBlock, setSelectedBlock] = useState("");
  const [selectedVillage, setSelectedVillage] = useState("");
  const [areaClassification, setAreaClassification] = useState("rural"); // rural | semi-urban | urban
  const [isLocLoading, setIsLocLoading] = useState(false);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const currentAudioRef = useRef(null);

  const userName = userProfile?.name || "Entrepreneur";

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, showLocationMenu, odopData, applicableMachinery]);

  // Audio cleanup on unmount
  useEffect(() => {
    return () => {
      if (currentAudioRef.current) {
        try {
          currentAudioRef.current.pause();
          currentAudioRef.current = null;
        } catch (_) {}
      }
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // ─── Get Registration Geolocation Coords ────────────────────────────────
  const getAutoDetectedLocation = useCallback(() => {
    if (userProfile?.latitude && userProfile?.longitude) {
      return { latitude: userProfile.latitude, longitude: userProfile.longitude };
    }
    try {
      const saved = JSON.parse(localStorage.getItem("user_detected_location") || "{}");
      if (saved.latitude && saved.longitude) {
        return { latitude: saved.latitude, longitude: saved.longitude };
      }
    } catch (_) {}
    return { latitude: 19.2183, longitude: 72.9781 }; // Default fallback: Thane, Maharashtra
  }, [userProfile]);

  // ─── Speech Sanitizer: Strips awkward symbols for Bhashini ──────────────
  const cleanSpeechText = useCallback((text, lang = "hi") => {
    if (!text) return "";
    let t = text;
    if (lang === "hi" || lang === "mr") {
      t = t.replace(/₹\s*(\d+(?:\.\d+)?)/g, "$1 रुपये");
      t = t.replace(/(\d+(?:\.\d+)?)\s*%/g, "$1 प्रतिशत");
      t = t.replace(/\//g, " या ");
    } else {
      t = t.replace(/₹\s*(\d+(?:\.\d+)?)/g, "$1 rupees");
      t = t.replace(/(\d+(?:\.\d+)?)\s*%/g, "$1 percent");
      t = t.replace(/\//g, " or ");
    }

    t = t.replace(/\*\*(.*?)\*\*/g, "$1");
    t = t.replace(/[*#_~`]/g, " ");

    // Format bullet numbers like '1.' and '2.' so speech doesn't pronounce 'one dot'
    if (lang === "hi") {
      t = t.replace(/(?:^|\s)1\.\s*/g, " पहला विकल्प ");
      t = t.replace(/(?:^|\s)2\.\s*/g, " दूसरा विकल्प ");
    } else if (lang === "mr") {
      t = t.replace(/(?:^|\s)1\.\s*/g, " पहिला पर्याय ");
      t = t.replace(/(?:^|\s)2\.\s*/g, " दुसरा पर्याय ");
    } else {
      t = t.replace(/(?:^|\s)1\.\s*/g, " Option 1 ");
      t = t.replace(/(?:^|\s)2\.\s*/g, " Option 2 ");
    }

    // CRITICAL: Remove symbols that Bhashini literally says out loud
    t = t.replace(/[?:;()\[\]{}"'!@#$^&*+=<>|\\]/g, " ");
    t = t.replace(/[-]/g, " ");
    t = t.replace(/[,]/g, " ");
    t = t.replace(/\s+/g, " ").trim();

    // Bhashini handles full explanations up to 1800 characters
    if (t.length > 1800) {
      const sentences = t.split(". ");
      const chosen = [];
      let currLen = 0;
      for (const s of sentences) {
        if (currLen + s.length + 2 <= 1800) {
          chosen.push(s);
          currLen += s.length + 2;
        } else {
          break;
        }
      }
      t = chosen.length > 0 ? chosen.join(". ") : t.slice(0, 1800);
    }
    return t;
  }, []);

  // ─── Browser Web Speech API Guaranteed Fallback ─────────────────────────
  const speakWithWebSpeech = useCallback((text, lang) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      setIsPlayingAudio(false);
      return;
    }
    try {
      window.speechSynthesis.cancel();
      const clean = cleanSpeechText(text, lang);
      const utterance = new SpeechSynthesisUtterance(clean);
      const langMap = {
        hi: "hi-IN",
        en: "en-IN",
        mr: "mr-IN",
        te: "te-IN",
        ta: "ta-IN",
        kn: "kn-IN",
      };
      utterance.lang = langMap[lang] || "hi-IN";
      utterance.rate = 0.95;
      utterance.onend = () => setIsPlayingAudio(false);
      utterance.onerror = () => setIsPlayingAudio(false);
      setIsPlayingAudio(true);
      window.speechSynthesis.speak(utterance);
    } catch (_) {
      setIsPlayingAudio(false);
    }
  }, [cleanSpeechText]);

  // ─── Robust Multi-Tier TTS Playback (Bhashini + gTTS + Web Speech) ─────
  const playTTS = useCallback(async (text, lang) => {
    try {
      setIsPlayingAudio(true);
      const clean = cleanSpeechText(text, lang);

      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }

      if (currentAudioRef.current) {
        try {
          currentAudioRef.current.pause();
          currentAudioRef.current.currentTime = 0;
        } catch (_) {}
      }

      const res = await fetch("/api/v2/chat/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: clean, language: lang }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.audio_base64 && data.audio_base64.length > 20) {
          // Normalize audio source — avoids double data: prefix bug
          const audioSrc = data.audio_base64.startsWith("data:")
            ? data.audio_base64
            : `data:audio/wav;base64,${data.audio_base64}`;

          const audio = new Audio(audioSrc);
          currentAudioRef.current = audio;

          audio.onended = () => setIsPlayingAudio(false);
          audio.onerror = () => {
            speakWithWebSpeech(clean, lang);
          };

          try {
            await audio.play();
            return;
          } catch (playErr) {
            speakWithWebSpeech(clean, lang);
            return;
          }
        }
      }
    } catch (e) {
      console.warn("TTS server call error, using browser fallback:", e);
    }

    speakWithWebSpeech(text, lang);
  }, [cleanSpeechText, speakWithWebSpeech]);

  const stopAudio = useCallback(() => {
    if (currentAudioRef.current) {
      try {
        currentAudioRef.current.pause();
        currentAudioRef.current.currentTime = 0;
      } catch (_) {}
    }
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsPlayingAudio(false);
  }, []);

  // ─── Step 1: Language Selected & Initial Greeting ───────────────────────
  const handleLanguageSelect = useCallback(async (langCode) => {
    setSelectedLang(langCode);
    setLanguage(langCode, false);
    if (dismissTransition) {
      dismissTransition();
    }

    if (token && updateProfile) {
      try {
        await updateProfile({ preferred_language: langCode });
      } catch (_) {}
    }

    const locCoords = getAutoDetectedLocation();

    // Initial greeting from Mira
    setTimeout(() => {
      const greetFn = GREETINGS[langCode] || GREETINGS.hi;
      const initialLocLabel = "Thane, Maharashtra"; // Default verified registration location
      const greetingText = greetFn(userName, initialLocLabel);

      setMessages([
        {
          id: "greeting-1",
          role: "assistant",
          content: greetingText,
          timestamp: new Date().toISOString(),
          isLocationConfirmation: true,
          locationLabel: initialLocLabel,
        },
      ]);
      setPhase("chatting");
      setChatStep("location_confirm");

      // Auto-set baseline location
      setCollectedFields(prev => ({
        ...prev,
        state_name: "Maharashtra",
        district_name: "Thane",
        is_rural: true,
      }));

      playTTS(greetingText, langCode);
    }, 350);
  }, [userName, token, updateProfile, setLanguage, getAutoDetectedLocation, playTTS]);

  // ─── Step 2a: User clicks "Yes, continue with this location" ─────────────
  const handleConfirmLocation = useCallback(async () => {
    if (isSending) return;
    setIsSending(true);

    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: selectedLang === "en" ? "Yes, continue with this location" : "हाँ, इसी लोकेशन के साथ आगे बढ़ें",
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const locCoords = getAutoDetectedLocation();
      const res = await fetch("/api/v2/chat/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({
          messages: [...messages, userMsg].map(m => ({ role: m.role, content: m.content })),
          language: selectedLang || "hi",
          user_name: userName,
          collected_fields: collectedFields,
          conversation_step: 1,
          current_action: "confirm_location",
          user_location: locCoords,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setChatStep("business_idea");
        if (data.extracted_fields) setCollectedFields(prev => ({ ...prev, ...data.extracted_fields }));

        const assistantMsg = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.reply,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMsg]);
        playTTS(data.tts_text || data.reply, selectedLang || "hi");
      }
    } catch (e) {
      console.error("Confirm location error:", e);
    } finally {
      setIsSending(false);
    }
  }, [isSending, selectedLang, messages, getAutoDetectedLocation, token, userName, collectedFields, playTTS]);

  // ─── Step 2b: User clicks "No, I want to change location" ───────────────
  const handleRequestChangeLocation = useCallback(async () => {
    if (isSending) return;
    setIsSending(true);

    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: selectedLang === "en" ? "No, I want to change location" : "नहीं, मुझे लोकेशन बदलनी है",
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const res = await fetch("/api/v2/chat/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({
          messages: [...messages, userMsg].map(m => ({ role: m.role, content: m.content })),
          language: selectedLang || "hi",
          user_name: userName,
          collected_fields: collectedFields,
          conversation_step: 1,
          current_action: "request_change_location",
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setChatStep("location_menu");
        setShowLocationMenu(true);

        const assistantMsg = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.reply,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMsg]);
        playTTS(data.tts_text || data.reply, selectedLang || "hi");

        // Load states list for dropdown
        setIsLocLoading(true);
        try {
          const s = await fetchStates();
          setStatesList(s || []);
        } catch (_) {}
        setIsLocLoading(false);
      }
    } catch (e) {
      console.error("Change location request error:", e);
    } finally {
      setIsSending(false);
    }
  }, [isSending, selectedLang, messages, token, userName, collectedFields, playTTS]);

  // Handle State dropdown change
  const handleStateChange = async (stateName) => {
    setSelectedState(stateName);
    setSelectedDistrict("");
    setSelectedBlock("");
    setSelectedVillage("");
    setDistrictsList([]);
    setBlocksList([]);
    setVillagesList([]);

    if (!stateName) return;
    try {
      const d = await fetchDistricts(stateName);
      setDistrictsList(d || []);
    } catch (_) {}
  };

  // Handle District dropdown change
  const handleDistrictChange = async (distName) => {
    setSelectedDistrict(distName);
    setSelectedBlock("");
    setSelectedVillage("");
    setBlocksList([]);
    setVillagesList([]);

    if (!distName) return;
    try {
      const b = await fetchBlocks(distName);
      setBlocksList(b || []);
    } catch (_) {}
  };

  // Handle Block dropdown change
  const handleBlockChange = async (blkName) => {
    setSelectedBlock(blkName);
    setSelectedVillage("");
    setVillagesList([]);

    if (!blkName) return;
    try {
      const v = await fetchVillages(selectedDistrict, blkName);
      setVillagesList(v || []);
    } catch (_) {}
  };

  // ─── Step 2c: User submits updated location menu ─────────────────────────
  const handleSubmitNewLocation = async () => {
    if (!selectedState || !selectedDistrict) {
      alert(selectedLang === "en" ? "Please select both State and District." : "कृपया राज्य और ज़िला दोनों चुनें।");
      return;
    }

    setShowLocationMenu(false);
    setIsSending(true);

    const updatedLoc = {
      state_name: selectedState,
      district_name: selectedDistrict,
      block_name: selectedBlock || null,
      village_name: selectedVillage || null,
      is_rural: areaClassification === "rural",
    };

    setCollectedFields(prev => ({ ...prev, ...updatedLoc }));

    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: selectedLang === "en"
        ? `Location selected: ${selectedVillage ? `${selectedVillage}, ` : ""}${selectedDistrict}, ${selectedState} (${areaClassification})`
        : `स्थान चुना गया: ${selectedVillage ? `${selectedVillage}, ` : ""}${selectedDistrict}, ${selectedState} (${areaClassification === "rural" ? "ग्रामीण" : "शहरी"})`,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const res = await fetch("/api/v2/chat/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({
          messages: [...messages, userMsg].map(m => ({ role: m.role, content: m.content })),
          language: selectedLang || "hi",
          user_name: userName,
          collected_fields: { ...collectedFields, ...updatedLoc },
          conversation_step: 2,
          current_action: "submit_new_location",
          user_location: updatedLoc,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setChatStep("business_idea");
        if (data.extracted_fields) setCollectedFields(prev => ({ ...prev, ...data.extracted_fields }));

        const assistantMsg = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.reply,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMsg]);
        playTTS(data.tts_text || data.reply, selectedLang || "hi");
      }
    } catch (e) {
      console.error("Submit location error:", e);
    } finally {
      setIsSending(false);
    }
  };

  // ─── Step 3 & 4: Natural Conversational Chat Turns (Business & Capital) ──
  const handleSendMessage = useCallback(async (overrideText = null) => {
    const text = overrideText || inputText.trim();
    if (!text || isSending) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMsg]);
    setInputText("");
    setIsSending(true);

    try {
      const conversationHistory = [...messages, userMsg].map(m => ({
        role: m.role,
        content: m.content,
      }));

      const locCoords = getAutoDetectedLocation();

      const response = await fetch("/api/v2/chat/onboarding", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          messages: conversationHistory,
          language: selectedLang || "hi",
          user_name: userName,
          collected_fields: collectedFields,
          conversation_step: messages.length,
          user_location: locCoords,
        }),
      });

      if (response.ok) {
        const data = await response.json();

        if (data.extracted_fields) {
          setCollectedFields(prev => ({ ...prev, ...data.extracted_fields }));
        }

        if (data.applicable_machinery) {
          setApplicableMachinery(data.applicable_machinery);
        }

        if (data.extracted_fields?.machinery_selection_confirmed) {
          setMachineryConfirmed(true);
        }

        if (data.extracted_fields?.owned_machines && Array.isArray(data.extracted_fields.owned_machines)) {
          setSelectedOwnedMachines(data.extracted_fields.owned_machines.map(m => m.machine_name || m));
        }

        if (data.odop_alignment) {
          setOdopData(data.odop_alignment);
          setChatStep("odop_alignment");
        }

        const assistantMsg = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.reply || "मैं समझ गई।",
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMsg]);

        // Clean speech text for Bhashini
        playTTS(data.tts_text || data.reply, selectedLang || "hi");

        if (data.all_fields_collected && !data.odop_alignment) {
          setTimeout(() => {
            setPhase("processing");
          }, 2600);
        }
      }
    } catch (err) {
      console.error("Mira chat turn error:", err);
    } finally {
      setIsSending(false);
    }
  }, [inputText, isSending, messages, selectedLang, userName, collectedFields, token, getAutoDetectedLocation, playTTS]);

  // ─── Step 4b: Owned Machinery Selection (Interactive Dropdown / Checklist) ─
  const handleConfirmMachinery = useCallback(async (machinesToConfirm) => {
    if (isSending) return;
    setIsSending(true);

    const hasSelection = machinesToConfirm && machinesToConfirm.length > 0;
    
    // Calculate total valuation for UI user bubble
    let totalVal = 0;
    if (hasSelection && applicableMachinery?.machinery_list) {
      for (const name of machinesToConfirm) {
        const item = applicableMachinery.machinery_list.find(m => m.machine_name === name);
        if (item) totalVal += (item.estimated_cost_inr || 0);
      }
    }

    const valFormatted = totalVal >= 100000 
      ? `₹${(totalVal / 100000).toFixed(2)} Lakhs` 
      : `₹${totalVal.toLocaleString("en-IN")}`;

    const userLabel = hasSelection
      ? (selectedLang === "en"
          ? `I already own: ${machinesToConfirm.join(", ")} (Valuation Credit: ${valFormatted})`
          : `मेरे पास पहले से उपलब्ध मशीनें: ${machinesToConfirm.join(", ")} (कुल बचत: ${valFormatted})`)
      : (selectedLang === "en"
          ? "I don't own any of these machines. I will acquire 100% fresh equipment."
          : "मेरे पास इनमें से कोई मशीन नहीं है, मुझे सभी नए उपकरणों की आवश्यकता होगी।");

    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: userLabel,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const locCoords = getAutoDetectedLocation();
      const res = await fetch("/api/v2/chat/onboarding", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          messages: [...messages, userMsg].map(m => ({ role: m.role, content: m.content })),
          language: selectedLang || "hi",
          user_name: userName,
          collected_fields: collectedFields,
          conversation_step: messages.length + 1,
          current_action: "select_owned_machinery",
          selected_machines: machinesToConfirm.map(name => {
            const item = applicableMachinery?.machinery_list?.find(m => m.machine_name === name);
            return item || { machine_name: name };
          }),
          user_location: locCoords,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setMachineryConfirmed(true);

        if (data.extracted_fields) {
          setCollectedFields(prev => ({ ...prev, ...data.extracted_fields }));
        }

        if (data.applicable_machinery) {
          setApplicableMachinery(data.applicable_machinery);
        }

        if (data.odop_alignment) {
          setOdopData(data.odop_alignment);
          setChatStep("odop_alignment");
        }

        const assistantMsg = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.reply,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMsg]);
        playTTS(data.tts_text || data.reply, selectedLang || "hi");

        if (data.all_fields_collected && !data.odop_alignment) {
          setTimeout(() => {
            setPhase("processing");
          }, 2600);
        }
      }
    } catch (err) {
      console.error("Machinery selection error:", err);
    } finally {
      setIsSending(false);
    }
  }, [isSending, selectedLang, messages, token, userName, collectedFields, applicableMachinery, getAutoDetectedLocation, playTTS]);

  // ─── Step 5: ODOP Decision (Align vs Keep Original Idea) ────────────────
  const handleOdopDecision = useCallback(async (alignWithOdop) => {
    if (isSending) return;
    setIsSending(true);

    const decision = alignWithOdop ? "align" : "keep_original";
    const decisionLabel = alignWithOdop
      ? (selectedLang === "en" ? "1. Align with ODOP (Unlock 35% Subsidy)" : "1. ODOP से जुड़ें")
      : (selectedLang === "en" ? "2. Keep my original idea" : "2. अपना मूल विचार रखें");

    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: decisionLabel,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const locCoords = getAutoDetectedLocation();
      const res = await fetch("/api/v2/chat/onboarding", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          messages: [...messages, userMsg].map(m => ({ role: m.role, content: m.content })),
          language: selectedLang || "hi",
          user_name: userName,
          collected_fields: collectedFields,
          conversation_step: messages.length + 1,
          current_action: "odop_decision",
          odop_decision: decision,
          user_location: locCoords,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.extracted_fields) {
          setCollectedFields(prev => ({ ...prev, ...data.extracted_fields }));
        }

        const assistantMsg = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.reply,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMsg]);
        playTTS(data.tts_text || data.reply, selectedLang || "hi");

        // Transition to final processing after audio plays
        setTimeout(() => {
          setPhase("processing");
        }, 2800);
      }
    } catch (err) {
      console.error("ODOP decision error:", err);
    } finally {
      setIsSending(false);
    }
  }, [isSending, selectedLang, messages, token, userName, collectedFields, getAutoDetectedLocation, playTTS]);

  // ─── Step 6: Final Feasibility Appraisal Report Generation ─────────────
  const handleFinalSubmit = useCallback(async () => {
    const submitFn = onWizardSubmit || createAndSaveBusiness;
    if (!submitFn) return;
    try {
      const locCoords = getAutoDetectedLocation();
      await submitFn({
        ...collectedFields,
        language: selectedLang || "en",
        latitude: locCoords?.latitude || null,
        longitude: locCoords?.longitude || null,
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      console.error("Final appraisal generation failed:", err);
    }
  }, [collectedFields, selectedLang, onWizardSubmit, createAndSaveBusiness, getAutoDetectedLocation, navigate]);

  // Audio Recording (Microphone)
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      audioChunksRef.current = [];
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });

        setIsSending(true);
        try {
          const formData = new FormData();
          formData.append("audio", audioBlob, "recording.webm");
          formData.append("language", selectedLang || "hi");
          formData.append("context", JSON.stringify({ onboarding: true, collected_fields: collectedFields }));

          const res = await fetch("/api/v2/chat/audio", {
            method: "POST",
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            body: formData,
          });

          if (res.ok) {
            const data = await res.json();
            const transcript = data.user_transcript || data.transcript || "";
            if (transcript.trim()) {
              handleSendMessage(transcript.trim());
            }
          }
        } catch (e) {
          console.error("Voice recording processing error:", e);
        } finally {
          setIsSending(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access error:", err);
    }
  }, [selectedLang, collectedFields, token, handleSendMessage]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // ─── Render: Language Selection Phase ───────────────────────────────────
  if (phase === "lang_select") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50/30 flex items-center justify-center px-4 py-8 relative overflow-hidden">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[40rem] h-[40rem] bg-sovereign-100/40 blur-[180px] rounded-full pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/3 w-80 h-80 bg-sky-100/40 blur-[140px] rounded-full pointer-events-none" />

        <div className="max-w-2xl w-full relative z-10">
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-rose-500 via-pink-600 to-indigo-700 text-white flex items-center justify-center text-2xl font-black mx-auto mb-4 shadow-xl shadow-pink-500/20 border border-white/40">
              M
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-display mb-2">
              Namaste {userName} Ji! 🙏
            </h1>
            <p className="text-sm text-slate-600 max-w-md mx-auto">
              Please choose your language to talk with <b>Mira</b>, your personal MSME guide.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5 sm:gap-4">
            {ONBOARDING_LANGUAGES.map((lang) => {
              const isSelected = selectedLang === lang.code;
              return (
                <button
                  key={lang.code}
                  onClick={() => handleLanguageSelect(lang.code)}
                  className={`group relative rounded-2xl p-4 sm:p-5 text-center transition-all duration-300 ease-out cursor-pointer border-2 ${
                    isSelected
                      ? `${lang.gradientBorder} ring-4 ${lang.selectedGlow} shadow-xl scale-[1.02]`
                      : `border-slate-200/80 hover:${lang.gradientBorder} hover:shadow-lg hover:scale-[1.01] shadow-sm`
                  } bg-white`}
                >
                  <div className={`absolute top-0 left-3 right-3 h-1 rounded-b-full bg-gradient-to-r ${lang.gradient} opacity-${isSelected ? '100' : '0'} group-hover:opacity-100 transition-opacity duration-300`} />
                  <div className="text-xl sm:text-2xl font-black text-slate-900 mb-1.5 group-hover:text-indigo-950 transition-colors">
                    {lang.native}
                  </div>
                  <div className="text-xs text-slate-500 font-semibold tracking-wide">
                    {lang.label}
                  </div>
                  {isSelected && (
                    <div className="absolute -top-1.5 -right-1.5">
                      <div className={`w-6 h-6 rounded-full bg-gradient-to-r ${lang.gradient} flex items-center justify-center shadow-md`}>
                        <CheckCircle2 className="w-4 h-4 text-white" />
                      </div>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        <style>{`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}</style>
      </div>
    );
  }

  // ─── Render: Chat Phase with Mira ───────────────────────────────────────
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-pink-50/20 flex flex-col relative overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[36rem] h-[36rem] bg-rose-100/25 blur-[160px] rounded-full pointer-events-none" />

      {/* Header Bar */}
      <header className="sticky top-0 z-30 bg-gradient-to-r from-slate-950 via-sovereign-900 to-indigo-950 text-white px-4 py-3 shadow-lg">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-500 to-indigo-600 flex items-center justify-center text-lg font-black border border-white/20 shadow-md">
            M
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-bold truncate flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-rose-300" />
              Mira — Business Advisor
            </h1>
            <p className="text-[11px] text-rose-200/90 truncate flex items-center gap-1.5">
              <span>{selectedLang && ONBOARDING_LANGUAGES.find(l => l.code === selectedLang)?.native}</span>
              <span>•</span>
              {isPlayingAudio ? (
                <span className="text-emerald-300 font-semibold animate-pulse flex items-center gap-1">
                  <Volume2 className="w-3 h-3" /> Speaking...
                </span>
              ) : (
                <span className="text-rose-200">Online & Listening</span>
              )}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {isPlayingAudio && (
              <button
                type="button"
                onClick={stopAudio}
                className="px-2.5 py-1 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-400/30 text-[10px] font-bold hover:bg-rose-500/30 transition-colors flex items-center gap-1 cursor-pointer"
                title="Stop speech"
              >
                <VolumeX className="w-3 h-3" /> Stop
              </button>
            )}

            {Object.keys(collectedFields).length > 0 && (
              <div className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded-lg border border-emerald-400/30 font-bold">
                {Object.keys(collectedFields).filter(k => !["latitude", "longitude"].includes(k)).length} Details Filled
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-3 sm:px-4 py-4 sm:py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className="space-y-2.5">
              <div
                className={`flex gap-2.5 animate-[fadeIn_0.3s_ease-out] ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.role === "assistant" && (
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-rose-500 to-indigo-600 flex items-center justify-center text-white text-xs font-black shrink-0 mt-0.5 shadow-md">
                    M
                  </div>
                )}

                <div
                  className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                    msg.role === "user"
                      ? "bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-indigo-900 text-white rounded-br-md"
                      : "bg-white text-slate-800 border border-slate-200/80 rounded-bl-md"
                  }`}
                >
                  <div className="whitespace-pre-wrap">
                    {msg.content.split("\n").map((line, i) => {
                      const boldParsed = line.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
                      return (
                        <p key={i} className={i > 0 ? "mt-1.5" : ""} dangerouslySetInnerHTML={{ __html: boldParsed }} />
                      );
                    })}
                  </div>

                  {msg.role === "assistant" && (
                    <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-end">
                      <button
                        type="button"
                        onClick={() => playTTS(msg.content, selectedLang || "hi")}
                        className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-700 hover:text-rose-900 cursor-pointer"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                        <span>{isPlayingAudio ? "Speaking..." : "Listen"}</span>
                      </button>
                    </div>
                  )}
                </div>

                {msg.role === "user" && (
                  <div className="w-8 h-8 rounded-xl bg-slate-200 flex items-center justify-center text-slate-600 text-xs font-bold shrink-0 mt-0.5">
                    {userName.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>

              {/* ─── Step 1 Action Buttons: Location Confirmation ─────────── */}
              {msg.isLocationConfirmation && chatStep === "location_confirm" && (
                <div className="flex flex-col sm:flex-row gap-2.5 max-w-[85%] sm:max-w-[75%] ml-10 animate-[fadeIn_0.3s_ease-out]">
                  <button
                    type="button"
                    onClick={handleConfirmLocation}
                    disabled={isSending}
                    className="flex-1 py-2.5 px-4 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 shadow-md shadow-emerald-950/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <Check className="w-4 h-4 text-emerald-200" />
                    <span>{selectedLang === "en" ? "Yes, continue with this location" : "हाँ, इसी लोकेशन के साथ आगे बढ़ें"}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleRequestChangeLocation}
                    disabled={isSending}
                    className="py-2.5 px-4 rounded-xl text-xs font-bold text-slate-700 bg-white border border-slate-300 hover:bg-slate-100 transition-colors flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
                  >
                    <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
                    <span>{selectedLang === "en" ? "No, I want to change location" : "नहीं, मुझे लोकेशन बदलनी है"}</span>
                  </button>
                </div>
              )}
            </div>
          ))}

          {/* ─── Step 2: Interactive Location Selector Dropdown Menu Card ─── */}
          {showLocationMenu && (
            <div className="animate-[fadeIn_0.4s_ease-out] max-w-lg mx-auto my-3">
              <div className="bg-white rounded-3xl border-2 border-indigo-200 shadow-xl overflow-hidden p-5 space-y-4">
                <div className="flex items-center gap-2 text-sm font-bold text-slate-900 border-b border-slate-100 pb-3">
                  <MapPin className="w-4 h-4 text-indigo-600" />
                  <span>{selectedLang === "en" ? "Select Your Enterprise Location" : "अपने व्यवसाय का नया स्थान चुनें"}</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* State Select */}
                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 mb-1">State / राज्य *</label>
                    <select
                      value={selectedState}
                      onChange={(e) => handleStateChange(e.target.value)}
                      className="w-full text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                    >
                      <option value="">{selectedLang === "en" ? "-- Choose State --" : "-- राज्य चुनें --"}</option>
                      {statesList.map(s => (
                        <option key={s.state_code || s.state_name} value={s.state_name}>{s.state_name}</option>
                      ))}
                    </select>
                  </div>

                  {/* District Select */}
                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 mb-1">District / ज़िला *</label>
                    <select
                      value={selectedDistrict}
                      onChange={(e) => handleDistrictChange(e.target.value)}
                      disabled={!selectedState}
                      className="w-full text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 disabled:opacity-50"
                    >
                      <option value="">{selectedLang === "en" ? "-- Choose District --" : "-- ज़िला चुनें --"}</option>
                      {districtsList.map(d => (
                        <option key={d.district_code || d.district_name} value={d.district_name}>{d.district_name}</option>
                      ))}
                    </select>
                  </div>

                  {/* Block Select */}
                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 mb-1">Block / ब्लॉक (वैकल्पिक)</label>
                    <select
                      value={selectedBlock}
                      onChange={(e) => handleBlockChange(e.target.value)}
                      disabled={!selectedDistrict}
                      className="w-full text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 disabled:opacity-50"
                    >
                      <option value="">{selectedLang === "en" ? "-- Choose Block --" : "-- ब्लॉक चुनें --"}</option>
                      {blocksList.map(b => (
                        <option key={b.development_block_code || b.development_block_name} value={b.development_block_name}>
                          {b.development_block_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Village Select */}
                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 mb-1">Village/Locality / गाँव/इलाका</label>
                    <select
                      value={selectedVillage}
                      onChange={(e) => setSelectedVillage(e.target.value)}
                      disabled={!selectedBlock}
                      className="w-full text-xs font-medium bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 disabled:opacity-50"
                    >
                      <option value="">{selectedLang === "en" ? "-- Choose Village --" : "-- गाँव चुनें --"}</option>
                      {villagesList.map(v => (
                        <option key={v.village_code || v.village_name} value={v.village_name}>{v.village_name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Area Classification */}
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 mb-1.5">Area Classification / क्षेत्र वर्गीकरण</label>
                  <div className="flex gap-2">
                    {[
                      { id: "rural", label: selectedLang === "en" ? "Rural (ग्रामीण)" : "ग्रामीण" },
                      { id: "semi-urban", label: selectedLang === "en" ? "Semi-Urban (अर्ध-शहरी)" : "अर्ध-शहरी" },
                      { id: "urban", label: selectedLang === "en" ? "Urban (शहरी)" : "शहरी" },
                    ].map(type => (
                      <button
                        type="button"
                        key={type.id}
                        onClick={() => setAreaClassification(type.id)}
                        className={`flex-1 py-2 px-2.5 rounded-xl text-xs font-bold transition-all border ${
                          areaClassification === type.id
                            ? "bg-indigo-50 border-indigo-500 text-indigo-800 shadow-xs"
                            : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
                        }`}
                      >
                        {type.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Submit Location Button */}
                <button
                  type="button"
                  onClick={handleSubmitNewLocation}
                  disabled={!selectedState || !selectedDistrict || isSending}
                  className="w-full py-3 rounded-xl font-bold text-xs text-white bg-gradient-to-r from-indigo-600 to-sovereign-800 hover:from-indigo-500 hover:to-sovereign-700 shadow-md shadow-indigo-950/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  <Check className="w-4 h-4" />
                  <span>{selectedLang === "en" ? "Submit Location" : "स्थान सुरक्षित करें"}</span>
                </button>
              </div>
            </div>
          )}

          {/* ─── Step 4b: Interactive Machinery Dropdown & Checklist Card ───── */}
          {applicableMachinery && applicableMachinery.machinery_list && applicableMachinery.machinery_list.length > 0 && (
            <div className="animate-[fadeIn_0.4s_ease-out] max-w-xl mx-auto my-3">
              <div className="bg-white rounded-3xl border-2 border-indigo-400/80 shadow-2xl overflow-hidden">
                {/* Header Banner */}
                <div className="bg-gradient-to-r from-slate-950 via-indigo-950 to-slate-900 text-white p-4 sm:p-5 relative">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-400/40">
                      <Wrench className="w-3.5 h-3.5" />
                      {selectedLang === "en" ? "Standard MSME Plant & Machinery" : "मानक प्लांट एवं मशीनरी"}
                    </span>
                    <span className="text-xs text-indigo-200 font-semibold flex items-center gap-1">
                      <Zap className="w-3.5 h-3.5 text-amber-400" />
                      {applicableMachinery.typical_capacity || "Commercial Scale"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-4 mt-2">
                    <div>
                      <h3 className="text-base sm:text-lg font-bold font-display text-white">
                        {applicableMachinery.business_name}
                      </h3>
                      <p className="text-xs text-indigo-200/90 mt-0.5">
                        {selectedLang === "en"
                          ? "Select any machines you already own from the dropdown or checklist below to credit their valuation against your bank loan & lower your EMI:"
                          : "क्या आपके पास इनमें से कोई मशीन पहले से है? नीचे ड्रॉपडाउन या सूची से चुनें—हम उसकी कीमत सीधे आपके लोन में से घटा देंगे:"}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 sm:p-6 space-y-4 text-slate-800">
                  {/* Quick-Pick Dropdown */}
                  <div className="p-3.5 rounded-2xl bg-indigo-50/70 border border-indigo-200">
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-indigo-950 mb-1.5 flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <ChevronDown className="w-3.5 h-3.5 text-indigo-700" />
                        {selectedLang === "en" ? "Select Machine from Dropdown:" : "मशीन ड्रॉपडाउन से चुनें:"}
                      </span>
                      <span className="text-[10px] text-indigo-600 font-semibold">
                        {applicableMachinery.machinery_list.length} {selectedLang === "en" ? "options" : "विकल्प"}
                      </span>
                    </label>
                    <select
                      disabled={machineryConfirmed || isSending}
                      value=""
                      onChange={(e) => {
                        const val = e.target.value;
                        if (!val) return;
                        setSelectedOwnedMachines(prev =>
                          prev.includes(val) ? prev.filter(m => m !== val) : [...prev, val]
                        );
                      }}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-indigo-300 bg-white text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm cursor-pointer disabled:opacity-60"
                    >
                      <option value="">{selectedLang === "en" ? "-- Tap to choose a machine from dropdown --" : "-- ड्रॉपडाउन से कोई भी मशीन चुनें --"}</option>
                      {applicableMachinery.machinery_list.map((mach, idx) => {
                        const isSelected = selectedOwnedMachines.includes(mach.machine_name);
                        return (
                          <option key={idx} value={mach.machine_name}>
                            {isSelected ? "✓ [Selected] " : "+ "} {mach.machine_name} (₹{(mach.estimated_cost_inr / 100000).toFixed(2)} Lakhs)
                          </option>
                        );
                      })}
                    </select>
                  </div>

                  {/* Visual Checklist Cards */}
                  <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                    <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 px-1">
                      {selectedLang === "en" ? "Or Tap Applicable Equipment Below:" : "या नीचे दिए गए उपकरणों पर टैप करें:"}
                    </div>
                    {applicableMachinery.machinery_list.map((mach, idx) => {
                      const isSelected = selectedOwnedMachines.includes(mach.machine_name);
                      return (
                        <div
                          key={idx}
                          onClick={() => {
                            if (machineryConfirmed || isSending) return;
                            setSelectedOwnedMachines(prev =>
                              prev.includes(mach.machine_name)
                                ? prev.filter(m => m !== mach.machine_name)
                                : [...prev, mach.machine_name]
                            );
                          }}
                          className={`p-3 rounded-2xl border transition-all cursor-pointer flex items-start gap-3 select-none ${
                            isSelected
                              ? "bg-emerald-50/90 border-emerald-400 shadow-sm ring-1 ring-emerald-300"
                              : "bg-slate-50 hover:bg-slate-100/80 border-slate-200"
                          } ${machineryConfirmed ? "cursor-default opacity-90" : ""}`}
                        >
                          {/* Styled Checkbox */}
                          <div className={`mt-0.5 w-5 h-5 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                            isSelected
                              ? "bg-emerald-600 text-white shadow-sm shadow-emerald-600/30"
                              : "border-2 border-slate-300 bg-white"
                          }`}>
                            {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                          </div>

                          {/* Machine Details */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2">
                              <span className="font-bold text-xs text-slate-900 truncate">
                                {mach.machine_name}
                              </span>
                              <span className="text-[11px] font-black text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full shrink-0">
                                ₹{(mach.estimated_cost_inr / 100000).toFixed(2)} Lakhs
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-600 mt-0.5 line-clamp-1">
                              {mach.technical_specs}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              {mach.power_hp > 0 && (
                                <span className="text-[10px] text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded font-medium border border-indigo-200">
                                  ⚡ {mach.power_hp} HP
                                </span>
                              )}
                              <span className="text-[10px] text-slate-500">
                                Qty: {mach.quantity || 1}
                              </span>
                              {mach.is_mandatory && (
                                <span className="text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded font-medium border border-amber-200">
                                  Core Machine
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Live Calculation / Benefit Banner */}
                  {selectedOwnedMachines.length > 0 && (
                    <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-300 text-xs text-emerald-950 space-y-1">
                      <div className="flex items-center justify-between font-bold">
                        <span className="flex items-center gap-1.5 text-emerald-900">
                          <Sparkles className="w-4 h-4 text-emerald-600" />
                          {selectedLang === "en" ? "In-Kind Asset Valuation Credited:" : "इन-काइंड एसेट क्रेडिट:"}
                        </span>
                        <span className="text-emerald-700 text-sm font-black">
                          ₹{(
                            applicableMachinery.machinery_list
                              .filter(m => selectedOwnedMachines.includes(m.machine_name))
                              .reduce((sum, m) => sum + (m.estimated_cost_inr || 0), 0) / 100000
                          ).toFixed(2)} Lakhs
                        </span>
                      </div>
                      <p className="text-[11px] text-emerald-800">
                        {selectedLang === "en"
                          ? `✓ Deducted directly from fresh loan requirement • Lowers your monthly EMI`
                          : `✓ आपके आवश्यक बैंक लोन में से घटाया जाएगा • मासिक EMI में भारी बचत`}
                      </p>
                    </div>
                  )}

                  {/* Action Buttons or Confirmed State */}
                  {machineryConfirmed ? (
                    <div className="pt-2 flex items-center justify-between gap-3">
                      <div className="flex-1 p-3 rounded-2xl bg-emerald-50 border border-emerald-300 font-bold text-xs text-emerald-900 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>
                          {selectedOwnedMachines.length > 0
                            ? (selectedLang === "en"
                                ? `Equipment Locked: ${selectedOwnedMachines.length} machine(s) credited`
                                : `मशीनरी सुरक्षित: ${selectedOwnedMachines.length} उपकरण का मूल्य घटाया गया`)
                            : (selectedLang === "en"
                                ? "100% Fresh Machinery Mode Confirmed"
                                : "सभी नए उपकरणों का विकल्प सुरक्षित किया गया")}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setMachineryConfirmed(false)}
                        disabled={isSending}
                        className="px-3 py-3 rounded-xl border border-slate-300 text-slate-600 hover:text-slate-900 hover:bg-slate-100 text-xs font-semibold cursor-pointer shrink-0 transition-colors"
                      >
                        {selectedLang === "en" ? "Change" : "बदलें"}
                      </button>
                    </div>
                  ) : (
                    <div className="pt-2 flex flex-col sm:flex-row gap-2.5">
                      {selectedOwnedMachines.length > 0 ? (
                        <>
                          <button
                            type="button"
                            onClick={() => handleConfirmMachinery(selectedOwnedMachines)}
                            disabled={isSending}
                            className="flex-1 py-3 px-4 rounded-xl font-bold text-xs text-white bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 hover:from-emerald-500 hover:to-teal-500 shadow-md shadow-emerald-950/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                          >
                            <Check className="w-4 h-4" />
                            <span>
                              {selectedLang === "en"
                                ? `Confirm ${selectedOwnedMachines.length} Machine(s) Owned`
                                : `मेरे पास उपलब्ध ${selectedOwnedMachines.length} मशीनें सुरक्षित करें`}
                            </span>
                          </button>
                          <button
                            type="button"
                            onClick={() => setSelectedOwnedMachines([])}
                            disabled={isSending}
                            className="sm:w-auto py-3 px-3 rounded-xl font-semibold text-xs text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/80 transition-colors cursor-pointer"
                          >
                            {selectedLang === "en" ? "Clear" : "हटाएं"}
                          </button>
                        </>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleConfirmMachinery([])}
                          disabled={isSending}
                          className="w-full py-3 px-4 rounded-xl font-bold text-xs text-slate-700 bg-slate-100 hover:bg-slate-200/80 border border-slate-300 shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                        >
                          <span>
                            {selectedLang === "en"
                              ? "I don't own any of these (I need all fresh machines)"
                              : "मेरे पास इनमें से कोई मशीन नहीं है (मुझे सभी नई मशीनें चाहिए)"}
                          </span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ─── Step 5: 0-100 Benchmarked ODOP Alignment Synergy Card ─────── */}
          {odopData && (
            <div className="animate-[fadeIn_0.4s_ease-out] max-w-xl mx-auto my-3">
              <div className="bg-white rounded-3xl border-2 border-emerald-400/80 shadow-2xl overflow-hidden">
                {/* Header Banner */}
                <div className="bg-gradient-to-r from-emerald-950 via-teal-900 to-slate-950 text-white p-4 sm:p-5 relative">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-400/40">
                      <Sparkles className="w-3.5 h-3.5" />
                      ODOP Synergy Benchmarking
                    </span>
                    <span className="text-xs text-emerald-200 font-semibold flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" /> 35% PMFME Subsidy Ready
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-4 mt-2">
                    <div>
                      <h3 className="text-base sm:text-lg font-bold font-display text-white">
                        {selectedLang === "en"
                          ? "One District One Product Synergy Match"
                          : "एक जिला एक उत्पाद (ODOP) तालमेल स्कोर"}
                      </h3>
                      <p className="text-xs text-emerald-200/90 mt-0.5">
                        {odopData.mira_recommendation || "Mira's Strategic Evaluation"}
                      </p>
                    </div>

                    {/* 0-100 Score Gauge Badge */}
                    <div className="shrink-0 flex flex-col items-center justify-center w-16 h-16 rounded-2xl bg-white/10 backdrop-blur-md border border-white/30 shadow-inner">
                      <span className="text-xl font-black text-emerald-300 leading-none">
                        {odopData.alignment_score || 85}
                      </span>
                      <span className="text-[10px] font-bold text-white/80 uppercase tracking-wider mt-0.5">
                        / 100
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-4 sm:p-6 space-y-4 text-slate-800">
                  {/* Explainer Box: What is ODOP? */}
                  <div className="p-3.5 rounded-2xl bg-emerald-50/80 border border-emerald-200 text-xs leading-relaxed text-emerald-950">
                    <p className="font-bold text-emerald-900 mb-1 flex items-center gap-1.5">
                      <Info className="w-4 h-4 text-emerald-700 shrink-0" />
                      {selectedLang === "en" ? "What is the ODOP Scheme?" : "ODOP योजना क्या है?"}
                    </p>
                    <p className="text-emerald-900/90">
                      {odopData.what_is_odop || "The One District One Product (ODOP) initiative by the central government focuses on each district's designated indigenous product to provide 35% PMFME capital subsidies, priority procurement on GeM, and cluster common facility centers."}
                    </p>
                  </div>

                  {/* Current Business & District ODOP Badges */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                        {selectedLang === "en" ? "Your Current Business" : "आपका वर्तमान व्यवसाय"}
                      </div>
                      <div className="font-bold text-sm text-slate-900 flex items-center gap-1.5">
                        <span>🏪</span>
                        <span className="truncate">{odopData.user_business || "Your Venture"}</span>
                      </div>
                    </div>

                    <div className="p-3 rounded-2xl bg-teal-50 border border-teal-200">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-teal-700 mb-1">
                        {selectedLang === "en" ? "The District's ODOP" : "जिले का आधिकारिक ODOP"}
                      </div>
                      <div className="font-bold text-sm text-teal-950 flex items-center gap-1.5">
                        <span>🌾</span>
                        <span className="truncate">{odopData.district_odop || odopData.odop_product}</span>
                      </div>
                    </div>
                  </div>

                  {/* How We Aligned Both (3 Structured Pillars) */}
                  <div className="space-y-2.5 pt-1">
                    <div className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-amber-500" />
                      <span>
                        {selectedLang === "en"
                          ? "How We Aligned Both (Strategic Synergy):"
                          : "हमने दोनों को कैसे जोड़ा (रणनीतिक तालमेल):"}
                      </span>
                    </div>

                    {/* Pillar 1: Product Innovation */}
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/90 space-y-1">
                      <div className="text-xs font-bold text-slate-900 flex items-center gap-2">
                        <span className="w-5 h-5 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center text-[11px] font-black shrink-0">1</span>
                        <span>{odopData.synergy_pillars?.product_innovation?.title || "Product Innovation"}</span>
                      </div>
                      <p className="text-xs text-slate-600 pl-7 leading-relaxed">
                        {odopData.synergy_pillars?.product_innovation?.description}
                      </p>
                    </div>

                    {/* Pillar 2: Local Sourcing Advantage */}
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/90 space-y-1">
                      <div className="text-xs font-bold text-slate-900 flex items-center gap-2">
                        <span className="w-5 h-5 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center text-[11px] font-black shrink-0">2</span>
                        <span>{odopData.synergy_pillars?.local_sourcing?.title || "Local Sourcing Advantage"}</span>
                      </div>
                      <p className="text-xs text-slate-600 pl-7 leading-relaxed">
                        {odopData.synergy_pillars?.local_sourcing?.description}
                      </p>
                    </div>

                    {/* Pillar 3: Financial Incentives */}
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/90 space-y-1">
                      <div className="text-xs font-bold text-slate-900 flex items-center gap-2">
                        <span className="w-5 h-5 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center text-[11px] font-black shrink-0">3</span>
                        <span>{odopData.synergy_pillars?.financial_incentives?.title || "Financial & Scheme Incentives"}</span>
                      </div>
                      <p className="text-xs text-slate-600 pl-7 leading-relaxed">
                        {odopData.synergy_pillars?.financial_incentives?.description}
                      </p>
                    </div>
                  </div>

                  {/* Decision Buttons or Confirmed State */}
                  {collectedFields.odop_decision ? (
                    <div className="pt-2">
                      <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-300 text-center font-bold text-xs text-emerald-950 flex items-center justify-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>
                          {collectedFields.odop_decision === "align"
                            ? (selectedLang === "en"
                                ? "Confirmed: Aligned with ODOP (35% PMFME Subsidy Unlocked) ✨"
                                : "स्वीकृत: ODOP से जोड़ा गया (35% PMFME सरकारी सब्सिडी सुरक्षित) ✨")
                            : (selectedLang === "en"
                                ? "Confirmed: Proceeding with Original Business Model (PMEGP/MUDRA)"
                                : "स्वीकृत: मूल व्यवसाय मॉडल के साथ आगे बढ़ रहे हैं (PMEGP/मुद्रा)")}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="pt-2 flex flex-col sm:flex-row gap-2.5">
                      <button
                        type="button"
                        onClick={() => handleOdopDecision(true)}
                        disabled={isSending}
                        className="flex-1 py-3 px-4 rounded-xl font-bold text-xs text-white bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 hover:from-emerald-500 hover:to-teal-500 shadow-md shadow-emerald-950/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                      >
                        <Sparkles className="w-4 h-4 text-emerald-200" />
                        <span>
                          {selectedLang === "en"
                            ? "Align with ODOP (Unlock 35% Subsidy) ✨"
                            : "ODOP से जोड़ें (35% सब्सिडी अनलॉक करें) ✨"}
                        </span>
                      </button>

                      <button
                        type="button"
                        onClick={() => handleOdopDecision(false)}
                        disabled={isSending}
                        className="sm:w-auto py-3 px-4 rounded-xl font-semibold text-xs text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/80 transition-colors cursor-pointer disabled:opacity-50"
                      >
                        {selectedLang === "en" ? "Keep My Idea" : "मेरा विचार रखें"}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Typing Indicator */}
          {isSending && (
            <div className="flex gap-2.5 animate-[fadeIn_0.2s_ease-out]">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-rose-500 to-indigo-600 flex items-center justify-center text-white text-xs font-black shrink-0">
                M
              </div>
              <div className="bg-white rounded-2xl rounded-bl-md px-4 py-3 border border-slate-200/80 shadow-sm">
                <div className="flex items-center gap-1.5">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-rose-400 rounded-full animate-bounce" style={{ animationDelay: "0s" }} />
                    <span className="w-2 h-2 bg-rose-400 rounded-full animate-bounce" style={{ animationDelay: "0.15s" }} />
                    <span className="w-2 h-2 bg-rose-400 rounded-full animate-bounce" style={{ animationDelay: "0.3s" }} />
                  </div>
                  <span className="text-xs text-slate-500 ml-1">Mira is thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Bar — Sticky at Bottom */}
      <div className="sticky bottom-0 z-20 bg-white/95 backdrop-blur-xl border-t border-slate-200/80 px-3 sm:px-4 py-3 shadow-[0_-4px_20px_rgba(0,0,0,0.04)]">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-2">
            <button
              type="button"
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onTouchStart={startRecording}
              onTouchEnd={stopRecording}
              disabled={isSending}
              className={`shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition-all duration-200 cursor-pointer ${
                isRecording
                  ? "bg-rose-500 text-white shadow-lg shadow-rose-500/30 scale-110 animate-pulse"
                  : "bg-slate-100 text-slate-600 hover:bg-rose-100 hover:text-rose-800 border border-slate-200"
              }`}
              title={isRecording ? "Recording... Release to stop" : "Hold to record voice"}
            >
              {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  selectedLang === "en"
                    ? "Type your message or hold mic to speak..."
                    : "अपना संदेश लिखें या बोलने के लिए माइक दबाएँ..."
                }
                rows={1}
                disabled={isSending}
                className="w-full resize-none rounded-xl bg-slate-50 border border-slate-200 px-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500/40 focus:border-rose-500 transition-all max-h-32 overflow-y-auto"
                style={{ minHeight: "44px" }}
              />
            </div>

            <button
              type="button"
              onClick={() => handleSendMessage()}
              disabled={!inputText.trim() || isSending}
              className="shrink-0 w-11 h-11 rounded-xl bg-gradient-to-r from-rose-600 via-pink-600 to-indigo-800 text-white flex items-center justify-center shadow-md shadow-pink-950/20 hover:shadow-lg disabled:opacity-40 transition-all duration-200 cursor-pointer"
            >
              {isSending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </div>

          <div className="mt-1.5 flex items-center justify-between text-[11px] text-slate-400 px-1">
            <span>
              {isRecording 
                ? "🎙️ Recording... Release button to send" 
                : (selectedLang === "en" ? "Press Enter to send" : "भेजने के लिए Enter दबाएँ")}
            </span>
            <span className="truncate max-w-[220px]">
              {collectedFields.district_name 
                ? `📍 ${collectedFields.district_name}, ${collectedFields.state_name || ''}` 
                : "📍 Thane, Maharashtra"}
            </span>
          </div>
        </div>
      </div>

      {/* ─── Processing Phase Overlay Modal ──────────────────────────────── */}
      {phase === "processing" && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center px-4">
          <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full p-8 text-center animate-[fadeIn_0.3s_ease-out]">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-500 flex items-center justify-center mx-auto mb-4 shadow-lg">
              <CheckCircle2 className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-xl font-extrabold text-slate-900 font-display mb-2">
              {selectedLang === "en" ? "All Information Collected! 🎉" : "सभी जानकारी एकत्र हो गई! 🎉"}
            </h2>
            <p className="text-sm text-slate-600 mb-6">
              {selectedLang === "en"
                ? "Mira has gathered your enterprise details and finalized your ODOP alignment. Click below to generate your complete bank-ready feasibility appraisal."
                : "Mira ने आपके उद्यम की सभी आवश्यक जानकारी एकत्र कर ली है और ODOP तालमेल तैयार कर लिया है। अपनी पूरी व्यवहार्यता रिपोर्ट और बैंक डीपीआर बनाने के लिए नीचे क्लिक करें।"}
            </p>

            {/* Collected Details Summary */}
            <div className="bg-slate-50 rounded-2xl border border-slate-200/90 p-4 mb-6 text-left space-y-3.5 max-h-72 overflow-y-auto">
              <div>
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-indigo-500" />
                  Enterprise & Location
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-medium">Enterprise Name</span>
                    <span className="font-bold text-slate-900 truncate max-w-[55%] text-right">{collectedFields.enterprise_name || `${userName}'s Venture`}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-medium">Sector & Category</span>
                    <span className="font-semibold text-slate-900 capitalize text-right">
                      {(collectedFields.sector || "MSME").replace(/_/g, " ")} • {collectedFields.business_category || "Manufacturing"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-medium">Target Location</span>
                    <span className="font-semibold text-slate-900 text-right">
                      {collectedFields.district_name || "Thane"}, {collectedFields.state_name || "Maharashtra"} ({collectedFields.is_rural ? "Rural" : "Urban"})
                    </span>
                  </div>
                </div>
              </div>

              <div className="border-t border-slate-200/70 pt-2.5">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  Financial Outlay & Promoter Equity
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-medium">Promoter Equity</span>
                    <span className="font-bold text-emerald-700">
                      ₹{Number(collectedFields.promoter_equity || 100000).toLocaleString('en-IN')}
                      {collectedFields.promoter_margin_pct && (
                        <span className="ml-1 text-[10px] text-slate-500 font-normal">({collectedFields.promoter_margin_pct}% Margin)</span>
                      )}
                    </span>
                  </div>
                  {collectedFields.gross_project_cost && Number(collectedFields.gross_project_cost) !== Number(collectedFields.project_cost) && (
                    <div className="flex justify-between">
                      <span className="text-slate-500 font-medium">Gross Project Outlay</span>
                      <span className="font-semibold text-slate-700">₹{Number(collectedFields.gross_project_cost).toLocaleString('en-IN')}</span>
                    </div>
                  )}
                  {Number(collectedFields.owned_machinery_value || 0) > 0 && (
                    <div className="text-emerald-800 bg-emerald-50/80 px-2 py-1.5 rounded-md space-y-0.5">
                      <div className="flex justify-between">
                        <span className="font-medium text-[11px]">Owned Machinery Credit</span>
                        <span className="font-bold text-[11px]">-₹{Number(collectedFields.owned_machinery_value).toLocaleString('en-IN')}</span>
                      </div>
                      {collectedFields.owned_machines && Array.isArray(collectedFields.owned_machines) && collectedFields.owned_machines.length > 0 && (
                        <div className="text-[10px] text-emerald-700/80 truncate">
                          Credited: {collectedFields.owned_machines.map(m => m.machine_name || m).join(", ")}
                        </div>
                      )}
                    </div>
                  )}
                  <div className="flex justify-between bg-white px-2 py-1 rounded-md border border-slate-200">
                    <span className="text-slate-900 font-bold text-xs">Net Fresh Bank Loan Base</span>
                    <span className="font-extrabold text-indigo-950 text-xs">₹{Number(collectedFields.project_cost || 500000).toLocaleString('en-IN')}</span>
                  </div>
                </div>
              </div>

              <div className="border-t border-slate-200/70 pt-2.5">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                  Statutory MSME Banking Policy
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-medium">Loan Repayment Period</span>
                    <span className="font-semibold text-slate-800">{collectedFields.tenure_years || 7.0} Years (RBI Norms)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-medium">Moratorium Grace Period</span>
                    <span className="font-semibold text-slate-800">{collectedFields.moratorium_months || 6} Months (Setup & Trial)</span>
                  </div>
                  {collectedFields.expected_monthly_units && (
                    <div className="flex justify-between">
                      <span className="text-slate-500 font-medium">Production Capacity</span>
                      <span className="font-semibold text-slate-800">
                        {Number(collectedFields.expected_monthly_units).toLocaleString('en-IN')} {collectedFields.capacity_unit_label || "units"}/mo
                      </span>
                    </div>
                  )}
                  {collectedFields.odop_product && (
                    <div className="flex justify-between">
                      <span className="text-slate-500 font-medium">ODOP Status</span>
                      <span className="font-semibold text-indigo-600 truncate max-w-[55%] text-right">
                        {collectedFields.odop_synergy_aligned ? `Aligned (${collectedFields.odop_product})` : "Standard Model"}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <button
              onClick={handleFinalSubmit}
              disabled={parentLoading}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-indigo-900 text-white font-bold text-sm shadow-lg shadow-sovereign-950/20 hover:shadow-xl transition-all duration-200 flex items-center justify-center gap-2 group disabled:opacity-50 cursor-pointer"
            >
              {parentLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{selectedLang === "en" ? "Generating Report..." : "रिपोर्ट बना रहे हैं..."}</span>
                </>
              ) : (
                <>
                  <span>{selectedLang === "en" ? "Generate Feasibility Report" : "व्यवहार्यता रिपोर्ट बनाएँ"}</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

export default OnboardingPage;
