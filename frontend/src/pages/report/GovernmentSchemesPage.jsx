import React from 'react';
import { SchemeComparisonChart } from '../../components/Dashboard/SchemeComparisonChart';
import { SchemeLeaderboardCard } from '../../components/Dashboard/SchemeLeaderboardCard';
import { Award, ShieldCheck, CheckCircle2, ArrowRight } from 'lucide-react';

export function GovernmentSchemesPage({ reportData }) {
  if (!reportData) return null;

  const schemes = reportData.scheme_optimization || [];
  const topScheme = schemes.find(s => s.eligible) || schemes[0] || {};

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-emerald-600 bg-gradient-to-r from-white via-emerald-50/20 to-white shadow-card border border-slate-200/90">
        <div className="text-xs font-bold uppercase tracking-wider text-emerald-700 mb-1 flex items-center gap-1.5">
          <Award className="w-4 h-4 text-emerald-600" />
          <span>Dimension 3 • Statutory MSME Schemes & Incentive Optimization</span>
        </div>
        <h1 className="text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
          Central & State Scheme Ranking, Capital Subsidies & Official Portals
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
          Automatically evaluated against statutory MSME guidelines (PMEGP, PMFME, MUDRA, Stand-Up India, PM Vishwakarma, DAY-NRLM, AHIDF). Verified official government portal links are provided for each eligible incentive scheme.
        </p>
      </div>

      {/* Comparison Chart: Subsidy vs Interest */}
      <SchemeComparisonChart schemes={schemes} />

      {/* Ranked Scheme Leaderboard with Verified Official URLs */}
      <SchemeLeaderboardCard schemes={schemes} />

    </div>
  );
}
export default GovernmentSchemesPage;
