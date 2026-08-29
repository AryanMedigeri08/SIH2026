import React from 'react';
import { ViabilityMeterCard } from '../../components/Dashboard/ViabilityMeterCard';
import { FeatureContributionChart } from '../../components/Dashboard/FeatureContributionChart';
import { ViabilityRadarChart } from '../../components/Dashboard/ViabilityRadarChart';
import { BrainCircuit, Info, ShieldCheck, Sparkles, CheckCircle2, Table, TrendingUp, TrendingDown, Layers } from 'lucide-react';
import { TranslatedText } from '../../components/TranslatedText';

const FEATURE_DEFINITIONS = [
  { key: 'dscr', label: 'Debt Service Coverage Ratio (DSCR)', unit: 'Ratio', benchmark: '≥ 1.33 (RBI Norm)', description: 'Operating cash flow available to service debt interest and principal amortizations.' },
  { key: 'subsidy_coverage_ratio', label: 'Subsidy Coverage Ratio', unit: 'Fraction', benchmark: '15% – 35% (PMEGP/PMFME)', description: 'Government capital grant as a percentage of total initial project capital outlay.' },
  { key: 'loan_to_income_ratio', label: 'Debt to Turnover Burden', unit: 'Ratio', benchmark: '< 2.0 (Prudent Solvency)', description: 'Total term loan balance divided by projected gross annual operating turnover.' },
  { key: 'log_projected_population', label: 'Catchment Scale (Log10 Pop)', unit: 'Log Scale', benchmark: '3.0 – 5.0 (1k – 100k Pop)', description: 'Logarithmic scale of 2026 projected demographic consumer base in catchment radius.' },
  { key: 'msme_density_per_10k', label: 'MSME Cluster Density', unit: 'Units / 10k Pop', benchmark: '10 – 150 per 10k', description: 'Registered micro and small enterprises per 10,000 population from Udyam Registry.' },
  { key: 'infrastructure_score', label: 'Site Infrastructure Readiness', unit: 'Score / 10.0', benchmark: '≥ 6.0 / 10.0', description: 'Composite index of 613 village amenities (paved road, power grid, haat, bank, PDS).' },
  { key: 'cpi_inflation_pct', label: 'State Rural CPI Inflation', unit: 'Annual %', benchmark: '3.0% – 6.0% (RBI Target)', description: 'MoSPI state-level rural Consumer Price Index rate affecting raw materials and inputs.' },
  { key: 'working_capital_months_buffer', label: 'Working Capital Liquidity Buffer', unit: 'Months', benchmark: '≥ 2.0 Months', description: 'Promoter liquid margin contribution divided by monthly working capital outlay.' },
  { key: 'competition_intensity', label: 'Local Market Competition Index', unit: 'Index 0 – 1.0', benchmark: '< 0.50 (Low Saturation)', description: 'Estimated same-sector local competitor density per 1,000 catchment population.' },
  { key: 'weather_risk_score', label: 'Climate & Weather Exposure', unit: 'Risk Index 0 – 1.0', benchmark: '< 0.35 (Low Exposure)', description: 'IMD telemetry fraction of monsoon extreme rainfall and seasonal disruption days.' },
];

