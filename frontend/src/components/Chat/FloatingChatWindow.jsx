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
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';
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
  const dragStartRef = useRef({ mouseX: 0, mouseY: 0, posX: 0, posY: 0 });
  const messagesEndRef = useRef(null);
  const windowRef = useRef(null);

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
    if (e.target.closest('button') || e.target.closest('input') || e.target.closest('textarea')) {
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

  const quickPrompts = [
    'What is my DSCR ratio and is my bank loan safe?',
    'How much subsidy can I get under PMEGP or Mudra?',
    'Explain the break-even pricing floor calculation.',
    'What statutory documents are required for my bank DPR?',
  ];

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
      className="flex flex-col bg-slate-900/95 backdrop-blur-2xl border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden font-sans text-slate-100 ring-1 ring-white/10 select-text"
      role="dialog"
      aria-label="AI Chatbot Advisor Window"
    >
      {/* Sovereign Top Gradient Bar */}
      <div className="h-[3px] w-full bg-gradient-to-r from-cyan-500 via-sky-400 to-indigo-500 shrink-0" />

      {/* Draggable Desktop Header */}
      <div
        onMouseDown={handlePointerDown}
        onTouchStart={handlePointerDown}
        className={`px-4 py-3 bg-slate-950/80 border-b border-slate-800/80 flex items-center justify-between gap-2 select-none cursor-grab ${
          isDragging ? 'cursor-grabbing bg-slate-900' : ''
        }`}
      >
        {/* Left: Avatar & Title */}
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-cyan-900/40 border border-cyan-400/30 shrink-0">
            <Bot className="w-4 h-4 text-cyan-200" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <h3 className="font-outfit font-bold text-xs text-white tracking-tight truncate">
                Udyam AI Assistant
              </h3>
              <span className="text-[9px] font-bold text-cyan-400 bg-cyan-950/60 border border-cyan-800 px-1.5 py-0.2 rounded-full">
                Groq
              </span>
            </div>
            <p className="text-[10px] text-slate-400 truncate flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse" />
              {activeEntTitle} {activeEntCost ? `• ₹${(activeEntCost / 100000).toFixed(1)}L` : ''}
            </p>
          </div>
        </div>

        {/* Right: Window Controls */}
        <div className="flex items-center gap-1 shrink-0">
          {/* Clear chat button */}
          <button
            type="button"
            onClick={clearChat}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 rounded-lg transition-colors cursor-pointer"
            title="Reset Conversation"
            aria-label="Reset Conversation"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Minimize Button (Mandatory) */}
          <button
            type="button"
            onClick={minimizeChat}
            className="p-1.5 text-cyan-400 hover:text-white hover:bg-cyan-900/50 rounded-lg transition-all border border-cyan-800/50 hover:border-cyan-600 cursor-pointer shadow-xs"
            title="Minimize to Navigation Bar (Alt + Space)"
            aria-label="Minimize Chatbot"
          >
            <Minus className="w-3.5 h-3.5 stroke-[2.5]" />
          </button>
        </div>
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3.5 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        {messages.map((m) => {
          const isUser = m.role === 'user';
          return (
            <div
              key={m.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} group`}
            >
              <div
                className={`max-w-[88%] px-3.5 py-2.5 rounded-2xl text-xs shadow-md transition-all ${
                  isUser
                    ? 'bg-gradient-to-r from-sovereign-900 via-sky-800 to-indigo-900 text-white rounded-br-xs border border-sky-500/30'
                    : m.isError
                    ? 'bg-rose-950/80 border border-rose-800 text-rose-200 rounded-bl-xs'
                    : 'bg-slate-800/90 border border-slate-700/80 text-slate-100 rounded-bl-xs'
                }`}
              >
                {isUser ? (
                  <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                ) : (
                  <ChatMarkdown content={m.content} />
                )}
              </div>

              {/* Message Footer Meta (Time & Model Pill & Copy) */}
              <div className="flex items-center gap-2 mt-1 px-1 text-[10px] text-slate-400">
                <span>
                  {new Date(m.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
                {!isUser && (
                  <>
                    <span>•</span>
                    <span className="text-[9px] text-cyan-400/80">
                      {m.isFallback ? 'Deterministic Advisor' : 'Groq AI'}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleCopy(m.id, m.content)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity hover:text-slate-200 cursor-pointer p-0.5"
                      title="Copy response text"
                    >
                      {copiedId === m.id ? (
                        <Check className="w-3 h-3 text-emerald-400" />
                      ) : (
                        <Copy className="w-3 h-3 text-slate-400" />
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
            <div className="bg-slate-800/90 border border-slate-700/80 px-3.5 py-2.5 rounded-2xl rounded-bl-xs text-xs text-cyan-300 flex items-center gap-2 shadow-md">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
              </span>
              <span className="text-[11px] font-medium text-slate-300">Analyzing enterprise telemetry...</span>
            </div>
          </div>
        )}

        {/* Quick Suggestion Chips (when only 1 or 2 messages exist) */}
        {messages.length <= 2 && !isLoading && (
          <div className="pt-2">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-cyan-400" /> Quick Inquiries
            </p>
            <div className="grid grid-cols-1 gap-1.5">
              {quickPrompts.map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => sendMessage(q)}
                  className="text-left text-[11px] text-slate-300 bg-slate-800/50 hover:bg-slate-800 hover:text-cyan-200 border border-slate-700/60 hover:border-cyan-500/50 px-3 py-1.5 rounded-xl transition-all shadow-xs cursor-pointer truncate"
                >
                  ⚡ {q}
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
        className="p-3 bg-slate-950/90 border-t border-slate-800/80 flex flex-col gap-2 shrink-0"
      >
        <div className="relative flex items-center">
          <textarea
            ref={chatInputRef}
            rows={1}
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Ask about your MSME feasibility or schemes... (Alt+Space)"
            className="w-full bg-slate-900/90 border border-slate-700/80 focus:border-cyan-400/80 focus:ring-1 focus:ring-cyan-400/50 text-slate-100 placeholder:text-slate-500 text-xs rounded-xl pl-3 pr-10 py-2.5 resize-none outline-none transition-all disabled:opacity-50"
            style={{ maxHeight: '90px' }}
          />

          <button
            type="submit"
            disabled={!inputVal.trim() || isLoading}
            className="absolute right-1.5 p-2 rounded-lg bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer shadow-md shadow-cyan-900/20"
            title="Send Message (Enter)"
            aria-label="Send Message"
          >
            <SendHorizontal className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Footer Subtext */}
        <div className="flex items-center justify-between text-[9px] text-slate-400 px-1">
          <span>Powered by Groq Cloud</span>
          <span className="font-mono bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800 text-slate-400">
            Alt + Space
          </span>
        </div>
      </form>
    </div>
  );
}
