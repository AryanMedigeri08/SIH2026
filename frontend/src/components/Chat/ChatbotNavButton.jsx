import React from 'react';
import { Bot, Sparkles, MessageSquareCode, Mic } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useLanguage } from '../../context/LanguageContext';
import { initSiriAudio } from '../../utils/siriAudio';

export function ChatbotNavButton() {
  const {
    isChatOpen,
    toggleChat,
    navButtonRef,
    currentTheme,
    isWakeWordSupported,
    isWakeWordEnabled,
    isWakeWordListening,
    wakeWordEngine,
    toggleWakeWord,
    siriToggleRef,
  } = useChat();
  const { t } = useLanguage();

  const isEmerald = currentTheme?.id === 'emerald';
  const isMidnight = currentTheme?.id === 'midnight';

  return (
    <div className="inline-flex items-center gap-1.5 shrink-0">
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

      {/* Voice Wake Word "Mira" — Small Circular Toggle */}
      <button
        ref={siriToggleRef}
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          initSiriAudio();
          toggleWakeWord();
        }}
        className={`relative flex items-center justify-center w-8 h-8 rounded-full border-2 transition-all duration-300 cursor-pointer shrink-0 ${
          isWakeWordEnabled
            ? 'bg-gradient-to-br from-purple-600 via-indigo-600 to-cyan-500 border-purple-400/60 shadow-lg shadow-purple-900/30 ring-2 ring-purple-400/25'
            : 'bg-white hover:bg-purple-50 border-slate-200 hover:border-purple-300 shadow-sm'
        }`}
        title={
          isWakeWordEnabled
            ? `🎙️ "Mira" is LISTENING in background [Backend Sarvam + Bhashini ASR]. Speak "Mira" anytime to activate! (Click to mute)`
            : '🎙️ Click to enable "Mira" voice activation'
        }
        aria-label="Toggle 'Mira' Voice Activation"
        aria-pressed={isWakeWordEnabled}
      >
        {/* Active listening ping ring */}
        {isWakeWordListening && (
          <span className="animate-ping absolute inline-flex w-full h-full rounded-full bg-purple-400 opacity-40" />
        )}
        <Mic
          className={`w-3.5 h-3.5 transition-all ${
            isWakeWordEnabled
              ? 'text-white drop-shadow-sm'
              : 'text-slate-400 hover:text-purple-600'
          }`}
        />
        {/* Tiny active dot indicator */}
        {isWakeWordEnabled && (
          <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-green-400 border border-white shadow-sm">
            <span className="absolute inset-0 rounded-full bg-green-400 animate-ping opacity-75" />
          </span>
        )}
      </button>
    </div>
  );
}