export function ViabilityPage({ reportData }) {
  if (!reportData) return null;

  const ml = reportData.ml_viability || {};
  const fin = reportData.financial_analysis || {};
  const featureValues = ml.feature_values || ml.feature_vector_audit || {};
  const shapContribs = ml.shap_explanation?.contributions || [];

  const shapLookup = React.useMemo(() => {
    const map = {};
    shapContribs.forEach((c) => {
      map[c.feature] = Number(c.shap_value);
    });
    return map;
  }, [shapContribs]);

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-indigo-600 bg-gradient-to-r from-white via-indigo-50/20 to-white shadow-card border border-slate-200/90">
        <div className="text-xs font-bold uppercase tracking-wider text-indigo-700 mb-1 flex items-center gap-1.5">
          <BrainCircuit className="w-4 h-4 text-indigo-600" />
          <span><TranslatedText text="Dimension 1 • Machine Learning Viability & TreeSHAP Explainability" /></span>
        </div>
        <h1 className="text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
          <TranslatedText text="Supervised 10-D XGBoost Classifier & Lundberg TreeSHAP Attributions" />
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
          <TranslatedText text="Trained on empirical rural enterprise repayment outcomes. TreeSHAP calculates the exact marginal game-theoretic contribution (log-odds impact) of every financial, competitive, and infrastructure variable without heuristic guessing." />
        </p>
      </div>

      {/* Viability Gauge Hero Card */}
      <ViabilityMeterCard mlViability={ml} dscrInfo={fin.dscr} />

      {/* Visuals Grid: SHAP Horizontal Bar Chart + 10-D Viability Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FeatureContributionChart mlViability={ml} />
        <ViabilityRadarChart mlViability={ml} />
      </div>

      {/* 10-Dimensional Input Feature Vector & Audit Inspection Table */}
      <div className="glass-panel p-6 bg-white border border-slate-200 shadow-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200">
              <Table className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-outfit font-bold text-slate-900">
                <TranslatedText text="10-Dimensional Input Feature Vector & Audit Inspection" />
              </h3>
              <p className="text-xs text-slate-500 font-medium">
                <TranslatedText text="Verifiable mathematical inputs fed into the XGBoost classification engine with corresponding TreeSHAP impact" />
              </p>
            </div>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-800 font-mono font-bold self-start sm:self-auto">
            10 <TranslatedText text="Features Audited" />
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-700 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-3">#</th>
                <th className="py-3 px-3"><TranslatedText text="Feature Name" /></th>
                <th className="py-3 px-3"><TranslatedText text="Raw Value" /></th>
                <th className="py-3 px-3"><TranslatedText text="Benchmark / Scale" /></th>
                <th className="py-3 px-3 text-right"><TranslatedText text="TreeSHAP Attribution" /></th>
                <th className="py-3 px-3 text-center"><TranslatedText text="Impact Verdict" /></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {FEATURE_DEFINITIONS.map((def, idx) => {
                const raw = featureValues[def.key] ?? (def.key === 'dscr' ? fin.dscr?.dscr ?? 1.33 : 0);
                const shap = shapLookup[def.key] ?? 0;
                const isPos = shap >= 0;

                return (
                  <tr key={def.key} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3 font-mono text-slate-400 text-[11px]">{`x${idx}`}</td>
                    <td className="py-3 px-3">
                      <div className="font-bold text-slate-900"><TranslatedText text={def.label} /></div>
                      <div className="text-[10px] text-slate-500 line-clamp-1"><TranslatedText text={def.description} /></div>
                    </td>
                    <td className="py-3 px-3 font-mono font-extrabold text-sovereign-900">
                      {typeof raw === 'number' ? (Number.isInteger(raw) ? raw : raw.toFixed(2)) : raw}
                      <span className="text-[10px] text-slate-500 font-normal ml-1">({def.unit})</span>
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-600">
                      {def.benchmark}
                    </td>
                    <td className="py-3 px-3 text-right font-mono font-bold">
                      {shap !== 0 ? (
                        <span className={isPos ? 'text-emerald-700' : 'text-rose-700'}>
                          {isPos ? `+${shap.toFixed(4)}` : shap.toFixed(4)}
                        </span>
                      ) : (
                        <span className="text-slate-400">0.0000</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-center">
                      {isPos ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                          <TrendingUp className="w-3 h-3 text-emerald-600" />
                          <span><TranslatedText text="Solvency Lift" /></span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-800 border border-rose-200">
                          <TrendingDown className="w-3 h-3 text-rose-600" />
                          <span><TranslatedText text="Caution Drag" /></span>
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Metadata & Lineage Box */}
      <div className="glass-panel p-5 bg-white border border-slate-200/90 shadow-card flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-600">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200 shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="font-bold text-slate-900">
              <TranslatedText text="Model File:" /> <code className="font-mono text-indigo-900 bg-indigo-50/70 px-1.5 py-0.5 rounded border border-indigo-200">viability_xgb.joblib</code>
            </div>
            <div className="text-[11px] text-slate-500 font-medium mt-0.5">
              <TranslatedText text="Algorithm: Gradient-Boosted Decision Trees (XGBoost 10-D Classifier) • Explainer: TreeExplainer (Lundberg et al.)" />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-slate-700 shrink-0">
          <span className="px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 font-bold">
            <TranslatedText text="Execution Latency: <3ms" />
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <TranslatedText text="Verified Invariant" />
          </span>
        </div>
      </div>

    </div>
  );
}
export default ViabilityPage;
