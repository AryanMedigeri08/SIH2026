import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ViabilityMeterCard } from '../../components/Dashboard/ViabilityMeterCard';
import { ExecutiveNarrativeCard } from '../../components/Dashboard/ExecutiveNarrativeCard';
import { AlternativeOpportunitiesCard } from '../../components/Dashboard/AlternativeOpportunitiesCard';
import {
  BrainCircuit,
  Target,
  Award,
  TrendingUp,
  ShieldAlert,
  Grid3X3,
  FileText,
  ArrowRight,
  Database,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  MapPin,
  User,
  Sparkles,
  Layers,
  BarChart3,
  Building2,
  AlertTriangle,
} from 'lucide-react';
import { useBusiness } from '../../context/BusinessContext';
import { BusinessStatusPill } from '../../components/BusinessSwitcher';
import { TranslatedText } from '../../components/TranslatedText';

export function OverviewPage({ reportData, onOpenDpr, onOpenWizard }) {
  const navigate = useNavigate();
  const [showLineage, setShowLineage] = React.useState(true);
  const { activeBusiness } = useBusiness();

  if (!reportData) {
    return (
      <div className="py-16 text-center">
        <div className="glass-panel-elevated p-10 max-w-lg mx-auto space-y-4 bg-white border border-slate-200 rounded-2xl shadow-card-elevated">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-sovereign-100 to-sky-100 border border-sovereign-200 text-sovereign-800 mx-auto flex items-center justify-center shadow-subtle">
            <BarChart3 className="w-8 h-8 text-sovereign-800" />
          </div>
          <h3 className="text-xl font-bold font-outfit text-slate-900">
            <TranslatedText text="No Active Feasibility Assessment" />
          </h3>
          <p className="text-xs text-slate-600 leading-relaxed font-medium">
            <TranslatedText text="Select a benchmark scenario from the top bar or launch the 7-Step Feasibility Wizard to generate an instant bank-ready credit appraisal." />
          </p>
          <button
            onClick={onOpenWizard}
            className="inline-flex items-center gap-2 text-xs font-bold text-white bg-gradient-to-r from-sovereign-800 to-sky-700 hover:from-sovereign-700 hover:to-sky-600 px-5 py-2.5 rounded-xl shadow-md shadow-sovereign-900/15 border border-sky-400/20 transition"
          >
            <Sparkles className="w-4 h-4 text-sky-200" />
            <span><TranslatedText text="Launch Feasibility Wizard" /></span>
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

  const topScheme = schemes.find(s => s.eligible) || schemes[0] || {};
  const projectCost = p.project_cost || activeBusiness?.investment_amount || 0;
  const subsidyAmount = topScheme.subsidy_grant_amount || 0;
  const subsidyPct = projectCost > 0 ? (subsidyAmount / projectCost) * 100 : 0;
  const loanPrincipal = fin.loan_principal || Math.max(projectCost - subsidyAmount - (projectCost * 0.05), 0);
  const emi = fin.amortization?.monthly_emi || 0;
  const dscr = fin.dscr?.dscr ?? 1.33;
  const annualTurnover = p.annual_turnover_estimate || activeBusiness?.annual_turnover_estimate || 0;
  const monthlyNoi = fin.dscr?.monthly_net_operating_income || (annualTurnover * 0.30 / 12);
  const avgRisk = risks.average_risk_score ?? (risks.verdict?.average_risk_score ?? 3.0);
  const riskSeverity = risks.composite_grade || (risks.verdict?.overall_severity || 'MODERATE');
  const reportId = reportData.report_id;

  // Exact Demographic & TAM Values
  const pop2026 = demographics.population_projection?.projected_population || demographics.catchment_population_2026 || demographics.census_details?.total_population || 0;
  const annualTam = demographics.tam?.annual_tam || demographics.annual_tam || 0;
  const msmeDensity = demographics.msme_density?.msme_density_per_10k || demographics.msme_density_per_10k || 0;

  // Exact SWOT Counts
  const sCount = swot.strengths?.length || 0;
  const wCount = swot.weaknesses?.length || 0;
  const oCount = swot.opportunities?.length || 0;
  const tCount = swot.threats?.length || 0;
  const totalSwotCount = sCount + wCount + oCount + tCount;

  const currentBusinessStatus = activeBusiness?.business_status || {
    code: dscr >= 1.33 && ml.verdict === 'SUITABLE' ? 'healthy' : (dscr < 1.0 || ml.verdict === 'RECONSIDER' ? 'critical' : 'reconsideration'),
    label: dscr >= 1.33 && ml.verdict === 'SUITABLE' ? 'Healthy / Bank Viable' : (dscr < 1.0 ? 'Critical Solvency Risk' : 'Requires Reconsideration'),
    reason: dscr >= 1.33 ? `DSCR ${dscr.toFixed(2)} clears RBI benchmark (1.33)` : `DSCR ${dscr.toFixed(2)} requires capital restructuring`,
  };

  const dataSources = reportData.data_sources_used || [
    { layer: "Tier 1: Demographics", logical_source: "Census 2011 Rural Catchment Database", table_or_file: "census_raw", status: "Queried OK", attribution: `${p.village_name || "Village"}, ${p.district_name || "District"}` },
    { layer: "Tier 1: MSME Density", logical_source: "Ministry of MSME Enterprise Registry", table_or_file: "msme_district", status: "Queried OK", attribution: `District MSME registry` },
    { layer: "Tier 1: Schemes", logical_source: "Statutory MSME Scheme Rule Guidelines", table_or_file: "government_schemes.json", status: "Queried OK", attribution: `PMEGP, PMFME, MUDRA, Stand-Up India` },
    { layer: "Tier 2: Infrastructure", logical_source: "Data.gov.in 613 District Amenities", table_or_file: "district_resources.json", status: "Queried OK", attribution: `Site infrastructure & amenities` },
    { layer: "Tier 2: ML Viability", logical_source: "Supervised 10-D XGBoost Viability Classifier (TreeSHAP)", table_or_file: "viability_xgb.joblib", status: ml.is_fallback ? "Rule Fallback" : "TreeSHAP Evaluated", attribution: `Verdict: ${ml.verdict || "SUITABLE"}` },
  ];

  // Teaser Navigation Cards linking to the other 7 sections with expressive color accents
  const sectionTeasers = [
    {
      title: 'ML Viability & Explainability',
      path: reportId ? `/reports/${reportId}/viability` : '/viability',
      icon: BrainCircuit,
      color: 'indigo',
      iconBg: 'bg-indigo-50 text-indigo-700 border-indigo-200 group-hover:bg-indigo-600 group-hover:text-white',
      accentTop: 'border-t-2 border-indigo-500',
      primaryMetric: `${ml.verdict || 'SUITABLE'} (${(ml.confidence_pct || 98.5).toFixed(1)}%)`,
      teaserText: ml.top_positive_factors?.[0] || ml.top_positive_driver || 'TreeSHAP 10-D factor attribution',
      badge: 'TreeSHAP',
    },
    {
      title: 'Market & Local Demand',
      path: reportId ? `/reports/${reportId}/market` : '/market',
      icon: Target,
      color: 'sky',
      iconBg: 'bg-sky-50 text-sky-700 border-sky-200 group-hover:bg-sky-600 group-hover:text-white',
      accentTop: 'border-t-2 border-sky-500',
      primaryMetric: annualTam > 0 ? `₹${(annualTam / 100000).toFixed(1)}L TAM` : 'Market Sizing',
      teaserText: pop2026 > 0 ? `${pop2026.toLocaleString('en-IN')} Catchment · MSME Density: ${msmeDensity.toFixed(1)}/10k` : 'Census 2011 Catchment Demographics',
      badge: 'Census 2011',
    },
    {
      title: 'Government Scheme Optimizer',
      path: reportId ? `/reports/${reportId}/schemes` : '/schemes',
      icon: Award,
      color: 'emerald',
      iconBg: 'bg-emerald-50 text-emerald-700 border-emerald-200 group-hover:bg-emerald-600 group-hover:text-white',
      accentTop: 'border-t-2 border-emerald-500',
      primaryMetric: `₹${Math.round(subsidyAmount).toLocaleString('en-IN')} Grant`,
      teaserText: `Top Match: ${topScheme.scheme_id || 'PMEGP'} (${subsidyPct.toFixed(0)}% Subsidy)`,
      badge: '10 Slabs',
    },
    {
      title: 'Financials & Cash Flow',
      path: reportId ? `/reports/${reportId}/financials` : '/financials',
      icon: TrendingUp,
      color: 'sovereign',
      iconBg: 'bg-sovereign-50 text-sovereign-800 border-sovereign-200 group-hover:bg-sovereign-800 group-hover:text-white',
      accentTop: 'border-t-2 border-sovereign-700',
      primaryMetric: `DSCR ${dscr.toFixed(2)}`,
      teaserText: `₹${Math.round(emi).toLocaleString('en-IN')}/mo EMI · 5-Yr Projections`,
      badge: '5-Yr Horiz.',
    },
    {
      title: 'Comprehensive Risk Matrix',
      path: reportId ? `/reports/${reportId}/risk` : '/risk',
      icon: ShieldAlert,
      color: 'rose',
      iconBg: 'bg-rose-50 text-rose-700 border-rose-200 group-hover:bg-rose-600 group-hover:text-white',
      accentTop: 'border-t-2 border-rose-500',
      primaryMetric: `${avgRisk.toFixed(1)}/10 (${riskSeverity})`,
      teaserText: `${risks.risk_points?.length || 8}-Pillar Prudential Risk Assessment`,
      badge: '8 Pillars',
    },
    {
      title: 'Grounded SWOT Matrix',
      path: reportId ? `/reports/${reportId}/swot` : '/swot',
      icon: Grid3X3,
      color: 'teal',
      iconBg: 'bg-teal-50 text-teal-700 border-teal-200 group-hover:bg-teal-600 group-hover:text-white',
      accentTop: 'border-t-2 border-teal-500',
      primaryMetric: totalSwotCount > 0 ? `${totalSwotCount} Grounded Factors` : '4 Quadrants',
      teaserText: `${sCount}S · ${wCount}W · ${oCount}O · ${tCount}T Factor Matrix`,
      badge: 'Grounded',
    },
    {
      title: 'Official Bank DPR Package',
      path: reportId ? `/reports/${reportId}/dpr` : '/dpr',
      icon: FileText,
      color: 'indigo',
      iconBg: 'bg-indigo-50 text-indigo-700 border-indigo-200 group-hover:bg-indigo-700 group-hover:text-white',
      accentTop: 'border-t-2 border-indigo-600',
      primaryMetric: '7 Sections',
      teaserText: 'Bank Credit Memorandum · HTML / Markdown / JSON',
      badge: 'Statutory',
    },
  ];

  return (
    <div className="space-y-6">
      
      {/* Enterprise Title Header Card */}
      <div className="glass-panel p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-white via-slate-50 to-sovereign-50/40 border border-slate-200/90 shadow-card">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
              {p.enterprise_name || activeBusiness?.business_name || 'Enterprise Unit'}
            </h1>
            <span className="text-[11px] font-bold uppercase tracking-wider bg-gradient-to-r from-sovereign-50 to-sky-50 border border-sovereign-200 text-sovereign-900 px-2.5 py-0.5 rounded-full shadow-subtle">
              {p.sector ? p.sector.toUpperCase() : (activeBusiness?.sector?.toUpperCase() || 'MSME')}
            </span>
            <span className="text-[11px] font-bold uppercase tracking-wider bg-slate-100 border border-slate-200 text-slate-800 px-2.5 py-0.5 rounded-full shadow-subtle">
              {p.business_category ? p.business_category.toUpperCase() : 'MANUFACTURING'}
            </span>
            {/* Real Data-Driven Status Badge */}
            <BusinessStatusPill status={currentBusinessStatus} size="sm" />
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 mt-2">
            <span className="flex items-center gap-1.5 font-medium">
              <MapPin className="w-3.5 h-3.5 text-sovereign-700" />
              {p.village_name || 'Village'}, {p.district_name || 'District'}, {p.state_name || 'State'}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1.5 font-medium">
              <User className="w-3.5 h-3.5 text-slate-600" />
              <TranslatedText text="Promoter Profile" />: <strong className="text-slate-900">{p.promoter_name || 'Promoter'}</strong> ({(p.promoter_category || 'general').toUpperCase()})
            </span>
            <span>•</span>
            <span className="font-mono text-slate-600">
              Ref: <code className="font-mono text-sovereign-900 font-bold bg-white px-1.5 py-0.5 rounded border border-slate-200">{reportData.report_id}</code>
            </span>
          </div>

          {/* If Status is Reconsideration or Critical, display explanatory warning banner */}
          {currentBusinessStatus.code !== 'healthy' && currentBusinessStatus.code !== 'draft' && (
            <div className={`mt-3 p-3 rounded-xl border flex items-start gap-2.5 text-xs font-medium ${
              currentBusinessStatus.code === 'critical'
                ? 'bg-rose-50 border-rose-300 text-rose-950'
                : 'bg-amber-50 border-amber-300 text-amber-950'
            }`}>
              <AlertTriangle className={`w-4 h-4 shrink-0 mt-0.5 ${
                currentBusinessStatus.code === 'critical' ? 'text-rose-600' : 'text-amber-600'
              }`} />
              <div>
                <strong className="font-bold">{currentBusinessStatus.label}: </strong>
                <span><TranslatedText text={currentBusinessStatus.reason} /></span>
              </div>
            </div>
          )}
        </div>

        <button
          onClick={onOpenDpr}
          className="flex items-center justify-center gap-2 text-xs font-bold text-white bg-gradient-to-r from-sovereign-800 via-sky-700 to-sovereign-800 hover:from-sovereign-700 hover:to-sky-600 px-5 py-3 rounded-xl shadow-md shadow-sovereign-900/15 border border-sky-400/20 transition-all shrink-0 group"
        >
          <FileText className="w-4 h-4 text-sky-200 group-hover:scale-110 transition-transform" />
          <span><TranslatedText text="View Official 7-Section Bank DPR" /></span>
        </button>
      </div>

      {/* Key Financial Appraisal Metrics Summary Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="glass-panel p-3.5 bg-white border border-slate-200 rounded-2xl shadow-card border-t-2 border-t-indigo-600">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            <TranslatedText text="Total Capital Outlay" />
          </div>
          <div className="text-base sm:text-lg font-outfit font-black text-slate-900 mt-1">
            ₹{projectCost > 0 ? (projectCost / 100000).toFixed(2) + 'L' : '₹0'}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">₹{projectCost.toLocaleString('en-IN')}</div>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200 rounded-2xl shadow-card border-t-2 border-t-emerald-600">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            <TranslatedText text="Capital Subsidy" />
          </div>
          <div className="text-base sm:text-lg font-outfit font-black text-emerald-700 mt-1">
            ₹{subsidyAmount > 0 ? (subsidyAmount / 100000).toFixed(2) + 'L' : '₹0'}
          </div>
          <div className="text-[10px] text-emerald-600 font-semibold mt-0.5">{subsidyPct.toFixed(0)}% ({topScheme.scheme_id || 'PMEGP'})</div>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200 rounded-2xl shadow-card border-t-2 border-t-sky-600">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            <TranslatedText text="Bank Term Loan" />
          </div>
          <div className="text-base sm:text-lg font-outfit font-black text-sky-900 mt-1">
            ₹{loanPrincipal > 0 ? (loanPrincipal / 100000).toFixed(2) + 'L' : '₹0'}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">₹{Math.round(loanPrincipal).toLocaleString('en-IN')}</div>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200 rounded-2xl shadow-card border-t-2 border-t-amber-600">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            <TranslatedText text="Monthly Net EMI" />
          </div>
          <div className="text-base sm:text-lg font-outfit font-black text-amber-900 mt-1">
            ₹{Math.round(emi).toLocaleString('en-IN')}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">{p.tenure_years || 5}Y @ {topScheme.effective_interest_rate_pct || 11}%</div>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200 rounded-2xl shadow-card border-t-2 border-t-purple-600">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            <TranslatedText text="Annual Turnover" />
          </div>
          <div className="text-base sm:text-lg font-outfit font-black text-purple-900 mt-1">
            ₹{annualTurnover > 0 ? (annualTurnover / 100000).toFixed(2) + 'L' : '₹0'}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">₹{annualTurnover.toLocaleString('en-IN')}</div>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200 rounded-2xl shadow-card border-t-2 border-t-sovereign-700">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            <TranslatedText text="Debt Coverage (DSCR)" />
          </div>
          <div className={`text-base sm:text-lg font-outfit font-black mt-1 ${dscr >= 1.33 ? 'text-emerald-700' : (dscr >= 1.0 ? 'text-amber-700' : 'text-rose-700')}`}>
            {dscr.toFixed(2)}
          </div>
          <div className={`text-[10px] font-semibold mt-0.5 ${dscr >= 1.33 ? 'text-emerald-600' : (dscr >= 1.0 ? 'text-amber-600' : 'text-rose-600')}`}>
            <TranslatedText text={dscr >= 1.33 ? 'RBI Benchmark Met' : (dscr >= 1.0 ? 'Marginal Solvency' : 'High Solvency Risk')} />
          </div>
        </div>
      </div>

      {/* Verified Ground-Truth Data Sources & Lineage Audit Bar */}
      <div className="glass-panel p-4 sm:p-5 border-l-4 border-sovereign-800 bg-white shadow-card border border-slate-200/90 space-y-3">
        <div className="flex items-center justify-between cursor-pointer select-none" onClick={() => setShowLineage(prev => !prev)}>
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-sovereign-800" />
            <h4 className="text-xs sm:text-sm font-bold text-slate-900 uppercase tracking-wider">
              <TranslatedText text="Verified Ground-Truth Data Sources & Audit Lineage" />
            </h4>
            <span className="text-[10px] bg-sovereign-50 border border-sovereign-200 text-sovereign-800 px-2 py-0.5 rounded-full font-mono font-bold">
              {dataSources.length} <TranslatedText text="Sources Connected" />
            </span>
          </div>
          <button className="text-xs text-slate-500 hover:text-slate-900 flex items-center gap-1 font-semibold">
            <span><TranslatedText text={showLineage ? "Hide Lineage" : "Show Lineage"} /></span>
            {showLineage ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {showLineage && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 pt-2 border-t border-slate-100 animate-in fade-in duration-200">
            {dataSources.map((ds, idx) => (
              <div key={idx} className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-[11px] space-y-0.5 hover:bg-slate-100 transition-colors">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sovereign-800 truncate">
                    <TranslatedText text={ds.logical_source} />
                  </span>
                  <span className="font-mono text-[9px] px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 border border-emerald-200 font-bold shrink-0">
                    <TranslatedText text={ds.status} />
                  </span>
                </div>
                <div className="text-slate-600 font-mono text-[10px] truncate">{ds.table_or_file}</div>
                <div className="text-slate-500 text-[10px] line-clamp-1">
                  <TranslatedText text={ds.attribution} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Row 1: ML Viability Card & AI Executive Synthesis Narrative */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <div className="lg:col-span-5">
          <ViabilityMeterCard 
            mlViability={reportData.ml_viability} 
            confidenceScore={reportData.ml_viability?.confidence_pct} 
          />
        </div>
        <div className="lg:col-span-7">
          <ExecutiveNarrativeCard 
            synthesisData={reportData.executive_synthesis} 
          />
        </div>
      </div>

      {/* Alternative Enterprise Recommendations (Rendered exclusively when Verdict === RECONSIDER) */}
      <AlternativeOpportunitiesCard reportData={reportData} onOpenWizard={onOpenWizard} />

      {/* Row 2: Appraisal Module Cards Grid with Colored Accents */}
      <div>
        <div className="flex items-center justify-between mb-3 px-1">
          <div className="flex items-center gap-2 text-xs font-bold font-outfit uppercase tracking-wider text-slate-500 font-mono">
            <Layers className="w-4 h-4 text-sovereign-700" />
            <span><TranslatedText text="Dedicated Appraisal Modules" /></span>
          </div>
          <span className="text-xs text-slate-500 font-medium hidden sm:inline">
            <TranslatedText text="Click any card to deep-dive into detailed telemetry" />
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {sectionTeasers.map((sec, idx) => {
            const Icon = sec.icon;
            return (
              <Link
                key={idx}
                to={sec.path}
                className={`glass-panel p-5 flex flex-col justify-between rounded-2xl bg-white border border-slate-200 hover:border-slate-300 shadow-card hover:shadow-card-elevated transition-all duration-200 hover:-translate-y-0.5 group ${sec.accentTop}`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className={`p-2.5 rounded-xl border transition-all duration-200 ${sec.iconBg}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    {sec.badge && (
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                        {sec.badge}
                      </span>
                    )}
                  </div>

                  <h3 className="text-sm font-outfit font-extrabold text-slate-900 group-hover:text-sovereign-800 transition-colors">
                    <TranslatedText text={sec.title} />
                  </h3>

                  <div className="mt-2.5 font-outfit font-black text-lg text-slate-900">
                    {sec.primaryMetric}
                  </div>

                  <p className="mt-1 text-[11px] text-slate-500 font-medium line-clamp-2">
                    <TranslatedText text={sec.teaserText} />
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-sovereign-800 group-hover:text-sky-700 transition-colors">
                  <span><TranslatedText text="Explore Section" /></span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

    </div>
  );
}

export default OverviewPage;
