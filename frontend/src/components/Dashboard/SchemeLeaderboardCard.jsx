import React from 'react';
import { Award, CheckCircle, XCircle, Percent, ArrowUpRight } from 'lucide-react';

export function SchemeLeaderboardCard({ schemes }) {
  const schemeList = schemes || [];

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Award className="w-4 h-4 text-cyan-400" />
            Statutory Government Scheme Optimization Leaderboard
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Auto-evaluated against PMEGP, PMFME, MUDRA, Stand-Up India & PM Vishwakarma eligibility rules.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {schemeList.map((s, idx) => {
          const isEligible = s.eligible;
          const isTop = idx === 0 && isEligible;

          return (
            <div 
              key={s.scheme_id || idx}
              className={`p-4 rounded-xl border transition-all ${
                isTop 
                  ? 'bg-gradient-to-b from-indigo-950/80 to-slate-900/90 border-cyan-500/40 shadow-glow'
                  : isEligible 
                  ? 'bg-slate-900/60 border-slate-700/80 hover:border-slate-600'
                  : 'bg-slate-950/40 border-slate-800/60 opacity-60'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-outfit font-extrabold text-sm text-white">{s.scheme_id}</span>
                    {isTop && (
                      <span className="text-[10px] font-bold bg-cyan-500 text-black px-2 py-0.5 rounded-md uppercase tracking-wider">
                        ★ Top Match
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-400 line-clamp-1">{s.full_name || s.scheme_name}</div>
                </div>

                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 ${
                  isEligible 
                    ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30' 
                    : 'bg-rose-500/10 text-rose-300 border border-rose-500/30'
                }`}>
                  {isEligible ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                  {isEligible ? 'Eligible' : 'Ineligible'}
                </span>
              </div>

              {/* Metrics */}
              <div className="pt-2 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-[10px] text-slate-500 block">Subsidy Grant</span>
                  <strong className="font-mono text-emerald-400">
                    {s.subsidy_grant_amount > 0 ? `₹${Math.round(s.subsidy_grant_amount).toLocaleString('en-IN')}` : '₹0 (Interest Subvention)'}
                  </strong>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block">Effective Interest</span>
                  <strong className="font-mono text-cyan-300">{s.effective_interest_rate_pct || 9.5}% p.a.</strong>
                </div>
              </div>

              <div className="text-[11px] text-slate-400 mt-2 line-clamp-1 italic">
                {s.match_rationale || s.eligibility_notes || "Applicable under current sector & promoter category."}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
