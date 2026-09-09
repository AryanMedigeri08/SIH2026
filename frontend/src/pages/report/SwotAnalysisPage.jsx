import React from 'react';
import { SwotMatrixCard } from '../../components/Dashboard/SwotMatrixCard';
import { Grid3X3, CheckCircle2, AlertTriangle, Lightbulb, ShieldAlert, Sparkles } from 'lucide-react';
import { TranslatedText } from '../../components/TranslatedText';

export function SwotAnalysisPage({ reportData }) {
  if (!reportData) return null;

  const swot = reportData.swot_matrix || {};
  const s = swot.strengths || [];
  const w = swot.weaknesses || [];
  const o = swot.opportunities || [];
  const t = swot.threats || [];

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-4 sm:p-6 border-l-4 border-amber-600 bg-gradient-to-r from-white via-amber-50/20 to-white shadow-card border border-slate-200/90">
        <div className="text-xs font-bold uppercase tracking-wider text-amber-700 mb-1 flex items-center gap-1.5">
          <Grid3X3 className="w-4 h-4 text-amber-600" />
          <span><TranslatedText text="Dimension 6 • Domain-Grounded Strategic Evaluation" /></span>
        </div>
        <h1 className="text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
          <TranslatedText text="Grounded SWOT Analysis Matrix" />
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
          <TranslatedText text="Comprehensive strategic appraisal derived from Census 2011 demographic growth, MSME saturation density, and supervised XGBoost viability factors." />
        </p>
      </div>

      {/* Strategic SWOT Intelligence Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-4">
        <div className="glass-panel p-3 sm:p-4 bg-emerald-50/40 border border-emerald-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-emerald-800 font-bold uppercase tracking-wider">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span className="truncate"><TranslatedText text="Strengths" /></span>
          </div>
          <strong className="text-lg sm:text-2xl font-mono font-extrabold text-emerald-900 block mt-1 truncate">
            {s.length} <TranslatedText text="Identified" />
          </strong>
          <span className="text-[10px] text-emerald-700 mt-0.5 block font-medium truncate">
            <TranslatedText text="Internal Core Drivers" />
          </span>
        </div>

        <div className="glass-panel p-3 sm:p-4 bg-amber-50/40 border border-amber-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-amber-800 font-bold uppercase tracking-wider">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span className="truncate"><TranslatedText text="Weaknesses" /></span>
          </div>
          <strong className="text-lg sm:text-2xl font-mono font-extrabold text-amber-900 block mt-1 truncate">
            {w.length} <TranslatedText text="Identified" />
          </strong>
          <span className="text-[10px] text-amber-700 mt-0.5 block font-medium truncate">
            <TranslatedText text="Internal Bottlenecks" />
          </span>
        </div>

        <div className="glass-panel p-3 sm:p-4 bg-sky-50/40 border border-sky-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-sky-800 font-bold uppercase tracking-wider">
            <Lightbulb className="w-3.5 h-3.5 text-sky-600 shrink-0" />
            <span className="truncate"><TranslatedText text="Opportunities" /></span>
          </div>
          <strong className="text-lg sm:text-2xl font-mono font-extrabold text-sky-900 block mt-1 truncate">
            {o.length} <TranslatedText text="Identified" />
          </strong>
          <span className="text-[10px] text-sky-700 mt-0.5 block font-medium truncate">
            <TranslatedText text="Market Growth Vectors" />
          </span>
        </div>

        <div className="glass-panel p-3 sm:p-4 bg-rose-50/40 border border-rose-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-rose-800 font-bold uppercase tracking-wider">
            <ShieldAlert className="w-3.5 h-3.5 text-rose-600 shrink-0" />
            <span className="truncate"><TranslatedText text="Threats" /></span>
          </div>
          <strong className="text-lg sm:text-2xl font-mono font-extrabold text-rose-900 block mt-1 truncate">
            {t.length} <TranslatedText text="Identified" />
          </strong>
          <span className="text-[10px] text-rose-700 mt-0.5 block font-medium truncate">
            <TranslatedText text="External Risk Factors" />
          </span>
        </div>
      </div>

      {/* SWOT 4-Quadrant Card Component */}
      <SwotMatrixCard swotData={swot} synthesisData={reportData.executive_synthesis} />

    </div>
  );
}
export default SwotAnalysisPage;
