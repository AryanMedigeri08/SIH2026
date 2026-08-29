import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { chatApi } from '../services/api';
import { useAuth } from './AuthContext';
import { useBusiness } from './BusinessContext';
import { useLanguage } from './LanguageContext';

const ChatContext = createContext(null);

const DEFAULT_WIDTH = 440;
const DEFAULT_HEIGHT = 600;
const POSITION_STORAGE_KEY = 'udyam_saathi_chat_window_pos_v1';
const MESSAGES_STORAGE_KEY = 'udyam_saathi_chat_history_v1';

export function ChatProvider({ children }) {
  const { token } = useAuth();
  const { reportData, activeBusiness } = useBusiness();
  const { language } = useLanguage();

  // Chat window open & animation state
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [animState, setAnimState] = useState('idle'); // 'opening' | 'minimizing' | 'idle'
  const [isLoading, setIsLoading] = useState(false);
  const [inputRefState, setInputRefState] = useState(null);

  // Position & Dimensions
  const [position, setPosition] = useState(() => {
    try {
      const saved = localStorage.getItem(POSITION_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        // Ensure within current screen bounds
        const maxX = Math.max(20, window.innerWidth - DEFAULT_WIDTH - 20);
        const maxY = Math.max(20, window.innerHeight - DEFAULT_HEIGHT - 20);
        return {
          x: Math.min(Math.max(20, parsed.x), maxX),
          y: Math.min(Math.max(70, parsed.y), maxY),
        };
      }
    } catch (_) {}
    // Default: Bottom Right floating position
    return {
      x: typeof window !== 'undefined' ? Math.max(20, window.innerWidth - DEFAULT_WIDTH - 30) : 100,
      y: typeof window !== 'undefined' ? Math.max(80, window.innerHeight - DEFAULT_HEIGHT - 30) : 100,
    };
  });

  const [size] = useState({ width: DEFAULT_WIDTH, height: DEFAULT_HEIGHT });

  // Conversation history
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(MESSAGES_STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch (_) {}
    return [
      {
        id: 'welcome-1',
        role: 'assistant',
        content: `👋 **Welcome to Udyam Saathi AI Advisor!**\n\nI can assist you with:\n- **Scheme Optimization**: Eligibility for PMEGP, Mudra, PMFME, and CGTMSE subsidies.\n- **Credit Feasibility**: Evaluating DSCR, monthly EMIs, and break-even realization.\n- **Regulatory Clearances**: Udyam, GST, FSSAI, and bank documentation.\n\nHow can I assist your enterprise today?`,
        timestamp: new Date().toISOString(),
      },
    ];
  });

  // Ref to the Chatbot button in Top Navigation bar to compute animation trajectory
  const navButtonRef = useRef(null);
  const chatInputRef = useRef(null);

  // Save position on change
  useEffect(() => {
    try {
      localStorage.setItem(POSITION_STORAGE_KEY, JSON.stringify(position));
    } catch (_) {}
  }, [position]);

  // Save messages on change
  useEffect(() => {
    try {
      localStorage.setItem(MESSAGES_STORAGE_KEY, JSON.stringify(messages));
    } catch (_) {}
  }, [messages]);

  // Window resize handler: Keep window on-screen if viewport resizes
  useEffect(() => {
    const handleResize = () => {
      setPosition((prev) => {
        const maxX = Math.max(20, window.innerWidth - size.width - 20);
        const maxY = Math.max(70, window.innerHeight - size.height - 20);
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
      // If already open, just focus input
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

    setIsAnimating(true);
    setAnimState('minimizing');

    setTimeout(() => {
      setIsChatOpen(false);
      setAnimState('idle');
      setIsAnimating(false);
    }, 280);
  }, [isChatOpen, isAnimating]);

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
      // Check for Alt + Space (or Option + Space on Mac)
      if (e.altKey && (e.code === 'Space' || e.key === ' ' || e.keyCode === 32)) {
        // Prevent accidental page scroll
        e.preventDefault();
        e.stopPropagation();

        if (!isChatOpen) {
          openChat();
        } else {
          // If already open, focus input
          if (chatInputRef.current) {
            chatInputRef.current.focus();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown, true);
    return () => window.removeEventListener('keydown', handleKeyDown, true);
  }, [isChatOpen, openChat]);

  // Extract Active Context for Groq Grounding
  const getGroundedContext = useCallback(() => {
    if (!reportData) {
      if (activeBusiness) {
        return {
          enterprise_name: activeBusiness.name,
          sector: activeBusiness.sector,
          business_category: activeBusiness.category,
          location: `${activeBusiness.district || ''}, ${activeBusiness.state || ''}`,
          project_cost: activeBusiness.project_cost,
        };
      }
      return null;
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
      current_tab: typeof window !== 'undefined' ? window.location.pathname.split('/').pop() : 'overview',
    };
  }, [reportData, activeBusiness]);

  // Send Message to Chatbot
  const sendMessage = useCallback(
    async (text) => {
      const clean = text?.trim();
      if (!clean || isLoading) return;

      const userMsgId = `user-${Date.now()}`;
      const userMsg = {
        id: userMsgId,
        role: 'user',
        content: clean,
        timestamp: new Date().toISOString(),
      };

      const updatedHistory = [...messages, userMsg];
      setMessages(updatedHistory);
      setIsLoading(true);

      try {
        const context = getGroundedContext();
        const payloadMessages = updatedHistory.map((m) => ({
          role: m.role,
          content: m.content,
        }));

        const response = await chatApi.sendChatMessage(
          payloadMessages,
          context,
          language || 'en',
          token
        );

        const assistantContent =
          response?.message?.content ||
          "I'm sorry, I couldn't generate a response. Please try again.";

        const assistantMsg = {
          id: `asst-${Date.now()}`,
          role: 'assistant',
          content: assistantContent,
          model: response?.model,
          isFallback: response?.is_fallback,
          latencyMs: response?.latency_ms,
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err) {
        console.error('Chat error:', err);
        const errorMsg = {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `⚠️ **Unable to connect to AI Assistant**\n\n*Error*: ${err.message || 'Network failure'}. Please check your connection or try again.`,
          isError: true,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [messages, isLoading, getGroundedContext, language, token]
  );

  // Clear Chat History
  const clearChat = useCallback(() => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: `👋 **Chat history reset.**\n\nHow can I help you analyze your MSME project, scheme eligibility, or financial ratios today?`,
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

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
        navButtonRef,
        chatInputRef,
        openChat,
        minimizeChat,
        toggleChat,
        sendMessage,
        clearChat,
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
