import React from 'react';
import { Bot, Sparkles, MessageSquareCode } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useLanguage } from '../../context/LanguageContext';

export function ChatbotNavButton() {
  const { isChatOpen, toggleChat, navButtonRef } = useChat();
  const { t } = useLanguage();

  return (
    <button
      ref={navButtonRef}
      type="button"
      onClick={toggleChat}
      className={`relative inline-flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full border transition-all duration-200 cursor-pointer shadow-subtle group ${
        isChatOpen
          ? 'bg-gradient-to-r from-sovereign-900 to-indigo-900 text-cyan-300 border-cyan-500/60 shadow-md shadow-cyan-900/20 ring-2 ring-cyan-500/30'
          : 'bg-white/90 text-slate-700 border-slate-200/90 hover:bg-slate-50 hover:text-sovereign-900 hover:border-slate-300'
      }`}
      title="AI Chatbot Advisor (Shortcut: Alt + Space)"
      aria-label="Toggle AI Chatbot Assistant"
      aria-expanded={isChatOpen}
    >
      {/* Bot Icon with active glowing beacon */}
      <span className="relative flex items-center justify-center">
        {isChatOpen && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-60" />
        )}
        <Bot
          className={`w-3.5 h-3.5 transition-transform group-hover:scale-110 ${
            isChatOpen ? 'text-cyan-300' : 'text-sky-600'
          }`}
        />
      </span>

      {/* Label */}
      <span className="font-semibold tracking-tight">
        {t('chatbot') || 'Chatbot'}
      </span>

      {/* Subtle AI Badge / Sparkle */}
      <span
        className={`text-[9px] font-extrabold px-1.5 py-0.2 rounded-full uppercase tracking-wider ${
          isChatOpen
            ? 'bg-cyan-400/20 text-cyan-200 border border-cyan-400/40'
            : 'bg-sky-50 text-sky-700 border border-sky-200'
        }`}
      >
        AI
      </span>
    </button>
  );
}
