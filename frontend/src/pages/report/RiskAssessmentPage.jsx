import React from 'react';
import { RiskRadarCard } from '../../components/Dashboard/RiskRadarCard';
import { ShieldAlert, ShieldCheck, Database, AlertTriangle, Coins, Activity, CheckCircle2 } from 'lucide-react';
import { TranslatedText } from '../../components/TranslatedText';

export function RiskAssessmentPage({ reportData }) {
  if (!reportData) return null;

  const risks = reportData.risk_assessment || {};
  const riskPoints = risks.risk_points || [];
  const verdict = risks.verdict || {};
  const avgScore = Number(verdict.average_risk_score ?? risks.average_risk_score ?? 3.2);
  const severity = verdict.overall_severity || risks.composite_grade || 'MODERATE';

  const highRiskCount = riskPoints.filter(r => r.severity === 'HIGH' || r.severity === 'SEVERE').length;
  const lowRiskCount = riskPoints.filter(r => r.severity === 'LOW').length;
  const totalRupeeBuffer = riskPoints.reduce((acc, r) => acc + (Number(r.rupee_buffer) || 0), 0);

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-rose-600 bg-gradient-to-r from-white via-rose-50/20 to-white shadow-card border border-slate-200/90">
        <div className="text-xs font-bold uppercase tracking-wider text-rose-700 mb-1 flex items-center gap-1.5">
          <ShieldAlert className="w-4 h-4 text-rose-600" />
          <span><TranslatedText text="Dimension 5 • Quantified Commercial & Operational Risk Evaluation" /></span>
        </div>
        <h1 className="text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
          <TranslatedText text="8-Point Risk Radar Matrix & Financial Contingency Buffers" />
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
          <TranslatedText text="Evaluated across 8 operational pillars: Raw Material Volatility, Power Reliability, Debt Repayment Stress, Market Saturation, Logistics Friction, Promoter Experience, Regulatory Compliance, and Environmental Shocks." />
        </p>
      </div>

      {/* Risk Appraisal Telemetry Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-panel p-4 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold uppercase tracking-wider">
            <Activity className="w-3.5 h-3.5 text-rose-600" />
            <span><TranslatedText text="Composite Risk Score" /></span>
          </div>
          <strong className="text-xl sm:text-2xl font-mono font-extrabold text-slate-900 block mt-1">
            {avgScore.toFixed(2)} / 10
          </strong>
          <span className={`text-[10px] font-bold mt-0.5 block ${
            severity === 'LOW' ? 'text-emerald-700' : severity === 'MODERATE' ? 'text-amber-700' : 'text-rose-700'
          }`}>
            <TranslatedText text={severity} /> <TranslatedText text="Overall Severity" />
          </span>
        </div>

        <div className="glass-panel p-4 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold uppercase tracking-wider">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span><TranslatedText text="Low Risk Pillars" /></span>
          </div>
          <strong className="text-xl sm:text-2xl font-mono font-extrabold text-emerald-700 block mt-1">
            {lowRiskCount} of {riskPoints.length || 8}
          </strong>
          <span className="text-[10px] text-slate-500 mt-0.5 block font-medium">
            <TranslatedText text="Safe Operational Baseline" />
          </span>
        </div>

        <div className="glass-panel p-4 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold uppercase tracking-wider">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span><TranslatedText text="Attention Items" /></span>
          </div>
          <strong className="text-xl sm:text-2xl font-mono font-extrabold text-amber-800 block mt-1">
            {highRiskCount} <TranslatedText text="Pillars" />
          </strong>
          <span className="text-[10px] text-slate-500 mt-0.5 block font-medium">
            <TranslatedText text="High / Severe Attention Items" />
          </span>
        </div>

        <div className="glass-panel p-4 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-bold uppercase tracking-wider">
            <Coins className="w-3.5 h-3.5 text-sovereign-700" />
            <span><TranslatedText text="Contingency Buffer" /></span>
          </div>
          <strong className="text-xl sm:text-2xl font-mono font-extrabold text-sovereign-900 block mt-1">
            ₹{Math.round(totalRupeeBuffer).toLocaleString('en-IN')}
          </strong>
          <span className="text-[10px] text-slate-500 mt-0.5 block font-medium">
            <TranslatedText text="Total Recommended Reserve" />
          </span>
        </div>
      </div>

      {/* 8-Point Risk Radar Card Component */}
      <RiskRadarCard riskData={risks} />

    </div>
  );
}
export default RiskAssessmentPage;
