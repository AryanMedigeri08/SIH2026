import React from 'react';
import { Target, CheckCircle2, AlertTriangle, Lightbulb, ShieldAlert } from 'lucide-react';

export function SwotMatrixCard({ swotData }) {
  const s = swotData?.strengths || [];
  const w = swotData?.weaknesses || [];
  const o = swotData?.opportunities || [];
  const t = swotData?.threats || [];

  return (
    <div className="glass-panel p-6">
      <div className="mb-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Target className="w-4 h-4 text-cyan-400" />
          Grounded SWOT Analysis Matrix
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">
          Domain-grounded enterprise evaluation derived from demographic, competitive, and financial signals.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Strengths */}
        <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-xl p-4 space-y-2">
          <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <CheckCircle2 className="w-4 h-4" /> Internal Strengths
          </div>
          <ul className="space-y-1.5 text-xs text-slate-200">
            {s.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-emerald-400 mt-0.5">•</span>
                <span>{item.text || item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Weaknesses */}
        <div className="bg-amber-950/20 border border-amber-500/20 rounded-xl p-4 space-y-2">
          <div className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <AlertTriangle className="w-4 h-4" /> Internal Weaknesses
          </div>
          <ul className="space-y-1.5 text-xs text-slate-200">
            {w.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-amber-400 mt-0.5">•</span>
                <span>{item.text || item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Opportunities */}
        <div className="bg-cyan-950/20 border border-cyan-500/20 rounded-xl p-4 space-y-2">
          <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <Lightbulb className="w-4 h-4" /> Market Opportunities
          </div>
          <ul className="space-y-1.5 text-xs text-slate-200">
            {o.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-cyan-400 mt-0.5">•</span>
                <span>{item.text || item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Threats */}
        <div className="bg-rose-950/20 border border-rose-500/20 rounded-xl p-4 space-y-2">
          <div className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <ShieldAlert className="w-4 h-4" /> Macro & External Threats
          </div>
          <ul className="space-y-1.5 text-xs text-slate-200">
            {t.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-rose-400 mt-0.5">•</span>
                <span>{item.text || item}</span>
              </li>
            ))}
          </ul>
        </div>

      </div>

      {/* Grounded Data Source Lineage Tag */}
      <div className="text-[10px] text-slate-500 flex flex-wrap items-center justify-between gap-2 pt-3 mt-4 border-t border-slate-800/60">
        <span>
          <strong className="text-slate-400">Data Source:</strong> Upstream Multi-Signal Matrix (Census 2011 + MSME Density + XGBoost Viability Output)
        </span>
        <span className="font-mono text-slate-400">
          SWOT Logic: Deterministic Domain Grounding
        </span>
      </div>

    </div>
  );
}

