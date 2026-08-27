import React from 'react';
import { RiskRadarCard } from '../../components/Dashboard/RiskRadarCard';
import { ShieldAlert, ShieldCheck, Database, AlertTriangle } from 'lucide-react';

export function RiskAssessmentPage({ reportData }) {
  if (!reportData) return null;

  const risks = reportData.risk_assessment || {};

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-rose-600 bg-gradient-to-r from-white via-rose-50/20 to-white shadow-card border border-slate-200/90">
        <div className="text-xs font-bold uppercase tracking-wider text-rose-700 mb-1 flex items-center gap-1.5">
          <ShieldAlert className="w-4 h-4 text-rose-600" />
          <span>Dimension 5 • Quantified Commercial & Operational Risk Evaluation</span>
        </div>
        <h1 className="text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
          8-Point Risk Radar Matrix & Financial Contingency Buffers
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
          Evaluated across 8 operational pillars: Raw Material Volatility, Power Reliability, Debt Repayment Stress, Market Saturation, Logistics Friction, Promoter Experience, Regulatory Compliance, and Environmental Shocks.
        </p>
      </div>

      {/* 8-Point Risk Radar Card Component */}
      <RiskRadarCard riskData={risks} />

    </div>
  );
}
export default RiskAssessmentPage;
