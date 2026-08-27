import React from 'react';
import { Target, CheckCircle2, AlertTriangle, Lightbulb, ShieldAlert } from 'lucide-react';

export function SwotMatrixCard({ swotData }) {
  const s = swotData?.strengths || [];
  const w = swotData?.weaknesses || [];
  const o = swotData?.opportunities || [];
  const t = swotData?.threats || [];

  return (
    <div className="glass-panel p-6 bg-white shadow-card border border-slate-200">
      <div className="mb-4">
        <div className="text-[11px] font-bold uppercase tracking-wider text-sovereign-700 flex items-center gap-1.5 mb-1">
          <Target className="w-3.5 h-3.5" />
          Strategic Commercial Evaluation
        </div>
        <h3 className="text-lg font-outfit font-bold text-slate-900">
          Grounded SWOT Analysis Matrix
        </h3>
        <p className="text-xs text-slate-600 mt-0.5">
          Domain-grounded enterprise evaluation derived from demographic, competitive, and financial signals.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Strengths */}
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 space-y-2">
          <div className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Internal Strengths
          </div>
          <ul className="space-y-1.5 text-xs text-slate-800 font-medium">
            {s.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-emerald-600 mt-0.5 font-bold">•</span>
                <span>{item.text || item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Weaknesses */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 space-y-2">
          <div className="text-xs font-bold text-amber-800 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" /> Internal Weaknesses
          </div>
          <ul className="space-y-1.5 text-xs text-slate-800 font-medium">
            {w.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-amber-600 mt-0.5 font-bold">•</span>
                <span>{item.text || item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Opportunities */}
        <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 space-y-2">
          <div className="text-xs font-bold text-sky-900 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <Lightbulb className="w-4 h-4 text-sky-700" /> Market Opportunities
          </div>
          <ul className="space-y-1.5 text-xs text-slate-800 font-medium">
            {o.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-sky-700 mt-0.5 font-bold">•</span>
                <span>{item.text || item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Threats */}
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 space-y-2">
          <div className="text-xs font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <ShieldAlert className="w-4 h-4 text-rose-600" /> Macro & External Threats
          </div>
          <ul className="space-y-1.5 text-xs text-slate-800 font-medium">
            {t.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-rose-600 mt-0.5 font-bold">•</span>
                <span>{item.text || item}</span>
              </li>
            ))}
          </ul>
        </div>

      </div>

      {/* Grounded Data Source Lineage Tag */}
      <div className="text-[10px] text-slate-500 flex flex-wrap items-center justify-between gap-2 pt-3 mt-4 border-t border-slate-200">
        <span>
          <strong className="text-slate-700">Data Source:</strong> Upstream Multi-Signal Matrix (Census 2011 + MSME Density + XGBoost Output)
        </span>
        <span className="font-mono text-slate-600 font-medium">
          SWOT Logic: Deterministic Domain Grounding
        </span>
      </div>

    </div>
  );
}
export default SwotMatrixCard;
