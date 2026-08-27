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
    ? 'text-emerald-700'
    : isCaution
    ? 'text-amber-700'
    : 'text-rose-700';

  const statusBg = isSolvent
    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
    : isCaution
    ? 'bg-amber-50 border-amber-200 text-amber-800'
    : 'bg-rose-50 border-rose-200 text-rose-800';

  const statusText = isSolvent
    ? 'RBI Solvency Standard Met'
    : isCaution
    ? 'Caution: Below RBI Recommended 1.33'
    : 'Solvency Deficit: High Default Risk';

  return (
    <div className="glass-panel p-6 border-slate-200 flex flex-col justify-between bg-white shadow-card">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-sovereign-700 flex items-center gap-1.5 mb-1">
              <Landmark className="w-3.5 h-3.5" />
              RBI Underwriting Standard Meter
            </div>
            <h3 className="text-lg font-outfit font-bold text-slate-900">
              Debt Service Coverage Ratio (DSCR)
            </h3>
          </div>
          <span className={`text-xs px-2.5 py-1 rounded-lg border font-bold ${statusBg}`}>
            {isSolvent ? 'SOLVENT' : isCaution ? 'CAUTION' : 'DEFICIT'}
          </span>
        </div>
        <p className="text-xs text-slate-600 mb-4">
          Measures cash flow available to service principal & interest payments. RBI benchmark requires DSCR ≥ 1.33.
        </p>
      </div>

      {/* Semicircle Gauge Visual */}
      <div className="relative flex flex-col items-center justify-center my-2">
        <svg viewBox="0 0 200 115" className="w-64 max-w-full overflow-visible">
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#dc2626" />
              <stop offset="33%" stopColor="#d97706" />
              <stop offset="44%" stopColor="#059669" />
              <stop offset="100%" stopColor="#047857" />
            </linearGradient>
          </defs>

          {/* Background Arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="#f1f5f9"
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
            opacity="0.95"
          />

          {/* Benchmark Tick at 1.33 (angle = 1.33/3 * 180 - 90 = -10.2 deg) */}
          <line
            x1="100"
            y1="20"
            x2="100"
            y2="34"
            stroke="#0b3b60"
            strokeWidth="2.5"
            transform="rotate(-10.2, 100, 100)"
          />

          {/* Needle */}
          <g transform={`rotate(${angle}, 100, 100)`}>
            <polygon points="97,100 103,100 100,24" fill="#0f172a" filter="drop-shadow(0 1px 3px rgba(0,0,0,0.3))" />
            <circle cx="100" cy="100" r="7" fill="#0b3b60" />
          </g>

          {/* Gauge Labels */}
          <text x="20" y="115" fill="#dc2626" fontSize="9" fontWeight="bold" textAnchor="middle">0.0</text>
          <text x="88" y="18" fill="#0b3b60" fontSize="8" fontWeight="bold" textAnchor="middle">1.33 (RBI)</text>
          <text x="180" y="115" fill="#047857" fontSize="9" fontWeight="bold" textAnchor="middle">3.0+</text>
        </svg>

        {/* Big DSCR Value Readout */}
        <div className="text-center mt-[-10px]">
          <div className={`text-3xl font-outfit font-extrabold ${statusColor}`}>
            {dscr.toFixed(2)}x
          </div>
          <div className="text-xs font-semibold text-slate-700 flex items-center justify-center gap-1.5 mt-0.5">
            {isSolvent ? (
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-600" />
            )}
            <span>{statusText}</span>
          </div>
        </div>
      </div>

      {/* Threshold Legend */}
      <div className="grid grid-cols-3 gap-2 text-center text-[10px] mt-4 pt-3 border-t border-slate-200">
        <div className="p-1.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 font-medium">
          <span className="font-bold">&lt; 1.00</span>: Deficit
        </div>
        <div className="p-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 font-medium">
          <span className="font-bold">1.00 – 1.33</span>: Caution
        </div>
        <div className="p-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 font-medium">
          <span className="font-bold">≥ 1.33</span>: Bankable
        </div>
      </div>
    </div>
  );
}
export default DscrGaugeChart;
