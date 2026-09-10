import React from 'react';
import { Bot, Sparkles, MessageSquareCode } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useLanguage } from '../../context/LanguageContext';

export function ChatbotNavButton() {
  const { isChatOpen, toggleChat, navButtonRef, currentTheme } = useChat();
  const { t } = useLanguage();

  const isEmerald = currentTheme?.id === 'emerald';
  const isMidnight = currentTheme?.id === 'midnight';

  return (
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

      {/* Label */}
      <span className="font-semibold tracking-tight whitespace-nowrap">
        {t('chatbot') || 'Chatbot'}
      </span>

      {/* Subtle AI Badge / Sparkle */}
      <span
        className={`text-[9px] font-extrabold px-1.5 py-0.2 rounded-full uppercase tracking-wider shrink-0 ${
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
  );
}
