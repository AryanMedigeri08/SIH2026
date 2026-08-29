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
} from 'lucide-react';
import { useChat, CHAT_THEMES } from '../../context/ChatContext';
import { useBusiness } from '../../context/BusinessContext';
import { useLanguage } from '../../context/LanguageContext';
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
    selectTheme,
    cycleTheme,
    getActiveTabTelemetry,
    navButtonRef,
    chatInputRef,
    minimizeChat,
    sendMessage,
    clearChat,
  } = useChat();

  const { reportData, activeBusiness } = useBusiness();
  const { t } = useLanguage();

  const [inputVal, setInputVal] = useState('');
  const [copiedId, setCopiedId] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showThemeMenu, setShowThemeMenu] = useState(false);
  const dragStartRef = useRef({ mouseX: 0, mouseY: 0, posX: 0, posY: 0 });
  const messagesEndRef = useRef(null);
  const windowRef = useRef(null);
  const themeMenuRef = useRef(null);

  const { tabTitle, icon, quickPrompts } = getActiveTabTelemetry();

  // Close theme menu on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (themeMenuRef.current && !themeMenuRef.current.contains(e.target)) {
        setShowThemeMenu(false);
      }
    };
    if (showThemeMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showThemeMenu]);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

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

  // Dragging logic from window header
  const handlePointerDown = (e) => {
    // Only drag when clicking header or drag-grip area
    if (e.target.closest('button') || e.target.closest('input') || e.target.closest('textarea') || e.target.closest('.theme-menu')) {
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

  // Submit User Message
  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!inputVal.trim() || isLoading) return;
    sendMessage(inputVal);
    setInputVal('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Copy assistant response
  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Don't render if closed and not animating
  if (!isChatOpen && !isAnimating) {
    return null;
  }

  const { dx, dy } = getTransformOriginDelta();

  // Animation styles based on animState
  let animStyles = {
    opacity: 1,
    transform: 'translate(0px, 0px) scale(1)',
    transition: 'all 260ms cubic-bezier(0.16, 1, 0.3, 1)',
  };

  if (animState === 'minimizing') {
    animStyles = {
      opacity: 0,
      transform: `translate(${dx}px, ${dy}px) scale(0.05)`,
      transition: 'all 260ms cubic-bezier(0.4, 0, 0.2, 1)',
      pointerEvents: 'none',
    };
  } else if (animState === 'opening') {
    animStyles = {
      opacity: 1,
      transform: 'translate(0px, 0px) scale(1)',
      transition: 'all 280ms cubic-bezier(0.16, 1, 0.3, 1)',
    };
  }

  const activeEntTitle =
    reportData?.enterprise_name ||
    reportData?.input_parameters?.enterprise_name ||
    activeBusiness?.name ||
    'Micro Enterprise';

  const activeEntCost =
    reportData?.financial_summary?.project_cost ||
    reportData?.input_parameters?.project_cost ||
    activeBusiness?.project_cost;

  return (
    <div
      ref={windowRef}
      style={{
        position: 'fixed',
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: `${size.width}px`,
        height: `${size.height}px`,
        zIndex: 60,
        ...animStyles,
      }}
      className={`flex flex-col rounded-2xl overflow-hidden font-sans select-text border transition-colors duration-200 ${currentTheme.windowBg}`}
      role="dialog"
      aria-label="AI Chatbot Advisor Window"
    >
      {/* Sovereign Top Gradient Accent Bar */}
      <div className={`h-[3px] w-full shrink-0 ${currentTheme.topBar}`} />

      {/* Draggable Desktop Header */}
      <div
        onMouseDown={handlePointerDown}
        onTouchStart={handlePointerDown}
        className={`px-4 py-3 flex items-center justify-between gap-2 select-none cursor-grab transition-colors relative ${currentTheme.headerBg} ${
          isDragging ? 'cursor-grabbing opacity-95' : ''
        }`}
      >
        {/* Left: Avatar & Title */}
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-sky-950/30 border border-sky-300/30 shrink-0">
            <Bot className="w-4 h-4 text-sky-100" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <h3 className={`font-outfit font-bold text-xs tracking-tight truncate ${currentTheme.headerTitle}`}>
                Udyam AI Assistant
              </h3>
              <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded-full ${currentTheme.headerBadge}`}>
                Groq
              </span>
            </div>
            <p className={`text-[10px] truncate flex items-center gap-1 ${currentTheme.headerSubtitle}`}>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse" />
              {activeEntTitle} {activeEntCost ? `• ₹${(activeEntCost / 100000).toFixed(1)}L` : ''}
            </p>
          </div>
        </div>

        {/* Right: Window Controls & Theme Switcher */}
        <div className="flex items-center gap-1 shrink-0">
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

            {/* Theme Selection Popover Menu */}
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

          {/* Minimize Button (Mandatory) */}
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
      <div className={`px-3.5 py-1.5 text-[10px] flex items-center justify-between border-b opacity-90 transition-colors ${
        chatTheme === 'midnight'
          ? 'bg-[#061826] border-sky-900/60 text-cyan-300'
          : chatTheme === 'emerald'
          ? 'bg-emerald-50/80 border-emerald-100 text-emerald-800'
          : 'bg-sky-50/80 border-sky-100 text-sovereign-900'
      }`}>
        <div className="flex items-center gap-1.5 truncate">
          <span>{icon}</span>
          <span className="font-semibold truncate">Active Viewport: {tabTitle}</span>
        </div>
        <button
          type="button"
          onClick={() => sendMessage(`Please summarize this ${tabTitle} page for me in detail.`)}
          className="font-bold underline text-[9px] hover:opacity-80 cursor-pointer shrink-0 ml-2"
        >
          Summarize Screen
        </button>
      </div>

      {/* Message List */}
      <div className={`flex-1 overflow-y-auto px-4 py-3 space-y-3.5 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-700 scrollbar-track-transparent ${currentTheme.bodyBg}`}>
        {messages.map((m) => {
          const isUser = m.role === 'user';
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
                  <p className={`whitespace-pre-wrap leading-relaxed ${currentTheme.userText}`}>{m.content}</p>
                ) : (
                  <ChatMarkdown content={m.content} sources={m.sources} />
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
                Analyzing {tabTitle} telemetry...
              </span>
            </div>
          </div>
        )}

        {/* Context-Aware Quick Suggestion Chips (Dynamically tailored to the active tab screen!) */}
        {messages.length <= 2 && !isLoading && (
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

      {/* Input Area */}
      <form
        onSubmit={handleSubmit}
        className={`p-3 flex flex-col gap-2 shrink-0 ${currentTheme.inputFooter}`}
      >
        <div className="relative flex items-center">
          <textarea
            ref={chatInputRef}
            rows={1}
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder={`Ask about ${tabTitle} or type 'Summarize page'...`}
            className={`w-full text-xs rounded-xl pl-3 pr-10 py-2.5 resize-none outline-none transition-all disabled:opacity-50 border ${currentTheme.textarea}`}
            style={{ maxHeight: '90px' }}
          />

          <button
            type="submit"
            disabled={!inputVal.trim() || isLoading}
            className={`absolute right-1.5 p-2 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer ${currentTheme.sendBtn}`}
            title="Send Message (Enter)"
            aria-label="Send Message"
          >
            <SendHorizontal className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Footer Subtext */}
        <div className={`flex items-center justify-between text-[9px] px-1 ${currentTheme.subText}`}>
          <span>Powered by Groq Cloud • {currentTheme.name}</span>
          <span className={`font-mono px-1.5 py-0.5 rounded border text-[9px] ${currentTheme.subBadge}`}>
            Alt + Space
          </span>
        </div>
      </form>
    </div>
  );
}
