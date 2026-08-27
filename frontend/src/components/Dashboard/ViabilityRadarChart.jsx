import React from 'react';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip,
} from 'recharts';
import { Activity, Shield } from 'lucide-react';

const FEATURE_CONFIG = [
  { key: 'dscr', label: 'DSCR Solvency', max: 3.0, normalize: (v) => Math.min((v / 2.5) * 100, 100) },
  { key: 'subsidy_coverage_ratio', label: 'Subsidy Support', max: 0.5, normalize: (v) => Math.min((v / 0.45) * 100, 100) },
  { key: 'loan_to_income_ratio', label: 'Debt Repayability', max: 2.0, normalize: (v) => Math.max(0, 100 - (v / 1.5) * 100) },
  { key: 'log_projected_population', label: 'Catchment Scale', max: 15.0, normalize: (v) => Math.min((v / 14.0) * 100, 100) },
  { key: 'msme_density_per_10k', label: 'Cluster Density', max: 100.0, normalize: (v) => Math.min((v / 80.0) * 100, 100) },
  { key: 'infrastructure_score', label: 'Infrastructure', max: 100.0, normalize: (v) => Math.min(v, 100) },
  { key: 'cpi_inflation_pct', label: 'Inflation Buffer', max: 12.0, normalize: (v) => Math.max(0, 100 - (v / 10.0) * 100) },
  { key: 'working_capital_months_buffer', label: 'Liquidity Buffer', max: 6.0, normalize: (v) => Math.min((v / 4.0) * 100, 100) },
  { key: 'competition_intensity', label: 'Market Room', max: 1.0, normalize: (v) => Math.max(0, 100 - v * 100) },
  { key: 'weather_risk_score', label: 'Climate Resilience', max: 100.0, normalize: (v) => Math.max(0, 100 - v) },
];

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;

  return (
    <div className="bg-slate-900/95 border border-slate-700/80 rounded-xl p-3 shadow-2xl backdrop-blur-md text-xs">
      <div className="font-bold text-white mb-1">{data.subject}</div>
      <div className="space-y-1 text-slate-300">
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">Normalized Score:</span>
          <span className="font-mono text-cyan-400 font-bold">{data.score.toFixed(1)} / 100</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">Raw Input:</span>
          <span className="font-mono text-slate-200">{data.rawValue.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
};

export function ViabilityRadarChart({ mlViability }) {
  const featureValues = mlViability?.feature_values || mlViability?.feature_vector_audit || {};

  const radarData = React.useMemo(() => {
    return FEATURE_CONFIG.map((cfg) => {
      const raw = Number(featureValues[cfg.key] ?? 50);
      const score = cfg.normalize ? cfg.normalize(raw) : raw;
      return {
        subject: cfg.label,
        score: Math.max(10, Math.min(100, score)),
        rawValue: raw,
      };
    });
  }, [featureValues]);

  return (
    <div className="glass-panel p-6 border-slate-800 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5 mb-1">
              <Activity className="w-3.5 h-3.5" />
              10-Dimensional Viability Profile
            </div>
            <h3 className="text-lg font-outfit font-bold text-white">
              Multi-Pillar Credit Radar
            </h3>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono">
            Radar Overlay
          </span>
        </div>
        <p className="text-xs text-slate-400 mb-2">
          Balanced radar scoring across solvency, market strength, infrastructure, liquidity, and resilience.
        </p>
      </div>

      <div className="h-72 w-full flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
            <PolarGrid stroke="#334155" strokeDasharray="3 3" />
            <PolarAngleAxis dataKey="subject" stroke="#94a3b8" fontSize={10} tickLine={false} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#475569" fontSize={9} />
            <Radar
              name="Viability"
              dataKey="score"
              stroke="#06b6d4"
              fill="#06b6d4"
              fillOpacity={0.4}
            />
            <Tooltip content={<CustomTooltip />} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div className="text-[10px] text-slate-500 pt-2 border-t border-slate-800/80 flex items-center justify-between">
        <span>Higher area coverage indicates superior overall bankability</span>
        <span className="font-mono text-slate-400">10 Dimensions Normalized</span>
      </div>
    </div>
  );
}
export default ViabilityRadarChart;
