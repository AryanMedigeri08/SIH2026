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
  reverseGeocodeCoords,
  detectLocationFromIP,
} from "../services/api";
import { chooseRecordingFormat, transcribeOnboardingAudio } from "../services/onboardingAudio";
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
  Edit3,
  User,
} from "lucide-react";

// ─── Caste Category Options ──────────────────────────────────────────────
const PROMOTER_CATEGORIES = [
  { value: "general", label: "General", labelHi: "सामान्य" },
  { value: "obc", label: "OBC", labelHi: "अन्य पिछड़ा वर्ग" },
  { value: "sc", label: "SC (Scheduled Caste)", labelHi: "अनुसूचित जाति" },
  { value: "st", label: "ST (Scheduled Tribe)", labelHi: "अनुसूचित जनजाति" },
  { value: "women", label: "Women Entrepreneur", labelHi: "महिला उद्यमी" },
  { value: "women_shg", label: "Women SHG", labelHi: "महिला स्वसहायता समूह" },
];

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

const STEP_NUMBER = {
  location_confirm: 1, location_menu: 1, business_idea: 2,
  odop_check_prompt: 3, odop_alignment: 3, enterprise_info: 4,
  promoter_equity: 5, machinery_selection: 6, split_screen: 7,
};

// ─── Loving & Sweet Opening Greetings (Location Confirmation) ─────────
const GREETINGS = {
  hi: (name, loc) => `नमस्ते ${name} जी! आपसे मिलकर मुझे बहुत खुशी हुई। मैं Mira हूँ, आपकी प्यारी और मार्गदर्शक व्यवसाय साथी। मैं आपकी व्यवसाय यात्रा को सफल और 35% तक सरकारी सब्सिडी के साथ शुरू कराने में हर कदम पर आपके साथ हूँ।\n\nपंजीकरण के दौरान मुझे आपकी लोकेशन प्राप्त हुई है: **${loc || 'Pune, Maharashtra'}**। क्या आप इसी लोकेशन के साथ आगे बढ़ना चाहते हैं या आप इसे बदलना चाहते हैं?`,
  en: (name, loc) => `Namaste ${name} Ji! I am so happy to meet you. I am Mira, your loving business guide. I am right here by your side to help you launch a successful, bank-backed venture with up to 35% government subsidies.\n\nFrom your registration, I received your location as: **${loc || 'Pune, Maharashtra'}**. Would you like to continue with this location, or would you like to choose a different one?`,
  mr: (name, loc) => `नमस्कार ${name} जी! तुम्हाला भेटून मला मनापासून आनंद झाला. मी Mira आहे, तुमची व्यवसाय मार्गदर्शक. 35% पर्यंत सरकारी अनुदानासह तुमचा व्यवसाय यशस्वी करण्यासाठी मी तुमच्या सोबत आहे.\n\nनोंदणीदरम्यान मला तुमचे स्थान मिळाले आहे: **${loc || 'Pune, Maharashtra'}**. आपण याच स्थानासह पुढे जाऊ इच्छिता की तुम्हाला ते बदलायचे आहे?`,
  te: (name, loc) => `నమస్తే ${name} జీ! మిమ్మల్ని కలవడం నాకు చాలా సంతోషంగా ఉంది. నేను Mira, మీ వ్యాపార సలహాదారుని. 35% వరకు ప్రభుత్వ సಬ್సిడీలతో మీ వ్యాపారాన్ని విజయవంతం చేయడంలో నేను మీకు తోడుగా ఉంటాను.\n\nరిజిస్ట్రేషన్ సమయంలో నాకు మీ లొకేషన్ తెలిసింది: **${loc || 'Pune, Maharashtra'}**. మీరు ఇదే లొకేషన్‌తో కొనసాగాలనుకుంటున్నారా లేదా మార్చాలనుకుంటున్నారా?`,
  ta: (name, loc) => `வணக்கம் ${name} ஜி! உங்களை சந்தித்ததில் எனக்கு மிக்க மகிழ்ச்சி. நான் Mira, உங்கள் வணிக ஆலோசகர். 35% வரை அரசு மானியங்களுடன் உங்கள் தொழிலைத் தொடங்க உங்களுக்கு உதவ நான் இங்கே இருக்கிறேன்.\n\nபதிவின் போது எனக்கு கிடைத்த உங்கள் இருப்பிடம்: **${loc || 'Pune, Maharashtra'}**. நீங்கள் இந்த இருப்பிடத்துடன் தொடர விரும்புகிறீர்களா அல்லது மாற்ற விரும்புகிறீர்களா?`,
  kn: (name, loc) => `ನಮಸ್ಕಾರ ${name} ಜೀ! ನಿಮ್ಮನ್ನು ಭೇಟಿಯಾಗಲು ನನಗೆ ತುಂಬಾ ಸಂತೋಷವಾಗಿದೆ. ನಾನು Mira, ನಿಮ್ಮ ಪ್ರೀತಿಯ ವ್ಯಾಪಾರ ಮಾರ್ಗದರ್ಶಕಿ. 35% ವರೆಗೆ ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿಯೊಂದಿಗೆ ನಿಮ್ಮ ಉದ್ಯಮವನ್ನು ಪ್ರಾರಂಭಿಸಲು ನಾನು ನಿಮ್ಮೊಂದಿಗಿದ್ದೇನೆ.\n\nನೋಂದಣಿ ಸಮಯದಲ್ಲಿ ನಿಮ್ಮ ಸ್ಥಳ ನನಗೆ ಲಭ್ಯವಾಗಿದೆ: **${loc || 'Pune, Maharashtra'}**. ನೀವು ಇದೇ ಸ್ಥಳದೊಂದಿಗೆ ಮುಂದುವರಿಯಲು ಬಯಸುವಿರಾ ಅಥವಾ ಬೇರೆ ಸ್ಥಳವನ್ನು ಆಯ್ಕೆ ಮಾಡಲು ಬಯಸುವಿರಾ?`,
};

// ─── Mira Avatar Component ──────────────────────────────────────────────
export function MiraAvatar({ size = "w-8 h-8", rounded = "rounded-xl", className = "" }) {
  return (
    <div className={`${size} ${rounded} overflow-hidden shrink-0 border border-rose-300/40 shadow-sm bg-rose-50 flex items-center justify-center ${className}`}>
      <img
        src="/mira-avatar.png"
        alt="Mira"
        className="w-full h-full object-cover"
        onError={(e) => {
          e.currentTarget.style.display = "none";
          if (e.currentTarget.parentElement) {
            e.currentTarget.parentElement.innerText = "M";
          }
        }}
      />
    </div>
  );
}

function FormattedMessage({ content }) {
  return String(content || "").split("\n").map((line, index) => (
    <p key={index} className={index ? "mt-2" : ""}>
      {line.split(/(\*\*[^*]+\*\*)/g).map((part, partIndex) =>
        part.startsWith("**") && part.endsWith("**")
          ? <strong key={partIndex}>{part.slice(2, -2)}</strong>
          : <React.Fragment key={partIndex}>{part}</React.Fragment>
      )}
    </p>
  ));
}

