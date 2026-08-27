import React from 'react';
import { ViabilityMeterCard } from './ViabilityMeterCard';
import { ExecutiveNarrativeCard } from './ExecutiveNarrativeCard';
import { CapitalReconciliationCard } from './CapitalReconciliationCard';
import { SchemeLeaderboardCard } from './SchemeLeaderboardCard';
import { CashflowProjectionsChart } from './CashflowProjectionsChart';
import { SwotMatrixCard } from './SwotMatrixCard';
import { RiskRadarCard } from './RiskRadarCard';
import { StatutoryChecklistCard } from './StatutoryChecklistCard';
import { Building2, MapPin, User, FileText, Sparkles } from 'lucide-react';

export function Dashboard({ reportData, onOpenDpr, onOpenWizard }) {
  if (!reportData) {
    return (
      <div className="max-w-4xl mx-auto py-16 px-4 text-center">
        <div className="glass-panel p-10 max-w-lg mx-auto space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 mx-auto flex items-center justify-center text-3xl">
            📊
          </div>
          <h3 className="text-xl font-bold font-outfit text-white">
            No Active Feasibility Assessment
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Click any of the SIH Jury Defense Benchmark Cases above, or launch the 6-Step Feasibility Wizard to generate an instant bank-ready credit appraisal.
          </p>
          <button
            onClick={onOpenWizard}
            className="inline-flex items-center gap-2 text-xs font-semibold text-white bg-gradient-to-r from-cyan-500 to-indigo-600 px-5 py-2.5 rounded-xl shadow-glow transition hover:shadow-glow-cyan"
          >
            <Sparkles className="w-4 h-4" />
            Launch Feasibility Wizard
          </button>
        </div>
      </div>
    );
  }

  const p = reportData.input_parameters || {};
  const ml = reportData.ml_viability || {};
  const fin = reportData.financial_analysis || {};
  const schemes = reportData.scheme_optimization || [];
  const synth = reportData.executive_synthesis || {};
  const swot = reportData.swot_matrix || {};
  const risks = reportData.risk_assessment || {};
  const pricing = reportData.pricing_recommendation || {};

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      
      {/* Enterprise Title Header Card */}
      <div className="glass-panel p-5 sm:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-outfit font-extrabold text-white">
              {p.enterprise_name || 'Enterprise Unit'}
            </h1>
            <span className="text-[11px] font-bold uppercase tracking-wider bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 px-2.5 py-0.5 rounded-full">
              {p.sector ? p.sector.toUpperCase() : 'MSME'}
            </span>
            <span className="text-[11px] font-bold uppercase tracking-wider bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 px-2.5 py-0.5 rounded-full">
              {p.business_category ? p.business_category.toUpperCase() : 'MANUFACTURING'}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-2">
            <span className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-cyan-400" />
              {p.village_name || 'Village'}, {p.district_name || 'District'}, {p.state_name || 'State'}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-indigo-400" />
              Promoter: <strong className="text-slate-200">{p.promoter_name || 'Promoter'}</strong> ({(p.promoter_category || 'general').toUpperCase()})
            </span>
            <span>•</span>
            <span>Report ID: <code className="font-mono text-cyan-400">{reportData.report_id}</code></span>
          </div>
        </div>

        <button
          onClick={onOpenDpr}
          className="flex items-center justify-center gap-2 text-xs font-bold text-white bg-gradient-to-r from-cyan-500 via-indigo-600 to-cyan-500 hover:from-cyan-400 hover:to-indigo-500 px-5 py-3 rounded-xl shadow-glow hover:shadow-glow-cyan transition shrink-0"
        >
          <FileText className="w-4 h-4" />
          <span>View Official 7-Section Bank DPR</span>
        </button>
      </div>

      {/* Viability Gauge Hero Card */}
      <ViabilityMeterCard mlViability={ml} dscrInfo={fin.dscr} />

      {/* Multi-Lingual Executive Synthesis Narrative */}
      <ExecutiveNarrativeCard synthesisData={synth} />

      {/* Capital Outlay & Means of Finance Reconciliation */}
      <CapitalReconciliationCard inputData={p} financialData={fin} schemeData={schemes} />

      {/* Government Scheme Optimization Leaderboard */}
      <SchemeLeaderboardCard schemes={schemes} />

      {/* 5-Year Cash Flow & Capacity Ramp Schedule */}
      <CashflowProjectionsChart inputData={p} financialData={fin} pricingData={pricing} />

      {/* Grounded SWOT Grid */}
      <SwotMatrixCard swotData={swot} />

      {/* 8-Point Quantified Risk Radar */}
      <RiskRadarCard riskData={risks} />

      {/* Statutory Bank Checklist */}
      <StatutoryChecklistCard />

    </div>
  );
}
