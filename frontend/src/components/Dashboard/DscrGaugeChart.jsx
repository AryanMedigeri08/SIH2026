import React from 'react';
import { ShieldCheck, AlertTriangle, AlertCircle, Info, Landmark } from 'lucide-react';

export function DscrGaugeChart({ dscrInfo, projections }) {
  const dscr = Number(dscrInfo?.dscr ?? dscrInfo?.average_dscr ?? 1.85);
  const benchmarkMet = dscrInfo?.dscr_benchmark_met ?? dscr >= 1.33;

  // Clamp display between 0 and 3.0 for the gauge angle
  const clampedDscr = Math.max(0, Math.min(3.0, dscr));
  // 180 degrees semicircular meter (0 = -90deg, 3.0 = 90deg)
  const angle = (clampedDscr / 3.0) * 180 - 90;

  const isSolvent = dscr >= 1.33;
  const isCaution = dscr >= 1.0 && dscr < 1.33;
  const isDeficit = dscr < 1.0;

  const statusColor = isSolvent
    ? 'text-emerald-400'
    : isCaution
    ? 'text-amber-400'
    : 'text-rose-400';

  const statusBg = isSolvent
    ? 'bg-emerald-500/10 border-emerald-500/30'
    : isCaution
    ? 'bg-amber-500/10 border-amber-500/30'
    : 'bg-rose-500/10 border-rose-500/30';

  const statusText = isSolvent
    ? 'RBI Solvency Standard Met'
    : isCaution
    ? 'Caution: Below RBI Recommended 1.33'
    : 'Solvency Deficit: High Default Risk';

  return (
    <div className="glass-panel p-6 border-slate-800 flex flex-col justify-between">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5 mb-1">
              <Landmark className="w-3.5 h-3.5" />
              RBI Underwriting Standard Meter
            </div>
            <h3 className="text-lg font-outfit font-bold text-white">
              Debt Service Coverage Ratio (DSCR)
            </h3>
          </div>
          <span className={`text-xs px-2.5 py-1 rounded-lg border font-bold ${statusBg} ${statusColor}`}>
            {isSolvent ? 'SOLVENT' : isCaution ? 'CAUTION' : 'DEFICIT'}
          </span>
        </div>
        <p className="text-xs text-slate-400 mb-4">
          Measures cash flow available to service principal & interest payments. RBI benchmark requires DSCR ≥ 1.33.
        </p>
      </div>

      {/* Semicircle Gauge Visual */}
      <div className="relative flex flex-col items-center justify-center my-2">
        <svg viewBox="0 0 200 115" className="w-64 max-w-full overflow-visible">
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="33%" stopColor="#f59e0b" />
              <stop offset="44%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#059669" />
            </linearGradient>
          </defs>

          {/* Background Arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="#1e293b"
            strokeWidth="16"
            strokeLinecap="round"
          />

          {/* Color Arc Track */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="14"
            strokeLinecap="round"
            opacity="0.85"
          />

          {/* Benchmark Tick at 1.33 (angle = 1.33/3 * 180 - 90 = -10.2 deg) */}
          <line
            x1="100"
            y1="20"
            x2="100"
            y2="34"
            stroke="#38bdf8"
            strokeWidth="2.5"
            transform="rotate(-10.2, 100, 100)"
          />

          {/* Needle */}
          <g transform={`rotate(${angle}, 100, 100)`}>
            <polygon points="97,100 103,100 100,24" fill="#ffffff" filter="drop-shadow(0 2px 4px rgba(0,0,0,0.5))" />
            <circle cx="100" cy="100" r="7" fill="#38bdf8" />
          </g>

          {/* Gauge Labels */}
          <text x="20" y="115" fill="#ef4444" fontSize="9" fontWeight="bold" textAnchor="middle">0.0</text>
          <text x="88" y="18" fill="#38bdf8" fontSize="8" fontWeight="bold" textAnchor="middle">1.33 (RBI)</text>
          <text x="180" y="115" fill="#10b981" fontSize="9" fontWeight="bold" textAnchor="middle">3.0+</text>
        </svg>

        {/* Big DSCR Value Readout */}
        <div className="text-center mt-[-10px]">
          <div className={`text-3xl font-outfit font-extrabold ${statusColor}`}>
            {dscr.toFixed(2)}x
          </div>
          <div className="text-xs font-semibold text-slate-300 flex items-center justify-center gap-1.5 mt-0.5">
            {isSolvent ? (
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            )}
            <span>{statusText}</span>
          </div>
        </div>
      </div>

      {/* Threshold Legend */}
      <div className="grid grid-cols-3 gap-2 text-center text-[10px] mt-4 pt-3 border-t border-slate-800/80">
        <div className="p-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300">
          <span className="font-bold">&lt; 1.00</span>: Deficit
        </div>
        <div className="p-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300">
          <span className="font-bold">1.00 – 1.33</span>: Caution
        </div>
        <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
          <span className="font-bold">≥ 1.33</span>: Bankable
        </div>
      </div>
    </div>
  );
}
export default DscrGaugeChart;
