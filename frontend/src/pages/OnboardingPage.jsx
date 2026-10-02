/**
 * OnboardingPage.jsx — MIRA Conversational Onboarding for Rural Entrepreneurs.
 * 
 * Replaces the 7-step wizard with an intelligent conversational interface:
 * 1. Language Selection with beautiful gradient cards
 * 2. MIRA greets user by name in selected language
 * 3. Collects business idea, capital, category via natural Q&A
 * 4. ODOP alignment check with pros/cons comparison
 * 5. Auto-fills wizard fields in the background
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
  Loader2,
  Sparkles,
  Globe,
  ArrowRight,
  CheckCircle2,
  MapPin,
  MessageSquare,
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

// ─── Greeting templates per language ──────────────────────────────────
const GREETINGS = {
  en: (name) => `Namaste ${name} Ji! 🙏\n\nI am MIRA, your business advisor. I'm here to help you start your business journey.\n\nPlease tell me:\n1. **What business do you want to start?** (e.g., dairy, mobile repair, clothing shop)\n2. **How much money do you have to invest?** (e.g., ₹2 lakh, ₹5 lakh)\n3. **Which category do you belong to?** (General / OBC / SC / ST / Women Entrepreneur)`,
  hi: (name) => `नमस्ते ${name} जी! 🙏\n\nमैं MIRA हूँ, आपकी व्यवसाय सहायक। मैं आपकी व्यवसाय यात्रा शुरू करने में आपकी मदद करने के लिए यहाँ हूँ।\n\nकृपया मुझे बताएँ:\n1. **आप कौन सा व्यवसाय शुरू करना चाहते हैं?** (जैसे डेयरी, मोबाइल रिपेयर, कपड़े की दुकान)\n2. **आपके पास निवेश के लिए कितने पैसे हैं?** (जैसे ₹2 लाख, ₹5 लाख)\n3. **आप किस वर्ग से हैं?** (सामान्य / OBC / SC / ST / महिला उद्यमी)`,
  mr: (name) => `नमस्कार ${name} जी! 🙏\n\nमी MIRA आहे, तुमची व्यवसाय सल्लागार. तुमचा व्यवसाय प्रवास सुरू करण्यात मदत करण्यासाठी मी येथे आहे.\n\nकृपया मला सांगा:\n1. **तुम्हाला कोणता व्यवसाय सुरू करायचा आहे?** (जसे डेअरी, मोबाइल दुरुस्ती, कापड दुकान)\n2. **तुमच्याकडे गुंतवणुकीसाठी किती पैसे आहेत?** (जसे ₹2 लाख, ₹5 लाख)\n3. **तुम्ही कोणत्या प्रवर्गातून आहात?** (सामान्य / OBC / SC / ST / महिला उद्योजक)`,
  te: (name) => `నమస్తే ${name} జీ! 🙏\n\nనేను MIRA, మీ వ్యాపార సలహాదారు. మీ వ్యాపార ప్రయాణాన్ని ప్రారంభించడంలో మీకు సహాయం చేయడానికి ఇక్కడ ఉన్నాను.\n\nదయచేసి నాకు చెప్పండి:\n1. **మీరు ఏ వ్యాపారం ప్రారంభించాలనుకుంటున్నారు?** (ఉదా: డైరీ, మొబైల్ రిపేర్, బట్టల దుకాణం)\n2. **మీ దగ్గర పెట్టుబడికి ఎంత డబ్బు ఉంది?** (ఉదా: ₹2 లక్షలు, ₹5 లక్షలు)\n3. **మీరు ఏ వర్గానికి చెందుతారు?** (జనరల్ / OBC / SC / ST / మహిళా వ్యాపారవేత్త)`,
  ta: (name) => `வணக்கம் ${name} ஜி! 🙏\n\nநான் MIRA, உங்கள் வணிக ஆலோசகர். உங்கள் வணிகப் பயணத்தைத் தொடங்க உதவ இங்கே இருக்கிறேன்.\n\nதயவுசெய்து சொல்லுங்கள்:\n1. **என்ன தொழில் தொடங்க விரும்புகிறீர்கள்?** (எ.கா: பால் பண்ணை, மொபைல் பழுது, ஆடை கடை)\n2. **எவ்வளவு பணம் முதலீடு செய்ய உள்ளது?** (எ.கா: ₹2 லட்சம், ₹5 லட்சம்)\n3. **நீங்கள் எந்தப் பிரிவில் இருக்கிறீர்கள்?** (பொது / OBC / SC / ST / பெண் தொழில்முனைவோர்)`,
  kn: (name) => `ನಮಸ್ಕಾರ ${name} ಜೀ! 🙏\n\nನಾನು MIRA, ನಿಮ್ಮ ವ್ಯಾಪಾರ ಸಲಹೆಗಾರ್ತಿ. ನಿಮ್ಮ ವ್ಯಾಪಾರ ಪ್ರಯಾಣವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಸಹಾಯ ಮಾಡಲು ನಾನಿಲ್ಲಿದ್ದೇನೆ.\n\nದಯವಿಟ್ಟು ನನಗೆ ಹೇಳಿ:\n1. **ನೀವು ಯಾವ ವ್ಯಾಪಾರ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೀರಿ?** (ಉದಾ: ಡೈರಿ, ಮೊಬೈಲ್ ರಿಪೇರಿ, ಬಟ್ಟೆ ಅಂಗಡಿ)\n2. **ನಿಮ್ಮ ಬಳಿ ಎಷ್ಟು ಹಣ ಹೂಡಲು ಇದೆ?** (ಉದಾ: ₹2 ಲಕ್ಷ, ₹5 ಲಕ್ಷ)\n3. **ನೀವು ಯಾವ ವರ್ಗಕ್ಕೆ ಸೇರಿದ್ದೀರಿ?** (ಸಾಮಾನ್ಯ / OBC / SC / ST / ಮಹಿಳಾ ಉದ್ಯಮಿ)`,
};

const LANG_SELECT_PROMPT = {
  en: "Choose your language",
  hi: "अपनी भाषा चुनें",
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
  const [conversationStep, setConversationStep] = useState(0); // track Q&A progress

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const userName = userProfile?.name || "Entrepreneur";

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ─── Language Selection Handler ─────────────────────────────────────
  const handleLanguageSelect = useCallback(async (langCode) => {
    setSelectedLang(langCode);
    setLanguage(langCode);

    // Save language preference to backend
    if (token && updateProfile) {
      try {
        await updateProfile({ preferred_language: langCode });
      } catch (e) {
        console.warn("Could not save language preference:", e);
      }
    }

    // Transition to chat phase with greeting
    setTimeout(() => {
      const greetFn = GREETINGS[langCode] || GREETINGS.en;
      const greetingText = greetFn(userName);
      
      setMessages([
        {
          id: "greeting-1",
          role: "assistant",
          content: greetingText,
          timestamp: new Date().toISOString(),
        },
      ]);
      setPhase("chatting");

      // Auto-play greeting via TTS
      playTTS(greetingText, langCode);
    }, 400);
  }, [userName, token, updateProfile, setLanguage]);

  // ─── TTS Playback ────────────────────────────────────────────────────
  const playTTS = useCallback(async (text, lang) => {
    try {
      setIsPlayingAudio(true);
      const res = await fetch("/api/v2/chat/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.replace(/[*#\n]/g, " ").slice(0, 500), language: lang }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.audio_base64) {
          const audio = new Audio(`data:audio/wav;base64,${data.audio_base64}`);
          audio.onended = () => setIsPlayingAudio(false);
          audio.onerror = () => setIsPlayingAudio(false);
          await audio.play().catch(() => setIsPlayingAudio(false));
          return;
        }
      }
    } catch (e) {
      console.warn("TTS playback error:", e);
    }
    setIsPlayingAudio(false);
  }, []);

  // ─── Send Text Message ──────────────────────────────────────────────
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
      // Build conversation history for the LLM
      const conversationHistory = [...messages, userMsg].map(m => ({
        role: m.role,
        content: m.content,
      }));

      // Send to backend onboarding endpoint
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
          user_location: {
            latitude: userProfile?.latitude || null,
            longitude: userProfile?.longitude || null,
          },
        }),
      });

      if (response.ok) {
        const data = await response.json();

        // Update collected fields from backend extraction
        if (data.extracted_fields) {
          setCollectedFields(prev => ({ ...prev, ...data.extracted_fields }));
        }

        // Update conversation step
        if (data.next_step !== undefined) {
          setConversationStep(data.next_step);
        }

        // ODOP alignment data
        if (data.odop_alignment) {
          setOdopData(data.odop_alignment);
        }

        // Add assistant response
        const assistantMsg = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.reply || data.message?.content || "I understand. Let me help you further.",
          timestamp: new Date().toISOString(),
          odop_comparison: data.odop_comparison || null,
        };
        setMessages(prev => [...prev, assistantMsg]);

        // Play TTS for the response
        playTTS(assistantMsg.content, selectedLang || "hi");

        // Check if all fields are collected — if so, show confirmation
        if (data.all_fields_collected) {
          setPhase("processing");
        }
      } else {
        // Fallback: use regular chat endpoint
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
  }, [inputText, isSending, messages, selectedLang, userName, collectedFields, conversationStep, token, userProfile, playTTS]);

  // ─── Audio Recording ────────────────────────────────────────────────
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

        // Send audio to voice chat endpoint
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

            // Add user's transcribed message
            if (data.user_transcript) {
              setMessages(prev => [...prev, {
                id: `user-voice-${Date.now()}`,
                role: "user",
                content: data.user_transcript,
                timestamp: new Date().toISOString(),
                isVoice: true,
              }]);
            }

            // Send the transcript through onboarding pipeline for field extraction
            if (data.user_transcript) {
              handleSendMessage(data.user_transcript);
            } else {
              // If no transcript, add the LLM reply directly
              setMessages(prev => [...prev, {
                id: `assistant-voice-${Date.now()}`,
                role: "assistant",
                content: data.reply || "मुझे आपकी आवाज़ स्पष्ट नहीं सुनाई दी। कृपया दोबारा बोलें।",
                timestamp: new Date().toISOString(),
              }]);

              // Play TTS
              if (data.audio_base64) {
                const audio = new Audio(`data:audio/wav;base64,${data.audio_base64}`);
                audio.play().catch(() => {});
              }
            }
          }
        } catch (e) {
          console.error("Voice processing error:", e);
        } finally {
          setIsSending(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied:", err);
    }
  }, [selectedLang, collectedFields, token, handleSendMessage]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  // ─── Handle Enter Key ───────────────────────────────────────────────
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // ─── ODOP Alignment Decision Handler ────────────────────────────────
  const handleOdopDecision = useCallback(async (alignWithOdop) => {
    const decision = alignWithOdop ? "align" : "keep_original";
    setCollectedFields(prev => ({ ...prev, odop_decision: decision }));

    const responseText = alignWithOdop
      ? (selectedLang === "en"
        ? "Excellent choice! I'll align your business with the district's ODOP product for additional benefits."
        : "बहुत अच्छा फैसला! मैं आपके व्यवसाय को जिले के ODOP उत्पाद के साथ जोड़ दूँगी जिससे आपको अतिरिक्त लाभ मिलेंगे।")
      : (selectedLang === "en"
        ? "Understood! I'll continue with your original business idea. There are still great schemes available for you."
        : "समझ गई! मैं आपके मूल व्यवसाय विचार के साथ आगे बढ़ूँगी। आपके लिए अभी भी बेहतरीन योजनाएँ उपलब्ध हैं।");

    setMessages(prev => [...prev, {
      id: `odop-decision-${Date.now()}`,
      role: "assistant",
      content: responseText,
      timestamp: new Date().toISOString(),
    }]);

    setOdopData(null);
    playTTS(responseText, selectedLang || "hi");
  }, [selectedLang, playTTS]);

  // ─── Process Collected Fields & Submit ──────────────────────────────
  const handleFinalSubmit = useCallback(async () => {
    const submitFn = onWizardSubmit || createAndSaveBusiness;
    if (!submitFn) return;
    try {
      await submitFn({
        ...collectedFields,
        language: selectedLang || "en",
        latitude: userProfile?.latitude || null,
        longitude: userProfile?.longitude || null,
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      console.error("Submission failed:", err);
    }
  }, [collectedFields, selectedLang, userProfile, onWizardSubmit, createAndSaveBusiness, navigate]);

  // ─── Render: Language Selection Phase ───────────────────────────────
  if (phase === "lang_select") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50/30 flex items-center justify-center px-4 py-8 relative overflow-hidden">
        {/* Background ambient glow */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[40rem] h-[40rem] bg-sovereign-100/40 blur-[180px] rounded-full pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/3 w-80 h-80 bg-sky-100/40 blur-[140px] rounded-full pointer-events-none" />

        <div className="max-w-2xl w-full relative z-10">
          {/* MIRA Avatar & Welcome */}
          <div className="text-center mb-8 animate-[fadeIn_0.5s_ease-out]">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-sovereign-900 via-sovereign-800 to-indigo-900 flex items-center justify-center text-white text-3xl font-black mx-auto mb-4 shadow-xl shadow-sovereign-950/20 ring-4 ring-white">
              उ
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold font-display text-slate-900 mb-2">
              नमस्ते {userName} जी! 🙏
            </h1>
            <p className="text-sm text-slate-600 font-medium mb-1">
              Welcome to Udyam Saathi
            </p>
            <p className="text-lg font-bold text-sovereign-800 mt-4">
              {LANG_SELECT_PROMPT.hi} / {LANG_SELECT_PROMPT.en}
            </p>
          </div>

          {/* Language Cards Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4 mb-8">
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
                  {/* Gradient top accent bar */}
                  <div className={`absolute top-0 left-3 right-3 h-1 rounded-b-full bg-gradient-to-r ${lang.gradient} opacity-${isSelected ? '100' : '0'} group-hover:opacity-100 transition-opacity duration-300`} />

                  {/* Language Initials (ABC equivalent in that script) */}
                  <div className={`text-2xl sm:text-3xl font-black mb-2 bg-gradient-to-r ${lang.gradient} bg-clip-text text-transparent leading-tight`}>
                    {lang.initials}
                  </div>

                  {/* Native Name */}
                  <div className="text-base sm:text-lg font-bold text-slate-900 mb-0.5">
                    {lang.native}
                  </div>

                  {/* English Label */}
                  <div className="text-[11px] text-slate-500 font-medium uppercase tracking-wider">
                    {lang.label}
                  </div>

                  {/* Selected check */}
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

        {/* CSS Animation */}
        <style>{`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}</style>
      </div>
    );
  }

  // ─── Render: Chat Phase ────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50/30 flex flex-col relative overflow-hidden">
      {/* Background ambient glow */}
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
              MIRA — Business Advisor
            </h1>
            <p className="text-[11px] text-sky-200/80 truncate">
              {selectedLang && ONBOARDING_LANGUAGES.find(l => l.code === selectedLang)?.native} • 
              {isPlayingAudio ? " 🔊 Speaking..." : " Online"}
            </p>
          </div>
          
          {/* Collected Fields Progress Indicator */}
          <div className="flex items-center gap-1.5">
            {Object.keys(collectedFields).length > 0 && (
              <div className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-lg border border-emerald-400/30 font-bold">
                {Object.keys(collectedFields).length} fields
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
              {/* Assistant Avatar */}
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
                {/* Render markdown-like text */}
                <div className="whitespace-pre-wrap">
                  {msg.content.split("\n").map((line, i) => {
                    // Bold text
                    const boldParsed = line.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
                    return (
                      <p key={i} className={i > 0 ? "mt-1.5" : ""} dangerouslySetInnerHTML={{ __html: boldParsed }} />
                    );
                  })}
                </div>

                {/* Voice indicator */}
                {msg.isVoice && (
                  <div className="mt-1.5 flex items-center gap-1 text-[10px] opacity-70">
                    <Mic className="w-3 h-3" />
                    <span>Voice message</span>
                  </div>
                )}

                {/* TTS playback button for assistant messages */}
                {msg.role === "assistant" && (
                  <button
                    onClick={() => playTTS(msg.content, selectedLang || "hi")}
                    className="mt-2 inline-flex items-center gap-1 text-[11px] text-sovereign-600 hover:text-sovereign-800 font-medium transition-colors"
                    disabled={isPlayingAudio}
                  >
                    <Volume2 className="w-3.5 h-3.5" />
                    <span>{isPlayingAudio ? "Playing..." : "Listen"}</span>
                  </button>
                )}
              </div>

              {/* User Avatar */}
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-xl bg-slate-200 flex items-center justify-center text-slate-600 text-xs font-bold shrink-0 mt-0.5">
                  {userName.charAt(0).toUpperCase()}
                </div>
              )}
            </div>
          ))}

          {/* ODOP Comparison Cards */}
          {odopData && (
            <div className="animate-[fadeIn_0.4s_ease-out]">
              <div className="bg-white rounded-2xl border border-sovereign-200 shadow-lg overflow-hidden max-w-lg mx-auto">
                <div className="bg-gradient-to-r from-sovereign-900 to-indigo-900 text-white px-4 py-3 text-sm font-bold flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-sky-300" />
                  ODOP Alignment Opportunity
                </div>
                <div className="p-4 space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    {/* Without ODOP */}
                    <div className="rounded-xl border border-slate-200 p-3 bg-slate-50">
                      <div className="text-[11px] font-bold text-slate-500 uppercase mb-1">Your Idea</div>
                      <div className="text-sm font-bold text-slate-900 mb-2">{odopData.user_business || "Your Business"}</div>
                      <ul className="text-[11px] text-slate-600 space-y-0.5">
                        {(odopData.without_odop_pros || []).map((p, i) => (
                          <li key={i} className="flex items-start gap-1">
                            <span className="text-emerald-500 mt-0.5">✓</span> {p}
                          </li>
                        ))}
                        {(odopData.without_odop_cons || []).map((c, i) => (
                          <li key={i} className="flex items-start gap-1">
                            <span className="text-rose-500 mt-0.5">✗</span> {c}
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* With ODOP */}
                    <div className="rounded-xl border-2 border-emerald-300 p-3 bg-emerald-50/50">
                      <div className="text-[11px] font-bold text-emerald-600 uppercase mb-1">ODOP Aligned</div>
                      <div className="text-sm font-bold text-slate-900 mb-2">{odopData.odop_product || "ODOP Product"}</div>
                      <ul className="text-[11px] text-slate-600 space-y-0.5">
                        {(odopData.with_odop_pros || []).map((p, i) => (
                          <li key={i} className="flex items-start gap-1">
                            <span className="text-emerald-500 mt-0.5">✓</span> {p}
                          </li>
                        ))}
                        {(odopData.with_odop_cons || []).map((c, i) => (
                          <li key={i} className="flex items-start gap-1">
                            <span className="text-rose-500 mt-0.5">✗</span> {c}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleOdopDecision(false)}
                      className="flex-1 py-2.5 text-xs font-bold rounded-xl border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors"
                    >
                      {selectedLang === "en" ? "Keep My Idea" : "मेरा विचार रखें"}
                    </button>
                    <button
                      onClick={() => handleOdopDecision(true)}
                      className="flex-1 py-2.5 text-xs font-bold rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-500 hover:to-teal-500 transition-all shadow-md"
                    >
                      {selectedLang === "en" ? "Align with ODOP ✨" : "ODOP से जोड़ें ✨"}
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

      {/* Input Bar — Fixed at bottom */}
      <div className="sticky bottom-0 z-20 bg-white/95 backdrop-blur-xl border-t border-slate-200/80 px-3 sm:px-4 py-3 shadow-[0_-4px_20px_rgba(0,0,0,0.04)]">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-2">
            {/* Voice Record Button */}
            <button
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onTouchStart={startRecording}
              onTouchEnd={stopRecording}
              disabled={isSending}
              className={`shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition-all duration-200 ${
                isRecording
                  ? "bg-rose-500 text-white shadow-lg shadow-rose-500/30 scale-110 animate-pulse"
                  : "bg-slate-100 text-slate-600 hover:bg-sovereign-100 hover:text-sovereign-800 border border-slate-200"
              }`}
              title={isRecording ? "Recording... Release to stop" : "Hold to record voice"}
            >
              {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            {/* Text Input */}
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

            {/* Send Button */}
            <button
              onClick={() => handleSendMessage()}
              disabled={!inputText.trim() || isSending}
              className="shrink-0 w-11 h-11 rounded-xl bg-gradient-to-r from-sovereign-800 via-sovereign-700 to-indigo-800 text-white flex items-center justify-center shadow-md shadow-sovereign-900/20 hover:shadow-lg disabled:opacity-40 disabled:shadow-none transition-all duration-200"
            >
              {isSending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>

          {/* Bottom hint */}
          <div className="text-center mt-2">
            <p className="text-[10px] text-slate-400 font-medium">
              {selectedLang === "en"
                ? "MIRA uses Sarvam AI & Bhashini for intelligent multilingual assistance"
                : "MIRA बुद्धिमान बहुभाषी सहायता के लिए Sarvam AI और भाषिनी का उपयोग करती है"}
            </p>
          </div>
        </div>
      </div>

      {/* Processing Phase Overlay */}
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
                ? "MIRA has understood your business idea. Click below to generate your complete feasibility report."
                : "MIRA ने आपके व्यवसाय के विचार को समझ लिया है। अपनी पूरी व्यवहार्यता रिपोर्ट बनाने के लिए नीचे क्लिक करें।"}
            </p>

            {/* Collected Fields Summary */}
            <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 mb-6 text-left">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Collected Details</div>
              <div className="space-y-1.5 text-xs text-slate-700">
                {Object.entries(collectedFields).map(([key, val]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-slate-500 font-medium capitalize">{key.replace(/_/g, " ")}</span>
                    <span className="font-semibold text-slate-900 text-right max-w-[60%] truncate">
                      {typeof val === "boolean" ? (val ? "Yes" : "No") : String(val)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={handleFinalSubmit}
              disabled={parentLoading}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-indigo-900 text-white font-bold text-sm shadow-lg shadow-sovereign-950/20 hover:shadow-xl transition-all duration-200 flex items-center justify-center gap-2 group disabled:opacity-50"
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

      {/* CSS Animation */}
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
