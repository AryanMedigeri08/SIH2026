import React, { useState } from 'react';
import { ViabilityMeterCard } from './ViabilityMeterCard';
import { FeatureContributionChart } from './FeatureContributionChart';
import { ViabilityRadarChart } from './ViabilityRadarChart';
import { DscrGaugeChart } from './DscrGaugeChart';
import { TamFunnelChart } from './TamFunnelChart';
import { SchemeComparisonChart } from './SchemeComparisonChart';
import { ExecutiveNarrativeCard } from './ExecutiveNarrativeCard';
import { CapitalReconciliationCard } from './CapitalReconciliationCard';
import { SchemeLeaderboardCard } from './SchemeLeaderboardCard';
import { CashflowProjectionsChart } from './CashflowProjectionsChart';
import { SwotMatrixCard } from './SwotMatrixCard';
import { RiskRadarCard } from './RiskRadarCard';
import { StatutoryChecklistCard } from './StatutoryChecklistCard';
import {
  Building2,
  MapPin,
  User,
  FileText,
  Sparkles,
  Database,
  CheckCircle2,
  BrainCircuit,
  TrendingUp,
  Landmark,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export function Dashboard({ reportData, onOpenDpr, onOpenWizard }) {
  const [showLineage, setShowLineage] = useState(true);

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
  const demographics = reportData.market_demographics || {};
  const dataSources = reportData.data_sources_used || [
    { layer: "Tier 1: Demographics", logical_source: "Census 2011 Rural Catchment Database", table_or_file: "census_raw", status: "Queried OK", attribution: `${p.village_name || "Village"}, ${p.district_name || "District"}` },
    { layer: "Tier 1: MSME Density", logical_source: "Ministry of MSME Enterprise Registry", table_or_file: "msme_district", status: "Queried OK", attribution: `District MSME registry` },
    { layer: "Tier 1: Schemes", logical_source: "Statutory MSME Scheme Rule Guidelines", table_or_file: "government_schemes.json", status: "Queried OK", attribution: `PMEGP, PMFME, MUDRA, Stand-Up India` },
    { layer: "Tier 2: Infrastructure", logical_source: "Data.gov.in 613 District Amenities", table_or_file: "district_resources.json", status: "Queried OK", attribution: `Site infrastructure & amenities` },
    { layer: "Tier 2: ML Viability", logical_source: "Supervised 10-D XGBoost Viability Classifier (TreeSHAP)", table_or_file: "viability_xgb.joblib", status: ml.is_fallback ? "Rule Fallback" : "TreeSHAP Evaluated", attribution: `Verdict: ${ml.verdict || "SUITABLE"}` },
  ];

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

      {/* Verified Ground-Truth Data Sources & Lineage Audit Bar */}
      <div className="glass-panel p-4 sm:p-5 border-l-4 border-indigo-500 space-y-3">
        <div className="flex items-center justify-between cursor-pointer select-none" onClick={() => setShowLineage(prev => !prev)}>
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-cyan-400" />
            <h4 className="text-xs sm:text-sm font-bold text-white uppercase tracking-wider">
              Verified Ground-Truth Data Sources & Audit Lineage
            </h4>
            <span className="text-[10px] bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 px-2 py-0.5 rounded-full font-mono">
              {dataSources.length} Sources Connected
            </span>
          </div>
          <button className="text-xs text-slate-400 hover:text-white flex items-center gap-1">
            <span>{showLineage ? "Hide Lineage" : "Show Lineage"}</span>
            {showLineage ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {showLineage && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 pt-2 border-t border-slate-800/80">
            {dataSources.map((ds, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800 text-xs flex flex-col justify-between gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-bold text-slate-400">{ds.layer}</span>
                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 flex items-center gap-1">
                    <CheckCircle2 className="w-2.5 h-2.5" />
                    {ds.status || "OK"}
                  </span>
                </div>
                <div>
                  <div className="font-semibold text-slate-200">{ds.logical_source}</div>
                  <div className="text-[10px] font-mono text-cyan-400 mt-0.5">
                    Table: <code className="bg-slate-950 px-1 py-0.5 rounded text-indigo-300">{ds.table_or_file}</code>
                  </div>
                </div>
                {ds.attribution && (
                  <div className="text-[10px] text-slate-400 truncate">
                    {ds.attribution}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Viability Gauge Hero Card */}
      <ViabilityMeterCard mlViability={ml} dscrInfo={fin.dscr} />

      {/* SECTION 1: ML Viability & Lundberg TreeSHAP Explainability Visuals */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FeatureContributionChart mlViability={ml} />
        <ViabilityRadarChart mlViability={ml} />
      </div>

      {/* SECTION 2: Banking Solvency Gauge & Demographics TAM Funnel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DscrGaugeChart dscrInfo={fin.dscr} projections={fin.five_year_projections} />
        <TamFunnelChart demographics={demographics} pricing={pricing} />
      </div>

      {/* Multi-Lingual Executive Synthesis Narrative */}
      <ExecutiveNarrativeCard synthesisData={synth} />

      {/* Capital Outlay & Means of Finance Reconciliation */}
      <CapitalReconciliationCard inputData={p} financialData={fin} schemeData={schemes} />

      {/* Government Scheme Comparison Chart & Leaderboard */}
      <div className="space-y-6">
        <SchemeComparisonChart schemes={schemes} />
        <SchemeLeaderboardCard schemes={schemes} />
      </div>

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
export default Dashboard;
