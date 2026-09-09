import React from 'react';
import { Award, CheckCircle, XCircle, Percent, ArrowUpRight, ExternalLink, Sparkles } from 'lucide-react';
import { TranslatedText } from '../TranslatedText';

export function SchemeLeaderboardCard({ schemes, isReconsider = false }) {
  const schemeList = schemes || [];

  return (
    <div className="glass-panel p-4 sm:p-6 bg-white shadow-card border border-slate-200">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-sovereign-700 flex items-center gap-1.5 mb-1">
            <Award className="w-3.5 h-3.5" />
            Statutory Incentive Optimization
          </div>
          <h3 className="text-lg font-outfit font-bold text-slate-900">
            Government Scheme Ranking & Subsidy Matrix
          </h3>
          <p className="text-xs text-slate-600 mt-0.5">
            Auto-evaluated against PMEGP, PMFME, MUDRA, Stand-Up India & PM Vishwakarma eligibility rules.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {schemeList.map((s, idx) => {
          const isEligible = s.eligible ?? s.is_eligible ?? (idx === 0);
          const isTop = idx === 0 && isEligible;
          const rationale = isEligible 
            ? (s.notes || s.match_rationale || s.eligibility_notes || "Applicable under current sector outlay & promoter category.") 
            : (s.ineligibility_reason || s.notes || "Ineligible under current parameters.");

          return (
            <div 
              key={s.scheme_id || idx}
              className={`p-4 rounded-xl border transition-all duration-200 ${
                isTop 
                  ? (isReconsider ? 'bg-rose-50/40 border-rose-200 shadow-sm' : 'bg-sovereign-50/50 border-sovereign-300 shadow-sm')
                  : isEligible
                  ? 'bg-white border-slate-200 hover:border-slate-300'
                  : 'bg-slate-50/50 border-slate-200 opacity-60'
              }`}
            >
              <div>
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-outfit font-extrabold text-sm text-slate-900">{s.scheme_id}</span>
                      {isTop && (
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider inline-flex items-center gap-1 shadow-xs ${
                          isReconsider ? 'bg-rose-800 text-white' : 'bg-sovereign-800 text-white'
                        }`}>
                          <Sparkles className="w-3 h-3 text-amber-300 fill-amber-300" />
                          <span>{isReconsider ? 'Conditional Policy Match' : 'Top Match'}</span>
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-500 line-clamp-1 font-medium">{s.full_name || s.scheme_name}</div>
                  </div>

                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 shrink-0 ${
                    isEligible 
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' 
                      : 'bg-slate-100 text-slate-600 border border-slate-200'
                  }`}>
                    {isEligible ? <CheckCircle className="w-3 h-3 text-emerald-600" /> : <XCircle className="w-3 h-3 text-slate-400" />}
                    {isEligible ? 'Eligible' : 'Ineligible'}
                  </span>
                </div>

                {/* Metrics */}
                <div className="pt-2 border-t border-slate-200/80 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-500 block font-semibold">Government Incentive</span>
                    <strong className="font-mono text-emerald-700 font-bold">
                      {s.subsidy_grant_amount > 0 
                        ? `₹${Math.round(s.subsidy_grant_amount).toLocaleString('en-IN')} (Capital Grant)`
                        : (s.benefit_type === 'INTEREST_SUBVENTION' || (s.effective_interest_rate_pct < 11.0 && isEligible))
                        ? `${(11.0 - (s.effective_interest_rate_pct || 11.0)).toFixed(1)}% p.a. Interest Subvention`
                        : isEligible
                        ? 'Collateral-Free Concessional Credit'
                        : '₹0 (Ineligible)'}
                    </strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block font-semibold">Effective Interest</span>
                    <strong className="font-mono text-sovereign-800 font-bold">{s.effective_interest_rate_pct || 9.5}% p.a.</strong>
                  </div>
                </div>

                <div className={`text-[11px] mt-2 line-clamp-2 italic ${isEligible ? 'text-slate-600' : 'text-rose-700'}`}>
                  <TranslatedText text={rationale} />
                </div>
              </div>

              {/* Official Scheme Portal External Link */}
              {s.official_url && (
                <div className="pt-2.5 mt-3 border-t border-slate-200/80 flex items-center justify-between">
                  <a
                    href={s.official_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] font-bold text-sovereign-800 hover:text-sovereign-950 hover:underline transition group"
                    title={`Visit official ${s.scheme_id} government portal (opens in new tab)`}
                  >
                    <span>Visit official {s.scheme_id} portal</span>
                    <ArrowUpRight className="w-3.5 h-3.5 text-sovereign-700 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                  </a>
                  <span className="text-[9px] text-slate-400 font-mono">official .gov.in</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Grounded Data Source Lineage Tag */}
      <div className="text-[10px] text-slate-500 flex flex-wrap items-center justify-between gap-2 pt-3 mt-4 border-t border-slate-200">
        <span>
          <strong className="text-slate-700">Data Source:</strong> Central & State Scheme Eligibility Matrix (<code className="font-mono text-sovereign-800 font-semibold">government_schemes.json</code>)
        </span>
        <span className="font-mono text-slate-600 font-medium">
          Source: Ministry of MSME, MoFPI & RBI Master Circulars
        </span>
      </div>

    </div>
  );
}
export default SchemeLeaderboardCard;
