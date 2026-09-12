import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { chatApi } from '../services/api';
import { useAuth } from './AuthContext';
import { useBusiness } from './BusinessContext';
import { useLanguage } from './LanguageContext';
import { useWakeWord } from '../hooks/useWakeWord';
import { playSiriActivationChime } from '../utils/siriAudio';

export const CHAT_THEMES = {
  sovereign: {
    id: 'sovereign',
    name: 'Sovereign Light',
    accentColor: 'sky',
    // Container
    windowBg: 'bg-white/95 backdrop-blur-2xl border-slate-200/90 shadow-2xl text-slate-800 ring-1 ring-slate-900/5',
    topBar: 'bg-gradient-to-r from-sovereign-900 via-sky-500 to-emerald-500',
    // Header
    headerBg: 'bg-gradient-to-r from-sovereign-950 via-sovereign-900 to-indigo-950 text-white border-b border-sovereign-800',
    headerTitle: 'text-white',
    headerSubtitle: 'text-sky-200/90',
    headerBadge: 'bg-sky-500/20 text-sky-300 border border-sky-400/30',
    headerBtn: 'text-slate-300 hover:text-white hover:bg-white/10',
    headerMinimizeBtn: 'text-sky-300 hover:text-white hover:bg-sky-500/20 border border-sky-400/30',
    // Body / Messages List
    bodyBg: 'bg-slate-50/80',
    userBubble: 'bg-gradient-to-r from-sovereign-900 via-sovereign-800 to-indigo-900 text-white border border-sky-400/20 shadow-md',
    userText: 'text-white',
    assistantBubble: 'bg-white text-slate-800 border border-slate-200/90 shadow-xs',
    metaText: 'text-slate-400',
    metaPill: 'text-sovereign-700 font-semibold',
    loadingBg: 'bg-white border border-slate-200 text-sovereign-800 shadow-sm',
    loadingText: 'text-slate-600',
    // Quick chips
    chipHeader: 'text-slate-500',
    chipBtn: 'bg-white hover:bg-sky-50 text-slate-700 hover:text-sovereign-900 border-slate-200 hover:border-sky-300 shadow-2xs',
    // Input
    inputFooter: 'bg-white border-t border-slate-200/90',
    textarea: 'bg-slate-50 border-slate-200 focus:bg-white focus:border-sky-500 focus:ring-1 focus:ring-sky-400/40 text-slate-900 placeholder:text-slate-400',
    sendBtn: 'bg-gradient-to-r from-sovereign-800 via-sky-700 to-sovereign-900 hover:from-sovereign-700 hover:to-sky-600 text-white shadow-md shadow-sovereign-900/10',
    subText: 'text-slate-400',
    subBadge: 'bg-slate-100 border-slate-200 text-slate-500',
    // Markdown
    mdText: 'text-slate-800',
    mdH3: 'text-sovereign-900 border-slate-200',
    mdH2: 'text-sovereign-950 border-slate-300',
    mdList: 'text-slate-700 marker:text-sky-600',
    mdBold: 'text-slate-950 font-bold',
    mdCode: 'bg-slate-100 text-sovereign-800 border-slate-200',
    mdQuote: 'border-sky-500 bg-sky-50/60 text-slate-700',
  },
  midnight: {
    id: 'midnight',
    name: 'Midnight Navy',
    accentColor: 'cyan',
    // Container
    windowBg: 'bg-[#041523]/95 backdrop-blur-2xl border-sky-900/60 shadow-2xl text-slate-100 ring-1 ring-white/10',
    topBar: 'bg-gradient-to-r from-cyan-400 via-sky-400 to-indigo-500',
    // Header
    headerBg: 'bg-[#020b12]/90 text-white border-b border-sky-950',
    headerTitle: 'text-white',
    headerSubtitle: 'text-cyan-300/80',
    headerBadge: 'bg-cyan-950/80 text-cyan-300 border border-cyan-700/60',
    headerBtn: 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/80',
    headerMinimizeBtn: 'text-cyan-400 hover:text-white hover:bg-cyan-900/50 border border-cyan-800/50',
    // Body / Messages List
    bodyBg: 'bg-[#071d2e]/40',
    userBubble: 'bg-gradient-to-r from-cyan-900 via-sky-800 to-indigo-900 text-white border border-cyan-400/30 shadow-md',
    userText: 'text-white',
    assistantBubble: 'bg-[#092237]/90 text-slate-100 border border-sky-800/60 shadow-xs',
    metaText: 'text-slate-400',
    metaPill: 'text-cyan-400/90 font-medium',
    loadingBg: 'bg-[#092237]/90 border border-sky-800/60 text-cyan-300 shadow-md',
    loadingText: 'text-slate-300',
    // Quick chips
    chipHeader: 'text-slate-400',
    chipBtn: 'bg-[#071d2e]/70 hover:bg-[#0c2a42] text-slate-200 hover:text-cyan-200 border-sky-800/60 hover:border-cyan-500/60 shadow-2xs',
    // Input
    inputFooter: 'bg-[#020b12]/95 border-t border-sky-950',
    textarea: 'bg-[#071d2e]/90 border-sky-900/80 focus:border-cyan-400/80 focus:ring-1 focus:ring-cyan-400/50 text-slate-100 placeholder:text-slate-500',
    sendBtn: 'bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white shadow-md shadow-cyan-950/40',
    subText: 'text-slate-400',
    subBadge: 'bg-slate-900 border-slate-800 text-slate-400',
    // Markdown
    mdText: 'text-slate-100',
    mdH3: 'text-cyan-300 border-slate-700/50',
    mdH2: 'text-slate-100 border-slate-700',
    mdList: 'text-slate-200 marker:text-cyan-400',
    mdBold: 'text-white font-bold',
    mdCode: 'bg-[#03111c] text-cyan-300 border-sky-800',
    mdQuote: 'border-cyan-500 bg-slate-800/40 text-slate-300',
  },
  emerald: {
    id: 'emerald',
    name: 'Emerald Mint',
    accentColor: 'emerald',
    // Container
    windowBg: 'bg-white/95 backdrop-blur-2xl border-emerald-200/90 shadow-2xl text-slate-800 ring-1 ring-emerald-900/5',
    topBar: 'bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-500',
    // Header
    headerBg: 'bg-gradient-to-r from-emerald-950 via-teal-950 to-slate-950 text-white border-b border-emerald-900',
    headerTitle: 'text-white',
    headerSubtitle: 'text-emerald-200/80',
    headerBadge: 'bg-emerald-500/20 text-emerald-300 border border-emerald-400/30',
    headerBtn: 'text-slate-300 hover:text-white hover:bg-white/10',
    headerMinimizeBtn: 'text-emerald-300 hover:text-white hover:bg-emerald-500/20 border border-emerald-400/30',
    // Body / Messages List
    bodyBg: 'bg-emerald-50/25',
    userBubble: 'bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 text-white border border-emerald-400/20 shadow-md',
    userText: 'text-white',
    assistantBubble: 'bg-white text-slate-800 border border-emerald-100/90 shadow-xs',
    metaText: 'text-slate-400',
    metaPill: 'text-emerald-700 font-semibold',
    loadingBg: 'bg-white border border-emerald-200 text-emerald-800 shadow-sm',
    loadingText: 'text-slate-600',
    // Quick chips
    chipHeader: 'text-slate-500',
    chipBtn: 'bg-white hover:bg-emerald-50 text-slate-700 hover:text-emerald-900 border-emerald-200 hover:border-emerald-300 shadow-2xs',
    // Input
    inputFooter: 'bg-white border-t border-emerald-100',
    textarea: 'bg-emerald-50/40 border-emerald-200 focus:bg-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-400/40 text-slate-900 placeholder:text-slate-400',
    sendBtn: 'bg-gradient-to-r from-emerald-700 via-teal-700 to-emerald-800 hover:from-emerald-600 hover:to-teal-600 text-white shadow-md shadow-emerald-950/20',
    subText: 'text-slate-400',
    subBadge: 'bg-emerald-50 border-emerald-200 text-emerald-700',
    // Markdown
    mdText: 'text-slate-800',
    mdH3: 'text-emerald-900 border-emerald-200',
    mdH2: 'text-emerald-950 border-emerald-300',
    mdList: 'text-slate-700 marker:text-emerald-600',
    mdBold: 'text-slate-950 font-bold',
    mdCode: 'bg-emerald-50 text-emerald-900 border-emerald-200',
    mdQuote: 'border-emerald-500 bg-emerald-50/60 text-slate-700',
  },
  royal: {
    id: 'royal',
    name: 'Royal Purple',
    accentColor: 'purple',
    // Container
    windowBg: 'bg-[#0e0720]/95 backdrop-blur-2xl border-purple-900/60 shadow-2xl text-purple-100 ring-1 ring-white/10',
    topBar: 'bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-500',
    // Header
    headerBg: 'bg-[#080214]/90 text-white border-b border-purple-950',
    headerTitle: 'text-white',
    headerSubtitle: 'text-purple-300/80',
    headerBadge: 'bg-purple-950/80 text-purple-300 border border-purple-700/60',
    headerBtn: 'text-purple-300 hover:text-white hover:bg-purple-900/40',
    headerMinimizeBtn: 'text-purple-300 hover:text-white hover:bg-purple-900/50 border border-purple-800/50',
    // Body / Messages List
    bodyBg: 'bg-[#150a2e]/40',
    userBubble: 'bg-gradient-to-r from-purple-900 via-indigo-900 to-pink-900 text-white border border-purple-400/30 shadow-md',
    userText: 'text-white',
    assistantBubble: 'bg-[#1c0f3d]/90 text-purple-100 border border-purple-800/60 shadow-xs',
    metaText: 'text-purple-400',
    metaPill: 'text-purple-300 font-medium',
    loadingBg: 'bg-[#1c0f3d]/90 border border-purple-800/60 text-purple-300 shadow-md',
    loadingText: 'text-purple-200',
    // Quick chips
    chipHeader: 'text-purple-400',
    chipBtn: 'bg-[#1c0f3d]/70 hover:bg-[#281655] text-purple-200 hover:text-pink-200 border-purple-800/60 hover:border-purple-500/60 shadow-2xs',
    // Input
    inputFooter: 'bg-[#080214]/95 border-t border-purple-950',
    textarea: 'bg-[#150a2e]/90 border-purple-900/80 focus:border-purple-400/80 focus:ring-1 focus:ring-purple-400/50 text-purple-100 placeholder:text-purple-400',
    sendBtn: 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white shadow-md shadow-purple-950/40',
    subText: 'text-purple-400',
    subBadge: 'bg-purple-950 border-purple-900 text-purple-400',
    // Markdown
    mdText: 'text-purple-100',
    mdH3: 'text-purple-300 border-purple-800/50',
    mdH2: 'text-purple-100 border-purple-800',
    mdList: 'text-purple-200 marker:text-pink-400',
    mdBold: 'text-white font-bold',
    mdCode: 'bg-[#0b041a] text-purple-300 border-purple-800',
    mdQuote: 'border-purple-500 bg-purple-950/40 text-purple-200',
  },
};

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const { token } = useAuth();
  const { reportData, activeBusiness } = useBusiness();
  const { language } = useLanguage();

  // Floating Window State
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [animState, setAnimState] = useState('idle'); // 'opening' | 'minimizing' | 'idle'
  const [isLoading, setIsLoading] = useState(false);

  // Audio Voice State
  const [autoPlayVoice, setAutoPlayVoice] = useState(() => {
    try {
      const saved = localStorage.getItem('udyam_saathi_voice_autoplay');
      return saved !== null ? JSON.parse(saved) : true;
    } catch (e) {
      return true;
    }
  });
  const [playingAudioId, setPlayingAudioId] = useState(null);
  const [ttsLoadingId, setTtsLoadingId] = useState(null);
  const currentAudioRef = useRef(null);

  // Theme State
  const [chatTheme, setChatTheme] = useState(() => {
    return localStorage.getItem('udyam_saathi_chat_theme') || 'sovereign';
  });

  // Window Dimension & Position State
  const [position, setPosition] = useState(() => {
    const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
    if (isMobile) {
      return { x: 12, y: 64 };
    }
    const winWidth = typeof window !== 'undefined' ? window.innerWidth : 1200;
    return { x: Math.max(20, winWidth - 460), y: 84 };
  });

  const [size, setSize] = useState(() => {
    const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
    return {
      width: isMobile ? (typeof window !== 'undefined' ? window.innerWidth - 24 : 360) : 420,
      height: isMobile ? (typeof window !== 'undefined' ? window.innerHeight - 100 : 560) : 590,
    };
  });

  // Conversation Messages State
  const [messages, setMessages] = useState([
    {
      id: 'welcome-init',
      role: 'assistant',
      content: `👋 **Namaste! I am Udyam Saathi's AI Advisor.**\n\nI am grounded in your enterprise parameters, 10-D XGBoost viability score, statutory scheme rankings (PMEGP, Mudra, PMFME), and 5-year bank cash flows.\n\nYou can **type or speak** in your chosen language anytime!`,
      timestamp: new Date().toISOString(),
      sources: ['Udyam Saathi MSME Credit & Feasibility Advisory Knowledge Base'],
    },
  ]);

  const navButtonRef = useRef(null);
  const chatInputRef = useRef(null);

  // Active Project Identifier
  const activeProjectKey =
    activeBusiness?.project_id ||
    reportData?.report_id ||
    reportData?.input_parameters?.enterprise_name ||
    (activeBusiness?.name ? `biz_${activeBusiness.name}` : null);

  const prevProjectKeyRef = useRef(null);

  // Helper to build a fresh, project-grounded initial welcome message
  const createProjectWelcomeMessage = useCallback((entName, sector, cost) => {
    const formattedCost = cost ? ` • ₹${(Number(cost) / 100000).toFixed(1)}L Outlay` : '';
    const formattedSector = sector ? ` (${sector})` : '';
    return {
      id: `welcome-${Date.now()}`,
      role: 'assistant',
      content: `👋 **Namaste! I am Udyam Saathi's AI Advisor.**\n\nI am grounded in your active enterprise parameters for **${entName || 'your enterprise'}**${formattedSector}${formattedCost}, including 10-D XGBoost viability score, statutory scheme rankings (PMEGP, Mudra, PMFME), and 5-year cash flows.\n\nYou can **type or speak** in your chosen language anytime!`,
      timestamp: new Date().toISOString(),
      sources: ['Udyam Saathi MSME Credit & Feasibility Advisory Knowledge Base'],
    };
  }, []);

  // Save Theme Preference
  useEffect(() => {
    localStorage.setItem('udyam_saathi_chat_theme', chatTheme);
  }, [chatTheme]);

  // Save AutoPlay Preference
  useEffect(() => {
    localStorage.setItem('udyam_saathi_voice_autoplay', JSON.stringify(autoPlayVoice));
  }, [autoPlayVoice]);

  const currentTheme = CHAT_THEMES[chatTheme] || CHAT_THEMES.sovereign;

  const selectTheme = useCallback((themeId) => {
    if (CHAT_THEMES[themeId]) {
      setChatTheme(themeId);
    }
  }, []);

  const cycleTheme = useCallback(() => {
    const themeKeys = Object.keys(CHAT_THEMES);
    const currentIndex = themeKeys.indexOf(chatTheme);
    const nextIndex = (currentIndex + 1) % themeKeys.length;
    setChatTheme(themeKeys[nextIndex]);
  }, [chatTheme]);

  // Stop currently playing audio
  const stopAudio = useCallback(() => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    setPlayingAudioId(null);
  }, []);

  // AUTOMATIC RESET ON PROJECT SWITCH:
  // Detects when the active project ID or report changes, stops any ongoing audio,
  // and starts a completely fresh, isolated conversation for the new project.
  useEffect(() => {
    if (!activeProjectKey) return;

    if (prevProjectKeyRef.current === null) {
      prevProjectKeyRef.current = activeProjectKey;
      return;
    }

    if (prevProjectKeyRef.current !== activeProjectKey) {
      prevProjectKeyRef.current = activeProjectKey;

      // 1. Stop any playing voice audio from previous project
      stopAudio();

      // 2. Clear any pending TTS loading state
      setTtsLoadingId(null);

      // 3. Reset conversation history completely for the new project
      const entName =
        reportData?.enterprise_name ||
        reportData?.input_parameters?.enterprise_name ||
        activeBusiness?.name ||
        'your enterprise';
      const sector =
        reportData?.sector ||
        reportData?.input_parameters?.sector ||
        activeBusiness?.sector ||
        '';
      const cost =
        reportData?.financial_summary?.project_cost ||
        reportData?.input_parameters?.project_cost ||
        activeBusiness?.project_cost;

      setMessages([createProjectWelcomeMessage(entName, sector, cost)]);
    }
  }, [activeProjectKey, activeBusiness, reportData, stopAudio, createProjectWelcomeMessage]);

  // Play audio from base64 data URL
  const playAudio = useCallback((audioBase64, msgId) => {
    if (!audioBase64) return;

    if (playingAudioId === msgId && currentAudioRef.current) {
      stopAudio();
      return;
    }

    stopAudio();

    try {
      const audio = new Audio(audioBase64);
      currentAudioRef.current = audio;
      setPlayingAudioId(msgId);

      audio.onended = () => {
        setPlayingAudioId(null);
        currentAudioRef.current = null;
      };

      audio.onerror = () => {
        setPlayingAudioId(null);
        currentAudioRef.current = null;
      };

      audio.play().catch((err) => {
        console.warn('Audio autoplay blocked or failed:', err);
        setPlayingAudioId(null);
      });
    } catch (e) {
      console.error('Audio playback error:', e);
      setPlayingAudioId(null);
    }
  }, [playingAudioId, stopAudio]);

  // Play TTS for any message on demand
  const playMessageTts = useCallback(async (msgId, text, msgAudioBase64) => {
    if (msgAudioBase64) {
      playAudio(msgAudioBase64, msgId);
      return;
    }

    if (ttsLoadingId) return;

    setTtsLoadingId(msgId);
    try {
      const res = await chatApi.generateTts(text, language || 'en', token);
      if (res && res.audio_base64) {
        setMessages((prev) =>
          prev.map((m) => (m.id === msgId ? { ...m, audio_base64: res.audio_base64 } : m))
        );
        playAudio(res.audio_base64, msgId);
      }
    } catch (err) {
      console.error('TTS request failed:', err);
    } finally {
      setTtsLoadingId(null);
    }
  }, [language, token, ttsLoadingId, playAudio]);

  // Ensure Window remains in viewport bounds on resize
  useEffect(() => {
    const handleResize = () => {
      if (typeof window === 'undefined') return;
      const isMobile = window.innerWidth < 768;
      if (isMobile) {
        setSize({
          width: window.innerWidth - 24,
          height: window.innerHeight - 100,
        });
        setPosition({ x: 12, y: 64 });
        return;
      }

      setPosition((prev) => {
        const maxX = window.innerWidth - size.width - 20;
        const maxY = window.innerHeight - size.height - 20;
        return {
          x: Math.min(Math.max(20, prev.x), maxX),
          y: Math.min(Math.max(70, prev.y), maxY),
        };
      });
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [size]);

  // Open Chat with Origin-Directed Expansion Animation
  const openChat = useCallback(() => {
    if (isChatOpen && animState === 'idle') {
      if (chatInputRef.current) {
        chatInputRef.current.focus();
      }
      return;
    }

    setIsChatOpen(true);
    setIsAnimating(true);
    setAnimState('opening');

    setTimeout(() => {
      setAnimState('idle');
      setIsAnimating(false);
      if (chatInputRef.current) {
        chatInputRef.current.focus();
      }
    }, 280);
  }, [isChatOpen, animState]);

  // Minimize Chat with Animation toward Navigation Button
  const minimizeChat = useCallback(() => {
    if (!isChatOpen || isAnimating) return;

    stopAudio();
    setIsAnimating(true);
    setAnimState('minimizing');

    setTimeout(() => {
      setIsChatOpen(false);
      setAnimState('idle');
      setIsAnimating(false);
    }, 280);
  }, [isChatOpen, isAnimating, stopAudio]);

  // Toggle Chat
  const toggleChat = useCallback(() => {
    if (isChatOpen) {
      minimizeChat();
    } else {
      openChat();
    }
  }, [isChatOpen, minimizeChat, openChat]);

  // Global Keyboard Shortcut: Alt + Space
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.altKey && (e.code === 'Space' || e.key === ' ' || e.keyCode === 32)) {
        e.preventDefault();
        e.stopPropagation();

        if (!isChatOpen) {
          openChat();
        } else {
          if (chatInputRef.current) {
            chatInputRef.current.focus();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown, true);
    return () => window.removeEventListener('keydown', handleKeyDown, true);
  }, [isChatOpen, openChat]);

  // Extract Active Dashboard Tab & Deep Page Content Telemetry
  const getActiveTabTelemetry = useCallback(() => {
    const path = typeof window !== 'undefined' ? window.location.pathname : '';
    let tabKey = 'overview';
    let tabTitle = 'Overview Synthesis Dashboard';
    let icon = '📊';

    if (path.includes('/viability')) {
      tabKey = 'viability';
      tabTitle = 'ML Viability & TreeSHAP Attributions';
      icon = '🧠';
    } else if (path.includes('/market')) {
      tabKey = 'market';
      tabTitle = 'Market Demand & Local Cluster Density';
      icon = '📍';
    } else if (path.includes('/schemes')) {
      tabKey = 'schemes';
      tabTitle = 'Government Scheme Optimizer';
      icon = '🏛️';
    } else if (path.includes('/financials')) {
      tabKey = 'financials';
      tabTitle = '5-Year Financials & Cash Flow Projections';
      icon = '📈';
    } else if (path.includes('/risk')) {
      tabKey = 'risk';
      tabTitle = 'Comprehensive Multi-Dimensional Risk Assessment';
      icon = '🛡️';
    } else if (path.includes('/swot')) {
      tabKey = 'swot';
      tabTitle = 'Strategic SWOT Analysis Matrix';
      icon = '🧭';
    } else if (path.includes('/dpr')) {
      tabKey = 'dpr';
      tabTitle = 'Official Bank Detailed Project Report (DPR)';
      icon = '📄';
    }

    let tabData = null;
    let quickPrompts = [];

    if (reportData) {
      if (tabKey === 'overview') {
        tabData = {
          enterprise_name: reportData.enterprise_name || reportData.input_parameters?.enterprise_name,
          project_cost: reportData.financial_summary?.project_cost || reportData.input_parameters?.project_cost,
          top_scheme: reportData.scheme_recommendations?.[0]?.scheme_id,
          subsidy_amount: reportData.scheme_recommendations?.[0]?.subsidy_grant_amount,
          ml_verdict: reportData.ml_viability?.verdict,
          dscr: reportData.financial_summary?.dscr_ratio,
        };
        quickPrompts = [
          'Summarize this Overview Synthesis page',
          'Is this project viable for a bank loan?',
          'What is the recommended government scheme?',
          'Explain the 5-year financial breakdown',
        ];
      } else if (tabKey === 'viability') {
        tabData = {
          verdict: reportData.ml_viability?.verdict,
          confidence_pct: reportData.ml_viability?.confidence_pct,
          probabilities: reportData.ml_viability?.class_probabilities,
          top_positive_driver: reportData.ml_viability?.top_positive_feature,
          top_risk_driver: reportData.ml_viability?.top_negative_feature,
        };
        quickPrompts = [
          'Explain the 10-D XGBoost viability score',
          'What are the main solvency drivers?',
          'How can I improve model confidence?',
        ];
      } else if (tabKey === 'market') {
        tabData = {
          catchment_pop_2026: reportData.market_demographics?.catchment_population_2026,
          annual_tam: reportData.market_demographics?.annual_tam,
          msme_density: reportData.market_demographics?.msme_density_per_10k,
          pricing_floor: reportData.pricing_recommendation?.cpi_adjusted_unit_price_floor,
        };
        quickPrompts = [
          'What is the annual local TAM demand?',
          'Explain the MSME competition density',
          'What is the recommended selling price band?',
        ];
      } else if (tabKey === 'schemes') {
        tabData = {
          top_scheme: reportData.scheme_recommendations?.[0],
          all_schemes: reportData.scheme_recommendations?.map((s) => ({
            id: s.scheme_id,
            eligible: s.eligible,
            subsidy: s.subsidy_grant_amount,
          })),
        };
        quickPrompts = [
          'Why was this scheme ranked #1?',
          'How do I apply on the official government portal?',
          'What is the promoter equity margin required?',
        ];
      } else if (tabKey === 'financials') {
        tabData = {
          project_cost: reportData.financial_summary?.project_cost,
          dscr: reportData.financial_summary?.dscr_ratio,
          monthly_emi: reportData.financial_summary?.amortization_schedule?.monthly_emi,
          projections: reportData.financial_summary?.projections_5yr,
        };
        quickPrompts = [
          'Explain the 5-year cash flow projections',
          'Is the DSCR ratio compliant with RBI norms?',
          'What is the monthly bank EMI repayment?',
        ];
      } else if (tabKey === 'risk') {
        tabData = {
          composite_score: reportData.risk_assessment?.average_risk_score,
          severity: reportData.risk_assessment?.composite_grade,
          contingency_buffer: reportData.risk_assessment?.total_rupee_buffer,
        };
        quickPrompts = [
          'What are the highest operational risk pillars?',
          'How much contingency buffer is recommended?',
          'How to mitigate raw material price risk?',
        ];
      } else if (tabKey === 'swot') {
        tabData = reportData.swot_matrix;
        quickPrompts = [
          'Summarize the core enterprise strengths',
          'What are the key market opportunities?',
          'What threats require immediate mitigation?',
        ];
      } else if (tabKey === 'dpr') {
        tabData = {
          report_id: reportData.report_id,
          checklist: reportData.statutory_checklist,
        };
        quickPrompts = [
          'Summarize the 7-section bank DPR document',
          'What documents are required for credit sanction?',
          'How to export this DPR to PDF/HTML?',
        ];
      }
    } else {
      if (activeBusiness) {
        quickPrompts = [
          `Tell me about ${activeBusiness.name}`,
          'What government schemes can I apply for?',
          'How is project viability calculated?',
        ];
      } else {
        quickPrompts = [
          'Summarize this enterprise feasibility assessment',
          'Is this business ready for a bank loan application?',
          'What are the key financial highlights?',
        ];
      }
    }

    return { tabKey, tabTitle, icon, tabData, quickPrompts };
  }, [reportData, activeBusiness]);

  // Extract Full Grounded Context Payload
  const getGroundedContext = useCallback(() => {
    const { tabKey, tabTitle, tabData } = getActiveTabTelemetry();

    if (!reportData) {
      if (activeBusiness) {
        return {
          enterprise_name: activeBusiness.name,
          sector: activeBusiness.sector,
          business_category: activeBusiness.category,
          location: `${activeBusiness.district || ''}, ${activeBusiness.state || ''}`,
          project_cost: activeBusiness.project_cost,
          current_tab: tabKey,
          active_tab_title: tabTitle,
          active_tab_data: tabData,
        };
      }
      return {
        current_tab: tabKey,
        active_tab_title: tabTitle,
      };
    }

    return {
      enterprise_name: reportData.enterprise_name || reportData.input_parameters?.enterprise_name,
      sector: reportData.sector || reportData.input_parameters?.sector,
      business_category: reportData.business_category || reportData.input_parameters?.business_category,
      location: `${reportData.input_parameters?.village_name || ''}, ${reportData.input_parameters?.block_name || ''}, ${reportData.input_parameters?.district_name || ''}, ${reportData.input_parameters?.state_name || ''}`,
      project_cost: reportData.financial_summary?.project_cost || reportData.input_parameters?.project_cost,
      promoter_margin: reportData.financial_summary?.promoter_margin_amount,
      top_scheme_name: reportData.scheme_recommendations?.[0]?.scheme_id || reportData.scheme_recommendations?.[0]?.full_name,
      subsidy_amount: reportData.scheme_recommendations?.[0]?.subsidy_grant_amount,
      effective_loan: reportData.financial_summary?.effective_loan_principal,
      monthly_emi: reportData.financial_summary?.amortization_schedule?.monthly_emi,
      dscr: reportData.financial_summary?.dscr_ratio,
      dscr_verdict: reportData.financial_summary?.dscr_verdict,
      ml_verdict: reportData.ml_viability?.verdict,
      ml_confidence_pct: reportData.ml_viability?.confidence_pct,
      current_tab: tabKey,
      active_tab_title: tabTitle,
      active_tab_data: tabData,
    };
  }, [reportData, activeBusiness, getActiveTabTelemetry]);

  // Send Text User Message
  const sendMessage = useCallback(
    async (text) => {
      const trimmed = (text || '').trim();
      if (!trimmed || isLoading) return;

      const userMsg = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: trimmed,
        timestamp: new Date().toISOString(),
      };

      const updatedHistory = [...messages, userMsg];
      setMessages(updatedHistory);
      setIsLoading(true);

      const activeContext = getGroundedContext();

      try {
        const payloadHistory = updatedHistory.map((m) => ({
          role: m.role,
          content: m.content,
        }));

        const data = await chatApi.sendChatMessage(
          payloadHistory,
          activeContext,
          language || 'en',
          token
        );

        const replyText =
          data?.reply ||
          data?.message?.content ||
          data?.content ||
          (typeof data === 'string' ? data : null);

        const botMsg = {
          id: `bot-${Date.now()}`,
          role: 'assistant',
          content: replyText || 'I could not generate a response. Please try again.',
          timestamp: data?.timestamp || new Date().toISOString(),
          isFallback: data?.is_fallback || false,
          model: data?.model || 'groq',
          sources: data?.sources || [],
        };

        setMessages((prev) => [...prev, botMsg]);
      } catch (err) {
        console.error('Chat error:', err);
        const errorMsg = {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `⚠️ **Connection Notice**: ${err.message || 'Could not communicate with Udyam Saathi advisor service.'}`,
          timestamp: new Date().toISOString(),
          isError: true,
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, messages, getGroundedContext, language, token]
  );

  // Send Voice Audio Message (Microphone WebM -> Whisper STT -> LLM -> gTTS Audio)
  const sendVoiceAudioMessage = useCallback(
    async (audioBlob) => {
      if (!audioBlob || isLoading) return;

      const tempUserMsgId = `user-voice-${Date.now()}`;
      const userMsg = {
        id: tempUserMsgId,
        role: 'user',
        content: '🎤 Transcribing your voice...',
        isVoice: true,
        timestamp: new Date().toISOString(),
      };

      const updatedHistory = [...messages, userMsg];
      setMessages(updatedHistory);
      setIsLoading(true);

      const activeContext = getGroundedContext();

      try {
        const payloadHistory = messages.map((m) => ({
          role: m.role,
          content: m.content,
        }));

        const data = await chatApi.sendVoiceAudio(
          audioBlob,
          activeContext,
          language || 'en',
          payloadHistory,
          token
        );

        const transcript = data?.user_transcript || '(Voice Input)';
        const replyText = data?.reply || 'I could not generate a response. Please try again.';
        const audioBase64 = data?.audio_base64 || null;

        // Update the user message with transcribed speech
        setMessages((prev) =>
          prev.map((m) => (m.id === tempUserMsgId ? { ...m, content: transcript, isVoice: true } : m))
        );

        const botMsgId = `bot-voice-${Date.now()}`;
        const botMsg = {
          id: botMsgId,
          role: 'assistant',
          content: replyText,
          audio_base64: audioBase64,
          timestamp: data?.timestamp || new Date().toISOString(),
          isFallback: data?.is_fallback || false,
          model: data?.model || 'whisper-large-v3 + groq-llm',
          sources: data?.sources || [],
          latencies: {
            stt_s: data?.stt_latency_s,
            llm_s: data?.llm_latency_s,
            tts_s: data?.tts_latency_s,
            total_s: data?.total_latency_s,
          },
        };

        setMessages((prev) => [...prev, botMsg]);

        // Auto-play voice response if enabled
        if (autoPlayVoice && audioBase64) {
          playAudio(audioBase64, botMsgId);
        }
      } catch (err) {
        console.error('Voice chat error:', err);
        // Update user message on error
        setMessages((prev) =>
          prev.map((m) =>
            m.id === tempUserMsgId ? { ...m, content: '🎤 [Voice Recording Failed]' } : m
          )
        );
        const errorMsg = {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `⚠️ **Voice Processing Notice**: ${err.message || 'Could not process audio recording. Please check microphone permissions and try again.'}`,
          timestamp: new Date().toISOString(),
          isError: true,
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, messages, getGroundedContext, language, token, autoPlayVoice, playAudio]
  );

  // Clear conversation history
  const clearChat = useCallback(() => {
    stopAudio();
    const { tabTitle } = getActiveTabTelemetry();
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: `👋 **Chat history reset.**\n\nI am analyzing your **${tabTitle}** screen. Ask me in text or voice to summarize this page or evaluate any financial or scheme metrics!`,
        timestamp: new Date().toISOString(),
      },
    ]);
  }, [getActiveTabTelemetry, stopAudio]);

  // Voice Wake-Word "Hey Siri" Detection Handler
  const [siriNotice, setSiriNotice] = useState(null);

  const handleWakeWordDetected = useCallback(
    ({ phrase, transcript, trailingQuery }) => {
      // 1. Play authentic Web Audio Siri Chime
      playSiriActivationChime();

      // 2. Open chat window
      openChat();

      // 3. Set visual toast notice
      setSiriNotice({
        phrase: phrase || 'Hey Siri',
        transcript: transcript || '',
        trailingQuery: trailingQuery || '',
        timestamp: Date.now(),
      });
      setTimeout(() => setSiriNotice(null), 5000);

      // 4. If trailing command is present, auto-dispatch to LLM
      if (trailingQuery && trailingQuery.trim().length > 2) {
        sendMessage(trailingQuery.trim());
      }
    },
    [openChat, sendMessage]
  );

  const {
    isSupported: isWakeWordSupported,
    isEnabled: isWakeWordEnabled,
    isListening: isWakeWordListening,
    error: wakeWordError,
    engineType: wakeWordEngine,
    toggleWakeWord,
    enableWakeWord,
    disableWakeWord,
  } = useWakeWord({
    onWakeWordDetected: handleWakeWordDetected,
    enabledByDefault: false,
  });

  return (
    <ChatContext.Provider
      value={{
        isChatOpen,
        isAnimating,
        animState,
        isLoading,
        position,
        setPosition,
        size,
        messages,
        chatTheme,
        currentTheme,
        autoPlayVoice,
        setAutoPlayVoice,
        playingAudioId,
        ttsLoadingId,
        setChatTheme,
        selectTheme,
        cycleTheme,
        getActiveTabTelemetry,
        navButtonRef,
        chatInputRef,
        openChat,
        minimizeChat,
        toggleChat,
        sendMessage,
        sendVoiceAudioMessage,
        playAudio,
        stopAudio,
        playMessageTts,
        clearChat,
        // Wake-Word "Hey Siri" APIs
        isWakeWordSupported,
        isWakeWordEnabled,
        isWakeWordListening,
        wakeWordError,
        wakeWordEngine,
        toggleWakeWord,
        enableWakeWord,
        disableWakeWord,
        siriNotice,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
export default ChatProvider;
