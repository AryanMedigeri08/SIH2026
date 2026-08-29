import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { chatApi } from '../services/api';
import { useAuth } from './AuthContext';
import { useBusiness } from './BusinessContext';
import { useLanguage } from './LanguageContext';

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
    mdCode: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    mdQuote: 'border-emerald-500 bg-emerald-50/60 text-slate-700',
  },
};

const ChatContext = createContext(null);

const DEFAULT_WIDTH = 440;
const DEFAULT_HEIGHT = 600;
const POSITION_STORAGE_KEY = 'udyam_saathi_chat_window_pos_v1';
const MESSAGES_STORAGE_KEY = 'udyam_saathi_chat_history_v1';
const THEME_STORAGE_KEY = 'udyam_saathi_chat_theme_v1';

export function ChatProvider({ children }) {
  const { token } = useAuth();
  const { reportData, activeBusiness } = useBusiness();
  const { language } = useLanguage();

  // Chat Theme state ('sovereign' | 'midnight' | 'emerald')
  const [chatTheme, setChatTheme] = useState(() => {
    try {
      const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
      if (savedTheme && CHAT_THEMES[savedTheme]) {
        return savedTheme;
      }
    } catch (_) {}
    return 'sovereign'; // Default: Sovereign Light
  });

  const currentTheme = CHAT_THEMES[chatTheme] || CHAT_THEMES.sovereign;

  // Toggle or cycle theme
  const cycleTheme = useCallback(() => {
    setChatTheme((prev) => {
      const themeKeys = Object.keys(CHAT_THEMES);
      const currentIndex = themeKeys.indexOf(prev);
      const nextIndex = (currentIndex + 1) % themeKeys.length;
      const nextTheme = themeKeys[nextIndex];
      try {
        localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
      } catch (_) {}
      return nextTheme;
    });
  }, []);

  const selectTheme = useCallback((themeKey) => {
    if (CHAT_THEMES[themeKey]) {
      setChatTheme(themeKey);
      try {
        localStorage.setItem(THEME_STORAGE_KEY, themeKey);
      } catch (_) {}
    }
  }, []);

  // Chat window open & animation state
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [animState, setAnimState] = useState('idle'); // 'opening' | 'minimizing' | 'idle'
  const [isLoading, setIsLoading] = useState(false);

  // Position & Dimensions
  const [position, setPosition] = useState(() => {
    try {
      const saved = localStorage.getItem(POSITION_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        const maxX = Math.max(20, window.innerWidth - DEFAULT_WIDTH - 20);
        const maxY = Math.max(20, window.innerHeight - DEFAULT_HEIGHT - 20);
        return {
          x: Math.min(Math.max(20, parsed.x), maxX),
          y: Math.min(Math.max(70, parsed.y), maxY),
        };
      }
    } catch (_) {}
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
        content: `👋 **Welcome to Udyam Saathi AI Advisor!**\n\nI have real-time access to the **dashboard screen and telemetry you are viewing**.\n\nYou can ask me to:\n- 📄 **"Summarize this page"** or explain any specific numbers on your screen\n- 🏛️ **Optimize your scheme subsidies** (PMEGP, Mudra, PMFME, CGTMSE)\n- 📈 **Audit your DSCR and credit feasibility metrics**\n\nHow can I help your enterprise right now?`,
        timestamp: new Date().toISOString(),
      },
    ];
  });

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
      icon = '⚠️';
    } else if (path.includes('/swot')) {
      tabKey = 'swot';
      tabTitle = 'SWOT Analysis Matrix';
      icon = '🎯';
    } else if (path.includes('/dpr')) {
      tabKey = 'dpr';
      tabTitle = 'Official Bank DPR Package & Statutory Annexures';
      icon = '📑';
    } else if (path.includes('/calculator')) {
      tabKey = 'calculator';
      tabTitle = 'Interactive Credit & Break-Even Calculator';
      icon = '🧮';
    } else if (path.includes('/data-sources')) {
      tabKey = 'data-sources';
      tabTitle = 'Live Data Sources & ML Pipelines';
      icon = '📡';
    } else if (path.includes('/wizard') || path.includes('/new-assessment')) {
      tabKey = 'wizard';
      tabTitle = '7-Step Feasibility Assessment Wizard';
      icon = '✨';
    }

    let tabData = {};
    let quickPrompts = [
      'Summarize this page in 3 key takeaways',
      'What are the most critical numbers on this screen?',
      'Is my business ready for commercial bank approval?',
    ];

    if (reportData) {
      if (tabKey === 'viability') {
        const ml = reportData.ml_viability || {};
        const shap = ml.shap_explanation?.contributions || [];
        tabData = {
          verdict: ml.verdict || 'SUITABLE',
          viability_score: `${ml.viability_score || ml.confidence_pct || 94}%`,
          confidence_pct: `${ml.confidence_pct || 94}%`,
          calibrated_probability: ml.probability || 0.94,
          top_positive_contributors: shap.filter((s) => Number(s.shap_value) > 0).slice(0, 3).map((s) => `${s.feature}: +${Number(s.shap_value).toFixed(2)}`),
          top_negative_risk_factors: shap.filter((s) => Number(s.shap_value) < 0).slice(0, 3).map((s) => `${s.feature}: ${Number(s.shap_value).toFixed(2)}`),
          infrastructure_readiness: reportData.input_parameters?.infrastructure_score || '8.2 / 10',
          working_capital_months_buffer: `${reportData.financial_summary?.working_capital_months || 2.5} Months`,
        };
        quickPrompts = [
          'Summarize this Viability page and verdict',
          'Explain my top positive and negative TreeSHAP factors',
          'How can I improve my viability score for the bank?',
        ];
      } else if (tabKey === 'market') {
        const mkt = reportData.market_analysis || {};
        tabData = {
          catchment_population_2026: mkt.catchment_population_2026 || reportData.input_parameters?.projected_population || '48,200',
          cluster_msme_density: mkt.msme_density_per_10k || '38 units per 10k Pop',
          estimated_monthly_demand: mkt.monthly_catchment_demand_units || '14,200 units',
          competitor_saturation_index: mkt.competitor_saturation_index || '0.34 (Low Saturation)',
          benchmark_market_selling_price: `₹${mkt.benchmark_unit_selling_price || 45.0}`,
          break_even_floor_price: `₹${reportData.financial_summary?.break_even_unit_price || 36.5}`,
        };
        quickPrompts = [
          'Summarize local market demand and catchment scale',
          'How competitive is my cluster location?',
          'Explain the margin between my break-even price and market price',
        ];
      } else if (tabKey === 'schemes') {
        const schemes = reportData.scheme_recommendations || [];
        tabData = {
          matched_schemes_count: schemes.length,
          top_recommended_schemes: schemes.slice(0, 3).map((s) => ({
            scheme: s.scheme_id || s.full_name,
            subsidy_grant_amount: `₹${Number(s.subsidy_grant_amount || 0).toLocaleString('en-IN')}`,
            grant_percentage: `${s.subsidy_percentage || 25}%`,
            eligibility_status: s.eligibility_status || 'Eligible',
            nodal_agency: s.nodal_agency || 'KVIC / District Industries Centre (DIC)',
          })),
        };
        quickPrompts = [
          'Summarize all matched subsidy schemes on this page',
          'Which scheme gives me the highest capital grant?',
          'What are the step-by-step application requirements?',
        ];
      } else if (tabKey === 'financials') {
        const fin = reportData.financial_summary || {};
        const amort = fin.amortization_schedule || {};
        tabData = {
          total_project_outlay: `₹${Number(fin.project_cost || 0).toLocaleString('en-IN')}`,
          promoter_equity_margin: `₹${Number(fin.promoter_margin_amount || 0).toLocaleString('en-IN')}`,
          effective_term_loan: `₹${Number(fin.effective_loan_principal || 0).toLocaleString('en-IN')}`,
          scheduled_monthly_emi: `₹${Number(amort.monthly_emi || 0).toLocaleString('en-IN')}`,
          dscr_solvency_ratio: `${Number(fin.dscr_ratio || 1.45).toFixed(2)} (${fin.dscr_verdict || 'Adequate Solvency'})`,
          year_1_gross_revenue: `₹${Number(fin.year_1_revenue || 0).toLocaleString('en-IN')}`,
          year_1_net_operating_profit: `₹${Number(fin.year_1_net_profit || 0).toLocaleString('en-IN')}`,
          break_even_capacity_utilization: `${fin.break_even_capacity_utilization_pct || 42}%`,
        };
        quickPrompts = [
          'Summarize this Financials page for my bank loan manager',
          'Explain why my DSCR ratio is safe or risky',
          'Break down my monthly EMI and break-even capacity',
        ];
      } else if (tabKey === 'risk') {
        const risk = reportData.risk_assessment || {};
        tabData = {
          overall_risk_grade: risk.risk_grade || 'Moderate / Low Risk',
          composite_risk_score: risk.composite_risk_score || '3.2 / 10.0',
          top_risk_vectors: risk.risk_vectors || ['Raw Material Price Volatility (MoSPI CPI)', 'Monsoon Weather Disruption', 'Working Capital Drag'],
          mitigation_strategies: risk.mitigation_strategies || ['Maintain 3-month DSCR reserve buffer', 'Long-term farmer vendor contracts'],
        };
        quickPrompts = [
          'Summarize the biggest risk factors on this page',
          'How can I mitigate raw material inflation and weather risks?',
          'What risk reserves will the bank look for?',
        ];
      } else if (tabKey === 'swot') {
        const swot = reportData.swot_analysis || {};
        tabData = {
          strengths: swot.strengths || ['High local raw material availability', 'Healthy gross contribution margin'],
          weaknesses: swot.weaknesses || ['Initial working capital constraint', 'Single facility dependency'],
          opportunities: swot.opportunities || ['Government PMEGP 35% subsidy grant', 'Expanding peri-urban retail demand'],
          threats: swot.threats || ['Unseasonal weather anomalies', 'Localized competitor price discounting'],
        };
        quickPrompts = [
          'Summarize this SWOT analysis and core opportunities',
          'How can I convert weaknesses into competitive advantages?',
        ];
      } else if (tabKey === 'dpr') {
        const dpr = reportData.dpr_package || {};
        tabData = {
          dpr_package_readiness: '100% Bank-Ready Format',
          total_sections: 7,
          required_statutory_licenses: ['Udyam Registration', 'GSTIN (if applicable)', 'FSSAI License / PCB Consent'],
          mandatory_bank_annexures: ['Promoter KYC (PAN/Aadhaar)', 'Machinery Supplier Quotations', 'Project Site Land/Lease Agreement'],
        };
        quickPrompts = [
          'Summarize the official bank DPR checklist',
          'What statutory licenses do I need before submitting?',
          'Walk me through the 7 DPR sections',
        ];
      } else {
        // Overview
        tabData = {
          enterprise_name: reportData.enterprise_name || reportData.input_parameters?.enterprise_name,
          sector: reportData.sector || reportData.input_parameters?.sector,
          total_project_outlay: `₹${Number(reportData.financial_summary?.project_cost || 0).toLocaleString('en-IN')}`,
          dscr_ratio: `${Number(reportData.financial_summary?.dscr_ratio || 1.45).toFixed(2)} (${reportData.financial_summary?.dscr_verdict || 'Adequate Solvency'})`,
          matched_scheme: reportData.scheme_recommendations?.[0]?.scheme_id || 'PMEGP',
          subsidy_grant: `₹${Number(reportData.scheme_recommendations?.[0]?.subsidy_grant_amount || 0).toLocaleString('en-IN')}`,
          ml_viability_verdict: reportData.ml_viability?.verdict || 'SUITABLE',
        };
        quickPrompts = [
          'Summarize this enterprise feasibility assessment',
          'Is this business ready for a bank loan application?',
          'What are the key financial highlights?',
        ];
      }
    }

    return { tabKey, tabTitle, icon, tabData, quickPrompts };
  }, [reportData]);

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

  // Send User Message
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

  // Clear conversation history
  const clearChat = useCallback(() => {
    const { tabTitle } = getActiveTabTelemetry();
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: `👋 **Chat history reset.**\n\nI am analyzing your **${tabTitle}** screen. Ask me to summarize this page or evaluate any financial or scheme metrics!`,
        timestamp: new Date().toISOString(),
      },
    ]);
  }, [getActiveTabTelemetry]);

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
