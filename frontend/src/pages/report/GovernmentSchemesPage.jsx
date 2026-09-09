import React from 'react';
import { SchemeComparisonChart } from '../../components/Dashboard/SchemeComparisonChart';
import { SchemeLeaderboardCard } from '../../components/Dashboard/SchemeLeaderboardCard';
import { Award, ShieldCheck, CheckCircle2, ArrowRight, Sparkles, Building, Landmark, BookOpen, ExternalLink } from 'lucide-react';
import { TranslatedText } from '../../components/TranslatedText';

const STATUTORY_SCHEME_SPECS = [
  {
    scheme_id: "PMEGP",
    name: "Prime Minister's Employment Generation Programme",
    ministry: "Ministry of MSME / KVIC",
    max_cost: "Mfg: ₹50 Lakhs | Service: ₹20 Lakhs",
    subsidy_slabs: "General: 15% (Urban) / 25% (Rural) | Special: 25% (Urban) / 35% (Rural)",
    promoter_margin: "General: 10% | Special: 5%",
    collateral: "Collateral-free up to ₹50 Lakhs under CGTMSE",
    portal: "https://pmegp.msme.gov.in/",
  },
  {
    scheme_id: "PMFME",
    name: "PM Formalisation of Micro Food Processing Enterprises",
    ministry: "Ministry of Food Processing Industries (MoFPI)",
    max_cost: "No ceiling (Subsidy capped at ₹10 Lakhs)",
    subsidy_slabs: "35% credit-linked capital subsidy (Max ₹10 Lakhs)",
    promoter_margin: "Minimum 10% of total project cost",
    collateral: "CGTMSE coverage eligible",
    portal: "https://pmfme.mofpi.gov.in/",
  },
  {
    scheme_id: "MUDRA (PMMY)",
    name: "Pradhan Mantri MUDRA Yojana",
    ministry: "Department of Financial Services (DFS)",
    max_cost: "Shishu: Up to ₹50k | Kishore: ₹50k–₹5L | Tarun: ₹5L–₹10L (Tarun Plus ₹20L)",
    subsidy_slabs: "0% upfront capital subsidy (Subsidized base bank interest rate)",
    promoter_margin: "Nil to 10%",
    collateral: "100% Collateral-free under CGFMU",
    portal: "https://www.mudra.org.in/",
  },
  {
    scheme_id: "Stand-Up India",
    name: "Stand-Up India Scheme for Women & SC/ST",
    ministry: "Department of Financial Services (DFS)",
    max_cost: "Composite loan: ₹10 Lakhs to ₹100 Lakhs",
    subsidy_slabs: "0% upfront capital subsidy (Composite term loan + working capital)",
    promoter_margin: "Up to 15% (can be converged with state subsidies)",
    collateral: "Collateral-free via CGFSIL guarantee cover",
    portal: "https://www.standupmitra.in/",
  },
  {
    scheme_id: "PM Vishwakarma",
    name: "PM Vishwakarma Artisan Support Scheme",
    ministry: "Ministry of MSME",
    max_cost: "Tranche 1: ₹1 Lakh | Tranche 2: ₹2 Lakhs (Total ₹3 Lakhs)",
    subsidy_slabs: "Concessional 5% fixed interest rate (8% interest subvention paid by MoMSME)",
    promoter_margin: "Nil",
    collateral: "100% Collateral-free government guarantee",
    portal: "https://pmvishwakarma.gov.in/",
  },
];