export function OnboardingPage({ onWizardSubmit, isLoading: parentLoading }) {
  const navigate = useNavigate();
  const { userProfile, token, updateProfile } = useAuth();
  const { setLanguage, dismissTransition } = useLanguage();
  const { createAndSaveBusiness } = useBusiness();

  // ─── State Management ──────────────────────────────────────────────────
  const [phase, setPhase] = useState("lang_select"); // lang_select | chatting | split_screen | processing
  const [selectedLang, setSelectedLang] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [chatError, setChatError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isStartingRecording, setIsStartingRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Chat conversational state
  const [chatStep, setChatStep] = useState("location_confirm"); // location_confirm | location_menu | business_idea | odop_check_prompt | odop_alignment | enterprise_info | promoter_equity | machinery_selection | split_screen | completed
  const [locationConfirmed, setLocationConfirmed] = useState(false);
  const [locationWasChanged, setLocationWasChanged] = useState(false);
  const [collectedFields, setCollectedFields] = useState({});
  const [odopIntroData, setOdopIntroData] = useState(null);
  const [showOdopIntroCard, setShowOdopIntroCard] = useState(false);
  const [odopData, setOdopData] = useState(null);
  const [showOdopAlignmentCard, setShowOdopAlignmentCard] = useState(false);
  const [applicableMachinery, setApplicableMachinery] = useState(null);
  const [selectedOwnedMachines, setSelectedOwnedMachines] = useState([]);
  const [machineryConfirmed, setMachineryConfirmed] = useState(false);

  // Enterprise Info Card state
  const [showEnterpriseCard, setShowEnterpriseCard] = useState(false);
  const [enterpriseNameInput, setEnterpriseNameInput] = useState("");
  const [promoterCategoryInput, setPromoterCategoryInput] = useState("general");

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

  // ─── Active Geolocation & Resolved District State ───────────────────────
  const [detectedLocationData, setDetectedLocationData] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem("user_detected_location") || "{}");
      if (saved.district_name && saved.district_name.toLowerCase() !== "thane") {
        return saved;
      }
    } catch (_) {}
    return {
      latitude: 18.5204,
      longitude: 73.8567,
      district_name: "Pune",
      state_name: "Maharashtra",
      locality_name: "",
    };
  });

  const messagesContainerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const splitMessagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const recordingStreamRef = useRef(null);
  const recordingStartingRef = useRef(false);
  const recordingStartedAtRef = useRef(0);
  const audioChunksRef = useRef([]);
  const currentAudioRef = useRef(null);

  const [splitInputText, setSplitInputText] = useState("");

  const userName = userProfile?.name || "Entrepreneur";

  // Auto-scroll logic: Only scroll down if 2+ messages exist or an action card opened; keep first greeting at top
  useEffect(() => {
    if (messages.length > 1 || showLocationMenu || showOdopIntroCard || showOdopAlignmentCard || showEnterpriseCard || applicableMachinery) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    } else if (messages.length <= 1) {
      if (messagesContainerRef.current) {
        messagesContainerRef.current.scrollTop = 0;
      }
    }
  }, [messages, showLocationMenu, showOdopIntroCard, showOdopAlignmentCard, showEnterpriseCard, applicableMachinery]);

  // Auto-scroll split-screen chat history
  useEffect(() => {
    if (phase === "split_screen" || phase === "processing") {
      splitMessagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, phase]);

  useEffect(() => {
    if (phase !== "split_screen") return;
    let active = true;
    Promise.all([
      fetchStates(),
      collectedFields.state_name ? fetchDistricts(collectedFields.state_name) : Promise.resolve([]),
      collectedFields.district_name ? fetchBlocks(collectedFields.district_name) : Promise.resolve([]),
      collectedFields.district_name && collectedFields.block_name
        ? fetchVillages(collectedFields.district_name, collectedFields.block_name)
        : Promise.resolve([]),
    ]).then(([stateOptions, districtOptions, blockOptions, villageOptions]) => {
      if (!active) return;
      setStatesList(stateOptions || []);
      setDistrictsList(districtOptions || []);
      setBlocksList(blockOptions || []);
      setVillagesList(villageOptions || []);
    }).catch(() => {});
    return () => { active = false; };
  }, [phase]);

  // Audio cleanup on unmount
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.onstop = null;
        if (mediaRecorderRef.current.state !== "inactive") mediaRecorderRef.current.stop();
      }
      recordingStreamRef.current?.getTracks().forEach(track => track.stop());
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

  // ─── Active Geolocation Resolution Hook ────────────────────────────────
  useEffect(() => {
    let isMounted = true;
    const detectLocation = async () => {
      // 1. If userProfile has coordinates
      if (userProfile?.latitude && userProfile?.longitude) {
        const geo = await reverseGeocodeCoords(userProfile.latitude, userProfile.longitude);
        if (!isMounted) return;
        if (geo?.district_name) {
          const locObj = {
            latitude: userProfile.latitude,
            longitude: userProfile.longitude,
            district_name: geo.district_name,
            state_name: geo.state_name || "Maharashtra",
            locality_name: geo.locality_name || "",
          };
          setDetectedLocationData(locObj);
          try {
            localStorage.setItem("user_detected_location", JSON.stringify(locObj));
          } catch (_) {}
          return;
        }
      }

      // 2. High accuracy browser GPS
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          async (pos) => {
            if (!isMounted) return;
            const lat = pos.coords.latitude;
            const lon = pos.coords.longitude;
            const geo = await reverseGeocodeCoords(lat, lon);
            if (!isMounted) return;
            const locObj = {
              latitude: lat,
              longitude: lon,
              district_name: geo?.district_name || "Pune",
              state_name: geo?.state_name || "Maharashtra",
              locality_name: geo?.locality_name || "",
            };
            setDetectedLocationData(locObj);
            try {
              localStorage.setItem("user_detected_location", JSON.stringify(locObj));
            } catch (_) {}
          },
          async (err) => {
            console.warn("GPS lookup note:", err.message);
            // 3. Fallback to IP geolocation
            const ipLoc = await detectLocationFromIP();
            if (!isMounted) return;
            if (ipLoc && ipLoc.district_name) {
              const locObj = {
                latitude: ipLoc.latitude,
                longitude: ipLoc.longitude,
                district_name: ipLoc.district_name,
                state_name: ipLoc.state_name || "Maharashtra",
                locality_name: "",
              };
              setDetectedLocationData(locObj);
              try {
                localStorage.setItem("user_detected_location", JSON.stringify(locObj));
              } catch (_) {}
            }
          },
          { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
        );
      } else {
        const ipLoc = await detectLocationFromIP();
        if (!isMounted) return;
        if (ipLoc && ipLoc.district_name) {
          const locObj = {
            latitude: ipLoc.latitude,
            longitude: ipLoc.longitude,
            district_name: ipLoc.district_name,
            state_name: ipLoc.state_name || "Maharashtra",
            locality_name: "",
          };
          setDetectedLocationData(locObj);
          try {
            localStorage.setItem("user_detected_location", JSON.stringify(locObj));
          } catch (_) {}
        }
      }
    };

    detectLocation();
    return () => { isMounted = false; };
  }, [userProfile]);

  // Dynamically update greeting text when GPS / IP location resolves if still on location confirmation step
  useEffect(() => {
    if (chatStep === "location_confirm" && !locationConfirmed && detectedLocationData?.district_name) {
      const locLabel = `${detectedLocationData.district_name}, ${detectedLocationData.state_name || "Maharashtra"}`;
      setCollectedFields(prev => ({
        ...prev,
        state_name: detectedLocationData.state_name || "Maharashtra",
        district_name: detectedLocationData.district_name,
      }));
      setMessages(prev => {
        if (!prev || prev.length === 0) return prev;
        const first = prev[0];
        if (first?.isLocationConfirmation) {
          const greetFn = GREETINGS[selectedLang] || GREETINGS.hi;
          const updatedGreeting = greetFn(userName, locLabel);
          return [
            {
              ...first,
              content: updatedGreeting,
              locationLabel: locLabel,
            },
            ...prev.slice(1),
          ];
        }
        return prev;
      });
    }
  }, [detectedLocationData, chatStep, locationConfirmed, selectedLang, userName]);

  // ─── Get Registration Geolocation Coords ────────────────────────────────
  const getAutoDetectedLocation = useCallback(() => {
    if (userProfile?.latitude && userProfile?.longitude) {
      return { latitude: userProfile.latitude, longitude: userProfile.longitude };
    }
    if (detectedLocationData?.latitude && detectedLocationData?.longitude) {
      return { latitude: detectedLocationData.latitude, longitude: detectedLocationData.longitude };
    }
    try {
      const saved = JSON.parse(localStorage.getItem("user_detected_location") || "{}");
      if (saved.latitude && saved.longitude) {
        return { latitude: saved.latitude, longitude: saved.longitude };
      }
    } catch (_) {}
    return { latitude: 18.5204, longitude: 73.8567 }; // Default fallback: Pune, Maharashtra
  }, [userProfile, detectedLocationData]);

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
      updateProfile({ preferred_language: langCode }).catch((error) => {
        console.warn("Could not save onboarding language preference:", error);
      });
    }

    // Initial greeting from Mira
    setTimeout(() => {
      const greetFn = GREETINGS[langCode] || GREETINGS.hi;
      const initialLocLabel = `${detectedLocationData?.district_name || "Pune"}, ${detectedLocationData?.state_name || "Maharashtra"}`;
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
        state_name: detectedLocationData?.state_name || "Maharashtra",
        district_name: detectedLocationData?.district_name || "Pune",
        is_rural: true,
      }));

      playTTS(greetingText, langCode);

      setTimeout(() => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTop = 0;
        }
      }, 60);
    }, 350);
  }, [userName, token, updateProfile, setLanguage, dismissTransition, detectedLocationData, playTTS]);

  // ─── Step 1a: User clicks "Yes, continue with this location" ─────────────
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
      const confirmedDistrict = collectedFields.district_name || detectedLocationData?.district_name || "Pune";
      const confirmedState = collectedFields.state_name || detectedLocationData?.state_name || "Maharashtra";
      const userLocPayload = {
        ...locCoords,
        district_name: confirmedDistrict,
        state_name: confirmedState,
      };
      const res = await fetch("/api/v2/chat/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({
          messages: [...messages, userMsg].map(m => ({ role: m.role, content: m.content })),
          language: selectedLang || "hi",
          user_name: userName,
          collected_fields: {
            ...collectedFields,
            district_name: confirmedDistrict,
            state_name: confirmedState,
          },
          conversation_step: 1,
          current_action: "confirm_location",
          user_location: userLocPayload,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setLocationConfirmed(true);
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

  // ─── Step 1b: User clicks "No, I want to change location" ───────────────
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
        setLocationConfirmed(true);
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

  const handleReviewLocationChange = async (field, value) => {
    if (field === "state_name") {
      setCollectedFields(prev => ({ ...prev, state_name: value, district_name: "", block_name: "", village_name: "" }));
      setDistrictsList(value ? (await fetchDistricts(value) || []) : []);
      setBlocksList([]);
      setVillagesList([]);
    } else if (field === "district_name") {
      setCollectedFields(prev => ({ ...prev, district_name: value, block_name: "", village_name: "" }));
      setBlocksList(value ? (await fetchBlocks(value) || []) : []);
      setVillagesList([]);
    } else if (field === "block_name") {
      setCollectedFields(prev => ({ ...prev, block_name: value, village_name: "" }));
      setVillagesList(value ? (await fetchVillages(collectedFields.district_name, value) || []) : []);
    } else {
      setCollectedFields(prev => ({ ...prev, village_name: value }));
    }
    setLocationWasChanged(true);
  };

  const handleReviseBusinessIdea = () => {
    setCollectedFields(prev => ({
      state_name: prev.state_name,
      district_name: prev.district_name,
      block_name: prev.block_name,
      village_name: prev.village_name,
      is_rural: prev.is_rural,
    }));
    setApplicableMachinery(null);
    setSelectedOwnedMachines([]);
    setMachineryConfirmed(false);
    setOdopData(null);
    setOdopIntroData(null);
    setShowOdopAlignmentCard(false);
    setShowOdopIntroCard(false);
    setShowEnterpriseCard(false);
    setChatStep("business_idea");
    setPhase("chatting");
    setMessages(prev => [...prev, {
      id: `assistant-revise-${Date.now()}`,
      role: "assistant",
      content: selectedLang === "en"
        ? "Let's revise your business idea. Tell me what you want to make, sell, or provide, and I will reassess the sector, equipment, and ODOP fit."
        : "आइए व्यवसाय विचार फिर से देखें। बताइए आप क्या बनाएँगे, बेचेंगे या सेवा देंगे; मैं क्षेत्र, उपकरण और ODOP तालमेल फिर जाँचूँगी।",
      timestamp: new Date().toISOString(),
    }]);
  };

  // ─── Step 1c: User submits updated location menu ─────────────────────────
  const handleSubmitNewLocation = async () => {
    if (!selectedState || !selectedDistrict) {
      alert(selectedLang === "en" ? "Please select both State and District." : "कृपया राज्य और ज़िला दोनों चुनें।");
      return;
    }

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
        setShowLocationMenu(false);
        setLocationConfirmed(true);
        setLocationWasChanged(true);
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

  // ─── Conversational Chat Turns (Business Idea, Promoter Equity, Q&A) ───
  const handleSendMessage = useCallback(async (overrideText = null) => {
    const text = overrideText || inputText.trim();
    if (!text || isSending || !["business_idea", "promoter_equity", "split_screen"].includes(chatStep)) return;
    setChatError("");

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

      const action = chatStep === "business_idea" ? "business_idea" : chatStep === "promoter_equity" ? "promoter_equity" : chatStep === "split_screen" ? "chat_only" : null;
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
          current_action: action,
          user_location: locCoords,
        }),
      });

      if (!response.ok) throw new Error(`Mira could not process this answer (${response.status}). Please try again.`);

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

        // Step 3: ODOP Intro & Check Prompt
        if (data.odop_intro || data.next_phase === "odop_check_prompt") {
          setOdopIntroData(data.odop_intro);
          setShowOdopIntroCard(true);
          setChatStep("odop_check_prompt");
        }

        // Step 4: ODOP Alignment Evaluation
        if (data.odop_alignment || data.next_phase === "odop_alignment") {
          setOdopData(data.odop_alignment);
          setShowOdopAlignmentCard(true);
          setChatStep("odop_alignment");
        }

        // Step 5: Enterprise Info Card
        if (data.next_phase === "enterprise_info") {
          setShowOdopIntroCard(false);
          setShowOdopAlignmentCard(false);
          setShowEnterpriseCard(true);
          setChatStep("enterprise_info");
          if (data.extracted_fields?.enterprise_name) {
            setEnterpriseNameInput(data.extracted_fields.enterprise_name);
          }
        }

        // Step 6: Promoter Equity
        if (data.next_phase === "promoter_equity") {
          setChatStep("promoter_equity");
        }

        // Step 7: Machinery Selection Card
        if (data.next_phase === "machinery_selection") {
          setShowEnterpriseCard(false);
          setChatStep("machinery_selection");
          if (data.applicable_machinery) {
            setApplicableMachinery(data.applicable_machinery);
            setMachineryConfirmed(false);
          }
        }

        // Step 8: 50/50 Split Screen Form
        if (data.next_phase === "split_screen" || (data.all_fields_collected && chatStep === "machinery_selection")) {
          setPhase("split_screen");
          setChatStep("split_screen");
        }

        const assistantMsg = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.reply || "मैं समझ गई।",
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMsg]);
        playTTS(data.tts_text || data.reply, selectedLang || "hi");

        if (data.next_phase === "split_screen") {
          setTimeout(() => {
            setPhase("split_screen");
          }, 1500);
        }
      }
    } catch (err) {
      console.error("Mira chat turn error:", err);
      setChatError(err.message || "Mira could not respond. Please try again.");
    } finally {
      setIsSending(false);
    }
  }, [inputText, isSending, messages, selectedLang, userName, collectedFields, token, getAutoDetectedLocation, playTTS, chatStep]);

  // ─── Step 3a: Check ODOP Alignment ("Let's Check") ─────────────────────
  const handleCheckOdopAlignment = useCallback(async () => {
    if (isSending) return;
    setIsSending(true);

    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: selectedLang === "en" ? "Let's Check" : "तालमेल जाँचें",
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
          current_action: "check_odop_alignment",
          user_location: locCoords,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setShowOdopIntroCard(false);
        if (data.extracted_fields) {
          setCollectedFields(prev => ({ ...prev, ...data.extracted_fields }));
        }
        if (data.odop_alignment) {
          setOdopData(data.odop_alignment);
          setShowOdopAlignmentCard(true);
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
      }
    } catch (err) {
      console.error("Check ODOP alignment error:", err);
    } finally {
      setIsSending(false);
    }
  }, [isSending, selectedLang, messages, token, userName, collectedFields, getAutoDetectedLocation, playTTS]);

  // ─── Step 3b: Skip ODOP Alignment ("Will go with my idea") ─────────────
  const handleSkipOdopAlignment = useCallback(async () => {
    if (isSending) return;
    setIsSending(true);

    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: selectedLang === "en" ? "Will go with my idea" : "मूल विचार से चलें",
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
          current_action: "skip_odop_alignment",
          user_location: locCoords,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setShowOdopIntroCard(false);
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

        if (data.next_phase === "enterprise_info") {
          setShowEnterpriseCard(true);
          setChatStep("enterprise_info");
          if (data.extracted_fields?.enterprise_name) {
            setEnterpriseNameInput(data.extracted_fields.enterprise_name);
          }
        }
      }
    } catch (err) {
      console.error("Skip ODOP alignment error:", err);
    } finally {
      setIsSending(false);
    }
  }, [isSending, selectedLang, messages, token, userName, collectedFields, getAutoDetectedLocation, playTTS]);

  // ─── Step 7: Owned Machinery Selection ──────────────────────────────────
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

        const assistantMsg = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.reply,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMsg]);
        playTTS(data.tts_text || data.reply, selectedLang || "hi");

        if (data.next_phase === "split_screen" || data.all_fields_collected) {
          setTimeout(() => {
            setPhase("split_screen");
          }, 1500);
        }
      }
    } catch (err) {
      console.error("Machinery selection error:", err);
    } finally {
      setIsSending(false);
    }
  }, [isSending, selectedLang, messages, token, userName, collectedFields, applicableMachinery, getAutoDetectedLocation, playTTS]);

  // ─── Step 4: ODOP Decision (Align vs Keep Original Idea) ────────────────
  const handleOdopDecision = useCallback(async (alignWithOdop) => {
    if (isSending) return;
    setIsSending(true);

    const decision = alignWithOdop ? "align" : "keep_original";
    const decisionLabel = alignWithOdop
      ? (selectedLang === "en" ? "1. Align with ODOP (Unlock 35% Subsidy)" : "1. ODOP से जुड़ें (35% सब्सिडी)")
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
        setShowOdopAlignmentCard(false);
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

        // After ODOP decision → Step 5: Show Enterprise Info card
        if (data.next_phase === "enterprise_info") {
          setShowEnterpriseCard(true);
          setChatStep("enterprise_info");
          if (data.extracted_fields?.enterprise_name) {
            setEnterpriseNameInput(data.extracted_fields.enterprise_name);
          } else if (collectedFields.enterprise_name) {
            setEnterpriseNameInput(collectedFields.enterprise_name);
          }
        }
      }
    } catch (err) {
      console.error("ODOP decision error:", err);
    } finally {
      setIsSending(false);
    }
  }, [isSending, selectedLang, messages, token, userName, collectedFields, getAutoDetectedLocation, playTTS]);

  // ─── Step 5: Enterprise Name + Caste Category Submission ────────────────
  const handleSubmitEnterpriseInfo = useCallback(async () => {
    if (isSending) return;
    const entName = enterpriseNameInput.trim() || `${userName}'s Enterprise`;
    const promCat = promoterCategoryInput || "general";

    setIsSending(true);

    const catLabel = PROMOTER_CATEGORIES.find(c => c.value === promCat)?.label || promCat;
    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: selectedLang === "en"
        ? `Enterprise: ${entName} | Category: ${catLabel}`
        : `उद्यम: ${entName} | श्रेणी: ${catLabel}`,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);

    // Update collected fields locally
    const updatedFields = { ...collectedFields, enterprise_name: entName, promoter_category: promCat };
    setCollectedFields(updatedFields);

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
          collected_fields: updatedFields,
          conversation_step: messages.length + 1,
          current_action: "submit_enterprise_info",
          user_location: locCoords,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setShowEnterpriseCard(false);
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
        setChatStep("promoter_equity");
        playTTS(data.tts_text || data.reply, selectedLang || "hi");

        if (data.all_fields_collected) {
          setTimeout(() => { setPhase("processing"); }, 2600);
        }
      }
    } catch (err) {
      console.error("Enterprise info submission error:", err);
    } finally {
      setIsSending(false);
    }
  }, [isSending, enterpriseNameInput, promoterCategoryInput, userName, selectedLang, messages, collectedFields, token, getAutoDetectedLocation, playTTS]);

  // ─── Step 6: Final Feasibility Appraisal Report Generation ─────────────
  const handleFinalSubmit = useCallback(async () => {
    const submitFn = onWizardSubmit || createAndSaveBusiness;
    if (!submitFn) return;
    if (!collectedFields.enterprise_name?.trim() || !collectedFields.state_name || !collectedFields.district_name || Number(collectedFields.project_cost) <= 0) {
      setSubmitError("Please provide an enterprise name, state, district, and a valid project cost.");
      return;
    }
    setSubmitError("");
    try {
      const locCoords = getAutoDetectedLocation();
      await submitFn({
        ...collectedFields,
        language: selectedLang || "en",
        latitude: locationWasChanged ? null : locCoords?.latitude || null,
        longitude: locationWasChanged ? null : locCoords?.longitude || null,
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      console.error("Final appraisal generation failed:", err);
      setSubmitError(err.message || "The report could not be generated. Please review the form and try again.");
    }
  }, [collectedFields, selectedLang, onWizardSubmit, createAndSaveBusiness, getAutoDetectedLocation, locationWasChanged, navigate]);

  // Tap once to record, then tap again to transcribe and send the answer.
  const startRecording = useCallback(async () => {
    if (recordingStartingRef.current || mediaRecorderRef.current || isSending || isTranscribing) return;
    recordingStartingRef.current = true;
    setIsStartingRecording(true);
    let stream;
    try {
      stopAudio();
      if (!navigator.mediaDevices?.getUserMedia) throw new Error("Microphone access is unavailable. Please use a secure browser connection.");
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const format = chooseRecordingFormat();
      const mediaRecorder = new MediaRecorder(stream, format.mimeType ? { mimeType: format.mimeType } : undefined);
      recordingStreamRef.current = stream;
      audioChunksRef.current = [];
      mediaRecorderRef.current = mediaRecorder;
      setChatError("");

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      mediaRecorder.onerror = () => setChatError("Recording stopped unexpectedly. Please try again.");

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        recordingStreamRef.current = null;
        mediaRecorderRef.current = null;
        setIsRecording(false);
        const audioBlob = new Blob(audioChunksRef.current, { type: format.mimeType || mediaRecorder.mimeType || "audio/webm" });
        if (Date.now() - recordingStartedAtRef.current < 500 || !audioBlob.size) {
          setChatError("Recording was too short. Tap the microphone, speak, then tap again to send.");
          return;
        }
        setIsTranscribing(true);
        try {
          const transcript = await transcribeOnboardingAudio(audioBlob, {
            language: selectedLang || "hi", token, extension: format.extension,
          });
          setIsTranscribing(false);
          await handleSendMessage(transcript);
        } catch (e) {
          console.error("Voice recording processing error:", e);
          setChatError(e.message || "Voice input failed. Please try again or type your answer.");
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorder.start();
      recordingStartedAtRef.current = Date.now();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access error:", err);
      stream?.getTracks().forEach(track => track.stop());
      recordingStreamRef.current = null;
      mediaRecorderRef.current = null;
      setChatError(err.name === "NotAllowedError" ? "Microphone permission was denied. Allow access in your browser and try again." : err.message || "Could not start the microphone.");
    } finally {
      recordingStartingRef.current = false;
      setIsStartingRecording(false);
    }
  }, [selectedLang, token, handleSendMessage, isSending, isTranscribing, stopAudio]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  const toggleRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") stopRecording();
    else startRecording();
  }, [startRecording, stopRecording]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // ─── Render: Language Selection Phase ───────────────────────────────────
  if (phase === "lang_select") {
    return (
      <div className="min-h-screen flex items-center px-4 py-10 sm:py-16 relative overflow-hidden" style={{ background: "linear-gradient(125deg, #fff1f2, #eff6ff, #f0fdf4, #fff7ed)", backgroundSize: "300% 300%", animation: "dynamicPastel 18s ease-in-out infinite" }}>
        <div className="absolute -top-24 -left-20 w-80 h-80 rounded-full bg-rose-200/45 blur-[100px] pointer-events-none" />
        <div className="absolute -bottom-24 right-0 w-96 h-96 rounded-full bg-sky-200/50 blur-[110px] pointer-events-none" />

        <div className="max-w-5xl w-full mx-auto relative z-10 grid lg:grid-cols-[0.9fr_1.1fr] gap-8 lg:gap-12 items-center">
          <div className="text-center lg:text-left">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/90 bg-white/75 px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.15em] text-indigo-700 shadow-sm mb-6"><Sparkles className="w-3.5 h-3.5 text-rose-500" /> Your journey starts here</span>
            <MiraAvatar size="w-24 h-24" rounded="rounded-[2rem]" className="mx-auto lg:mx-0 mb-6 shadow-xl shadow-pink-500/20 ring-4 ring-white" />
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-slate-900 font-display tracking-tight leading-tight mb-4">
              Namaste, {userName} Ji<span className="text-rose-500">.</span>
            </h1>
            <p className="text-base text-slate-600 max-w-lg mx-auto lg:mx-0 leading-relaxed">
              Meet Mira, your guide from the first idea to a bank-ready enterprise plan. Choose the language you feel most comfortable speaking.
            </p>
            <div className="mt-7 flex flex-wrap justify-center lg:justify-start gap-2 text-xs font-semibold text-slate-600">
              <span className="rounded-full bg-white/80 border border-white px-3 py-2">01 · Choose language</span>
              <span className="rounded-full bg-white/60 border border-white px-3 py-2">02 · Tell Mira your idea</span>
              <span className="rounded-full bg-white/60 border border-white px-3 py-2">03 · Review your plan</span>
            </div>
          </div>

          <div className="rounded-[2rem] border border-white/90 bg-white/80 backdrop-blur-xl shadow-2xl shadow-indigo-950/10 p-5 sm:p-7">
            <div className="mb-5">
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-rose-600">Speak naturally</p>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">Choose your language</h2>
              <p className="text-sm text-slate-500 mt-1">You can change it later from the dashboard.</p>
            </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {ONBOARDING_LANGUAGES.map((lang) => {
              const isSelected = selectedLang === lang.code;
              return (
                <button
                  key={lang.code}
                  onClick={() => handleLanguageSelect(lang.code)}
                  aria-label={`Continue in ${lang.label}`}
                  className={`group relative rounded-2xl p-5 text-left transition-all duration-300 ease-out cursor-pointer border-2 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-300 ${
                    isSelected
                      ? `${lang.gradientBorder} ring-4 ${lang.selectedGlow} shadow-xl scale-[1.02]`
                      : `border-slate-200/80 hover:border-indigo-300 hover:shadow-lg hover:-translate-y-0.5 shadow-sm`
                  } bg-white`}
                >
                  <div className={`absolute top-0 left-3 right-3 h-1 rounded-b-full bg-gradient-to-r ${lang.gradient} ${isSelected ? 'opacity-100' : 'opacity-0'} group-hover:opacity-100 transition-opacity duration-300`} />
                  <div className="text-xl sm:text-2xl font-black text-slate-900 mb-2 group-hover:text-indigo-950 transition-colors">
                    {lang.native}
                  </div>
                  <div className="flex items-center justify-between gap-2 text-xs text-slate-500 font-semibold tracking-wide">
                    <span>{lang.label}</span><ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all" />
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
          <p className="text-[11px] text-slate-500 mt-5 text-center">Your selection is saved to your account.</p>
          </div>
        </div>

        <style>{`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
          }
          @keyframes dynamicPastel {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
          }
        `}</style>
      </div>
    );
  }

  // ─── Render: Chat Phase with Mira ───────────────────────────────────────
  return (
    <div
      className="min-h-screen flex flex-col relative overflow-hidden"
      style={{
        background: 'linear-gradient(-45deg, #fef2f2 0%, #fff7ed 16%, #fdf4ff 33%, #eff6ff 50%, #f0fdf4 67%, #fefce8 84%, #faf5ff 100%)',
        backgroundSize: '350% 350%',
        animation: 'dynamicPastel 14s ease-in-out infinite',
      }}
    >
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[36rem] h-[36rem] bg-rose-100/25 blur-[160px] rounded-full pointer-events-none" />

      {/* Header Bar */}
      <header className="sticky top-0 z-30 bg-white/85 backdrop-blur-2xl text-slate-900 px-4 py-3 border-b border-white/90 shadow-[0_8px_30px_rgba(30,41,59,0.05)]">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <MiraAvatar size="w-11 h-11" rounded="rounded-2xl" className="ring-2 ring-rose-100" />
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-bold truncate flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-rose-500" />
              Mira <span className="font-medium text-slate-400">/</span> Your business guide
            </h1>
            <p className="text-[11px] text-slate-500 truncate flex items-center gap-1.5">
              <span>{selectedLang && ONBOARDING_LANGUAGES.find(l => l.code === selectedLang)?.native}</span>
              <span>•</span>
              {isPlayingAudio ? (
                <span className="text-emerald-300 font-semibold animate-pulse flex items-center gap-1">
                  <Volume2 className="w-3 h-3" /> Speaking...
                </span>
              ) : (
                <span className="text-emerald-700">Here to help you plan</span>
              )}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {isPlayingAudio && (
              <button
                type="button"
                onClick={stopAudio}
                className="px-2.5 py-1 rounded-lg bg-rose-50 text-rose-700 border border-rose-200 text-[10px] font-bold hover:bg-rose-100 transition-colors flex items-center gap-1 cursor-pointer"
                title="Stop speech"
              >
                <VolumeX className="w-3 h-3" /> Stop
              </button>
            )}

            {Object.keys(collectedFields).length > 0 && (
              <div className="text-[10px] bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-lg border border-emerald-200 font-bold">
                {Object.keys(collectedFields).filter(k => !["latitude", "longitude"].includes(k)).length} Details Filled
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-4xl w-full mx-auto px-4 pt-5">
        <div className="rounded-2xl bg-white/85 backdrop-blur border border-white/90 shadow-[0_12px_35px_rgba(30,41,59,0.06)] px-4 sm:px-5 py-4 flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-bold tracking-[0.18em] uppercase text-rose-600">Your venture, step by step</p>
            <p className="text-sm font-semibold text-slate-800">
              {{ location_confirm: "Confirm your location", location_menu: "Choose your location", business_idea: "Describe your idea", odop_check_prompt: "Explore district ODOP", odop_alignment: "Choose your ODOP path", enterprise_info: "Name your enterprise", promoter_equity: "Plan your investment", machinery_selection: "Review equipment" }[chatStep] || "Review your plan"}
            </p>
          </div>
          <span className="shrink-0 rounded-full bg-rose-50 border border-rose-200 text-rose-700 px-3 py-1 text-xs font-bold">
            {STEP_NUMBER[chatStep] || 7} / 7
          </span>
        </div>
        <div className="mt-2 h-1.5 rounded-full bg-white/70 overflow-hidden" aria-label={`Onboarding step ${STEP_NUMBER[chatStep] || 7} of 7`}>
          <div className="h-full rounded-full bg-gradient-to-r from-rose-400 via-amber-400 to-emerald-400 transition-all duration-500" style={{ width: `${((STEP_NUMBER[chatStep] || 7) / 7) * 100}%` }} />
        </div>
      </div>

      {/* Messages Area */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-3 sm:px-4 pt-6 sm:pt-8 pb-6 scroll-smooth">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className="space-y-2.5">
              <div
                className={`flex gap-2.5 animate-[fadeIn_0.3s_ease-out] ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.role === "assistant" && (
                  <MiraAvatar size="w-8 h-8" rounded="rounded-xl" className="mt-0.5" />
                )}

                <div
                  className={`max-w-[85%] sm:max-w-[75%] rounded-[1.4rem] px-4 sm:px-5 py-3.5 text-sm leading-7 shadow-[0_8px_24px_rgba(30,41,59,0.07)] ${
                    msg.role === "user"
                      ? "bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-indigo-900 text-white rounded-br-md"
                      : "bg-white/95 text-slate-800 border border-white rounded-bl-md"
                  }`}
                >
                  <div className="whitespace-pre-wrap"><FormattedMessage content={msg.content} /></div>

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

              {/* ─── Step 1 Action Buttons: Location Confirmation (Auto-closes on click) ─── */}
              {msg.isLocationConfirmation && chatStep === "location_confirm" && !locationConfirmed && (
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

          {/* ─── Step 3: ODOP Introduction & Check Prompt Card (auto-closes on click) ─── */}
          {showOdopIntroCard && odopIntroData && (
            <div className="animate-[fadeIn_0.4s_ease-out] max-w-xl mx-auto my-3">
              <div className="bg-white rounded-3xl border-2 border-amber-400/80 shadow-2xl overflow-hidden">
                {/* Header Banner */}
                <div className="bg-gradient-to-r from-amber-50 via-orange-50 to-rose-50 text-slate-900 p-4 sm:p-5 relative border-b border-amber-200">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-white text-amber-800 border border-amber-300">
                      <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                      {selectedLang === "en" ? "ODOP Scheme Opportunity" : "ODOP योजना अवसर"}
                    </span>
                    <span className="text-xs text-amber-800 font-semibold flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> {selectedLang === "en" ? "Eligibility check" : "पात्रता जाँच"}
                    </span>
                  </div>

                  <h3 className="text-base sm:text-lg font-bold font-display text-slate-900">
                    {selectedLang === "en"
                      ? `Could ${collectedFields.business_idea || "your idea"} fit the district ODOP?`
                      : `क्या ${collectedFields.business_idea || "आपका विचार"} ज़िला ODOP से जुड़ सकता है?`}
                  </h3>
                  <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                    {selectedLang === "en"
                      ? `ODOP means One District One Product. ${odopIntroData.district} identifies ${odopIntroData.odop_product} as its product. A real link may help local sourcing and eligibility for ${odopIntroData.scheme}; benefits depend on scheme rules. Shall I assess your idea?`
                      : `ODOP यानी एक ज़िला एक उत्पाद। ${odopIntroData.district} का उत्पाद ${odopIntroData.odop_product} है। वास्तविक तालमेल से स्थानीय आपूर्ति और ${odopIntroData.scheme} की पात्रता जाँची जा सकती है; लाभ नियमों पर निर्भर हैं। क्या मैं आपके विचार की जाँच करूँ?`}
                  </p>
                </div>

                <div className="p-4 sm:p-5 space-y-4">
                  {/* District & Scheme Badge */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="p-3 rounded-2xl bg-amber-50/80 border border-amber-200">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-amber-800 mb-0.5">
                        {selectedLang === "en" ? "District ODOP Produce" : "ज़िला ODOP उत्पाद"}
                      </div>
                      <div className="font-bold text-sm text-slate-900 flex items-center gap-1.5">
                        <span>🌾</span>
                        <span className="truncate">{odopIntroData.odop_product}</span>
                      </div>
                    </div>
                    <div className="p-3 rounded-2xl bg-emerald-50/80 border border-emerald-200">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 mb-0.5">
                        {selectedLang === "en" ? "Government Scheme" : "पात्र सरकारी योजना"}
                      </div>
                      <div className="font-bold text-sm text-emerald-950 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span className="truncate">{odopIntroData.scheme || "PMEGP / ODOP Scheme"}</span>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="pt-1 flex flex-col sm:flex-row gap-2.5">
                    <button
                      type="button"
                      onClick={handleCheckOdopAlignment}
                      disabled={isSending}
                      className="flex-1 py-3 px-4 rounded-xl font-bold text-xs text-white bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 hover:from-emerald-500 hover:to-teal-500 shadow-md shadow-emerald-950/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                    >
                      <Sparkles className="w-4 h-4 text-emerald-200" />
                      <span>
                        {selectedLang === "en" ? "Let's Check (Evaluate Synergy)" : "तालमेल जाँचें (Let's Check)"}
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={handleSkipOdopAlignment}
                      disabled={isSending}
                      className="sm:w-auto py-3 px-4 rounded-xl font-semibold text-xs text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/80 transition-colors cursor-pointer disabled:opacity-50"
                    >
                      {selectedLang === "en" ? "Will go with my idea" : "मूल विचार से चलें"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ─── Step 4: 0-100 Benchmarked ODOP Alignment Synergy Card (auto-closes on decision) ─── */}
          {showOdopAlignmentCard && odopData && !collectedFields.odop_decision && (
            <div className="animate-[fadeIn_0.4s_ease-out] max-w-xl mx-auto my-3">
              <div className="bg-white rounded-3xl border-2 border-emerald-400/80 shadow-2xl overflow-hidden">
                {/* Header Banner */}
                <div className="bg-gradient-to-r from-emerald-50 via-teal-50 to-sky-50 text-slate-900 p-4 sm:p-5 relative border-b border-emerald-200">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-white text-emerald-800 border border-emerald-300">
                      <Sparkles className="w-3.5 h-3.5" />
                      ODOP Synergy Benchmarking
                    </span>
                    <span className="text-xs text-emerald-800 font-semibold flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" /> {selectedLang === "en" ? "Assessment complete" : "मूल्यांकन पूरा"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-4 mt-2">
                    <div>
                      <h3 className="text-base sm:text-lg font-bold font-display text-slate-900">
                        {selectedLang === "en"
                          ? "One District One Product Synergy Match"
                          : "एक जिला एक उत्पाद (ODOP) तालमेल स्कोर"}
                      </h3>
                      <p className="text-xs text-emerald-900 mt-0.5">
                        {odopData.mira_recommendation || "Mira's Strategic Evaluation"}
                      </p>
                    </div>

                    {/* 0-100 Score Gauge Badge */}
                    <div className="shrink-0 flex flex-col items-center justify-center w-16 h-16 rounded-2xl bg-white border border-emerald-200 shadow-sm">
                      <span className="text-xl font-black text-emerald-700 leading-none">
                        {odopData.alignment_score ?? 0}
                      </span>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mt-0.5">
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
                      {odopData.what_is_odop || "The One District One Product (ODOP) initiative by the central government focuses on each district's designated indigenous product to provide capital subsidies, priority procurement on GeM, and cluster common facility centers."}
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

                  {/* Decision Buttons */}
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
                          ? "Align with ODOP strategy"
                          : "ODOP रणनीति से जोड़ें"}
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
                </div>
              </div>
            </div>
          )}

          {/* ─── Step 5: Enterprise Name + Caste Category Card (auto-closes on submit) ─── */}
          {showEnterpriseCard && (
            <div className="animate-[fadeIn_0.4s_ease-out] max-w-lg mx-auto my-3">
              <div className="bg-white rounded-3xl border-2 border-violet-400/80 shadow-2xl overflow-hidden">
                <div className="bg-gradient-to-r from-violet-50 via-indigo-50 to-sky-50 text-slate-900 p-4 sm:p-5 border-b border-violet-200">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-white text-violet-800 border border-violet-200">
                      <User className="w-3.5 h-3.5" />
                      {selectedLang === "en" ? "Enterprise Details" : "उद्यम विवरण"}
                    </span>
                  </div>
                  <h3 className="text-base sm:text-lg font-bold font-display text-slate-900">
                    {selectedLang === "en"
                      ? "Your Enterprise Name & Category"
                      : "आपके उद्यम का नाम और जाति श्रेणी"}
                  </h3>
                  <p className="text-xs text-slate-600 mt-1">
                    {selectedLang === "en"
                      ? "Please share your enterprise name and caste category for government scheme eligibility."
                      : "कृपया अपने उद्यम का नाम और सरकारी योजना पात्रता के लिए जाति श्रेणी बताएं।"}
                  </p>
                </div>

                <div className="p-4 sm:p-6 space-y-4">
                  {/* Enterprise Name Input */}
                  <div>
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1.5 flex items-center gap-1.5">
                      <Edit3 className="w-3.5 h-3.5 text-violet-600" />
                      {selectedLang === "en" ? "Enterprise Name" : "उद्यम का नाम"}
                    </label>
                    <input
                      type="text"
                      value={enterpriseNameInput}
                      onChange={(e) => setEnterpriseNameInput(e.target.value)}
                      placeholder={selectedLang === "en" ? `${userName}'s Enterprise` : `${userName} का उद्यम`}
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500 transition-all"
                    />
                  </div>

                  {/* Caste Category Dropdown */}
                  <div>
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1.5 flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                      {selectedLang === "en" ? "Caste Category (for Subsidy Eligibility)" : "जाति श्रेणी (सब्सिडी पात्रता हेतु)"}
                    </label>
                    <select
                      value={promoterCategoryInput}
                      onChange={(e) => setPromoterCategoryInput(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-violet-500/40 cursor-pointer"
                    >
                      {PROMOTER_CATEGORIES.map(cat => (
                        <option key={cat.value} value={cat.value}>
                          {selectedLang === "en" ? cat.label : cat.labelHi} ({cat.value.toUpperCase()})
                        </option>
                      ))}
                    </select>
                    <p className="mt-1.5 text-[10px] text-slate-500">
                      {selectedLang === "en"
                        ? "SC/ST/OBC categories may qualify for higher PMEGP subsidy (25-35% vs 15-25%)."
                        : "SC/ST/OBC श्रेणियों को PMEGP में अधिक सब्सिडी (25-35% बनाम 15-25%) मिल सकती है।"}
                    </p>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="button"
                    onClick={handleSubmitEnterpriseInfo}
                    disabled={isSending}
                    className="w-full py-3.5 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-violet-600 via-indigo-600 to-violet-700 hover:from-violet-500 hover:to-indigo-500 shadow-lg shadow-violet-950/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                  >
                    <Check className="w-4 h-4" />
                    <span>
                      {selectedLang === "en"
                        ? "Save & Continue"
                        : "सुरक्षित करें और आगे बढ़ें"}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ─── Step 7: Interactive Machinery Dropdown & Checklist Card (auto-closes on confirm) ───── */}
          {chatStep === "machinery_selection" && applicableMachinery && !machineryConfirmed && (
            <div className="animate-[fadeIn_0.4s_ease-out] max-w-xl mx-auto my-3">
              <div className="bg-white rounded-3xl border-2 border-indigo-400/80 shadow-2xl overflow-hidden">
                {/* Header Banner */}
                <div className="bg-gradient-to-r from-sky-50 via-indigo-50 to-violet-50 text-slate-900 p-4 sm:p-5 relative border-b border-indigo-200">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-white text-indigo-800 border border-indigo-200">
                      <Wrench className="w-3.5 h-3.5" />
                      {selectedLang === "en" ? "Standard MSME Plant & Machinery" : "मानक प्लांट एवं मशीनरी"}
                    </span>
                    <span className="text-xs text-indigo-700 font-semibold flex items-center gap-1">
                      <Zap className="w-3.5 h-3.5 text-amber-400" />
                      {applicableMachinery.typical_capacity || (selectedLang === "en" ? "Idea-specific plan" : "आपके विचार के अनुसार")}
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-4 mt-2">
                    <div>
                      <h3 className="text-base sm:text-lg font-bold font-display text-slate-900">
                        {applicableMachinery.business_name || collectedFields.business_idea || "Your business"}
                      </h3>
                      <p className="text-xs text-slate-600 mt-0.5">
                        {selectedLang === "en"
                          ? "Here is the catalogue-backed equipment for your idea. Select what you already own so its verified estimate can be considered in the project outlay."
                          : "यह आपके विचार के लिए सूचीबद्ध उपकरण हैं। जो पहले से आपके पास हैं उन्हें चुनें, ताकि उनकी सत्यापित अनुमानित लागत परियोजना में गिनी जा सके।"}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 sm:p-6 space-y-4 text-slate-800">
                  {applicableMachinery.machinery_list.length === 0 && (
                    <div className="rounded-2xl bg-amber-50 border border-amber-200 p-4 text-sm text-amber-950">
                      {selectedLang === "en"
                        ? "The machinery catalogue has no production equipment for this idea. If you plan to manufacture rather than sell finished goods, describe that in the review form."
                        : "इस विचार के लिए उत्पादन मशीनें सूची में नहीं हैं। यदि आप तैयार सामान बेचने के बजाय बनाना चाहते हैं, तो समीक्षा फॉर्म में यह स्पष्ट करें।"}
                    </div>
                  )}
                  {/* Quick-Pick Dropdown */}
                  {applicableMachinery.machinery_list.length > 0 && <div className="p-3.5 rounded-2xl bg-indigo-50/70 border border-indigo-200">
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
                  </div>}

                  {/* Visual Checklist Cards */}
                  {applicableMachinery.machinery_list.length > 0 && <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
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
                  </div>}

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

                  {/* Action Buttons */}
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
                            ? (applicableMachinery.machinery_list.length ? "I don't own any of these" : "Continue with this idea")
                            : (applicableMachinery.machinery_list.length ? "मेरे पास इनमें से कोई मशीन नहीं है" : "इस विचार के साथ आगे बढ़ें")}
                        </span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Typing Indicator */}
          {chatError && (
            <div role="alert" className="max-w-xl mx-auto rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
              {chatError}
            </div>
          )}
          {isSending && (
            <div className="flex gap-2.5 animate-[fadeIn_0.2s_ease-out]">
              <MiraAvatar size="w-8 h-8" rounded="rounded-xl" />
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
      <div className="sticky bottom-0 z-20 bg-white/90 backdrop-blur-xl border-t border-white px-3 sm:px-4 py-3 shadow-[0_-12px_35px_rgba(30,41,59,0.07)]">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-2">
            <button
              type="button"
              onClick={toggleRecording}
              disabled={isSending || isTranscribing || isStartingRecording || !["business_idea", "promoter_equity"].includes(chatStep)}
              aria-label={isRecording ? "Stop recording and transcribe" : "Start voice recording"}
              aria-pressed={isRecording}
              className={`shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition-all duration-200 cursor-pointer ${
                isRecording
                  ? "bg-rose-500 text-white shadow-lg shadow-rose-500/30 scale-110 animate-pulse"
                  : "bg-slate-100 text-slate-600 hover:bg-rose-100 hover:text-rose-800 border border-slate-200"
              }`}
              title={isRecording ? "Tap to stop and send" : "Tap to start recording"}
            >
              {isStartingRecording || isTranscribing ? <Loader2 className="w-5 h-5 animate-spin" /> : isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  selectedLang === "en"
                    ? "Type your answer or tap the mic to speak..."
                    : "जवाब लिखें या बोलने के लिए माइक दबाएँ..."
                }
                rows={1}
                disabled={isSending || !["business_idea", "promoter_equity"].includes(chatStep)}
                className="w-full resize-none rounded-xl bg-slate-50 border border-slate-200 px-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500/40 focus:border-rose-500 transition-all max-h-32 overflow-y-auto"
                style={{ minHeight: "44px" }}
              />
            </div>

            <button
              type="button"
              onClick={() => handleSendMessage()}
              disabled={!inputText.trim() || isSending || !["business_idea", "promoter_equity"].includes(chatStep)}
              className="shrink-0 w-11 h-11 rounded-xl bg-gradient-to-r from-rose-600 via-pink-600 to-indigo-800 text-white flex items-center justify-center shadow-md shadow-pink-950/20 hover:shadow-lg disabled:opacity-40 transition-all duration-200 cursor-pointer"
            >
              {isSending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </div>

          <div className="mt-1.5 flex items-center justify-between text-[11px] text-slate-400 px-1">
            <span>
              {isRecording
                ? "🎙️ Recording · tap the mic again to send"
                : isTranscribing ? "Transcribing your voice..." : isStartingRecording ? "Opening microphone..."
                : (selectedLang === "en" ? "Enter to send · tap mic to record" : "भेजने के लिए Enter दबाएँ · रिकॉर्ड करने के लिए माइक दबाएँ")}
            </span>
            <span className="truncate max-w-[220px]">
              {collectedFields.district_name 
                ? `📍 ${collectedFields.district_name}, ${collectedFields.state_name || ''}` 
                : `📍 ${collectedFields.district_name || detectedLocationData?.district_name || "Pune"}, ${collectedFields.state_name || "Maharashtra"}`}
            </span>
          </div>
        </div>
      </div>

      {/* ─── Step 8: 50/50 Split-Screen (Left=Chat, Right=Editable Form) ── */}
      {(phase === "split_screen" || phase === "processing") && (
          <div className="fixed inset-0 z-50 backdrop-blur-xl flex flex-col lg:flex-row animate-[fadeIn_0.3s_ease-out]" style={{ background: "linear-gradient(-45deg, #fff1f2, #fff7ed, #eff6ff, #ecfdf5, #faf5ff)", backgroundSize: "350% 350%", animation: "dynamicPastel 16s ease-in-out infinite" }}>
          {/* Left Panel: Chat History + Active Input (scrollable) */}
          <div className="w-full lg:w-1/2 h-[44%] lg:h-full border-b lg:border-b-0 lg:border-r border-white/90 flex flex-col bg-gradient-to-br from-rose-50/60 via-white to-indigo-50/60">
            <div className="bg-white/85 backdrop-blur text-slate-900 px-5 py-4 flex items-center justify-between shrink-0 border-b border-white shadow-sm">
              <div className="flex items-center gap-3">
                <MiraAvatar size="w-11 h-11" rounded="rounded-2xl" className="ring-2 ring-rose-100" />
                <div>
                  <h2 className="text-sm sm:text-base font-bold flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-rose-500" />
                    {selectedLang === "en" ? "Chat with Mira" : "Mira से बातचीत"}
                  </h2>
                  <p className="text-[11px] text-slate-500">{selectedLang === "en" ? "Your plan is ready to review together" : "आपकी योजना समीक्षा के लिए तैयार है"}</p>
                </div>
              </div>

              {isPlayingAudio && (
                <button
                  type="button"
                  onClick={stopAudio}
                  className="px-2.5 py-1 rounded-lg bg-rose-50 text-rose-700 border border-rose-200 text-[10px] font-bold hover:bg-rose-100 transition-colors flex items-center gap-1 cursor-pointer"
                  title="Stop speech"
                >
                  <VolumeX className="w-3 h-3" /> Stop
                </button>
              )}
            </div>

            <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-5 space-y-4">
              {messages.map(msg => (
                <div key={msg.id} className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  {msg.role === "assistant" && (
                    <MiraAvatar size="w-7 h-7" rounded="rounded-lg" />
                  )}
                  <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs sm:text-sm leading-relaxed shadow-sm ${
                    msg.role === "user"
                      ? "bg-gradient-to-r from-sovereign-900 to-indigo-900 text-white rounded-br-sm shadow-sm"
                      : "bg-white text-slate-700 border border-white rounded-bl-sm"
                  }`}>
                    <div className="whitespace-pre-wrap"><FormattedMessage content={msg.content} /></div>
                  </div>
                  {msg.role === "user" && (
                    <div className="w-7 h-7 rounded-lg bg-slate-200 flex items-center justify-center text-slate-700 text-[10px] font-bold shrink-0 mt-0.5">
                      {userName.charAt(0).toUpperCase()}
                    </div>
                  )}
                </div>
              ))}
              {isSending && (
                <div className="flex gap-2 items-center text-xs text-slate-500 pt-1">
                  <MiraAvatar size="w-6 h-6" rounded="rounded-lg" />
                  <span className="italic flex items-center gap-1.5">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-500" />
                    Mira is thinking...
                  </span>
                </div>
              )}
              <div ref={splitMessagesEndRef} />
            </div>

            {/* Active Live Chat Bar inside Split-Screen */}
            <div className="shrink-0 p-3 sm:p-4 border-t border-white bg-white/90 backdrop-blur-md shadow-[0_-8px_25px_rgba(30,41,59,0.05)]">
              {chatError && <p role="alert" className="mb-2 text-xs text-rose-700">{chatError}</p>}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={toggleRecording}
                  disabled={isSending || isTranscribing || isStartingRecording}
                  aria-label={isRecording ? "Stop recording and transcribe" : "Start voice recording"}
                  aria-pressed={isRecording}
                  className={`shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all cursor-pointer ${
                    isRecording
                      ? "bg-rose-500 text-white shadow-md shadow-rose-500/30 scale-105 animate-pulse"
                      : "bg-slate-100 text-slate-600 hover:bg-rose-50 hover:text-rose-700 border border-slate-200"
                  }`}
                  title={isRecording ? "Tap to stop and send" : "Tap to start recording"}
                >
                  {isStartingRecording || isTranscribing ? <Loader2 className="w-4 h-4 animate-spin" /> : isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>
                <input
                  type="text"
                  value={splitInputText}
                  onChange={(e) => setSplitInputText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey && splitInputText.trim() && !isSending) {
                      e.preventDefault();
                      const t = splitInputText.trim();
                      setSplitInputText("");
                      handleSendMessage(t);
                    }
                  }}
                  placeholder={
                    selectedLang === "en"
                      ? "Ask Mira anything or give instructions..."
                      : "मीरा से कुछ भी पूछें या निर्देश दें..."
                  }
                  disabled={isSending}
                  className="flex-1 rounded-xl bg-slate-50 border border-slate-200 px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500/40 focus:border-rose-500 transition-all"
                />
                <button
                  type="button"
                  onClick={() => {
                    if (splitInputText.trim() && !isSending) {
                      const t = splitInputText.trim();
                      setSplitInputText("");
                      handleSendMessage(t);
                    }
                  }}
                  disabled={!splitInputText.trim() || isSending}
                  className="shrink-0 w-10 h-10 rounded-xl bg-gradient-to-r from-rose-600 to-indigo-800 text-white flex items-center justify-center shadow-sm disabled:opacity-40 transition-all cursor-pointer hover:shadow-md"
                >
                  {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-[10px] text-slate-500 mt-2 px-1">{isRecording ? "Recording · tap again to send" : isTranscribing ? "Transcribing your voice..." : "Ask for a change before generating your report"}</p>
            </div>
          </div>

          {/* Right Panel: Editable Summary Form */}
          <div className="w-full lg:w-1/2 h-[56%] lg:h-full flex flex-col bg-gradient-to-br from-emerald-50/60 via-white to-sky-50/70">
            <div className="bg-white/90 backdrop-blur text-slate-900 px-5 sm:px-7 py-4 flex items-center justify-between shrink-0 border-b border-white shadow-sm gap-2">
              <div className="flex items-center gap-3">
                <span className="w-10 h-10 rounded-2xl bg-emerald-50 flex items-center justify-center border border-emerald-100"><CheckCircle2 className="w-5 h-5 text-emerald-600" /></span>
                <div><p className="text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-700">Final step · 07 / 07</p>
                <h2 className="text-sm sm:text-base font-bold">{selectedLang === "en" ? "Review your enterprise plan" : "अपनी उद्यम योजना जाँचें"}</h2></div>
              </div>
              <span className="hidden sm:inline text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">✓ {selectedLang === "en" ? "Editable before submitting" : "भेजने से पहले बदल सकते हैं"}</span>
            </div>

            <div className="flex-1 overflow-y-auto px-4 sm:px-7 py-5 space-y-4">
              <p className="text-xs text-slate-600 leading-relaxed rounded-2xl border border-sky-100 bg-sky-50/80 px-4 py-3">{selectedLang === "en" ? "Mira filled this from your conversation. Review and edit any field, then generate your feasibility report." : "Mira ने बातचीत के आधार पर यह फ़ॉर्म भरा है। किसी भी जानकारी को बदलें, फिर रिपोर्ट बनाएँ।"}</p>
              {/* Enterprise & Location Section */}
              <div className="bg-white rounded-2xl border border-slate-200/90 p-4 space-y-3 shadow-xs">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-indigo-500" />
                  Enterprise & Location
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500 font-medium">Enterprise Name</span>
                    <input
                      type="text"
                      value={collectedFields.enterprise_name || `${userName}'s Venture`}
                      onChange={(e) => setCollectedFields(prev => ({ ...prev, enterprise_name: e.target.value }))}
                      className="text-right font-bold text-slate-900 bg-transparent border-b border-dashed border-slate-300 focus:border-indigo-500 focus:outline-none px-1 py-0.5 max-w-[55%] text-xs"
                    />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500 font-medium">Promoter name</span>
                    <input type="text" value={collectedFields.promoter_name || userName} onChange={(e) => setCollectedFields(prev => ({ ...prev, promoter_name: e.target.value }))}
                      className="text-right font-semibold text-slate-900 bg-transparent border-b border-dashed border-slate-300 focus:border-indigo-500 focus:outline-none px-1 py-0.5 max-w-[55%] text-xs" />
                  </div>
                  <div className="space-y-1">
                    <label className="text-slate-500 font-medium" htmlFor="review-business-idea">Business idea</label>
                    <textarea id="review-business-idea" rows={2} readOnly value={collectedFields.business_idea || collectedFields.additional_business_details || ""}
                      className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2 text-slate-900" />
                    <button type="button" onClick={handleReviseBusinessIdea} className="text-indigo-700 font-semibold hover:underline">
                      {selectedLang === "en" ? "Change idea and reassess equipment" : "विचार बदलें और उपकरण फिर जाँचें"}
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <label className="space-y-1 text-slate-500 font-medium">Industry sector
                      <select value={collectedFields.sector || "general"} onChange={(e) => setCollectedFields(prev => ({ ...prev, sector: e.target.value }))}
                        className="w-full rounded-lg border border-slate-200 bg-white p-2 text-slate-900">
                        {["dairy", "food_processing", "apparel", "repair", "fabrication", "artisan_trades", "general"].map(sector => <option key={sector} value={sector}>{sector.replace(/_/g, " ")}</option>)}
                      </select>
                    </label>
                    <label className="space-y-1 text-slate-500 font-medium">Business type
                      <select value={collectedFields.business_category || "service"} onChange={(e) => setCollectedFields(prev => ({ ...prev, business_category: e.target.value }))}
                        className="w-full rounded-lg border border-slate-200 bg-white p-2 text-slate-900">
                        <option value="manufacturing">Manufacturing</option><option value="service">Service / retail</option>
                      </select>
                    </label>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500 font-medium">Promoter Category</span>
                    <select
                      value={collectedFields.promoter_category || "general"}
                      onChange={(e) => setCollectedFields(prev => ({ ...prev, promoter_category: e.target.value }))}
                      className="text-right font-semibold text-slate-900 bg-transparent border-b border-dashed border-slate-300 focus:border-indigo-500 focus:outline-none px-1 py-0.5 text-xs cursor-pointer"
                    >
                      {PROMOTER_CATEGORIES.map(c => (
                        <option key={c.value} value={c.value}>{c.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <label className="space-y-1 text-slate-500 font-medium">State
                      <select value={collectedFields.state_name || ""} onChange={(e) => handleReviewLocationChange("state_name", e.target.value)} className="w-full rounded-lg border border-slate-200 bg-white p-2 text-slate-900">
                        {!statesList.some(s => s.state_name === collectedFields.state_name) && <option value={collectedFields.state_name || ""}>{collectedFields.state_name || "Select state"}</option>}
                        {statesList.map(s => <option key={s.state_code || s.state_name} value={s.state_name}>{s.state_name}</option>)}
                      </select>
                    </label>
                    <label className="space-y-1 text-slate-500 font-medium">District
                      <select value={collectedFields.district_name || ""} onChange={(e) => handleReviewLocationChange("district_name", e.target.value)} className="w-full rounded-lg border border-slate-200 bg-white p-2 text-slate-900">
                        {!districtsList.some(d => d.district_name === collectedFields.district_name) && <option value={collectedFields.district_name || ""}>{collectedFields.district_name || "Select district"}</option>}
                        {districtsList.map(d => <option key={d.district_code || d.district_name} value={d.district_name}>{d.district_name}</option>)}
                      </select>
                    </label>
                    <label className="space-y-1 text-slate-500 font-medium">Block
                      <select value={collectedFields.block_name || ""} onChange={(e) => handleReviewLocationChange("block_name", e.target.value)} className="w-full rounded-lg border border-slate-200 bg-white p-2 text-slate-900">
                        <option value="">Select block</option>
                        {collectedFields.block_name && !blocksList.some(b => b.development_block_name === collectedFields.block_name) && <option value={collectedFields.block_name}>{collectedFields.block_name}</option>}
                        {blocksList.map(b => <option key={b.development_block_code || b.development_block_name} value={b.development_block_name}>{b.development_block_name}</option>)}
                      </select>
                    </label>
                    <label className="space-y-1 text-slate-500 font-medium">Village / locality
                      <select value={collectedFields.village_name || ""} onChange={(e) => handleReviewLocationChange("village_name", e.target.value)} className="w-full rounded-lg border border-slate-200 bg-white p-2 text-slate-900">
                        <option value="">Select village</option>
                        {collectedFields.village_name && !villagesList.some(v => v.village_name === collectedFields.village_name) && <option value={collectedFields.village_name}>{collectedFields.village_name}</option>}
                        {villagesList.map(v => <option key={v.village_code || v.village_name} value={v.village_name}>{v.village_name}</option>)}
                      </select>
                    </label>
                  </div>
                  <label className="flex items-center justify-between text-slate-500 font-medium">Area type
                    <select value={collectedFields.is_rural ? "rural" : "urban"} onChange={(e) => setCollectedFields(prev => ({ ...prev, is_rural: e.target.value === "rural" }))} className="rounded-lg border border-slate-200 bg-white p-2 text-slate-900">
                      <option value="rural">Rural</option><option value="urban">Urban / semi-urban</option>
                    </select>
                  </label>
                </div>
              </div>

              {/* Financial Section */}
              <div className="bg-white rounded-2xl border border-slate-200/90 p-4 space-y-3 shadow-xs">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  Financial Outlay & Promoter Equity
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500 font-medium">Promoter Equity</span>
                    <div className="flex items-center gap-1">
                      <span className="font-bold text-emerald-700 text-xs">₹</span>
                      <input
                        type="number"
                        value={collectedFields.promoter_equity ?? ""}
                        onChange={(e) => setCollectedFields(prev => ({ ...prev, promoter_equity: Number(e.target.value) }))}
                        className="text-right font-bold text-emerald-700 bg-transparent border-b border-dashed border-slate-300 focus:border-emerald-500 focus:outline-none px-1 py-0.5 w-28 text-xs"
                      />
                      {collectedFields.promoter_margin_pct && (
                        <span className="text-[10px] text-slate-500 font-normal">({collectedFields.promoter_margin_pct}% Margin)</span>
                      )}
                    </div>
                  </div>
                  {Number(collectedFields.owned_machinery_value || 0) > 0 && (
                    <div className="text-emerald-800 bg-emerald-50/80 px-2.5 py-1.5 rounded-xl border border-emerald-200 space-y-0.5">
                      <div className="flex justify-between">
                        <span className="font-medium text-[11px]">Owned Machinery Credit</span>
                        <span className="font-bold text-[11px]">-₹{Number(collectedFields.owned_machinery_value).toLocaleString('en-IN')}</span>
                      </div>
                      {collectedFields.owned_machines && Array.isArray(collectedFields.owned_machines) && collectedFields.owned_machines.length > 0 && (
                        <div className="text-[10px] text-emerald-700/80 truncate">
                          {collectedFields.owned_machines.map(m => m.machine_name || m).join(", ")}
                        </div>
                      )}
                    </div>
                  )}
                  <div className="flex justify-between bg-slate-50 px-2.5 py-2 rounded-xl border border-slate-200">
                    <label htmlFor="review-project-cost" className="text-slate-900 font-bold">Project cost (₹)</label>
                    <input id="review-project-cost" type="number" min="1" value={collectedFields.project_cost ?? ""}
                      onChange={(e) => setCollectedFields(prev => ({ ...prev, project_cost: Number(e.target.value), explicit_project_cost: Number(e.target.value) }))}
                      className="w-32 text-right font-extrabold text-indigo-950 bg-white rounded-md border border-slate-200 px-2 py-1" />
                  </div>
                  <p className="text-[11px] text-slate-500">This is Mira's estimate. If you edit your investment or project cost, the entered values will be used for the final appraisal.</p>
                  {collectedFields.annual_turnover_estimate > 0 && <div className="flex justify-between text-slate-600"><span>Estimated annual sales</span><span>₹{Number(collectedFields.annual_turnover_estimate).toLocaleString("en-IN")}</span></div>}
                </div>
              </div>

              {/* Banking Policy Section */}
              <div className="bg-white rounded-2xl border border-slate-200/90 p-4 space-y-3 shadow-xs">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                  MSME Banking Policy
                </div>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500 font-medium">Loan Tenure</span>
                    <select
                      value={collectedFields.tenure_years || 7}
                      onChange={(e) => setCollectedFields(prev => ({ ...prev, tenure_years: Number(e.target.value) }))}
                      className="text-right font-semibold text-slate-800 bg-transparent border-b border-dashed border-slate-300 focus:border-indigo-500 focus:outline-none px-1 py-0.5 text-xs cursor-pointer"
                    >
                      {[3, 5, 7, 8, 10].map(y => (
                        <option key={y} value={y}>{y} Years</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500 font-medium">Moratorium</span>
                    <select
                      value={collectedFields.moratorium_months ?? 6}
                      onChange={(e) => setCollectedFields(prev => ({ ...prev, moratorium_months: Number(e.target.value) }))}
                      className="text-right font-semibold text-slate-800 bg-transparent border-b border-dashed border-slate-300 focus:border-indigo-500 focus:outline-none px-1 py-0.5 text-xs cursor-pointer"
                    >
                      {[0, 3, 6, 9, 12].map(m => (
                        <option key={m} value={m}>{m} Months</option>
                      ))}
                    </select>
                  </div>
                  {collectedFields.odop_product && (
                    <div className="flex justify-between">
                      <span className="text-slate-500 font-medium">ODOP Status</span>
                      <span className="font-semibold text-indigo-600">
                        {collectedFields.odop_synergy_aligned ? `Aligned (${collectedFields.odop_product})` : "Standard Model"}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Submit Button — pinned at bottom */}
            <div className="shrink-0 px-5 sm:px-7 py-4 border-t border-white bg-white/95 backdrop-blur shadow-[0_-10px_30px_rgba(30,41,59,0.06)]">
              {submitError && <p role="alert" className="mb-3 text-sm text-rose-700">{submitError}</p>}
              <button
                onClick={handleFinalSubmit}
                disabled={parentLoading}
                className="w-full py-4 rounded-2xl bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-indigo-900 text-white font-bold text-sm shadow-xl shadow-sovereign-950/20 hover:shadow-2xl hover:scale-[1.01] transition-all duration-200 flex items-center justify-center gap-2.5 group disabled:opacity-50 cursor-pointer"
              >
                {parentLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>{selectedLang === "en" ? "Generating Report..." : "रिपोर्ट बना रहे हैं..."}</span>
                  </>
                ) : (
                  <>
                    <span className="text-base">{selectedLang === "en" ? "Generate Feasibility Report" : "व्यवहार्यता रिपोर्ट बनाएँ"}</span>
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes dynamicPastel {
          0% { background-position: 0% 50%; }
          25% { background-position: 100% 25%; }
          50% { background-position: 100% 50%; }
          75% { background-position: 0% 75%; }
          100% { background-position: 0% 50%; }
        }
        @keyframes gradientShift {
          0% { background-position: 0% 50%; }
          25% { background-position: 100% 25%; }
          50% { background-position: 100% 50%; }
          75% { background-position: 0% 75%; }
          100% { background-position: 0% 50%; }
        }
      `}</style>
    </div>
  );
}

export default OnboardingPage;
