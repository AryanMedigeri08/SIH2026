import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ReferenceLine,
} from 'recharts';
import { BrainCircuit, Info, TrendingUp, TrendingDown, CheckCircle2, AlertTriangle, ShieldCheck, Sparkles } from 'lucide-react';
import { useViewMode, VIEW_MODES } from '../../context/ViewModeContext';
import { TranslatedText } from '../TranslatedText';

const FEATURE_LABELS = {
  dscr: 'Debt Service Coverage (DSCR)',
  subsidy_coverage_ratio: 'Subsidy Coverage Ratio',
  loan_to_income_ratio: 'Debt to Turnover Burden',
  log_projected_population: 'Catchment Scale (Log Pop)',
  msme_density_per_10k: 'MSME Cluster Density',
  infrastructure_score: 'Infrastructure Index',
  cpi_inflation_pct: 'CPI Inflation Exposure',
  working_capital_months_buffer: 'Working Capital Runway',
  competition_intensity: 'Market Competition Intensity',
  weather_risk_score: 'Climate & Weather Resilience',
};

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;
  const isPos = data.shapValue >= 0;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-xl text-xs max-w-xs">
      <div className="font-bold text-slate-900 mb-1 flex items-center justify-between gap-2">
        <span>{data.label}</span>
        <span
          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
            isPos ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800 border border-rose-200'
          }`}
        >
          {isPos ? 'Positive Driver' : 'Risk Drag'}
        </span>
      </div>
      <div className="space-y-1 text-slate-700">
        <div className="flex justify-between">
          <span className="text-slate-500">Raw Feature Value:</span>
          <span className="font-mono text-sovereign-800 font-bold">{data.featureValue.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">SHAP Attribution:</span>
          <span className={`font-mono font-bold ${isPos ? 'text-emerald-700' : 'text-rose-700'}`}>
            {data.shapValue > 0 ? `+${data.shapValue.toFixed(4)}` : data.shapValue.toFixed(4)}
          </span>
        </div>
        <div className="text-[11px] text-slate-600 pt-1 border-t border-slate-100">
          {isPos
            ? `Pushes model confidence towards ${data.predictedClass} classification.`
            : `Pulls confidence down / introduces cautionary credit drag.`}
        </div>
      </div>
    </div>
  );
};

export function FeatureContributionChart({ mlViability }) {
  const [isMobile, setIsMobile] = React.useState(false);
  const { isBeneficiary, setViewMode } = useViewMode();

  React.useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 640);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const shapExp = mlViability?.shap_explanation;
  const rawContribs = shapExp?.contributions || [];
  const predictedClass = shapExp?.predicted_class || mlViability?.verdict || 'SUITABLE';
  const baseValue = shapExp?.base_value ?? 0.85;
  const topPositives = mlViability?.top_positive_factors || [];
  const topRisks = mlViability?.top_risk_factors || [];

  // Beneficiary Friendly Rendering
  if (isBeneficiary) {
    return (
      <div className="glass-panel p-4 sm:p-6 border-slate-200 flex flex-col justify-between bg-white shadow-card space-y-4">
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1.5 mb-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                <TranslatedText text="Beneficiary Business Health Breakdown" />
              </div>
              <h3 className="text-lg font-outfit font-bold text-slate-900">
                <TranslatedText text="Why the Bank Approves Your Project" />
              </h3>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 self-start sm:self-auto">
              <TranslatedText text="Grounded Strengths" />
            </span>
          </div>

          <p className="text-xs text-slate-600 mt-2 mb-3 leading-relaxed font-medium">
            <TranslatedText text="Our AI verified these grounded operational and financial strengths for your loan application:" />
          </p>

          <div className="space-y-2">
            {topPositives.slice(0, 3).map((pos, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-emerald-50/50 border border-emerald-200/80 flex items-start gap-2.5 shadow-subtle">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div className="text-xs text-emerald-950 font-medium leading-relaxed">
                  <TranslatedText text={pos} />
                </div>
              </div>
            ))}

            {topRisks.length > 0 && (
              <div className="pt-2">
                <div className="text-[11px] font-bold uppercase tracking-wider text-amber-800 mb-2 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  <TranslatedText text="Things to Prepare Before Visiting the Bank Branch" />
                </div>
                <div className="space-y-2">
                  {topRisks.slice(0, 2).map((risk, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-amber-50/50 border border-amber-200/80 flex items-start gap-2.5 shadow-subtle">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <div className="text-xs text-amber-950 font-medium leading-relaxed">
                        <TranslatedText text={risk} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Auditor Toggle Switch Tip */}
        <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-2 text-[10px] text-slate-500">
          <span className="flex items-center gap-1 font-medium">
            <Sparkles className="w-3 h-3 text-sovereign-700 shrink-0" />
            <TranslatedText text="Beneficiary View active. Need raw C++ TreeSHAP marginal math?" />
          </span>
          <button
            type="button"
            onClick={() => setViewMode(VIEW_MODES.BANKER)}
            className="text-sovereign-800 font-bold hover:underline cursor-pointer"
          >
            <TranslatedText text="Switch to Banker & Auditor Mode →" />
          </button>
        </div>
      </div>
    );
  }

  // Format and sort contributions for chart display
  const chartData = React.useMemo(() => {
    if (!rawContribs.length) return [];
    return [...rawContribs]
      .sort((a, b) => Math.abs(a.shap_value) - Math.abs(b.shap_value))
      .map((c) => ({
        feature: c.feature,
        label: FEATURE_LABELS[c.feature] || c.feature.replace(/_/g, ' '),
        shapValue: Number(c.shap_value),
        featureValue: Number(c.feature_value),
        predictedClass,
      }));
  }, [rawContribs, predictedClass]);

  if (!rawContribs.length) {
    return (
      <div className="glass-panel p-4 sm:p-6 border-slate-200 flex flex-col items-center justify-center text-center min-h-[280px] bg-white shadow-card">
        <BrainCircuit className="w-10 h-10 text-slate-400 mb-3" />
        <h3 className="text-sm font-bold text-slate-800 mb-1">SHAP Explainability Waterfall</h3>
        <p className="text-xs text-slate-500 max-w-md">
          {mlViability?.is_fallback
            ? 'Deterministic rule-based engine active. Real tree margin attributions available when XGBoost native model runs.'
            : 'Evaluating feature vector attributions...'}
        </p>
      </div>
    );
  }

  const positiveTotal = chartData.filter((d) => d.shapValue > 0).reduce((acc, cur) => acc + cur.shapValue, 0);
  const negativeTotal = chartData.filter((d) => d.shapValue < 0).reduce((acc, cur) => acc + cur.shapValue, 0);

  return (
    <div className="glass-panel p-4 sm:p-6 border-slate-200 flex flex-col justify-between bg-white shadow-card">
      {/* Header */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-sovereign-700 flex items-center gap-1.5 mb-1">
              <BrainCircuit className="w-3.5 h-3.5" />
              Lundberg TreeSHAP Explainability Layer
            </div>
            <h3 className="text-lg font-outfit font-bold text-slate-900">
              Feature Attribution Margin Impact ({predictedClass})
            </h3>
          </div>
          <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs bg-slate-50 px-2.5 sm:px-3 py-1.5 rounded-xl border border-slate-200 font-mono">
            <span className="text-slate-600">Base: <strong className="text-slate-900">{baseValue.toFixed(3)}</strong></span>
            <span className="text-emerald-700 font-bold flex items-center gap-0.5">
              <TrendingUp className="w-3 h-3" /> +{positiveTotal.toFixed(2)}
            </span>
            <span className="text-rose-700 font-bold flex items-center gap-0.5">
              <TrendingDown className="w-3 h-3" /> {negativeTotal.toFixed(2)}
            </span>
          </div>
        </div>

        <p className="text-xs text-slate-600 mb-4">
          Shows how each 10-D indicator shifts the model’s credit score relative to the nationwide baseline.
          Green bars increase viability score; red bars represent risk drag.
        </p>
      </div>

      {/* Chart */}
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: isMobile ? 12 : 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
            <XAxis
              type="number"
              stroke="#64748b"
              fontSize={10}
              tickFormatter={(v) => (v > 0 ? `+${v.toFixed(2)}` : v.toFixed(2))}
              domain={['auto', 'auto']}
            />
            <YAxis
              type="category"
              dataKey="label"
              stroke="#334155"
              fontSize={isMobile ? 9.5 : 11}
              width={isMobile ? 115 : 160}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.02)' }} />
            <ReferenceLine x={0} stroke="#94a3b8" strokeWidth={1.5} />
            <Bar dataKey="shapValue" radius={[4, 4, 4, 4]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.shapValue >= 0 ? '#059669' : '#dc2626'}
                  opacity={0.9}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Footer Lineage */}
      <div className="text-[10px] text-slate-500 pt-3 mt-3 border-t border-slate-200 flex flex-wrap items-center justify-between gap-2">
        <span className="flex items-center gap-1 text-slate-600">
          <Info className="w-3 h-3 text-sovereign-700 shrink-0" />
          <span>Native XGBoost Booster Attributions • Exact Lundberg TreeSHAP Path Attribution</span>
        </span>
        <span className="font-mono text-slate-500 font-medium">10 Input Features Evaluated</span>
      </div>
    </div>
  );
}
export default FeatureContributionChart;
