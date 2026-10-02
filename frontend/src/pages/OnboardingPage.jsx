/**
 * OnboardingPage.jsx — MIRA Conversational Onboarding for Rural & Semi-Urban MSME Entrepreneurs.
 * 
 * Replaces the 7-step wizard with an intelligent conversational interface:
 * 1. Regional Language Selection with beautiful gradient cards
 * 2. MIRA greets user by name in selected language, acknowledging auto-detected GPS location
 * 3. Collects business idea, capital, and category via natural empathetic Q&A
 * 4. 3-Pillar ODOP Strategic Synergy (Product Innovation, Local Sourcing, 35% PMFME Subsidy)
 * 5. Multi-tier TTS Voice Synthesis (Bhashini Indic Voice + gTTS + Web Speech API fallback)
 * 6. Background calculation of annual sales and bank feasibility parameters
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { useBusiness } from "../context/BusinessContext";
import { chatApi } from "../services/api";
import {
  Mic,
  MicOff,
  Send,
  Volume2,
  VolumeX,
  Loader2,
  Sparkles,
  Globe,
  ArrowRight,
  CheckCircle2,
  MapPin,
  MessageSquare,
  Info,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";

// ─── Language Cards Configuration ─────────────────────────────────────
const ONBOARDING_LANGUAGES = [
  {
    code: "en",
    label: "English",
    native: "English",
    initials: "ABC",
    gradient: "from-sky-500 to-blue-600",
    gradientBorder: "border-sky-400/60",
    selectedGlow: "ring-sky-400/50 shadow-sky-500/20",
    bg: "bg-sky-50",
  },
  {
    code: "hi",
    label: "Hindi",
    native: "हिन्दी",
    initials: "अआइ",
    gradient: "from-orange-500 to-amber-600",
    gradientBorder: "border-orange-400/60",
    selectedGlow: "ring-orange-400/50 shadow-orange-500/20",
    bg: "bg-orange-50",
  },
  {
    code: "mr",
    label: "Marathi",
    native: "मराठी",
    initials: "अआइ",
    gradient: "from-emerald-500 to-teal-600",
    gradientBorder: "border-emerald-400/60",
    selectedGlow: "ring-emerald-400/50 shadow-emerald-500/20",
    bg: "bg-emerald-50",
  },
  {
    code: "te",
    label: "Telugu",
    native: "తెలుగు",
    initials: "అఆఇ",
    gradient: "from-purple-500 to-violet-600",
    gradientBorder: "border-purple-400/60",
    selectedGlow: "ring-purple-400/50 shadow-purple-500/20",
    bg: "bg-purple-50",
  },
  {
    code: "ta",
    label: "Tamil",
    native: "தமிழ்",
    initials: "அஆஇ",
    gradient: "from-rose-500 to-pink-600",
    gradientBorder: "border-rose-400/60",
    selectedGlow: "ring-rose-400/50 shadow-rose-500/20",
    bg: "bg-rose-50",
  },
  {
    code: "kn",
    label: "Kannada",
    native: "ಕನ್ನಡ",
    initials: "ಅಆಇ",
    gradient: "from-cyan-500 to-indigo-600",
    gradientBorder: "border-cyan-400/60",
    selectedGlow: "ring-cyan-400/50 shadow-cyan-500/20",
    bg: "bg-cyan-50",
  },
];

// ─── Warm Natural Greeting Templates (Acknowledging Location Without Asking Again) ───
const GREETINGS = {
  en: (name, loc) => `Namaste ${name} Ji! 🙏\n\nI am MIRA, your MSME business advisor. ${loc ? `I see you are planning your venture in **${loc}**! ` : ""}I'm here to help you turn your idea into a successful, bank-funded enterprise.\n\nPlease tell me:\n1. **What business or product do you want to start?** (e.g., dairy, ice cream, food processing, clothes, mobile repair)\n2. **How much capital do you have to invest?** (e.g., ₹2 lakh, ₹5 lakh)`,
  hi: (name, loc) => `नमस्ते ${name} जी! 🙏\n\nमैं MIRA हूँ, आपकी MSME व्यवसाय सलाहकार। ${loc ? `मैंने देखा कि आप **${loc}** में अपना उद्यम शुरू करने की योजना बना रहे हैं! ` : ""}मैं आपकी व्यवसाय यात्रा शुरू करने और 35% तक सरकारी सब्सिडी प्राप्त करने में मदद करूँगी।\n\nकृपया मुझे बताएँ:\n1. **आप कौन सा व्यवसाय या उत्पाद शुरू करना चाहते हैं?** (जैसे डेयरी, आइसक्रीम, खाद्य प्रसंस्करण, कपड़े, मोबाइल रिपेयर)\n2. **आपके पास निवेश के लिए कितना पैसा / पूँजी है?** (जैसे ₹2 लाख, ₹5 लाख)`,
  mr: (name, loc) => `नमस्कार ${name} जी! 🙏\n\nमी MIRA आहे, तुमची MSME व्यवसाय सल्लागार. ${loc ? `मी पाहिले की तुम्ही **${loc}** मध्ये तुमचा व्यवसाय सुरू करण्याचा विचार करत आहात! ` : ""}तुमचा व्यवसाय प्रवास सुरू करण्यात आणि 35% पर्यंत सरकारी अनुदान मिळवण्यात मदत करण्यासाठी मी येथे आहे.\n\nकृपया मला सांगा:\n1. **तुम्हाला कोणता व्यवसाय किंवा उत्पादन सुरू करायचे आहे?** (जसे डेअरी, आईस्क्रीम, अन्न प्रक्रिया, कापड, मोबाइल दुरुस्ती)\n2. **तुमच्याकडे गुंतवणुकीसाठी किती पैसे आहेत?** (जसे ₹2 लाख, ₹5 लाख)`,
  te: (name, loc) => `నమస్తే ${name} జీ! 🙏\n\nనేను MIRA, మీ MSME వ్యాపార సలహాదారు. ${loc ? `మీరు **${loc}** లో మీ వ్యాపారాన్ని ప్రారంభించాలనుకుంటున్నారని నేను చూశాను! ` : ""}మీ వ్యాపార ప్రయాణాన్ని విజయవంతం చేయడానికి మరియు ప్రభుత్వ సబ్సిడీలను పొందడంలో మీకు సహాయం చేయడానికి నేను ఇక్కడ ఉన్నాను.\n\nదయచేసి నాకు చెప్పండి:\n1. **మీరు ఏ వ్యాపారం లేదా ఉత్పత్తిని ప్రారంభించాలనుకుంటున్నారు?** (ఉదా: డైరీ, ఐస్ క్రీం, ఫుడ్ ప్రాసెసింగ్, బట్టలు, మొబైల్ రిపేర్)\n2. **మీ దగ్గర పెట్టుబడికి ఎంత డబ్బు ఉంది?** (ఉదా: ₹2 లక్షలు, ₹5 లక్షలు)`,
  ta: (name, loc) => `வணக்கம் ${name} ஜி! 🙏\n\nநான் MIRA, உங்கள் MSME வணிக ஆலோசகர். ${loc ? `நீங்கள் **${loc}** இல் தொழில் தொடங்க திட்டமிட்டுள்ளீர்கள் என்பதை நான் காண்கிறேன்! ` : ""}உங்கள் தொழில் பயணத்தைத் தொடங்கவும் அரசு மானியங்களைப் பெறவும் உதவ நான் இங்கே இருக்கிறேன்.\n\nதயவுசெய்து சொல்லுங்கள்:\n1. **என்ன தொழில் அல்லது தயாரிப்பைத் தொடங்க விரும்புகிறீர்கள்?** (எ.கா: பால் பண்ணை, ஐஸ்கிரீம், உணவு பதப்படுத்துதல், ஆடை, மொபைல் பழுது)\n2. **எவ்வளவு முதலீடு செய்ய பணம் உள்ளது?** (எ.கா: ₹2 லட்சம், ₹5 லட்சம்)`,
  kn: (name, loc) => `ನಮಸ್ಕಾರ ${name} ಜೀ! 🙏\n\nನಾನು MIRA, ನಿಮ್ಮ MSME ವ್ಯಾಪಾರ ಸಲಹೆಗಾರ್ತಿ. ${loc ? `ನೀವು **${loc}** ನಲ್ಲಿ ನಿಮ್ಮ ಉದ್ಯಮವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಯೋಜಿಸುತ್ತಿರುವುದನ್ನು ನಾನು ನೋಡಿದ್ದೇನೆ! ` : ""}ನಿಮ್ಮ ವ್ಯಾಪಾರ ಪ್ರಯಾಣವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಮತ್ತು ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿಗಳನ್ನು ಪಡೆಯಲು ಸಹಾಯ ಮಾಡಲು ನಾನಿಲ್ಲಿದ್ದೇನೆ.\n\nದಯವಿಟ್ಟು ನನಗೆ ಹೇಳಿ:\n1. **ನೀವು ಯಾವ ವ್ಯಾಪಾರ ಅಥವಾ ಉತ್ಪನ್ನವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೀರಿ?** (ಉದಾ: ಡೈರಿ, ಐಸ್ ಕ್ರೀಮ್, ಆಹಾರ ಸಂಸ್ಕರಣೆ, ಬಟ್ಟೆ, ಮೊಬೈಲ್ ರಿಪೇರಿ)\n2. **ನಿಮ್ಮ ಬಳಿ ಹೂಡಿಕೆಗೆ ಎಷ್ಟು ಹಣ ಇದೆ?** (ಉದಾ: ₹2 ಲಕ್ಷ, ₹5 ಲಕ್ಷ)`,
};

export function OnboardingPage({ onWizardSubmit, isLoading: parentLoading }) {
  const navigate = useNavigate();
  const { userProfile, token, updateProfile } = useAuth();
  const { setLanguage } = useLanguage();
  const { createAndSaveBusiness } = useBusiness();

  // ─── State ────────────────────────────────────────────────────────────
  const [phase, setPhase] = useState("lang_select"); // lang_select | chatting | processing
  const [selectedLang, setSelectedLang] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [collectedFields, setCollectedFields] = useState({});
  const [odopData, setOdopData] = useState(null);
  const [conversationStep, setConversationStep] = useState(0);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const currentAudioRef = useRef(null);

  const userName = userProfile?.name || "Entrepreneur";

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Clean up audio on unmount
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

  // ─── Browser Web Speech API Guaranteed Fallback ─────────────────────────
  const speakWithWebSpeech = useCallback((text, lang) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      setIsPlayingAudio(false);
      return;
    }
    try {
      window.speechSynthesis.cancel();
      const clean = text.replace(/[*#_~`]/g, " ").replace(/\n+/g, ". ").slice(0, 350);
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
  }, []);

  // ─── Robust Multi-Tier TTS Playback ─────────────────────────────────────
  const playTTS = useCallback(async (text, lang) => {
    try {
      setIsPlayingAudio(true);
      const clean = text.replace(/[*#_~`]/g, " ").replace(/\n+/g, ". ").slice(0, 450);

      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }

      if (currentAudioRef.current) {
        try {
          currentAudioRef.current.pause();
          currentAudioRef.current.currentTime = 0;
        } catch (_) {}
      }

      // Try server TTS endpoint (Bhashini Indic / gTTS)
      const res = await fetch("/api/v2/chat/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: clean, language: lang }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.audio_base64 && data.audio_base64.length > 20) {
          // Normalize audio source — prevents double data URL prefix bug
          const audioSrc = data.audio_base64.startsWith("data:")
            ? data.audio_base64
            : `data:audio/wav;base64,${data.audio_base64}`;

          const audio = new Audio(audioSrc);
          currentAudioRef.current = audio;

          audio.onended = () => setIsPlayingAudio(false);
          audio.onerror = (e) => {
            console.warn("Audio element error, using browser speech synthesis:", e);
            speakWithWebSpeech(clean, lang);
          };

          try {
            await audio.play();
            return;
          } catch (playErr) {
            console.warn("Audio autoplay blocked by browser policy, using browser synthesis:", playErr);
            speakWithWebSpeech(clean, lang);
            return;
          }
        }
      }
    } catch (e) {
      console.warn("TTS server call error, falling back to Web Speech:", e);
    }

    // Fallback: browser speech synthesis
    speakWithWebSpeech(text, lang);
  }, [speakWithWebSpeech]);

  // ─── Stop Audio Playback ────────────────────────────────────────────────
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

  // ─── Retrieve Auto-Detected Location ────────────────────────────────────
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
    return null;
  }, [userProfile]);

  // ─── Language Selection Handler ─────────────────────────────────────────
  const handleLanguageSelect = useCallback(async (langCode) => {
    setSelectedLang(langCode);
    setLanguage(langCode);

    if (token && updateProfile) {
      try {
        await updateProfile({ preferred_language: langCode });
      } catch (e) {
        console.warn("Could not save language preference:", e);
      }
    }

    const locCoords = getAutoDetectedLocation();

    // Transition to chat phase with personalized greeting
    setTimeout(() => {
      const greetFn = GREETINGS[langCode] || GREETINGS.en;
      const initialLocLabel = collectedFields.district_name 
        ? `${collectedFields.district_name}, ${collectedFields.state_name || ''}`
        : "";
      const greetingText = greetFn(userName, initialLocLabel);
      
      setMessages([
        {
          id: "greeting-1",
          role: "assistant",
          content: greetingText,
          timestamp: new Date().toISOString(),
        },
      ]);
      setPhase("chatting");

      playTTS(greetingText, langCode);
    }, 350);
  }, [userName, token, updateProfile, setLanguage, collectedFields, getAutoDetectedLocation, playTTS]);

  // ─── Send Text Message ──────────────────────────────────────────────────
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
          conversation_step: conversationStep,
          user_location: locCoords,
        }),
      });

      if (response.ok) {
        const data = await response.json();

        if (data.extracted_fields) {
          setCollectedFields(prev => ({ ...prev, ...data.extracted_fields }));
        }

        if (data.next_step !== undefined) {
          setConversationStep(data.next_step);
        }

        if (data.odop_alignment) {
          setOdopData(data.odop_alignment);
        }

        const assistantMsg = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.reply || data.message?.content || "मैं समझ गई। कृपया और बताएँ।",
          timestamp: new Date().toISOString(),
          odop_comparison: data.odop_comparison || null,
        };
        setMessages(prev => [...prev, assistantMsg]);

        playTTS(assistantMsg.content, selectedLang || "hi");

        if (data.all_fields_collected) {
          setPhase("processing");
        }
      } else {
        // Fallback: general chat endpoint
        const fallbackRes = await chatApi.sendMessage(
          [...messages, userMsg].map(m => ({ role: m.role, content: m.content })),
          { onboarding: true },
          selectedLang || "hi",
          token
        );
        const assistantMsg = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: fallbackRes?.reply || fallbackRes?.message?.content || "मैं समझ गई। कृपया और बताएँ।",
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMsg]);
        playTTS(assistantMsg.content, selectedLang || "hi");
      }
    } catch (err) {
      console.error("Onboarding chat error:", err);
      const errorMsg = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: selectedLang === "en"
          ? "I apologize, there was a connection issue. Please try again."
          : "माफ़ कीजिए, कनेक्शन में समस्या आई। कृपया दोबारा प्रयास करें।",
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  }, [inputText, isSending, messages, selectedLang, userName, collectedFields, conversationStep, token, getAutoDetectedLocation, playTTS]);

  // ─── Audio Recording (Microphone) ───────────────────────────────────────
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

  // ─── 3-Pillar ODOP Strategic Synergy Decision Handler ───────────────────
  const handleOdopDecision = useCallback(async (alignWithOdop) => {
    const decision = alignWithOdop ? "align" : "keep_original";

    let synergyNote = "";
    if (alignWithOdop && odopData) {
      const pInnov = odopData.synergy_pillars?.product_innovation?.title || "";
      const pDesc = odopData.synergy_pillars?.product_innovation?.description || "";
      synergyNote = `ODOP Strategic Synergy: ${pInnov}. ${pDesc}`;
    }

    setCollectedFields(prev => ({
      ...prev,
      odop_decision: decision,
      odop_synergy_aligned: alignWithOdop,
      odop_product: odopData?.primary_odop_product || odopData?.district_odop || odopData?.odop_product || null,
      additional_business_details: [
        prev.additional_business_details || "",
        synergyNote,
      ].filter(Boolean).join(" | "),
    }));

    const responseText = alignWithOdop
      ? (selectedLang === "en"
        ? `Brilliant decision! We have strategically aligned your enterprise with ${odopData?.primary_odop_product || 'district ODOP'}. This unlocks the 35% PMFME capital subsidy on machinery and priority GeM onboarding!`
        : `शानदार निर्णय! हमने आपके व्यवसाय को ${odopData?.primary_odop_product || 'जिले के ODOP'} के साथ जोड़ दिया है। इससे आपको मशीनरी पर 35% PMFME सरकारी सब्सिडी और GeM पोर्टल पर प्राथमिकता मिलेगी!`)
      : (selectedLang === "en"
        ? "Understood! We will proceed with your original business model under standard PMEGP & MUDRA loan schemes."
        : "समझ गई! हम मानक PMEGP और मुद्रा ऋण योजनाओं के तहत आपके मूल व्यवसाय मॉडल के साथ आगे बढ़ेंगे।");

    setMessages(prev => [...prev, {
      id: `odop-decision-${Date.now()}`,
      role: "assistant",
      content: responseText,
      timestamp: new Date().toISOString(),
    }]);

    setOdopData(null);
    playTTS(responseText, selectedLang || "hi");
  }, [selectedLang, odopData, playTTS]);

  // ─── Final Report Generation Submission ─────────────────────────────────
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
      console.error("Submission failed:", err);
    }
  }, [collectedFields, selectedLang, onWizardSubmit, createAndSaveBusiness, getAutoDetectedLocation, navigate]);

  // ─── Render: Language Selection Phase ───────────────────────────────────
  if (phase === "lang_select") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50/30 flex items-center justify-center px-4 py-8 relative overflow-hidden">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[40rem] h-[40rem] bg-sovereign-100/40 blur-[180px] rounded-full pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/3 w-80 h-80 bg-sky-100/40 blur-[140px] rounded-full pointer-events-none" />

        <div className="max-w-2xl w-full relative z-10">
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-sovereign-900 via-sovereign-800 to-indigo-900 text-white flex items-center justify-center text-2xl font-black mx-auto mb-4 shadow-xl shadow-sovereign-950/20 border border-sovereign-700/50">
              उ
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-display mb-2">
              Namaste {userName} Ji! 🙏
            </h1>
            <p className="text-sm text-slate-600 max-w-md mx-auto">
              Please choose your preferred language to begin your conversational onboarding with MIRA.
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
                  <div className={`text-2xl sm:text-3xl font-black mb-2 bg-gradient-to-r ${lang.gradient} bg-clip-text text-transparent leading-tight`}>
                    {lang.initials}
                  </div>
                  <div className="text-base sm:text-lg font-bold text-slate-900 mb-0.5">
                    {lang.native}
                  </div>
                  <div className="text-[11px] text-slate-500 font-medium uppercase tracking-wider">
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

  // ─── Render: Chat Phase ────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50/30 flex flex-col relative overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[36rem] h-[36rem] bg-sovereign-100/30 blur-[160px] rounded-full pointer-events-none" />

      {/* Header Bar */}
      <header className="sticky top-0 z-30 bg-gradient-to-r from-sovereign-950 via-sovereign-900 to-indigo-950 text-white px-4 py-3 shadow-lg">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur-sm flex items-center justify-center text-lg font-black border border-white/20">
            उ
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-bold truncate flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-sky-300" />
              MIRA — Business & Credit Advisor
            </h1>
            <p className="text-[11px] text-sky-200/80 truncate flex items-center gap-1.5">
              <span>{selectedLang && ONBOARDING_LANGUAGES.find(l => l.code === selectedLang)?.native}</span>
              <span>•</span>
              {isPlayingAudio ? (
                <span className="text-emerald-300 font-semibold animate-pulse flex items-center gap-1">
                  <Volume2 className="w-3 h-3" /> Speaking...
                </span>
              ) : (
                <span className="text-sky-300">Ready to assist</span>
              )}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {isPlayingAudio && (
              <button
                type="button"
                onClick={stopAudio}
                className="px-2.5 py-1 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-400/30 text-[10px] font-bold hover:bg-rose-500/30 transition-colors flex items-center gap-1"
                title="Stop speech"
              >
                <VolumeX className="w-3 h-3" /> Stop
              </button>
            )}

            {Object.keys(collectedFields).length > 0 && (
              <div className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded-lg border border-emerald-400/30 font-bold">
                {Object.keys(collectedFields).filter(k => !["latitude", "longitude"].includes(k)).length} Details Extracted
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-3 sm:px-4 py-4 sm:py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-2.5 animate-[fadeIn_0.3s_ease-out] ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sovereign-900 to-indigo-900 flex items-center justify-center text-white text-xs font-black shrink-0 mt-0.5 shadow-md">
                  उ
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
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-sovereign-700 hover:text-sovereign-900 cursor-pointer"
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
          ))}

          {/* ─── 3-Pillar ODOP Strategic Synergy Card (User-Centric Alignment) ─── */}
          {odopData && (
            <div className="animate-[fadeIn_0.4s_ease-out] max-w-xl mx-auto my-3">
              <div className="bg-white rounded-3xl border-2 border-emerald-400/80 shadow-2xl overflow-hidden">
                {/* Top Banner */}
                <div className="bg-gradient-to-r from-emerald-950 via-teal-900 to-sovereign-950 text-white p-4 sm:p-5 relative">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-400/40">
                      <Sparkles className="w-3.5 h-3.5" />
                      ODOP Strategic Alignment
                    </span>
                    <span className="text-xs text-emerald-200 font-semibold flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" /> 35% PMFME Subsidy Ready
                    </span>
                  </div>
                  <h3 className="text-base sm:text-lg font-bold font-display text-white">
                    {selectedLang === "en"
                      ? "Align Your Business with District ODOP for 35% Capital Subsidy"
                      : "जिले के ODOP से जुड़कर 35% सरकारी सब्सिडी का लाभ उठाएँ"}
                  </h3>
                </div>

                <div className="p-4 sm:p-6 space-y-4 text-slate-800">
                  {/* Explainer Box: What is ODOP? */}
                  <div className="p-3.5 rounded-2xl bg-emerald-50/80 border border-emerald-200 text-xs leading-relaxed text-emerald-950">
                    <p className="font-bold text-emerald-900 mb-1 flex items-center gap-1.5">
                      <Info className="w-4 h-4 text-emerald-700 shrink-0" />
                      {selectedLang === "en" ? "What is the ODOP Initiative?" : "ODOP योजना क्या है?"}
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
                        <span className="truncate">{odopData.user_business || "Your Enterprise"}</span>
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
                      className="flex-1 py-3 px-4 rounded-xl font-bold text-xs text-white bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 hover:from-emerald-500 hover:to-teal-500 shadow-md shadow-emerald-950/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
                    >
                      <Sparkles className="w-4 h-4 text-emerald-200" />
                      <span>
                        {selectedLang === "en"
                          ? "Adopt ODOP Synergy (Unlock 35% Subsidy) ✨"
                          : "ODOP तालमेल अपनाएँ (35% सब्सिडी अनलॉक करें) ✨"}
                      </span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleOdopDecision(false)}
                      className="sm:w-auto py-3 px-4 rounded-xl font-semibold text-xs text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/80 transition-colors cursor-pointer"
                    >
                      {selectedLang === "en" ? "Continue Standard Idea" : "सामान्य रूप से जारी रखें"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Typing Indicator */}
          {isSending && (
            <div className="flex gap-2.5 animate-[fadeIn_0.2s_ease-out]">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sovereign-900 to-indigo-900 flex items-center justify-center text-white text-xs font-black shrink-0">
                उ
              </div>
              <div className="bg-white rounded-2xl rounded-bl-md px-4 py-3 border border-slate-200/80 shadow-sm">
                <div className="flex items-center gap-1.5">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-sovereign-400 rounded-full animate-bounce" style={{ animationDelay: "0s" }} />
                    <span className="w-2 h-2 bg-sovereign-400 rounded-full animate-bounce" style={{ animationDelay: "0.15s" }} />
                    <span className="w-2 h-2 bg-sovereign-400 rounded-full animate-bounce" style={{ animationDelay: "0.3s" }} />
                  </div>
                  <span className="text-xs text-slate-500 ml-1">MIRA is thinking...</span>
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
                  : "bg-slate-100 text-slate-600 hover:bg-sovereign-100 hover:text-sovereign-800 border border-slate-200"
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
                className="w-full resize-none rounded-xl bg-slate-50 border border-slate-200 px-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sovereign-500/40 focus:border-sovereign-500 transition-all max-h-32 overflow-y-auto"
                style={{ minHeight: "44px" }}
              />
            </div>

            <button
              type="button"
              onClick={() => handleSendMessage()}
              disabled={!inputText.trim() || isSending}
              className="shrink-0 w-11 h-11 rounded-xl bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-indigo-900 text-white flex items-center justify-center shadow-md shadow-sovereign-950/20 hover:shadow-lg disabled:opacity-40 transition-all duration-200 cursor-pointer"
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
                : "📍 Auto-detecting location..."}
            </span>
          </div>
        </div>
      </div>

      {/* Processing Phase Overlay Modal */}
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
                ? "MIRA has gathered your enterprise details. Click below to generate your complete bank-ready feasibility appraisal."
                : "MIRA ने आपके व्यवसाय की सभी आवश्यक जानकारी एकत्र कर ली है। अपनी पूरी व्यवहार्यता रिपोर्ट और बैंक डीपीआर बनाने के लिए नीचे क्लिक करें।"}
            </p>

            {/* Collected Fields Summary */}
            <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 mb-6 text-left">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Verified Enterprise Parameters</div>
              <div className="space-y-1.5 text-xs text-slate-700">
                {Object.entries(collectedFields)
                  .filter(([key]) => !["latitude", "longitude", "odop_decision", "additional_business_details"].includes(key))
                  .map(([key, val]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-slate-500 font-medium capitalize">{key.replace(/_/g, " ")}</span>
                      <span className="font-semibold text-slate-900 text-right max-w-[60%] truncate">
                        {key === "project_cost" 
                          ? `₹${Number(val).toLocaleString('en-IN')}`
                          : (typeof val === "boolean" ? (val ? "Yes" : "No") : String(val))}
                      </span>
                    </div>
                  ))}
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
