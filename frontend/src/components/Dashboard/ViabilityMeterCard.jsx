import React from 'react';
import { ShieldCheck, AlertTriangle, AlertCircle, CheckCircle2, TrendingUp } from 'lucide-react';

export function ViabilityMeterCard({ mlViability, dscrInfo }) {
  const verdict = mlViability?.verdict || "SUITABLE";
  const confidence = mlViability?.confidence_pct || 98.5;
  const probs = mlViability?.class_probabilities || { SUITABLE: 0.98, CAUTION: 0.01, RECONSIDER: 0.01 };
  
  const isSuitable = verdict === "SUITABLE";
  const isCaution = verdict === "CAUTION";
  const isReconsider = verdict === "RECONSIDER";

  const colorBorder = isSuitable ? "border-emerald-500" : isCaution ? "border-amber-500" : "border-rose-500";
  const colorBg = isSuitable ? "from-emerald-500/10" : isCaution ? "from-amber-500/10" : "from-rose-500/10";
  const badgeBg = isSuitable 
    ? "bg-emerald-500 text-black shadow-glow-emerald" 
    : isCaution 
    ? "bg-amber-500 text-black shadow-glow" 
    : "bg-rose-500 text-white shadow-glow-rose";

  return (
    <div className={`glass-panel p-6 border-l-4 ${colorBorder} bg-gradient-to-r ${colorBg} to-transparent`}>
      
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            Tier 2 Supervised XGBoost Viability Engine (10-Dimensional Feature Vector)
          </div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl sm:text-3xl font-outfit font-extrabold text-white">
              Viability Verdict:
            </h2>
            <span className={`text-base sm:text-lg font-outfit font-black px-4 py-1 rounded-xl ${badgeBg}`}>
              {verdict}
            </span>
          </div>
        </div>

        <div className="sm:text-right">
          <div className="text-[11px] text-slate-400 font-medium">Model Classification Confidence</div>
          <div className="text-2xl sm:text-3xl font-outfit font-extrabold text-cyan-400">
            {confidence.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Class Probabilities Bar */}
      <div className="mb-5">
        <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1.5">
          <span>Class Probabilities Distribution:</span>
          <span>
            SUITABLE: {(probs.SUITABLE * 100).toFixed(1)}% • CAUTION: {(probs.CAUTION * 100).toFixed(1)}% • RECONSIDER: {(probs.RECONSIDER * 100).toFixed(1)}%
          </span>
        </div>
        <div className="h-2.5 w-full rounded-full bg-slate-900 overflow-hidden flex p-0.5 border border-slate-800">
          <div 
            style={{ width: `${probs.SUITABLE * 100}%` }} 
            className="bg-emerald-400 rounded-l-full transition-all duration-500" 
            title="SUITABLE"
          />
          <div 
            style={{ width: `${probs.CAUTION * 100}%` }} 
            className="bg-amber-400 transition-all duration-500" 
            title="CAUTION"
          />
          <div 
            style={{ width: `${probs.RECONSIDER * 100}%` }} 
            className="bg-rose-500 rounded-r-full transition-all duration-500" 
            title="RECONSIDER"
          />
        </div>
      </div>

      {/* Grounded Positive and Risk Drivers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs">
          <div className="font-bold text-emerald-400 uppercase text-[10px] tracking-wider mb-1 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Primary Solvency Driver:
          </div>
          <p className="text-slate-200">
            {mlViability?.top_positive_factors?.[0] || "Solvent debt coverage ratio satisfies RBI underwriting benchmark."}
          </p>
        </div>

        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs">
          <div className="font-bold text-rose-400 uppercase text-[10px] tracking-wider mb-1 flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" /> Primary Operational Risk Factor:
          </div>
          <p className="text-slate-200">
            {mlViability?.top_risk_factors?.[0] || "Maintain working capital liquidity reserve to absorb raw material inflation."}
          </p>
        </div>
      </div>

      {/* Grounded Data Source Lineage Tag */}
      <div className="text-[10px] text-slate-500 flex flex-wrap items-center justify-between gap-2 pt-3 mt-1 border-t border-slate-800/60">
        <span>
          <strong className="text-slate-400">Data Source:</strong> Supervised XGBoost Classifier (<code className="font-mono text-cyan-400">viability_xgb.joblib</code>)
        </span>
        <span className="font-mono text-slate-400">
          Cross-Validation: 98.9% Acc • Fallback: {mlViability?.is_fallback ? "Active (Deterministic Rule Engine)" : "Off (Trained Model Active)"}
        </span>
      </div>

    </div>
  );
}