export function GovernmentSchemesPage({ reportData }) {
  if (!reportData) return null;

  const p = reportData.input_parameters || {};
  const ml = reportData.ml_viability || {};
  const fin = reportData.financial_analysis || {};
  const schemes = reportData.scheme_optimization || [];
  const topScheme = schemes.find(s => s.eligible) || schemes[0] || {};
  
  const projectCost = p.project_cost || 0;
  const subsidyAmount = topScheme.subsidy_grant_amount || 0;
  const subsidyPct = projectCost > 0 ? ((subsidyAmount / projectCost) * 100).toFixed(0) : '0';
  const promoterMargin = fin.promoter_margin_amount || (projectCost * (p.promoter_category === 'general' ? 0.10 : 0.05));
  const termLoan = fin.loan_principal || Math.max(projectCost - subsidyAmount - promoterMargin, 0);
  const dscr = fin.dscr?.dscr ?? 1.33;

  const isReconsider = ml.verdict === 'RECONSIDER' || dscr < 1.0;
  const isCaution = ml.verdict === 'CAUTION' || (dscr >= 1.0 && dscr < 1.33);

  const cardBorderClass = isReconsider 
    ? 'border-l-4 border-rose-500' 
    : isCaution 
    ? 'border-l-4 border-amber-500' 
    : 'border-l-4 border-emerald-600';

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-4 sm:p-6 border-l-4 border-emerald-600 bg-gradient-to-r from-white via-emerald-50/20 to-white shadow-card border border-slate-200/90">
        <div className="text-xs font-bold uppercase tracking-wider text-emerald-700 mb-1 flex items-center gap-1.5">
          <Award className="w-4 h-4 text-emerald-600" />
          <span><TranslatedText text="Dimension 3 • Statutory MSME Schemes & Incentive Optimization" /></span>
        </div>
        <h1 className="text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
          <TranslatedText text="Central & State Scheme Ranking, Capital Subsidies & Official Portals" />
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
          <TranslatedText text="Automatically evaluated against statutory MSME guidelines (PMEGP, PMFME, MUDRA, Stand-Up India, PM Vishwakarma, DAY-NRLM, AHIDF). Verified official government portal links are provided for each eligible incentive scheme." />
        </p>
      </div>

      {/* Top Scheme Recommendation Hero Banner */}
      <div className={`p-4 sm:p-6 bg-white rounded-2xl shadow-card border border-slate-200/90 ${cardBorderClass}`}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 sm:gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              {isReconsider ? (
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-50 border border-rose-200 text-rose-800 text-xs font-bold font-mono">
                  <span className="w-2 h-2 rounded-full bg-rose-600 animate-pulse" />
                  <span><TranslatedText text="Optimal Policy Match • Capital Restructuring Required" /></span>
                </div>
              ) : isCaution ? (
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800 text-xs font-bold font-mono">
                  <span className="w-2 h-2 rounded-full bg-amber-600" />
                  <span><TranslatedText text="Optimal Policy Match • Tight Debt Coverage" /></span>
                </div>
              ) : (
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold font-mono">
                  <Sparkles className="w-3.5 h-3.5 text-amber-600 fill-amber-500" />
                  <span><TranslatedText text="Rank 1 Recommended Statutory Match" /></span>
                </div>
              )}
            </div>

            <h2 className="text-2xl sm:text-3xl font-outfit font-extrabold text-slate-900 tracking-tight">
              {topScheme.scheme_id}: <TranslatedText text={topScheme.full_name} />
            </h2>
            <p className="text-xs text-slate-600 max-w-2xl font-medium leading-relaxed">
              <TranslatedText text="Provides the highest Net Financial Benefit by maximizing upfront non-repayable capital subsidy and minimizing debt service burden." />
            </p>
          </div>

          {/* Quick Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-3 shrink-0">
            <div className="p-3 sm:p-3.5 rounded-xl bg-emerald-50/60 border border-emerald-200">
              <div className="text-[10px] text-emerald-800 font-bold uppercase tracking-wider">
                <TranslatedText text="Capital Subsidy" />
              </div>
              <div className="text-xl font-mono font-black text-emerald-700 mt-0.5">
                ₹{Math.round(subsidyAmount).toLocaleString('en-IN')}
              </div>
              <div className="text-[10px] text-emerald-700 font-semibold">{subsidyPct}% <TranslatedText text="Capital Subsidy" /></div>
            </div>

            <div className="p-3.5 rounded-xl bg-sky-50/60 border border-sky-200">
              <div className="text-[10px] text-sky-800 font-bold uppercase tracking-wider">
                <TranslatedText text="Promoter Equity" />
              </div>
              <div className="text-xl font-mono font-black text-sky-900 mt-0.5">
                ₹{Math.round(promoterMargin).toLocaleString('en-IN')}
              </div>
              <div className="text-[10px] text-sky-700 font-semibold">{p.promoter_category === 'general' ? '10%' : '5%'} <TranslatedText text="Own Equity" /></div>
            </div>

            <div className="p-3.5 rounded-xl bg-amber-50/60 border border-amber-200 col-span-2 sm:col-span-1">
              <div className="text-[10px] text-amber-800 font-bold uppercase tracking-wider">
                <TranslatedText text="Bank Term Loan" />
              </div>
              <div className="text-xl font-mono font-black text-amber-900 mt-0.5">
                ₹{Math.round(termLoan).toLocaleString('en-IN')}
              </div>
              <div className="text-[10px] text-amber-700 font-semibold">@ {topScheme.effective_interest_rate_pct || 11}% p.a.</div>
            </div>
          </div>
        </div>

        {/* Subtle Context-Aware Credit Appraisal Advisory Note */}
        {isReconsider ? (
          <div className="mt-4 p-3.5 rounded-xl bg-rose-50/90 border border-rose-200 text-xs text-rose-950 flex items-start gap-2.5">
            <span className="p-1 rounded-md bg-rose-100 text-rose-700 font-bold shrink-0 text-[10px] font-mono uppercase"><TranslatedText text="Notice" /></span>
            <div className="leading-relaxed">
              <strong className="font-bold text-rose-900"><TranslatedText text="Prudential Underwriting Advisory:" />{" "}</strong>
              <span>
                <TranslatedText text={`While ${topScheme.scheme_id} provides the highest statutory grant support, the enterprise's current Debt Service Coverage Ratio is below the RBI viability benchmark (1.33). To qualify for formal bank loan sanction, it is recommended to increase promoter equity contribution, request an extended repayment moratorium, or restructure initial capital outlay.`} />
              </span>
            </div>
          </div>
        ) : isCaution ? (
          <div className="mt-4 p-3.5 rounded-xl bg-amber-50/90 border border-amber-200 text-xs text-amber-950 flex items-start gap-2.5">
            <span className="p-1 rounded-md bg-amber-100 text-amber-700 font-bold shrink-0 text-[10px] font-mono uppercase"><TranslatedText text="Advisory" /></span>
            <div className="leading-relaxed">
              <strong className="font-bold text-amber-900"><TranslatedText text="Solvency Advisory:" />{" "}</strong>
              <span>
                <TranslatedText text={`${topScheme.scheme_id} is the optimal financial match; however, debt coverage is tight. Maintaining a 3-month EMI reserve before bank disbursal is recommended.`} />
              </span>
            </div>
          </div>
        ) : null}
      </div>

      {/* Comparison Chart: Subsidy vs Interest */}
      <SchemeComparisonChart schemes={schemes} />

      {/* Ranked Scheme Leaderboard with Verified Official URLs */}
      <SchemeLeaderboardCard schemes={schemes} isReconsider={isReconsider} />

      {/* Statutory Scheme Specifications & Norms Reference Matrix */}
      <div className="glass-panel p-4 sm:p-6 bg-white border border-slate-200 shadow-card space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <div className="p-2 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-outfit font-bold text-slate-900">
              <TranslatedText text="Statutory Government Scheme Reference Matrix (2025–2026 Guidelines)" />
            </h3>
            <p className="text-xs text-slate-500 font-medium">
              <TranslatedText text="Official credit guidelines, subsidy slabs, promoter contribution norms, and collateral-free thresholds" />
            </p>
          </div>
        </div>

        <div className="overflow-x-auto scroll-touch-x">
          <table className="w-full text-left text-xs border-collapse min-w-[640px]">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-700 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-3"><TranslatedText text="Scheme ID" /></th>
                <th className="py-3 px-3"><TranslatedText text="Nodal Ministry" /></th>
                <th className="py-3 px-3"><TranslatedText text="Project Cost Limit" /></th>
                <th className="py-3 px-3"><TranslatedText text="Subsidy / Subvention Slab" /></th>
                <th className="py-3 px-3"><TranslatedText text="Promoter Share" /></th>
                <th className="py-3 px-3"><TranslatedText text="Collateral Norms" /></th>
                <th className="py-3 px-3 text-right"><TranslatedText text="Official Portal" /></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {STATUTORY_SCHEME_SPECS.map((spec) => (
                <tr key={spec.scheme_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-3">
                    <span className="font-outfit font-extrabold text-sm text-slate-900 block">{spec.scheme_id}</span>
                    <span className="text-[10px] text-slate-500 line-clamp-1"><TranslatedText text={spec.name} /></span>
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-slate-600">
                    <TranslatedText text={spec.ministry} />
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-sovereign-900 font-bold">
                    <TranslatedText text={spec.max_cost} />
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-emerald-800 font-semibold">
                    <TranslatedText text={spec.subsidy_slabs} />
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-slate-700">
                    <TranslatedText text={spec.promoter_margin} />
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-slate-600">
                    <TranslatedText text={spec.collateral} />
                  </td>
                  <td className="py-3 px-3 text-right">
                    <a
                      href={spec.portal}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-sovereign-800 hover:text-sky-700 underline"
                    >
                      <span><TranslatedText text="Portal" /></span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
export default GovernmentSchemesPage;
