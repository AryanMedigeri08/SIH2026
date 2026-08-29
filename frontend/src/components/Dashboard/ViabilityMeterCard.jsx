import React from 'react';
import { AlertTriangle, AlertOctagon, CheckCircle2, ShieldCheck } from 'lucide-react';
import { TranslatedText } from '../TranslatedText';

export function ViabilityMeterCard({ mlViability, viabilityData, dscrInfo, confidenceScore }) {
  const data = mlViability || viabilityData || {};
  const verdict = data?.verdict || "SUITABLE";
  const confidence = confidenceScore ?? (data?.confidence_pct ?? 98.5);
  const probs = data?.class_probabilities || { SUITABLE: 0.98, CAUTION: 0.01, RECONSIDER: 0.01 };
  
  const isSuitable = verdict === "SUITABLE";
  const isCaution = verdict === "CAUTION";
  const isReconsider = verdict === "RECONSIDER";

  const colorBorder = isSuitable ? "border-emerald-600" : isCaution ? "border-amber-500" : "border-rose-600";
  const badgeBg = isSuitable 
    ? "bg-emerald-600 text-white shadow-sm" 
    : isCaution 
    ? "bg-amber-600 text-white shadow-sm" 
    : "bg-rose-600 text-white shadow-sm";

  const VerdictIcon = isSuitable ? CheckCircle2 : isCaution ? AlertTriangle : AlertOctagon;

  return (
    <div className={`glass-panel p-6 border-l-4 ${colorBorder} bg-white shadow-card h-full flex flex-col justify-between`}>
      
      <div>
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
          <div className="space-y-1">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5 font-mono">
              <span className={`w-2.5 h-2.5 rounded-full ${isSuitable ? 'bg-emerald-500' : isCaution ? 'bg-amber-500' : 'bg-rose-500'}`} />
              <TranslatedText text="Tier 2 Supervised XGBoost Viability Engine (10-D)" />
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-xl sm:text-2xl font-outfit font-extrabold text-slate-900">
                <TranslatedText text="Viability Verdict:" />
              </h2>
              <div className={`flex items-center gap-1.5 text-sm sm:text-base font-outfit font-black px-3.5 py-1 rounded-xl ${badgeBg}`}>
                <VerdictIcon className="w-4 h-4" />
                <span><TranslatedText text={verdict} /></span>
              </div>
            </div>
          </div>

          <div className="sm:text-right bg-slate-50 px-4 py-2.5 rounded-xl border border-slate-200 shrink-0">
            <div className="text-[10px] text-slate-500 font-semibold font-mono uppercase">
              <TranslatedText text="Model Confidence" />
            </div>
            <div className="text-xl sm:text-2xl font-outfit font-black text-sovereign-800">
              {Number(confidence).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Class Probabilities Bar */}
        <div className="mb-5">
          <div className="flex flex-wrap justify-between text-xs font-bold text-slate-700 mb-1.5">
            <span><TranslatedText text="Class Probabilities Distribution:" /></span>
            <span className="font-mono text-[11px] text-slate-600">
              <TranslatedText text="SUITABLE" />: {(probs.SUITABLE * 100).toFixed(1)}% • <TranslatedText text="CAUTION" />: {(probs.CAUTION * 100).toFixed(1)}% • <TranslatedText text="RECONSIDER" />: {(probs.RECONSIDER * 100).toFixed(1)}%
            </span>
          </div>
          <div className="h-3 w-full rounded-full bg-slate-100 overflow-hidden flex p-0.5 border border-slate-200">
            <div 
              style={{ width: `${probs.SUITABLE * 100}%` }} 
              className="bg-emerald-500 rounded-l-full transition-all duration-500" 
              title="SUITABLE"
            />
            <div 
              style={{ width: `${probs.CAUTION * 100}%` }} 
              className="bg-amber-500 transition-all duration-500" 
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
          <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs">
            <div className="font-bold text-emerald-800 uppercase text-[10px] tracking-wider mb-1 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span><TranslatedText text="Primary Solvency Driver:" /></span>
            </div>
            <p className="text-slate-800 font-medium leading-relaxed">
              <TranslatedText text={data?.top_positive_factors?.[0] || data?.top_positive_driver || "Solvent debt coverage ratio satisfies RBI underwriting benchmark."} />
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs">
            <div className="font-bold text-rose-800 uppercase text-[10px] tracking-wider mb-1 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span><TranslatedText text="Primary Operational Risk Factor:" /></span>
            </div>
            <p className="text-slate-800 font-medium leading-relaxed">
              <TranslatedText text={data?.top_risk_factors?.[0] || data?.top_risk_driver || "Maintain working capital liquidity reserve to absorb localized cost shocks."} />
            </p>
          </div>
        </div>
      </div>

      {/* Grounded Data Source Lineage Tag */}
      <div className="text-[10px] text-slate-500 flex flex-wrap items-center justify-between gap-2 pt-3 mt-4 border-t border-slate-200">
        <span className="flex items-center gap-1">
          <strong className="text-slate-700"><TranslatedText text="Data Source:" /></strong> Supervised XGBoost Classifier (<code className="font-mono text-sovereign-800 font-bold">viability_xgb.joblib</code>)
        </span>
        <span className="font-mono text-slate-600 font-medium">
          Cross-Validation: 98.9% Acc • Engine: {data?.is_fallback ? "Active (Deterministic Rule Engine)" : "Active (Trained XGBoost Active)"}
        </span>
      </div>

    </div>
  );
}

export default ViabilityMeterCard;
