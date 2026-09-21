import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Bot,
  Minus,
  RotateCcw,
  SendHorizontal,
  Sparkles,
  GripHorizontal,
  Copy,
  Check,
  Building2,
  AlertCircle,
  HelpCircle,
  Palette,
  CheckCircle2,
  Layers,
  ArrowUpRight,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Play,
  Pause,
  Square,
  Radio,
  Loader2,
  Languages,
} from 'lucide-react';
import { useChat, CHAT_THEMES } from '../../context/ChatContext';
import { useBusiness } from '../../context/BusinessContext';
import { useLanguage, LANGUAGES } from '../../context/LanguageContext';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { ChatMarkdown } from './ChatMarkdown';

export function FloatingChatWindow() {
  const {
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
    selectTheme,
    cycleTheme,
    getActiveTabTelemetry,
    navButtonRef,
    chatInputRef,
    minimizeChat,
    sendMessage,
    sendVoiceAudioMessage,
    playAudio,
    stopAudio,
    playMessageTts,
    clearChat,
    // "Mira" wake-word state
    isWakeWordSupported,
    isWakeWordEnabled,
    isWakeWordListening,
    toggleWakeWord,
    siriNotice,
  } = useChat();

  const { reportData, activeBusiness } = useBusiness();
  const { language, setLanguage } = useLanguage();

  const [inputVal, setInputVal] = useState('');
  const [copiedId, setCopiedId] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showThemeMenu, setShowThemeMenu] = useState(false);
  const [showLangMenu, setShowLangMenu] = useState(false);

  const dragStartRef = useRef({ mouseX: 0, mouseY: 0, posX: 0, posY: 0 });
  const messagesEndRef = useRef(null);
  const windowRef = useRef(null);
  const themeMenuRef = useRef(null);
  const langMenuRef = useRef(null);

  // Responsive detection
  const [isMobile, setIsMobile] = useState(() => typeof window !== 'undefined' && window.innerWidth < 768);
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const { tabTitle, icon, quickPrompts } = getActiveTabTelemetry();

  // Active language metadata
  const currentLangObj = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0];

  // Callback when voice recording completes (auto-stops on silence or manual stop)
  const handleVoiceRecordingComplete = useCallback(
    (audioBlob) => {
      sendVoiceAudioMessage(audioBlob);
    },
    [sendVoiceAudioMessage]
  );

  // Hook for dynamic silence detection and volume monitoring
  const {
    isRecording,
    isSpeaking,
    volume,
    duration,
    error: recorderError,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useVoiceRecorder({
    onRecordingComplete: handleVoiceRecordingComplete,
    silenceThresholdMs: 1600,
    minSpeechThreshold: 0.025,
  });

  // Close menus on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (themeMenuRef.current && !themeMenuRef.current.contains(e.target)) {
        setShowThemeMenu(false);
      }
      if (langMenuRef.current && !langMenuRef.current.contains(e.target)) {
        setShowLangMenu(false);
      }
    };
    if (showThemeMenu || showLangMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showThemeMenu, showLangMenu]);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, isRecording]);

  // Compute Animation Trajectory Delta (From Window center to Nav Button center)
  const getTransformOriginDelta = useCallback(() => {
    if (!navButtonRef?.current) {
      return { dx: 0, dy: -200 };
    }
    const navRect = navButtonRef.current.getBoundingClientRect();
    const navCenterX = navRect.left + navRect.width / 2;
    const navCenterY = navRect.top + navRect.height / 2;

    const winCenterX = position.x + size.width / 2;
    const winCenterY = position.y + size.height / 2;

    return {
      dx: Math.round(navCenterX - winCenterX),
      dy: Math.round(navCenterY - winCenterY),
    };
  }, [navButtonRef, position, size]);

  // Dragging logic from window header (desktop only — disabled on mobile)
  const handlePointerDown = (e) => {
    if (isMobile) return; // No drag on mobile
    if (
      e.target.closest('button') ||
      e.target.closest('input') ||
      e.target.closest('textarea') ||
      e.target.closest('.theme-menu') ||
      e.target.closest('.lang-menu')
    ) {
      return;
    }

    e.preventDefault();
    setIsDragging(true);

    const clientX = e.clientX || (e.touches && e.touches[0]?.clientX) || 0;
    const clientY = e.clientY || (e.touches && e.touches[0]?.clientY) || 0;

    dragStartRef.current = {
      mouseX: clientX,
      mouseY: clientY,
      posX: position.x,
      posY: position.y,
    };
  };

  useEffect(() => {
    const handlePointerMove = (e) => {
      if (!isDragging) return;

      const clientX = e.clientX || (e.touches && e.touches[0]?.clientX) || 0;
      const clientY = e.clientY || (e.touches && e.touches[0]?.clientY) || 0;

      const deltaX = clientX - dragStartRef.current.mouseX;
      const deltaY = clientY - dragStartRef.current.mouseY;

      const maxX = Math.max(10, window.innerWidth - size.width - 10);
      const maxY = Math.max(10, window.innerHeight - size.height - 10);

      const nextX = Math.min(Math.max(10, dragStartRef.current.posX + deltaX), maxX);
      const nextY = Math.min(Math.max(10, dragStartRef.current.posY + deltaY), maxY);

      setPosition({ x: nextX, y: nextY });
    };

    const handlePointerUp = () => {
      if (isDragging) {
        setIsDragging(false);
      }
    };

    if (isDragging) {
      window.addEventListener('mousemove', handlePointerMove);
      window.addEventListener('mouseup', handlePointerUp);
      window.addEventListener('touchmove', handlePointerMove);
      window.addEventListener('touchend', handlePointerUp);
    }

    return () => {
      window.removeEventListener('mousemove', handlePointerMove);
      window.removeEventListener('mouseup', handlePointerUp);
      window.removeEventListener('touchmove', handlePointerMove);
      window.removeEventListener('touchend', handlePointerUp);
    };
  }, [isDragging, size, setPosition]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputVal.trim() || isLoading) return;
    sendMessage(inputVal);
    setInputVal('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (!isChatOpen && !isAnimating) return null;

  const { dx, dy } = getTransformOriginDelta();

  const animationStyle =
    animState === 'opening'
      ? {
          transform: `translate3d(0, 0, 0) scale(1)`,
          opacity: 1,
          transition: 'all 280ms cubic-bezier(0.16, 1, 0.3, 1)',
        }
      : animState === 'minimizing'
      ? {
          transform: `translate3d(${dx}px, ${dy}px, 0) scale(0.12)`,
          opacity: 0,
          transition: 'all 260ms cubic-bezier(0.4, 0, 0.2, 1)',
          pointerEvents: 'none',
        }
      : {
          transform: 'translate3d(0, 0, 0) scale(1)',
          opacity: 1,
          transition: isDragging ? 'none' : 'box-shadow 200ms ease',
        };

  const activeEntTitle =
    reportData?.enterprise_name ||
    reportData?.input_parameters?.enterprise_name ||
    activeBusiness?.name ||
    'Active Enterprise Grounded';

  const activeEntCost =
    reportData?.financial_summary?.project_cost ||
    reportData?.input_parameters?.project_cost ||
    activeBusiness?.project_cost;

  // Waveform bars calculation (8 dynamic height bars reacting to microphone volume)
  const barMultipliers = [0.4, 0.8, 1.2, 1.6, 1.4, 1.0, 0.7, 0.3];

  return (
    <div
      ref={windowRef}
      role="dialog"
      aria-label="Udyam Saathi Groq AI Conversational Advisor"
      style={isMobile ? {
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        ...animationStyle,
      } : {
        position: 'fixed',
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: `${size.width}px`,
        height: `${size.height}px`,
        zIndex: 9999,
        ...animationStyle,
      }}
      className={`${
        isMobile ? 'flex flex-col overflow-hidden border-0 rounded-none' : 'rounded-2xl flex flex-col overflow-hidden border shadow-2xl'
      } transition-colors select-none ${currentTheme.windowBg}`}
    >
      {/* Top Accent Gradient Line */}
      <div className={`h-1.5 w-full shrink-0 ${currentTheme.topBar}`} />

      {/* Window Header */}
      <div
        onMouseDown={handlePointerDown}
        onTouchStart={handlePointerDown}
        className={`px-3.5 py-2.5 flex items-center justify-between shrink-0 ${
          isMobile ? '' : 'cursor-move'
        } ${currentTheme.headerBg}`}
      >
        {/* Left: Bot Identity & Active Enterprise */}
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center text-white shadow-md shadow-sky-950/30 border border-sky-300/40 shrink-0">
            <img src="/mira-avatar.png" alt="Mira" className="w-full h-full object-cover object-top" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <h3 className={`font-outfit font-bold text-xs tracking-tight truncate ${currentTheme.headerTitle}`}>
                Mira • AI Voice Advisor
              </h3>
              <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded-full ${currentTheme.headerBadge}`}>
                Sarvam AI
              </span>
            </div>
            <p className={`text-[10px] truncate flex items-center gap-1 ${currentTheme.headerSubtitle}`}>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse" />
              {activeEntTitle} {activeEntCost ? `• ₹${(activeEntCost / 100000).toFixed(1)}L` : ''}
            </p>
          </div>
        </div>

        {/* Right: Controls (Language Sync, Voice AutoPlay, Theme, Reset, Minimize) */}
        <div className="flex items-center gap-1 shrink-0">
          {/* Language Selector Dropdown in Chat Header */}
          <div className="relative" ref={langMenuRef}>
            <button
              type="button"
              onClick={() => setShowLangMenu((prev) => !prev)}
              className={`p-1.5 rounded-lg transition-colors cursor-pointer flex items-center gap-1 text-[10px] font-bold ${currentTheme.headerBtn}`}
              title="Change Voice & Chatbot Language"
            >
              <Languages className="w-3.5 h-3.5 text-sky-300" />
              <span className="hidden sm:inline uppercase">{currentLangObj.code}</span>
            </button>

            {showLangMenu && (
              <div className="absolute right-0 mt-1.5 w-40 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl py-1 z-70 lang-menu text-slate-800 dark:text-slate-100 animate-in fade-in zoom-in-95 duration-150">
                <div className="px-3 py-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800">
                  Voice Language
                </div>
                {LANGUAGES.map((l) => (
                  <button
                    key={l.code}
                    type="button"
                    onClick={() => {
                      setLanguage(l.code);
                      setShowLangMenu(false);
                    }}
                    className={`w-full px-3 py-2 text-left text-xs flex items-center justify-between gap-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer ${
                      language === l.code ? 'font-bold text-sky-600 dark:text-sky-400 bg-sky-50 dark:bg-sky-950/40' : ''
                    }`}
                  >
                    <span>{l.native} ({l.label})</span>
                    {language === l.code && <CheckCircle2 className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Voice AutoPlay Toggle */}
          <button
            type="button"
            onClick={() => setAutoPlayVoice((prev) => !prev)}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              autoPlayVoice ? 'text-emerald-400 hover:text-emerald-300 bg-emerald-950/40' : 'text-slate-400 hover:text-slate-200'
            }`}
            title={autoPlayVoice ? 'Auto-play voice responses: ON (Click to Mute)' : 'Auto-play voice responses: MUTED (Click to Enable)'}
            aria-label="Toggle Voice AutoPlay"
          >
            {autoPlayVoice ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
          </button>

          {/* Wake on 'Mira' Voice Activation Toggle (Always Visible) */}
          <button
            type="button"
            onClick={toggleWakeWord}
            className={`p-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1 ${
              isWakeWordEnabled
                ? 'text-purple-300 hover:text-purple-200 bg-purple-950/60 ring-1 ring-purple-400/40'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/10'
            }`}
            title={
              isWakeWordEnabled
                ? "Wake on 'Mira': ACTIVE (Listening in background - Click to Disable)"
                : "Wake on 'Mira': OFF (Click to Enable voice activation)"
            }
            aria-label="Toggle 'Mira' Wake Word"
          >
            <Mic className={`w-3.5 h-3.5 ${isWakeWordListening ? 'text-purple-300 animate-pulse' : ''}`} />
          </button>

          {/* Theme Switcher Button */}
          <div className="relative" ref={themeMenuRef}>
            <button
              type="button"
              onClick={() => setShowThemeMenu((prev) => !prev)}
              className={`p-1.5 rounded-lg transition-colors cursor-pointer ${currentTheme.headerBtn}`}
              title="Change Chat Color Scheme"
              aria-label="Change Color Theme"
            >
              <Palette className="w-3.5 h-3.5" />
            </button>

            {showThemeMenu && (
              <div className="absolute right-0 mt-1.5 w-44 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl py-1 z-70 theme-menu text-slate-800 dark:text-slate-100 animate-in fade-in zoom-in-95 duration-150">
                <div className="px-3 py-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800">
                  Color Scheme
                </div>
                {Object.values(CHAT_THEMES).map((thm) => (
                  <button
                    key={thm.id}
                    type="button"
                    onClick={() => {
                      selectTheme(thm.id);
                      setShowThemeMenu(false);
                    }}
                    className={`w-full px-3 py-2 text-left text-xs flex items-center justify-between gap-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer ${
                      chatTheme === thm.id ? 'font-bold text-sky-600 dark:text-sky-400 bg-sky-50 dark:bg-sky-950/40' : ''
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2.5 h-2.5 rounded-full ${
                          thm.id === 'sovereign'
                            ? 'bg-gradient-to-r from-sky-600 to-indigo-700'
                            : thm.id === 'midnight'
                            ? 'bg-[#071d2e] border border-cyan-400'
                            : 'bg-emerald-500'
                        }`}
                      />
                      <span>{thm.name}</span>
                    </div>
                    {chatTheme === thm.id && <CheckCircle2 className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Clear chat button */}
          <button
            type="button"
            onClick={clearChat}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${currentTheme.headerBtn}`}
            title="Reset Conversation"
            aria-label="Reset Conversation"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Minimize Button */}
          <button
            type="button"
            onClick={minimizeChat}
            className={`p-1.5 rounded-lg transition-all cursor-pointer shadow-xs ${currentTheme.headerMinimizeBtn}`}
            title="Minimize to Navigation Bar (Alt + Space)"
            aria-label="Minimize Chatbot"
          >
            <Minus className="w-3.5 h-3.5 stroke-[2.5]" />
          </button>
        </div>
      </div>

      {/* Active Tab Screen Awareness Sub-Header */}
      <div
        className={`px-3.5 py-1.5 text-[10px] flex items-center justify-between border-b opacity-90 transition-colors ${
          chatTheme === 'midnight'
            ? 'bg-[#061826] border-sky-900/60 text-cyan-300'
            : chatTheme === 'emerald'
            ? 'bg-emerald-50/80 border-emerald-100 text-emerald-800'
            : 'bg-sky-50/80 border-sky-100 text-sovereign-900'
        }`}
      >
        <div className="flex items-center gap-1.5 truncate">
          <span>{icon}</span>
          <span className="font-semibold truncate">Active Viewport: {tabTitle}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-white/60 border border-slate-200 text-slate-700">
            {currentLangObj.native}
          </span>
          <button
            type="button"
            onClick={() => sendMessage(`Please summarize this ${tabTitle} page for me in detail.`)}
            className="font-bold underline text-[9px] hover:opacity-80 cursor-pointer"
          >
            Summarize Screen
          </button>
        </div>
      </div>

      {/* Mira Voice Trigger Live Banner */}
      {siriNotice && (
        <div className="mx-3.5 mt-2 px-3 py-2 rounded-xl bg-gradient-to-r from-purple-950/95 via-indigo-950/95 to-slate-950/95 border border-purple-400/50 text-white shadow-lg flex items-center justify-between gap-2 animate-in fade-in slide-in-from-top-2 duration-200 shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <span className="relative flex h-2.5 w-2.5 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-purple-500" />
            </span>
            <div className="min-w-0">
              <p className="text-[11px] font-bold text-purple-200 flex items-center gap-1.5">
                <img src="/mira-avatar.png" alt="Mira" className="w-4 h-4 rounded-full object-cover object-top ring-1 ring-purple-300/60" />
                <span>🎙️ &ldquo;Mira&rdquo; Activated</span>
              </p>
              {siriNotice.trailingQuery ? (
                <p className="text-[10px] text-purple-300/90 truncate font-mono">
                  "{siriNotice.trailingQuery}"
                </p>
              ) : (
                <p className="text-[10px] text-purple-300/80">
                  Listening for your query...
                </p>
              )}
            </div>
          </div>
          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-purple-500/30 text-purple-200 border border-purple-400/40 uppercase shrink-0">
            Voice Sync
          </span>
        </div>
      )}

      {/* Message List */}
      <div
        className={`flex-1 overflow-y-auto px-4 py-3 space-y-3.5 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-700 scrollbar-track-transparent ${currentTheme.bodyBg}`}
      >
        {messages.map((m) => {
          const isUser = m.role === 'user';
          const isPlaying = playingAudioId === m.id;
          const isTtsLoading = ttsLoadingId === m.id;

          return (
            <div
              key={m.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} group`}
            >
              <div
                className={`max-w-[88%] px-3.5 py-2.5 rounded-2xl text-xs shadow-xs transition-all ${
                  isUser
                    ? `${currentTheme.userBubble} rounded-br-xs`
                    : m.isError
                    ? 'bg-rose-50 border border-rose-200 text-rose-800 rounded-bl-xs'
                    : `${currentTheme.assistantBubble} rounded-bl-xs`
                }`}
              >
                {isUser ? (
                  <div className="space-y-1">
                    {m.isVoice && (
                      <div className="flex items-center gap-1 text-[10px] text-sky-200 font-bold mb-0.5">
                        <Mic className="w-3 h-3 text-sky-300 animate-pulse" />
                        <span>Voice Query</span>
                      </div>
                    )}
                    <p className={`whitespace-pre-wrap leading-relaxed ${currentTheme.userText}`}>{m.content}</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <ChatMarkdown content={m.content} sources={m.sources} />

                    {/* Spoken Voice Audio Player Pill for Assistant Responses */}
                    <div className="pt-1.5 border-t border-slate-100 dark:border-slate-700/60 flex items-center justify-between gap-2">
                      <button
                        type="button"
                        onClick={() => playMessageTts(m.id, m.content, m.audio_base64)}
                        disabled={isTtsLoading}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold transition-all cursor-pointer ${
                          isPlaying
                            ? 'bg-emerald-500 text-white shadow-xs animate-pulse'
                            : isTtsLoading
                            ? 'bg-slate-100 text-slate-500'
                            : 'bg-slate-100 hover:bg-sky-100 text-slate-700 hover:text-sky-800 dark:bg-slate-800 dark:text-slate-300'
                        }`}
                      >
                        {isTtsLoading ? (
                          <>
                            <Loader2 className="w-3 h-3 animate-spin" />
                            <span>Generating Voice...</span>
                          </>
                        ) : isPlaying ? (
                          <>
                            <Pause className="w-3 h-3 fill-current" />
                            <span>Playing Audio in {currentLangObj.native}...</span>
                          </>
                        ) : (
                          <>
                            <Play className="w-3 h-3 fill-current" />
                            <span>Listen ({currentLangObj.native})</span>
                          </>
                        )}
                      </button>

                      {/* Latency telemetry breakdown if voice turn */}
                      {m.latencies && (
                        <span className="text-[9px] font-mono text-slate-400" title={`STT: ${m.latencies.stt_s}s | LLM: ${m.latencies.llm_s}s | TTS: ${m.latencies.tts_s}s`}>
                          ⚡ {m.latencies.total_s}s total
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Message Footer Meta (Time & Model Pill & Copy) */}
              <div className={`flex items-center gap-2 mt-1 px-1 text-[10px] ${currentTheme.metaText}`}>
                <span>
                  {new Date(m.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
                {!isUser && (
                  <>
                    <span>•</span>
                    <span className={`text-[9px] ${currentTheme.metaPill}`}>
                      {m.isFallback ? 'Deterministic Advisor' : 'Groq AI'}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleCopy(m.id, m.content)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer p-0.5"
                      title="Copy response text"
                    >
                      {copiedId === m.id ? (
                        <Check className="w-3 h-3 text-emerald-500" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-start gap-2">
            <div className={`px-3.5 py-2.5 rounded-2xl rounded-bl-xs text-xs flex items-center gap-2 ${currentTheme.loadingBg}`}>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-500 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-sky-600" />
              </span>
              <span className={`text-[11px] font-medium ${currentTheme.loadingText}`}>
                Analyzing in {currentLangObj.label} ({currentLangObj.native})...
              </span>
            </div>
          </div>
        )}

        {/* Context-Aware Quick Suggestion Chips */}
        {messages.length <= 2 && !isLoading && !isRecording && (
          <div className="pt-2">
            <p className={`text-[10px] font-bold uppercase tracking-wider mb-2 flex items-center gap-1 ${currentTheme.chipHeader}`}>
              <Sparkles className="w-3 h-3 text-sky-500" /> Quick Inquiries for {tabTitle.split(' ')[0]}
            </p>
            <div className="grid grid-cols-1 gap-1.5">
              {quickPrompts.map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => sendMessage(q)}
                  className={`text-left text-[11px] px-3 py-1.5 rounded-xl transition-all cursor-pointer truncate flex items-center justify-between group ${currentTheme.chipBtn}`}
                >
                  <span className="truncate">⚡ {q}</span>
                  <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-1" />
                </button>
              ))}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Dynamic Voice Recording HUD Drawer (When Recording via Mic) */}
      {isRecording && (
        <div className="p-4 bg-gradient-to-r from-rose-950/90 via-slate-900/95 to-sovereign-950/95 border-t border-rose-500/40 text-white flex flex-col gap-3 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500" />
              </span>
              <span className="text-xs font-bold text-rose-200">
                Listening in {currentLangObj.label} ({currentLangObj.native})...
              </span>
            </div>
            <span className="font-mono font-bold text-xs text-rose-300">
              00:{duration < 10 ? `0${duration}` : duration}
            </span>
          </div>

          {/* Real-time Dynamic Waveform Bars */}
          <div className="flex items-center justify-center gap-1.5 h-8 py-1 bg-black/40 rounded-xl px-4 border border-rose-500/20">
            {barMultipliers.map((mult, i) => {
              const heightPct = Math.min(100, Math.max(15, (volume * mult * 350)));
              return (
                <div
                  key={i}
                  className="w-1.5 bg-gradient-to-t from-rose-500 to-amber-300 rounded-full transition-all duration-75"
                  style={{ height: `${heightPct}%` }}
                />
              );
            })}
          </div>

          <p className="text-[10px] text-center text-slate-300">
            {isSpeaking ? (
              <span className="text-emerald-400 font-bold">🗣️ Speech Detected... Will auto-send when you pause.</span>
            ) : (
              <span>Speak clearly into your microphone (auto-stops when finished)</span>
            )}
          </p>

          <div className="flex items-center justify-center gap-3 pt-1">
            <button
              type="button"
              onClick={cancelRecording}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={stopRecording}
              className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-rose-600 to-emerald-600 hover:from-rose-500 hover:to-emerald-500 text-white text-xs font-bold shadow-md shadow-rose-950/50 flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <Square className="w-3 h-3 fill-current" />
              <span>Done Speaking</span>
            </button>
          </div>
        </div>
      )}

      {/* Input Area */}
      {!isRecording && (
        <form
          onSubmit={handleSubmit}
          className={`p-3 flex flex-col gap-2 shrink-0 ${currentTheme.inputFooter}`}
        >
          <div className="relative flex items-center gap-1.5">
            <textarea
              ref={chatInputRef}
              rows={1}
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder={`Ask in ${currentLangObj.native} or click Mic to speak...`}
              className={`w-full text-xs rounded-xl pl-3 pr-20 py-2.5 resize-none outline-none transition-all disabled:opacity-50 border ${currentTheme.textarea}`}
              style={{ maxHeight: '90px' }}
            />

            {/* Action Buttons: Microphone (Voice Mode) + Send */}
            <div className="absolute right-1.5 flex items-center gap-1">
              {/* Dynamic Mic Voice Button */}
              <button
                type="button"
                onClick={startRecording}
                disabled={isLoading}
                className="p-2 rounded-lg bg-sky-100 hover:bg-sky-200 text-sky-800 dark:bg-sky-950/60 dark:hover:bg-sky-900 dark:text-sky-300 transition-all cursor-pointer"
                title={`Speak in ${currentLangObj.label} (${currentLangObj.native})`}
                aria-label="Start Voice Recording"
              >
                <Mic className="w-3.5 h-3.5" />
              </button>

              {/* Text Send Button */}
              <button
                type="submit"
                disabled={!inputVal.trim() || isLoading}
                className={`p-2 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer ${currentTheme.sendBtn}`}
                title="Send Message (Enter)"
                aria-label="Send Message"
              >
                <SendHorizontal className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Footer Subtext */}
          <div className={`flex items-center justify-between text-[9px] px-1 ${currentTheme.subText}`}>
            <span className="flex items-center gap-1">
              <span>Sarvam LLM + Bhashini Voice</span>
              <span>•</span>
              <span className="font-bold text-sky-600 dark:text-sky-400">{currentLangObj.native}</span>
            </span>
            <span className={`font-mono px-1.5 py-0.5 rounded border text-[9px] ${currentTheme.subBadge}`}>
              Alt + Space
            </span>
          </div>
        </form>
      )}
    </div>
  );
}
export default FloatingChatWindow;
