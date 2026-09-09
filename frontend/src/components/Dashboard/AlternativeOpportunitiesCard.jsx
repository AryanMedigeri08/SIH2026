import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Lightbulb,
  Sparkles,
  TrendingUp,
  ShieldCheck,
  Award,
  ArrowRight,
  RefreshCw,
  Cpu,
  Layers,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  DollarSign,
  Briefcase,
  ChevronRight,
  Check,
  Loader2,
  Star,
  Zap,
  Building2,
  ChevronDown,
  ChevronUp,
  Percent,
  Activity,
  FileCheck,
} from 'lucide-react';
import { recommendationsApi, generateFeasibility } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useBusiness } from '../../context/BusinessContext';
import { TranslatedText } from '../TranslatedText';
import confetti from 'canvas-confetti';

const STORAGE_KEY_ALTERNATIVES = 'udyam_saathi_current_alternatives';

export function AlternativeOpportunitiesCard({ reportData, onOpenWizard }) {
  const { token } = useAuth();
  const { createAndSaveBusiness, activeBusiness, setReportData } = useBusiness();
  const navigate = useNavigate();

  const [recommendations, setRecommendations] = useState([]);
  const [source, setSource] = useState('GROQ_LLM');
  const [loading, setLoading] = useState(false);
  const [switchingRank, setSwitchingRank] = useState(null);
  const [error, setError] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const verdict = reportData?.ml_viability?.verdict;
  const isReconsider = verdict === 'RECONSIDER';
  const currentSector = reportData?.input_parameters?.sector || activeBusiness?.sector;

  // Load recommendations from API when verdict is RECONSIDER
  const loadRecommendations = useCallback(async () => {
    if (!reportData || !isReconsider) return;
    setLoading(true);
    setError(null);

    try {
      let res;
      if (reportData.report_id) {
        res = await recommendationsApi.fetchRecommendationsFromReport(reportData.report_id, token);
      } else {
        res = await recommendationsApi.fetchRecommendations(reportData.input_parameters || {}, token);
      }

      if (res && res.recommendations && res.recommendations.length > 0) {
        const top3 = res.recommendations.slice(0, 3);
        setRecommendations(top3);
        setSource(res.source || 'GROQ_LLM');
      } else {
        setRecommendations([]);
      }
    } catch (err) {
      console.warn('Failed to fetch recommendations:', err);
      setError(err.message || 'Unable to load recommendations');
    } finally {
      setLoading(false);
    }
  }, [reportData, isReconsider, token]);

  // Only fetch recommendations when the enterprise is flagged as RECONSIDER
  useEffect(() => {
    if (isReconsider) {
      loadRecommendations();
    } else {
      setRecommendations([]);
    }
  }, [isReconsider, loadRecommendations]);

  // Handle 1-Click Auto-Generation & Switch
  const handleSwitchToEnterprise = async (rec) => {
    if (switchingRank !== null) return;
    setSwitchingRank(rec.rank);

    try {
      const originalParams = reportData?.input_parameters || {};
      // Use the recommended alternative's enterprise name for the new dashboard
      const newEnterpriseName = rec.enterprise_name || originalParams.enterprise_name || 'Alternative Enterprise';

      const payload = {
        enterprise_name: newEnterpriseName,
        business_category: rec.business_category || 'manufacturing',
        sector: rec.sector || 'general',
        project_cost: Number(rec.estimated_project_cost),
        annual_turnover_estimate: Number(rec.estimated_annual_turnover),
        state_name: originalParams.state_name || 'Maharashtra',
        district_name: originalParams.district_name || 'Pune',
        block_name: originalParams.block_name || 'N/A',
        village_name: originalParams.village_name || 'N/A',
        is_rural: originalParams.is_rural ?? true,
        promoter_name: originalParams.promoter_name || 'Enterprise Promoter',
        promoter_category: originalParams.promoter_category || 'general',
        gender: originalParams.gender || 'Unspecified',
        tenure_years: Number(originalParams.tenure_years || 5),
        moratorium_months: Number(originalParams.moratorium_months || 6),
        language: originalParams.language || 'en',
        additional_business_details: `Switched from reconsidered project to recommended alternative #${rec.rank} (${rec.enterprise_name}). Rationale: ${rec.rationale}`,
      };

      // Generate report and create/save business in BusinessContext
      const created = await createAndSaveBusiness(payload);

      try {
        confetti({ particleCount: 75, spread: 70, origin: { y: 0.8 } });
      } catch (_) {}

      if (created?.project_id) {
        navigate(`/reports/${created.project_id}`);
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      console.error('Failed to auto-generate alternative enterprise:', err);
      alert(`Failed to switch enterprise: ${err.message || 'Server error'}`);
    } finally {
      setSwitchingRank(null);
    }
  };

  // Strictly hide if verdict is not RECONSIDER (e.g. SUITABLE or CAUTION)
  if (!isReconsider) {
    return null;
  }

  // Ensure exactly up to 3 recommendations are displayed
  const displayRecs = recommendations.slice(0, 3);

  return (
    <div
      className={`glass-panel p-6 bg-gradient-to-br from-amber-50/60 via-white to-sky-50/40 border-2 rounded-2xl shadow-card space-y-5 relative overflow-hidden transition-all duration-300 ${
        isReconsider ? 'border-amber-300/90' : 'border-emerald-300/90'
      }`}
    >
      {/* Decorative ambient background glows */}
      <div className="absolute -top-16 -right-16 w-56 h-56 bg-amber-200/25 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-16 -left-16 w-56 h-56 bg-emerald-200/25 rounded-full blur-3xl pointer-events-none" />

      {/* Top Header & Context Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-amber-200/60 relative z-10">
        <div className="flex items-start gap-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-md shrink-0 text-white ${
              isReconsider
                ? 'bg-gradient-to-br from-amber-500 to-amber-600 shadow-amber-500/20'
                : 'bg-gradient-to-br from-emerald-600 to-teal-600 shadow-emerald-500/20'
            }`}
          >
            {isReconsider ? (
              <Lightbulb className="w-5 h-5 animate-pulse" />
            ) : (
              <CheckCircle2 className="w-5 h-5" />
            )}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-base sm:text-lg font-outfit font-black text-slate-900 tracking-tight">
                <TranslatedText text="AI-Curated Alternative Enterprise Recommendations Matrix" />
              </h3>
              {isReconsider ? (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 flex items-center gap-1 shadow-xs">
                  <Sparkles className="w-3 h-3 text-amber-700" />
                  <TranslatedText text="3 Viable Alternatives" />
                </span>
              ) : (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 flex items-center gap-1 shadow-xs">
                  <CheckCircle2 className="w-3 h-3 text-emerald-700" />
                  <TranslatedText text="Switched Enterprise Active" />
                </span>
              )}
            </div>
            <p className="text-xs text-slate-600 font-medium mt-0.5 max-w-3xl">
              {isReconsider ? (
                <TranslatedText text="The proposed project was flagged for reconsideration. Below are 3 high-solvency alternative enterprise models compared across financial parameters, statutory subsidies, and debt coverage." />
              ) : (
                <TranslatedText text="Viewing persistent recommendations matrix. You can explore parameters or switch between the other recommended enterprises at any time." />
              )}
            </p>
          </div>
        </div>

        {/* Engine Source Badge, Refresh & Collapse */}
        <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
          <span className="text-[11px] font-mono font-bold px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-700 shadow-subtle flex items-center gap-1.5">
            {source === 'GROQ_LLM' ? (
              <>
                <Cpu className="w-3.5 h-3.5 text-indigo-600" />
                <span>Groq GPT-OSS-20B AI</span>
              </>
            ) : (
              <>
                <Layers className="w-3.5 h-3.5 text-sovereign-700" />
                <span><TranslatedText text="Regional Engine" /></span>
              </>
            )}
          </span>

          <button
            onClick={loadRecommendations}
            disabled={loading}
            className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition shadow-subtle disabled:opacity-50"
            title="Refresh recommendations"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-amber-600' : ''}`} />
          </button>

          <button
            onClick={() => setIsCollapsed((prev) => !prev)}
            className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition shadow-subtle"
            title={isCollapsed ? 'Expand comparison table' : 'Collapse comparison table'}
          >
            {isCollapsed ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading && !isCollapsed && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="p-4 rounded-xl bg-white/80 border border-amber-100 shadow-subtle animate-pulse space-y-4"
            >
              <div className="flex items-center justify-between">
                <div className="h-4 bg-amber-200/60 rounded w-24" />
                <div className="h-4 bg-slate-200 rounded w-16" />
              </div>
              <div className="h-6 bg-slate-200 rounded w-3/4" />
              <div className="space-y-2 pt-2">
                <div className="h-10 bg-slate-100 rounded" />
                <div className="h-10 bg-slate-100 rounded" />
                <div className="h-10 bg-slate-100 rounded" />
              </div>
              <div className="h-10 bg-slate-200 rounded w-full" />
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {!loading && error && displayRecs.length === 0 && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2 font-medium">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span><TranslatedText text="Unable to compute alternative recommendations at this time." /></span>
          </div>
          <button
            onClick={loadRecommendations}
            className="px-3 py-1 bg-white border border-rose-300 text-rose-900 rounded-lg font-bold hover:bg-rose-100 transition"
          >
            <TranslatedText text="Retry" />
          </button>
        </div>
      )}

      {/* 3-Column Structured Comparison Table & Action Rows */}
      {!loading && !isCollapsed && displayRecs.length > 0 && (
        <div className="relative z-10 space-y-4">
          {/* 3-Column Grid Cards Matrix */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-5 items-stretch">
            {displayRecs.map((rec, idx) => {
              const isTopMatch = rec.rank === 1 || idx === 0;
              const isCurrentActive =
                rec.sector?.toLowerCase() === currentSector?.toLowerCase() ||
                (reportData?.input_parameters?.project_cost === rec.estimated_project_cost &&
                  reportData?.input_parameters?.sector === rec.sector);

              const costLakh = rec.estimated_project_cost
                ? (rec.estimated_project_cost / 100000).toFixed(2)
                : '5.00';
              const turnoverLakh = rec.estimated_annual_turnover
                ? (rec.estimated_annual_turnover / 100000).toFixed(2)
                : '9.00';
              const dscrVal = rec.estimated_dscr ? Number(rec.estimated_dscr).toFixed(2) : '1.75';
              const isGeneratingThis = switchingRank === rec.rank;

              return (
                <div
                  key={idx}
                  className={`flex flex-col justify-between rounded-2xl transition-all duration-200 overflow-hidden ${
                    isTopMatch
                      ? 'border-2 border-emerald-500 shadow-xl shadow-emerald-500/10 ring-2 ring-emerald-500/20 bg-gradient-to-b from-emerald-50/50 via-white to-white'
                      : 'border border-slate-200 shadow-subtle bg-white hover:border-slate-300 hover:shadow-card'
                  }`}
                >
                  {/* Top Match Highlight Banner (Column 1) */}
                  {isTopMatch && (
                    <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-600 text-white px-3.5 py-1.5 text-[11px] font-bold flex items-center justify-between shadow-xs">
                      <span className="flex items-center gap-1.5 uppercase tracking-wider">
                        <Star className="w-3.5 h-3.5 fill-amber-300 text-amber-300" />
                        <TranslatedText text="Top Recommended Match" />
                      </span>
                      <span className="bg-white/20 text-white text-[10px] px-2 py-0.2 rounded-full font-mono">
                        <TranslatedText text="Rank #1" />
                      </span>
                    </div>
                  )}

                  <div className="p-4 sm:p-5 space-y-4 flex-1">
                    {/* Header Row: Rank Badge & Sector Pills */}
                    <div className="flex items-center justify-between gap-2">
                      {!isTopMatch && (
                        <span className="text-[10px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200 flex items-center gap-1">
                          <span>#{rec.rank || idx + 1}</span>
                          <span><TranslatedText text="Alternative" /></span>
                        </span>
                      )}

                      <div className="flex items-center gap-1.5 ml-auto">
                        <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200">
                          {rec.relevant_scheme || 'PMEGP'}
                        </span>
                        <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-md bg-sky-50 text-sky-800 border border-sky-200">
                          {rec.business_category || 'MANUFACTURING'}
                        </span>
                      </div>
                    </div>

                    {/* Enterprise Title */}
                    <div>
                      <h4 className="text-base font-outfit font-black text-slate-900 leading-snug">
                        <TranslatedText text={rec.enterprise_name} />
                      </h4>
                      <div className="text-xs font-semibold text-slate-500 capitalize mt-1 flex items-center gap-1">
                        <Briefcase className="w-3 h-3 text-slate-400" />
                        <span><TranslatedText text={rec.sector ? rec.sector.replace(/_/g, ' ') : 'Agri-Business'} /></span>
                      </div>
                    </div>

                    {/* Structured Parameter Rows Matrix */}
                    <div className="space-y-2 pt-2 border-t border-slate-100">
                      
                      {/* Parameter 1: Capital Outlay */}
                      <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100 text-xs">
                        <span className="text-slate-600 font-medium flex items-center gap-1.5">
                          <DollarSign className="w-3.5 h-3.5 text-slate-500" />
                          <TranslatedText text="Est. Capital Outlay" />
                        </span>
                        <span className="font-outfit font-black text-slate-900 text-sm">
                          ₹{costLakh} Lakhs
                        </span>
                      </div>

                      {/* Parameter 2: Annual Turnover */}
                      <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100 text-xs">
                        <span className="text-slate-600 font-medium flex items-center gap-1.5">
                          <TrendingUp className="w-3.5 h-3.5 text-sky-600" />
                          <TranslatedText text="Projected Turnover" />
                        </span>
                        <span className="font-outfit font-black text-slate-900 text-sm">
                          ₹{turnoverLakh} Lakhs
                        </span>
                      </div>

                      {/* Parameter 3: DSCR Debt Solvency */}
                      <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-50/60 border border-emerald-100 text-xs">
                        <span className="text-emerald-900 font-medium flex items-center gap-1.5">
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                          <TranslatedText text="Debt Solvency (DSCR)" />
                        </span>
                        <span className="font-outfit font-black text-emerald-700 text-sm flex items-center gap-1">
                          {dscrVal}
                          <span className="text-[9px] font-bold text-emerald-600 bg-emerald-100 px-1 py-0.2 rounded">
                            ≥1.33 RBI
                          </span>
                        </span>
                      </div>

                      {/* Parameter 4: Suitability Index */}
                      <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100 text-xs">
                        <span className="text-slate-600 font-medium flex items-center gap-1.5">
                          <Activity className="w-3.5 h-3.5 text-indigo-500" />
                          <TranslatedText text="Suitability Match" />
                        </span>
                        <span className="font-mono font-bold text-indigo-700 text-xs">
                          {Math.round(rec.suitability_score || 85)} / 100
                        </span>
                      </div>
                    </div>

                    {/* Parameter 5: Grounded Strategic Rationale */}
                    <div className="p-3 rounded-xl bg-amber-50/50 border border-amber-200/60 text-xs text-slate-700 font-medium leading-relaxed">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-amber-900 mb-1 flex items-center gap-1">
                        <Zap className="w-3 h-3 text-amber-700" />
                        <span><TranslatedText text="Strategic Advantage & Feasibility" /></span>
                      </div>
                      <TranslatedText text={rec.rationale} />
                    </div>
                  </div>

                  {/* Last Row: Action Row with Switch Button */}
                  <div
                    className={`p-4 pt-3 border-t ${
                      isTopMatch ? 'bg-emerald-50/40 border-emerald-100' : 'bg-slate-50/60 border-slate-100'
                    }`}
                  >
                    {isCurrentActive ? (
                      <div className="w-full py-2.5 px-3 rounded-xl bg-emerald-100 text-emerald-900 border border-emerald-300 font-outfit font-bold text-xs flex items-center justify-center gap-2 shadow-xs">
                        <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                        <span><TranslatedText text="Currently Active Enterprise" /></span>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleSwitchToEnterprise(rec)}
                        disabled={switchingRank !== null}
                        className={`w-full py-2.5 px-4 rounded-xl font-outfit font-bold text-xs text-white shadow-md flex items-center justify-center gap-2 transition-all duration-200 group disabled:opacity-60 ${
                          isTopMatch
                            ? 'bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 hover:from-emerald-700 hover:to-teal-800 shadow-emerald-700/20'
                            : 'bg-gradient-to-r from-sovereign-800 to-slate-800 hover:from-sovereign-700 hover:to-slate-700 shadow-sovereign-900/15'
                        }`}
                      >
                        {isGeneratingThis ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin text-white" />
                            <span><TranslatedText text="Generating Feasibility Dashboard..." /></span>
                          </>
                        ) : (
                          <>
                            <span><TranslatedText text="Switch to this Enterprise" /></span>
                            <ArrowRight className="w-4 h-4 text-white/80 group-hover:translate-x-1 transition-transform" />
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default AlternativeOpportunitiesCard;
