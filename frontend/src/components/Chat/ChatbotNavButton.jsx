import React, { useEffect } from 'react';
import { Bot, Sparkles, Zap } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useLanguage } from '../../context/LanguageContext';

export function ChatbotNavButton() {
  const {
    isChatOpen,
    toggleChat,
    navButtonRef,
    currentTheme,
    voiceAgentState,
    startVoiceConversation,
    endVoiceConversation,
    siriToggleRef,
  } = useChat();
  const { t } = useLanguage();

  const isEmerald = currentTheme?.id === 'emerald';
  const isMidnight = currentTheme?.id === 'midnight';
  const isMiraActive = voiceAgentState && voiceAgentState !== 'IDLE';

  // Toggle Mira on/off
  const handleMiraToggle = (e) => {
    e.stopPropagation();
    if (isMiraActive) {
      endVoiceConversation();
    } else {
      startVoiceConversation();
    }
  };

  // Global Keyboard Shortcut: Alt + M → Toggle Mira
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.altKey && (e.key === 'm' || e.key === 'M' || e.code === 'KeyM')) {
        e.preventDefault();
        e.stopPropagation();
        if (isMiraActive) {
          endVoiceConversation();
        } else {
          startVoiceConversation();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown, true);
    return () => window.removeEventListener('keydown', handleKeyDown, true);
  }, [isMiraActive, startVoiceConversation, endVoiceConversation]);

  return (
    <div className="inline-flex items-center gap-1.5 shrink-0">
      {/* Chatbot Button */}
      <button
        ref={navButtonRef}
        type="button"
        onClick={toggleChat}
        className={`relative inline-flex items-center gap-1.5 sm:gap-2 text-xs font-semibold px-2.5 sm:px-3 py-1.5 rounded-full border transition-all duration-200 cursor-pointer shadow-subtle group shrink-0 ${
          isChatOpen
            ? isEmerald
              ? 'bg-gradient-to-r from-emerald-950 via-teal-900 to-slate-950 text-emerald-200 border-emerald-400/60 shadow-md shadow-emerald-950/20 ring-2 ring-emerald-400/30'
              : isMidnight
              ? 'bg-[#020b12] text-cyan-300 border-cyan-500/60 shadow-md shadow-cyan-950/40 ring-2 ring-cyan-500/30'
              : 'bg-gradient-to-r from-sovereign-950 via-sovereign-900 to-indigo-950 text-sky-200 border-sky-400/60 shadow-md shadow-sovereign-900/20 ring-2 ring-sky-400/30'
            : 'bg-white/90 text-slate-700 border-slate-200/90 hover:bg-slate-50 hover:text-sovereign-900 hover:border-slate-300'
        }`}
        title="AI Chatbot Advisor (Shortcut: Alt + Space)"
        aria-label="Toggle AI Chatbot Assistant"
        aria-expanded={isChatOpen}
      >
        {/* Bot Icon with active glowing beacon */}
        <span className="relative flex items-center justify-center shrink-0">
          {isChatOpen && (
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-60 ${
                isEmerald ? 'bg-emerald-400' : isMidnight ? 'bg-cyan-400' : 'bg-sky-400'
              }`}
            />
          )}
          <Bot
            className={`w-3.5 h-3.5 transition-transform group-hover:scale-110 ${
              isChatOpen
                ? isEmerald
                  ? 'text-emerald-300'
                  : isMidnight
                  ? 'text-cyan-300'
                  : 'text-sky-300'
                : 'text-sky-600'
            }`}
          />
        </span>

        {/* Label — hidden on small mobile to save horizontal space */}
        <span className="hidden sm:inline font-semibold tracking-tight whitespace-nowrap">
          {t('chatbot') || 'Chatbot'}
        </span>

        {/* Subtle AI Badge / Sparkle — hidden on xs */}
        <span
          className={`hidden sm:inline text-[9px] font-extrabold px-1.5 py-0.2 rounded-full uppercase tracking-wider shrink-0 ${
            isChatOpen
              ? isEmerald
                ? 'bg-emerald-500/20 text-emerald-200 border border-emerald-400/40'
                : isMidnight
                ? 'bg-cyan-400/20 text-cyan-200 border border-cyan-400/40'
                : 'bg-sky-400/20 text-sky-200 border border-sky-400/40'
              : 'bg-sky-50 text-sky-700 border border-sky-200'
          }`}
        >
          AI
        </span>
      </button>

      {/* ─── Dedicated MIRA Voice Agent Button ─── */}
      <button
        ref={siriToggleRef}
        type="button"
        onClick={handleMiraToggle}
        className={`relative inline-flex items-center gap-1.5 text-xs font-bold px-2.5 sm:px-3 py-1.5 rounded-full border-2 transition-all duration-300 cursor-pointer shrink-0 ${
          isMiraActive
            ? 'bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 text-white border-purple-400/60 shadow-lg shadow-purple-900/40 ring-2 ring-purple-400/30 scale-105'
            : 'bg-white/90 text-purple-700 border-purple-200/80 hover:bg-purple-50 hover:border-purple-400 hover:shadow-md hover:shadow-purple-100 shadow-sm'
        }`}
        title={
          isMiraActive
            ? '🎙️ Mira is active — click to stop (Alt+M)'
            : '🎙️ Activate Mira Voice Assistant (Alt+M)'
        }
        aria-label="Toggle Mira Voice Assistant"
        aria-pressed={isMiraActive}
      >
        {/* Active pulsing ring */}
        {isMiraActive && (
          <span className="animate-ping absolute inset-0 rounded-full bg-purple-400 opacity-25" />
        )}

        {/* Mira icon — sparkle/zap */}
        <span className="relative flex items-center justify-center shrink-0">
          {isMiraActive ? (
            <Sparkles className="w-3.5 h-3.5 text-white drop-shadow-sm animate-pulse" />
          ) : (
            <Sparkles className="w-3.5 h-3.5 text-purple-500 group-hover:text-purple-600 transition-colors" />
          )}
        </span>

        {/* MIRA label */}
        <span className="font-extrabold tracking-wide whitespace-nowrap">
          MIRA
        </span>

        {/* Keyboard shortcut badge — hidden on mobile */}
        <span
          className={`hidden sm:inline text-[8px] font-mono px-1 py-0.5 rounded ${
            isMiraActive
              ? 'bg-white/20 text-white/80'
              : 'bg-purple-50 text-purple-400 border border-purple-200/60'
          }`}
        >
          Alt+M
        </span>

        {/* Active indicator dot */}
        {isMiraActive && (
          <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-green-400 border-2 border-white shadow-sm">
            <span className="absolute inset-0 rounded-full bg-green-400 animate-ping opacity-75" />
          </span>
        )}
      </button>
    </div>
  );
}
