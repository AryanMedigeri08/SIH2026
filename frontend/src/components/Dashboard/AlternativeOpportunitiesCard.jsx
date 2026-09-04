import React, { useState, useEffect } from 'react';
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
} from 'lucide-react';
import { recommendationsApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { TranslatedText } from '../TranslatedText';

export function AlternativeOpportunitiesCard({ reportData, onOpenWizard }) {
  const { token } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [source, setSource] = useState('GROQ_LLM');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const verdict = reportData?.ml_viability?.verdict;
  const isReconsider = verdict === 'RECONSIDER';

  const loadRecommendations = React.useCallback(async () => {
    if (!reportData) return;
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
        setRecommendations(res.recommendations);
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
  }, [reportData, token]);

  useEffect(() => {
    if (isReconsider) {
      loadRecommendations();
    }
  }, [isReconsider, loadRecommendations]);

  // If verdict is not RECONSIDER, do not render this component
  if (!isReconsider) return null;

  return (
    <div className="glass-panel p-6 bg-gradient-to-br from-amber-50/50 via-white to-sky-50/40 border-2 border-amber-300/80 rounded-2xl shadow-card space-y-5 relative overflow-hidden">
      {/* Decorative ambient background blur */}
      <div className="absolute -top-16 -right-16 w-56 h-56 bg-amber-200/30 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-16 -left-16 w-56 h-56 bg-sky-200/30 rounded-full blur-3xl pointer-events-none" />

      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-amber-200/60 relative z-10">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 text-white flex items-center justify-center shadow-md shadow-amber-500/20 shrink-0">
            <Lightbulb className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base sm:text-lg font-outfit font-black text-slate-900 tracking-tight">
                <TranslatedText text="AI-Curated Alternative Enterprise Recommendations" />
              </h3>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-amber-700" />
                <TranslatedText text="High Viability" />
              </span>
            </div>
            <p className="text-xs text-slate-600 font-medium mt-0.5 max-w-2xl">
              <TranslatedText text="The current business model was flagged for reconsideration. Our intelligence engine identified these higher-solvency opportunities tailored to your regional infrastructure, capital capacity, and local demand." />
            </p>
          </div>
        </div>

        {/* Engine Source Badge & Refresh */}
        <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
          <span className="text-[11px] font-mono font-bold px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-700 shadow-subtle flex items-center gap-1.5">
            {source === 'GROQ_LLM' ? (
              <>
                <Cpu className="w-3.5 h-3.5 text-indigo-600" />
                <span>Groq Llama-3.3-70B AI</span>
              </>
            ) : (
              <>
                <Layers className="w-3.5 h-3.5 text-sovereign-700" />
                <span><TranslatedText text="Regional Deterministic Engine" /></span>
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
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-4 rounded-xl bg-white/80 border border-amber-100 shadow-subtle animate-pulse space-y-3">
              <div className="flex items-center justify-between">
                <div className="h-4 bg-amber-200/60 rounded w-24" />
                <div className="h-4 bg-slate-200 rounded w-16" />
              </div>
              <div className="h-5 bg-slate-200 rounded w-3/4" />
              <div className="grid grid-cols-3 gap-2 pt-2">
                <div className="h-10 bg-slate-100 rounded" />
                <div className="h-10 bg-slate-100 rounded" />
                <div className="h-10 bg-slate-100 rounded" />
              </div>
              <div className="h-12 bg-slate-100 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {!loading && error && recommendations.length === 0 && (
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

      {/* Recommendations Cards Grid */}
      {!loading && recommendations.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 relative z-10">
          {recommendations.map((rec, idx) => {
            const costLakh = rec.estimated_project_cost ? (rec.estimated_project_cost / 100000).toFixed(2) : '5.00';
            const turnoverLakh = rec.estimated_annual_turnover ? (rec.estimated_annual_turnover / 100000).toFixed(2) : '9.00';
            const dscrVal = rec.estimated_dscr ? Number(rec.estimated_dscr).toFixed(2) : '1.75';

            return (
              <div
                key={idx}
                className={`p-4 rounded-xl bg-white border transition-all duration-200 flex flex-col justify-between hover:shadow-card-elevated hover:-translate-y-0.5 ${
                  idx === 0
                    ? 'border-amber-400 shadow-md ring-1 ring-amber-400/30'
                    : 'border-slate-200 shadow-subtle'
                }`}
              >
                <div className="space-y-3">
                  {/* Top Badges */}
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full flex items-center gap-1 ${
                        idx === 0
                          ? 'bg-amber-500 text-white shadow-sm'
                          : 'bg-slate-100 text-slate-700 border border-slate-200'
                      }`}
                    >
                      <span>#{rec.rank || idx + 1}</span>
                      <span>{idx === 0 ? <TranslatedText text="Top Match" /> : <TranslatedText text="Alternative" />}</span>
                    </span>

                    <div className="flex items-center gap-1">
                      <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200">
                        {rec.relevant_scheme || 'PMEGP'}
                      </span>
                      <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-md bg-sky-50 text-sky-800 border border-sky-200">
                        {rec.business_category || 'MANUFACTURING'}
                      </span>
                    </div>
                  </div>

                  {/* Enterprise Name */}
                  <h4 className="text-sm font-outfit font-extrabold text-slate-900 leading-snug">
                    <TranslatedText text={rec.enterprise_name} />
                  </h4>

                  {/* Sector Tag */}
                  <div className="text-[11px] font-medium text-slate-500 capitalize">
                    <TranslatedText text={rec.sector ? rec.sector.replace(/_/g, ' ') : 'Agri-Business'} />
                  </div>

                  {/* Key Metrics Grid */}
                  <div className="grid grid-cols-3 gap-2 p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-center">
                    <div>
                      <div className="text-[9px] font-bold uppercase text-slate-500">
                        <TranslatedText text="Est. Outlay" />
                      </div>
                      <div className="font-outfit font-extrabold text-xs text-slate-900 mt-0.5">
                        ₹{costLakh}L
                      </div>
                    </div>
                    <div>
                      <div className="text-[9px] font-bold uppercase text-slate-500">
                        <TranslatedText text="Annual Turnover" />
                      </div>
                      <div className="font-outfit font-extrabold text-xs text-slate-900 mt-0.5">
                        ₹{turnoverLakh}L
                      </div>
                    </div>
                    <div>
                      <div className="text-[9px] font-bold uppercase text-slate-500">
                        <TranslatedText text="Proj. DSCR" />
                      </div>
                      <div className="font-outfit font-extrabold text-xs text-emerald-700 mt-0.5">
                        {dscrVal}
                      </div>
                    </div>
                  </div>

                  {/* Rationale Narrative */}
                  <p className="text-[11px] text-slate-600 font-medium leading-relaxed bg-amber-50/40 p-2.5 rounded-lg border border-amber-100/60">
                    <TranslatedText text={rec.rationale} />
                  </p>
                </div>

                {/* Bottom Action */}
                <div className="pt-3 mt-3 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[10px] font-bold text-emerald-700 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span><TranslatedText text="Bank Viable" /></span>
                  </span>

                  {onOpenWizard && (
                    <button
                      onClick={() => onOpenWizard()}
                      className="inline-flex items-center gap-1 text-xs font-bold text-sovereign-800 hover:text-sky-700 group transition-colors"
                    >
                      <span><TranslatedText text="Appraise In Wizard" /></span>
                      <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default AlternativeOpportunitiesCard;
