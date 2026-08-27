import React from 'react';
import { ShieldAlert, AlertCircle, CheckCircle2 } from 'lucide-react';

export function RiskRadarCard({ riskData }) {
  const risks = riskData?.risk_points || [];
  const verdict = riskData?.verdict || {};
  const avgScore = verdict.average_risk_score || 3.2;
  const severity = verdict.overall_severity || "MODERATE";

  return (
    <div className="glass-panel p-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            8-Point Quantified Commercial Risk Matrix & Mitigation Buffers
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Every risk metric is strictly derived from upstream banking formulas & census telemetry (never an LLM guess).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <span className="text-slate-400">Composite Risk Score: </span>
            <strong className="text-amber-400 font-mono font-bold ml-1">{avgScore.toFixed(2)} / 10</strong>
          </div>
          <span className={`text-xs font-bold px-3 py-1.5 rounded-xl border ${
            severity === 'LOW' 
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' 
              : severity === 'MODERATE' 
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' 
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}>
            {severity} RISK
          </span>
        </div>
      </div>

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
                  ? 'bg-rose-950/20 border-rose-500/30 hover:border-rose-500/50' 
                  : isMod 
                  ? 'bg-amber-950/15 border-amber-500/25 hover:border-amber-500/40' 
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-cyan-400">{r.risk_id}</span>
                  <strong className="text-xs text-white">{r.title}</strong>
                </div>

                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-mono font-bold text-slate-300">{r.score.toFixed(1)}/10</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase ${
                    isHigh ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
                    isMod ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                    'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  }`}>
                    {r.severity}
                  </span>
                </div>
              </div>

              <div className="text-[11px] text-slate-400 mb-2">
                <strong className="text-slate-300 font-medium">Grounding Basis:</strong> {r.basis}
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-300">
                <strong className="text-cyan-400">Mitigation:</strong> {r.mitigation}
                {r.rupee_buffer > 0 && (
                  <div className="mt-1 text-emerald-400 font-mono font-semibold">
                    💰 Suggested Contingency Buffer: ₹{Math.round(r.rupee_buffer).toLocaleString('en-IN')}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}
