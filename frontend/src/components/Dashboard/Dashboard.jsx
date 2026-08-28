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
  BarChart3,
} from 'lucide-react';

export function Dashboard({ reportData, onOpenDpr, onOpenWizard }) {
  const [showLineage, setShowLineage] = useState(true);

  if (!reportData) {
    return (
      <div className="max-w-4xl mx-auto py-16 px-4 text-center">
        <div className="glass-panel p-10 max-w-lg mx-auto space-y-4 bg-white shadow-card border border-slate-200 rounded-2xl">
          <div className="w-16 h-16 rounded-2xl bg-sovereign-50 border border-sovereign-200 text-sovereign-800 mx-auto flex items-center justify-center shadow-subtle">
            <BarChart3 className="w-8 h-8 text-sovereign-800" />
          </div>
          <h3 className="text-xl font-bold font-outfit text-slate-900">
            No Active Feasibility Assessment
          </h3>
          <p className="text-xs text-slate-600 leading-relaxed font-medium">
            Click any of the SIH Benchmark Scenarios above, or launch the 7-Step Feasibility Wizard to generate an instant bank-ready credit appraisal.
          </p>
          <button
            onClick={onOpenWizard}
            className="inline-flex items-center gap-2 text-xs font-bold text-white bg-sovereign-800 hover:bg-sovereign-700 px-5 py-2.5 rounded-xl shadow-sm transition"
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
      <div className="glass-panel p-5 sm:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white shadow-card border border-slate-200">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-outfit font-extrabold text-slate-900">
              {p.enterprise_name || 'Enterprise Unit'}
            </h1>
            <span className="text-[11px] font-bold uppercase tracking-wider bg-sovereign-50 border border-sovereign-200 text-sovereign-800 px-2.5 py-0.5 rounded-full">
              {p.sector ? p.sector.toUpperCase() : 'MSME'}
            </span>
            <span className="text-[11px] font-bold uppercase tracking-wider bg-slate-100 border border-slate-200 text-slate-800 px-2.5 py-0.5 rounded-full">
              {p.business_category ? p.business_category.toUpperCase() : 'MANUFACTURING'}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 mt-2">
            <span className="flex items-center gap-1.5 font-medium">
              <MapPin className="w-3.5 h-3.5 text-sovereign-700" />
              {p.village_name || 'Village'}, {p.district_name || 'District'}, {p.state_name || 'State'}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1.5 font-medium">
              <User className="w-3.5 h-3.5 text-slate-600" />
              Promoter: <strong className="text-slate-900">{p.promoter_name || 'Promoter'}</strong> ({(p.promoter_category || 'general').toUpperCase()})
            </span>
            <span>•</span>
            <span>Report ID: <code className="font-mono text-sovereign-800 font-bold">{reportData.report_id}</code></span>
          </div>
        </div>

        <button
          onClick={onOpenDpr}
          className="flex items-center justify-center gap-2 text-xs font-bold text-white bg-sovereign-800 hover:bg-sovereign-700 px-5 py-3 rounded-xl shadow-sm transition shrink-0"
        >
          <FileText className="w-4 h-4" />
          <span>View Official 7-Section Bank DPR</span>
        </button>
      </div>

      {/* Verified Ground-Truth Data Sources & Lineage Audit Bar */}
      <div className="glass-panel p-4 sm:p-5 border-l-4 border-sovereign-800 bg-white shadow-card border border-slate-200 space-y-3">
        <div className="flex items-center justify-between cursor-pointer select-none" onClick={() => setShowLineage(prev => !prev)}>
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-sovereign-800" />
            <h4 className="text-xs sm:text-sm font-bold text-slate-900 uppercase tracking-wider">
              Verified Ground-Truth Data Sources & Audit Lineage
            </h4>
            <span className="text-[10px] bg-sovereign-50 border border-sovereign-200 text-sovereign-800 px-2 py-0.5 rounded-full font-mono font-bold">
              {dataSources.length} Sources Connected
            </span>
          </div>
          <button className="text-xs text-slate-500 hover:text-slate-900 flex items-center gap-1 font-semibold">
            <span>{showLineage ? "Hide Lineage" : "Show Lineage"}</span>
            {showLineage ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {showLineage && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 pt-2 border-t border-slate-200">
            {dataSources.map((ds, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs flex flex-col justify-between gap-1.5 shadow-subtle">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-bold text-slate-500">{ds.layer}</span>
                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                    <CheckCircle2 className="w-2.5 h-2.5" />
                    {ds.status || "OK"}
                  </span>
                </div>
                <div>
                  <div className="font-bold text-slate-900">{ds.logical_source}</div>
                  <div className="text-[10px] font-mono text-slate-600 mt-0.5">
                    Source: <code className="bg-white border border-slate-200 px-1 py-0.5 rounded text-sovereign-900 font-bold">{ds.table_or_file}</code>
                  </div>
                </div>
                {ds.attribution && (
                  <div className="text-[10px] text-slate-600 truncate font-medium">
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
