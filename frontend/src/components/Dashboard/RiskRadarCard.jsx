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
import { ShieldAlert, AlertTriangle, ShieldCheck, Database, Coins } from 'lucide-react';

const CustomRadarTooltip = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;
  const isHigh = data.score >= 6.0;
  const isMod = data.score >= 4.0 && data.score < 6.0;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-xl text-xs">
      <div className="font-bold text-slate-900 mb-1 flex items-center justify-between gap-2">
        <span>{data.fullTitle}</span>
        <span
          className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
            isHigh
              ? 'bg-rose-50 text-rose-800 border border-rose-200'
              : isMod
              ? 'bg-amber-50 text-amber-800 border border-amber-200'
              : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
          }`}
        >
          {data.severity}
        </span>
      </div>
      <div className="space-y-1 text-slate-700">
        <div className="flex justify-between">
          <span className="text-slate-500">Risk Score:</span>
          <span className="font-mono font-bold text-rose-700">{data.score.toFixed(1)} / 10.0</span>
        </div>
        {data.rupee_buffer > 0 && (
          <div className="flex justify-between text-emerald-700 font-mono font-semibold">
            <span>Buffer:</span>
            <span>₹{Math.round(data.rupee_buffer).toLocaleString('en-IN')}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export function RiskRadarCard({ riskData }) {
  const risks = riskData?.risk_points || [];
  const verdict = riskData?.verdict || {};
  const avgScore = verdict.average_risk_score || 3.2;
  const severity = verdict.overall_severity || 'MODERATE';

  // Format the 8 risk points for Recharts Radar
  const radarChartData = React.useMemo(() => {
    return risks.map((r) => ({
      subject: r.title?.split(' ')?.[0] || r.risk_id,
      fullTitle: r.title || r.risk_id,
      score: Number(r.score || 0),
      severity: r.severity,
      rupee_buffer: r.rupee_buffer,
    }));
  }, [risks]);

  return (
    <div className="glass-panel p-6 bg-white shadow-card border border-slate-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-rose-700 flex items-center gap-1.5 mb-1">
            <ShieldAlert className="w-3.5 h-3.5" />
            8-Point Quantified Commercial Risk Matrix
          </div>
          <h3 className="text-lg font-outfit font-bold text-slate-900">
            Operational Risk Radar & Financial Mitigation Buffers
          </h3>
          <p className="text-xs text-slate-600 mt-0.5">
            Every risk metric is strictly derived from upstream banking formulas & census telemetry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200 text-xs">
            <span className="text-slate-500">Composite Risk: </span>
            <strong className="text-amber-800 font-mono font-bold ml-1">{avgScore.toFixed(2)} / 10</strong>
          </div>
          <span
            className={`text-xs font-bold px-3 py-1.5 rounded-xl border ${
              severity === 'LOW'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : severity === 'MODERATE'
                ? 'bg-amber-50 border-amber-200 text-amber-800'
                : 'bg-rose-50 border-rose-200 text-rose-800'
            }`}
          >
            {severity} RISK
          </span>
        </div>
      </div>

      {/* Radar Chart Visual (if risk points exist) */}
      {radarChartData.length > 0 && (
        <div className="bg-slate-50 rounded-2xl border border-slate-200 p-4 mb-5 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="w-full md:w-1/2 h-56 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarChartData}>
                <PolarGrid stroke="#cbd5e1" strokeDasharray="3 3" />
                <PolarAngleAxis dataKey="subject" stroke="#334155" fontSize={10} tickLine={false} />
                <PolarRadiusAxis angle={30} domain={[0, 10]} stroke="#94a3b8" fontSize={9} />
                <Radar
                  name="Risk Score"
                  dataKey="score"
                  stroke="#dc2626"
                  fill="#dc2626"
                  fillOpacity={0.2}
                />
                <Tooltip content={<CustomRadarTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div className="w-full md:w-1/2 space-y-2 text-xs">
            <div className="text-slate-900 font-bold mb-1">Risk Pillar Overview:</div>
            <p className="text-slate-600 text-[11px] leading-relaxed font-medium">
              The polygon outlines exposure across raw material volatility, power interruptions, debt pressure, and climate shock.
              Smaller area indicates lower systemic credit risk.
            </p>
            <div className="grid grid-cols-2 gap-2 pt-2">
              <div className="p-2 rounded-lg bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-800 font-mono flex items-center gap-1.5 font-bold">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span>{risks.filter((r) => r.severity === 'LOW').length} Low Risk Pillars</span>
              </div>
              <div className="p-2 rounded-lg bg-rose-50 border border-rose-200 text-[11px] text-rose-800 font-mono flex items-center gap-1.5 font-bold">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                <span>{risks.filter((r) => r.severity === 'HIGH' || r.severity === 'SEVERE').length} Attention Items</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 8 Risk Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {risks.map((r) => {
          const isHigh = r.severity === 'HIGH' || r.severity === 'SEVERE';
          const isMod = r.severity === 'MODERATE';

          return (
            <div
              key={r.risk_id}
              className={`p-4 rounded-xl border transition-all ${
                isHigh
                  ? 'bg-rose-50/70 border-rose-200 hover:border-rose-300'
                  : isMod
                  ? 'bg-amber-50/70 border-amber-200 hover:border-amber-300'
                  : 'bg-white border-slate-200 hover:border-slate-300 shadow-subtle'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-sovereign-800">{r.risk_id}</span>
                  <strong className="text-xs text-slate-900 font-bold">{r.title}</strong>
                </div>

                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-mono font-bold text-slate-700">{r.score.toFixed(1)}/10</span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase ${
                      isHigh
                        ? 'bg-rose-100 text-rose-900 border border-rose-300'
                        : isMod
                        ? 'bg-amber-100 text-amber-900 border border-amber-300'
                        : 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                    }`}
                  >
                    {r.severity}
                  </span>
                </div>
              </div>

              <div className="text-[11px] text-slate-600 mb-2">
                <strong className="text-slate-800 font-medium">Grounding Basis:</strong> {r.basis}
              </div>

              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-800">
                <strong className="text-sovereign-800">Mitigation:</strong> {r.mitigation}
                {r.rupee_buffer > 0 && (
                  <div className="mt-1 text-emerald-800 font-mono font-bold flex items-center gap-1.5">
                    <Coins className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Suggested Contingency Buffer: ₹{Math.round(r.rupee_buffer).toLocaleString('en-IN')}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Grounded Data Source Lineage Tag */}
      <div className="text-[10px] text-slate-500 flex flex-wrap items-center justify-between gap-2 pt-3 mt-4 border-t border-slate-200">
        <span className="flex items-center gap-1 text-slate-600">
          <Database className="w-3 h-3 text-sovereign-700" />
          <strong className="text-slate-700">Data Source:</strong> MoSPI State CPI, IMD Weather Telemetry & RBI Prudential Benchmark Matrix
        </span>
        <span className="font-mono text-slate-600 font-medium">
          Risk Evaluation: Deterministic Mathematical Model
        </span>
      </div>
    </div>
  );
}
export default RiskRadarCard;
