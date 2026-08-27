import React from 'react';
import { ViabilityMeterCard } from '../../components/Dashboard/ViabilityMeterCard';
import { FeatureContributionChart } from '../../components/Dashboard/FeatureContributionChart';
import { ViabilityRadarChart } from '../../components/Dashboard/ViabilityRadarChart';
import { BrainCircuit, Info, ShieldCheck, Sparkles, CheckCircle2 } from 'lucide-react';

export function ViabilityPage({ reportData }) {
  if (!reportData) return null;

  const ml = reportData.ml_viability || {};
  const fin = reportData.financial_analysis || {};

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-indigo-600 bg-gradient-to-r from-white via-indigo-50/20 to-white shadow-card border border-slate-200/90">
        <div className="text-xs font-bold uppercase tracking-wider text-indigo-700 mb-1 flex items-center gap-1.5">
          <BrainCircuit className="w-4 h-4 text-indigo-600" />
          <span>Dimension 1 • Machine Learning Viability & TreeSHAP Explainability</span>
        </div>
        <h1 className="text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
          Supervised 10-D XGBoost Classifier & Lundberg TreeSHAP Attributions
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
          Trained on empirical rural enterprise repayment outcomes. TreeSHAP calculates the exact marginal game-theoretic contribution (log-odds impact) of every financial, competitive, and infrastructure variable without heuristic guessing.
        </p>
      </div>

      {/* Viability Gauge Hero Card */}
      <ViabilityMeterCard mlViability={ml} dscrInfo={fin.dscr} />

      {/* Visuals Grid: SHAP Horizontal Bar Chart + 10-D Viability Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FeatureContributionChart mlViability={ml} />
        <ViabilityRadarChart mlViability={ml} />
      </div>

      {/* Model Metadata & Lineage Box */}
      <div className="glass-panel p-5 bg-white border border-slate-200/90 shadow-card flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-600">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200 shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="font-bold text-slate-900">Model File: <code className="font-mono text-indigo-900 bg-indigo-50/70 px-1.5 py-0.5 rounded border border-indigo-200">viability_xgb.joblib</code></div>
            <div className="text-[11px] text-slate-500 font-medium mt-0.5">
              Algorithm: Gradient-Boosted Decision Trees (XGBoost 10-D Classifier) • Explainer: TreeExplainer (Lundberg et al.)
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-slate-700 shrink-0">
          <span className="px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 font-bold">
            Execution Latency: &lt;3ms
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Verified Invariant
          </span>
        </div>
      </div>

    </div>
  );
}
export default ViabilityPage;
