import React from 'react';
import { SchemeComparisonChart } from '../../components/Dashboard/SchemeComparisonChart';
import { SchemeLeaderboardCard } from '../../components/Dashboard/SchemeLeaderboardCard';
import { Award, ShieldCheck, CheckCircle2, ArrowRight, Sparkles, Building, Landmark, BookOpen, ExternalLink } from 'lucide-react';

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
  const fin = reportData.financial_analysis || {};
  const schemes = reportData.scheme_optimization || [];
  const topScheme = schemes.find(s => s.eligible) || schemes[0] || {};
  
  const projectCost = p.project_cost || 0;
  const subsidyAmount = topScheme.subsidy_grant_amount || 0;
  const subsidyPct = projectCost > 0 ? ((subsidyAmount / projectCost) * 100).toFixed(0) : '0';
  const promoterMargin = fin.promoter_margin_amount || (projectCost * (p.promoter_category === 'general' ? 0.10 : 0.05));
  const termLoan = fin.loan_principal || Math.max(projectCost - subsidyAmount - promoterMargin, 0);

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-emerald-600 bg-gradient-to-r from-white via-emerald-50/20 to-white shadow-card border border-slate-200/90">
        <div className="text-xs font-bold uppercase tracking-wider text-emerald-700 mb-1 flex items-center gap-1.5">
          <Award className="w-4 h-4 text-emerald-600" />
          <span>Dimension 3 • Statutory MSME Schemes & Incentive Optimization</span>
        </div>
        <h1 className="text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
          Central & State Scheme Ranking, Capital Subsidies & Official Portals
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
          Automatically evaluated against statutory MSME guidelines (PMEGP, PMFME, MUDRA, Stand-Up India, PM Vishwakarma, DAY-NRLM, AHIDF). Verified official government portal links are provided for each eligible incentive scheme.
        </p>
      </div>

      {/* Top Scheme Recommendation Hero Banner */}
      <div className="glass-panel p-6 bg-gradient-to-r from-emerald-900 via-sovereign-900 to-slate-900 text-white rounded-2xl shadow-xl border border-emerald-500/30">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-xs font-bold font-mono">
              <Sparkles className="w-3.5 h-3.5 text-amber-300 fill-amber-300" />
              <span>Rank 1 Recommended Statutory Match</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-outfit font-extrabold text-white">
              {topScheme.scheme_id}: {topScheme.full_name}
            </h2>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Provides the highest Net Financial Benefit by maximizing upfront non-repayable capital subsidy and minimizing debt service burden.
            </p>
          </div>

          {/* Quick Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 shrink-0">
            <div className="p-3 rounded-xl bg-white/10 backdrop-blur-md border border-white/10">
              <div className="text-[10px] text-emerald-300 font-bold uppercase">Subsidy Grant</div>
              <div className="text-lg font-outfit font-black text-white mt-0.5">
                ₹{Math.round(subsidyAmount).toLocaleString('en-IN')}
              </div>
              <div className="text-[10px] text-emerald-200">{subsidyPct}% Capital Subsidy</div>
            </div>

            <div className="p-3 rounded-xl bg-white/10 backdrop-blur-md border border-white/10">
              <div className="text-[10px] text-sky-300 font-bold uppercase">Promoter Margin</div>
              <div className="text-lg font-outfit font-black text-white mt-0.5">
                ₹{Math.round(promoterMargin).toLocaleString('en-IN')}
              </div>
              <div className="text-[10px] text-sky-200">{p.promoter_category === 'general' ? '10%' : '5%'} Own Equity</div>
            </div>

            <div className="p-3 rounded-xl bg-white/10 backdrop-blur-md border border-white/10 col-span-2 sm:col-span-1">
              <div className="text-[10px] text-amber-300 font-bold uppercase">Net Bank Loan</div>
              <div className="text-lg font-outfit font-black text-white mt-0.5">
                ₹{Math.round(termLoan).toLocaleString('en-IN')}
              </div>
              <div className="text-[10px] text-amber-200">@ {topScheme.effective_interest_rate_pct || 11}% p.a.</div>
            </div>
          </div>
        </div>
      </div>

      {/* Comparison Chart: Subsidy vs Interest */}
      <SchemeComparisonChart schemes={schemes} />

      {/* Ranked Scheme Leaderboard with Verified Official URLs */}
      <SchemeLeaderboardCard schemes={schemes} />

      {/* Statutory Scheme Specifications & Norms Reference Matrix */}
      <div className="glass-panel p-6 bg-white border border-slate-200 shadow-card space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <div className="p-2 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-outfit font-bold text-slate-900">
              Statutory Government Scheme Reference Matrix (2025–2026 Guidelines)
            </h3>
            <p className="text-xs text-slate-500 font-medium">
              Official credit guidelines, subsidy slabs, promoter contribution norms, and collateral-free thresholds
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-700 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-3">Scheme ID</th>
                <th className="py-3 px-3">Nodal Ministry</th>
                <th className="py-3 px-3">Project Cost Limit</th>
                <th className="py-3 px-3">Subsidy / Subvention Slab</th>
                <th className="py-3 px-3">Promoter Share</th>
                <th className="py-3 px-3">Collateral Norms</th>
                <th className="py-3 px-3 text-right">Official Portal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {STATUTORY_SCHEME_SPECS.map((spec) => (
                <tr key={spec.scheme_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-3">
                    <span className="font-outfit font-extrabold text-sm text-slate-900 block">{spec.scheme_id}</span>
                    <span className="text-[10px] text-slate-500 line-clamp-1">{spec.name}</span>
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-slate-600">
                    {spec.ministry}
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-sovereign-900 font-bold">
                    {spec.max_cost}
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-emerald-800 font-semibold">
                    {spec.subsidy_slabs}
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-slate-700">
                    {spec.promoter_margin}
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-slate-600">
                    {spec.collateral}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <a
                      href={spec.portal}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-sovereign-800 hover:text-sky-700 underline"
                    >
                      <span>Portal</span>
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
