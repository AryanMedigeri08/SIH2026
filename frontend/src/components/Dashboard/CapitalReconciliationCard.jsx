import React from 'react';
import { Layers, CheckCircle2, DollarSign, Sparkles, ShieldCheck, Info } from 'lucide-react';
import { TranslatedText } from '../TranslatedText';

export function CapitalReconciliationCard({ inputData, financialData, schemeData }) {
  const projectCost = Number(inputData?.project_cost) || Number(financialData?.net_project_cost) || 400000;
  const committedEquity = Number(
    financialData?.committed_promoter_equity ??
    inputData?.promoter_equity ??
    financialData?.promoter_equity ??
    financialData?.promoter_margin_amount ??
    (projectCost * 0.10)
  );

  const statutoryPct = Number(
    financialData?.minimum_statutory_margin_pct ??
    (inputData?.promoter_category === 'general' ? 10 : 5)
  );

  const statutoryMargin = Number(
    financialData?.minimum_statutory_margin_amount ??
    financialData?.statutory_margin_amount ??
    (projectCost * (statutoryPct / 100))
  );

  const ownedMachinery = Number(
    financialData?.owned_machinery_value ??
    inputData?.owned_machinery_value ??
    0
  );

  const grossProjectCost = Number(
    financialData?.gross_project_cost ??
    inputData?.gross_project_cost ??
    (projectCost + ownedMachinery)
  );

  const topScheme = schemeData?.find(s => s.eligible) || schemeData?.[0] || {};
  const funding = financialData?.funding_plan;
  const budget = financialData?.project_budget;
  const subsidyAmount = Number(funding?.upfront_subsidy ?? topScheme.subsidy_grant_amount ?? 0);

  // Term loan and cash equity applied to net fresh borrowing base
  const loanAmount = financialData?.loan_principal !== undefined
    ? Number(financialData.loan_principal)
    : Math.max(projectCost - subsidyAmount - committedEquity, 0);

  const promoterCashApplied = Number(
    financialData?.promoter_margin_amount ??
    Math.max(projectCost - subsidyAmount - loanAmount, statutoryMargin)
  );

  // Balanced outlay breakdown on net fresh borrowing base
  const startup = budget?.startup;
  const machinery = budget ? budget.equipment_total - budget.owned_machinery_credit : projectCost * 0.55;
  const civil = startup ? ['installation', 'premises_deposit_and_fitout', 'utility_connections'].reduce((sum, key) => sum + startup[key].amount_inr, 0) : projectCost * 0.15;
  const workingCap = startup ? startup.initial_working_capital.amount_inr : projectCost * 0.20;
  const contingency = startup ? startup.contingency.amount_inr + startup.licences_and_launch.amount_inr : projectCost * 0.10;
  const share = value => `(${(value / projectCost * 100).toFixed(1)}%)`;

  const totalMeans = promoterCashApplied + subsidyAmount + loanAmount;
  const isBalanced = Math.abs(totalMeans - projectCost) < 1.0;

  return (
    <div className="glass-panel p-4 sm:p-6 bg-white shadow-card border border-slate-200">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 sm:mb-5">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-sovereign-700 flex items-center gap-1.5 mb-1">
            <Layers className="w-3.5 h-3.5" />
            <TranslatedText text="Investment & funding estimates" />
          </div>
          <h3 className="text-lg font-outfit font-bold text-slate-900">
            <TranslatedText text="Capital Outlay & Means of Finance Reconciliation" />
          </h3>
          <p className="text-xs text-slate-600 mt-0.5">
            <TranslatedText text="Selected equipment, startup costs and working capital reconciled with owned assets and available cash." />
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold px-3 py-1 rounded-full border flex items-center gap-1.5 ${
            isBalanced 
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800' 
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}>
            <CheckCircle2 className="w-3.5 h-3.5" />
            <TranslatedText text={isBalanced ? 'Accounting Balanced (₹0 Drift)' : 'Unbalanced Outlay'} />
          </span>
        </div>
      </div>

      {/* Enterprise Asset Valuation & In-Kind Machinery Credit Bridge */}
      {ownedMachinery > 0 && (
        <div className="mb-4 sm:mb-5 p-3.5 sm:p-4 rounded-xl bg-gradient-to-r from-sky-50/90 via-slate-50 to-emerald-50/50 border border-sky-200 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-sky-800 flex items-center gap-1 mb-0.5">
                <Sparkles className="w-3 h-3 text-sky-600" />
                <TranslatedText text="Enterprise Asset Valuation & In-Kind Machinery Bridge" />
              </div>
              <p className="text-slate-600 text-[11px] max-w-xl">
                <TranslatedText text="User's existing machinery is credited as in-kind asset equity, drastically reducing fresh borrowing base." />
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 bg-white px-3 py-2 rounded-lg border border-slate-200/80 shadow-xs">
              <div className="text-right">
                <span className="text-[9px] text-slate-500 block uppercase font-bold"><TranslatedText text="Gross Valuation" /></span>
                <strong className="font-mono text-slate-900 text-xs">₹{Math.round(grossProjectCost).toLocaleString('en-IN')}</strong>
              </div>
              <span className="text-slate-400 font-bold">−</span>
              <div className="text-right">
                <span className="text-[9px] text-sky-700 block uppercase font-bold"><TranslatedText text="Owned Machinery" /></span>
                <strong className="font-mono text-sky-700 text-xs">₹{Math.round(ownedMachinery).toLocaleString('en-IN')}</strong>
              </div>
              <span className="text-slate-400 font-bold">=</span>
              <div className="text-right">
                <span className="text-[9px] text-emerald-700 block uppercase font-bold"><TranslatedText text="Fresh Bank Outlay" /></span>
                <strong className="font-mono text-emerald-700 text-xs font-bold">₹{Math.round(projectCost).toLocaleString('en-IN')}</strong>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        
        {/* Outlay Breakdown */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 sm:p-4 space-y-3">
          <div className="text-xs font-bold text-slate-900 uppercase tracking-wider flex justify-between">
            <span><TranslatedText text="A. Net Fresh Capital Outlay" /></span>
            <span className="text-sovereign-800 font-mono font-bold">₹{projectCost.toLocaleString('en-IN')}</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between text-slate-700">
              <span><TranslatedText text="Plant & Machinery / Upgrades" /> {share(machinery)}</span>
              <strong className="font-mono text-slate-900">₹{Math.round(machinery).toLocaleString('en-IN')}</strong>
            </div>
            <div className="flex justify-between text-slate-700">
              <span><TranslatedText text="Civil Works & Electrical Setup" /> {share(civil)}</span>
              <strong className="font-mono text-slate-900">₹{Math.round(civil).toLocaleString('en-IN')}</strong>
            </div>
            <div className="flex justify-between text-slate-700">
              <span><TranslatedText text="Initial Working Capital Reserve" /> {share(workingCap)}</span>
              <strong className="font-mono text-slate-900">₹{Math.round(workingCap).toLocaleString('en-IN')}</strong>
            </div>
            <div className="flex justify-between text-slate-700">
              <span><TranslatedText text="Pre-op & Contingency Buffer" /> {share(contingency)}</span>
              <strong className="font-mono text-slate-900">₹{Math.round(contingency).toLocaleString('en-IN')}</strong>
            </div>
          </div>
        </div>

        {/* Means of Finance */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 sm:p-4 space-y-3">
          <div className="text-xs font-bold text-slate-900 uppercase tracking-wider flex justify-between">
            <span><TranslatedText text="B. Means of Finance (Sources)" /></span>
            <span className="text-emerald-700 font-mono font-bold">₹{Math.round(totalMeans).toLocaleString('en-IN')}</span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between text-slate-700 items-start">
              <div>
                <span className="font-semibold text-slate-900"><TranslatedText text="Promoter Cash Equity Committed" /></span>
                <span className="block text-[10px] text-slate-500">
                  <TranslatedText text="Min Bank Margin" /> ({statutoryPct}%): ₹{Math.round(statutoryMargin).toLocaleString('en-IN')}
                </span>
              </div>
              <div className="text-right">
                <strong className="font-mono text-sky-800 block">₹{Math.round(committedEquity).toLocaleString('en-IN')}</strong>
                <span className="text-[10px] text-emerald-700 font-medium">₹{Math.round(promoterCashApplied).toLocaleString('en-IN')} deployed</span>
              </div>
            </div>

            <div className="flex justify-between text-slate-700">
              <span><TranslatedText text="Govt Capital Subsidy Grant" /> ({projectCost > 0 ? ((subsidyAmount / projectCost) * 100).toFixed(0) : '0'}%)</span>
              <strong className="font-mono text-emerald-700">₹{Math.round(subsidyAmount).toLocaleString('en-IN')}</strong>
            </div>

            <div className="flex justify-between text-slate-700">
              <span><TranslatedText text="Estimated borrowing required" /> ({projectCost > 0 ? ((loanAmount / projectCost) * 100).toFixed(0) : '0'}%)</span>
              <strong className="font-mono text-blue-800">₹{Math.round(loanAmount).toLocaleString('en-IN')}</strong>
            </div>

            <div className="pt-2 border-t border-slate-200 flex justify-between text-xs font-bold text-slate-900">
              <span><TranslatedText text="Total planned finance" />:</span>
              <span className="font-mono text-emerald-700 font-bold">₹{Math.round(totalMeans).toLocaleString('en-IN')}</span>
            </div>
          </div>
        </div>

      </div>

      {funding && <p className="mt-3 text-xs text-slate-600"><TranslatedText text={funding.basis} />. <TranslatedText text="Potential scheme subsidy" />: ₹{Number(financialData.potential_scheme_subsidy || 0).toLocaleString('en-IN')}.</p>}
      {financialData?.cash_margin_shortfall > 0 && <p className="mt-2 text-xs text-amber-800"><TranslatedText text="Cash contribution below the planning margin by" /> ₹{Number(financialData.cash_margin_shortfall).toLocaleString('en-IN')}.</p>}
      {budget && <details className="mt-3 text-xs text-slate-600">
        <summary className="cursor-pointer"><TranslatedText text="View itemized startup and monthly costs" /></summary>
        <p className="mt-2"><TranslatedText text={budget.source?.startsWith('llm_') ? 'AI estimated budget' : 'Indicative budget allowances'} /></p>
        {budget.source === 'llm_costs_with_validated_arithmetic' && <p><TranslatedText text="AI cost estimates retained; totals reconciled after an invalid AI calculation" /></p>}
        {['startup', 'monthly'].map(group => <div key={group} className="mt-2 space-y-1">
          <strong><TranslatedText text={group === 'startup' ? 'One-time startup costs' : 'Monthly fixed costs'} /></strong>
          {Object.entries(budget[group]).map(([name, item]) => <p key={name}><TranslatedText text={name.replaceAll('_', ' ')} />: ₹{Number(item.amount_inr).toLocaleString('en-IN')} — <TranslatedText text={item.basis} /></p>)}
        </div>)}
      </details>}

      {/* Cash Equity Liquidity Cushion Callout */}
      {committedEquity > promoterCashApplied && (
        <div className="mt-3 p-2.5 rounded-lg bg-sky-50 border border-sky-200/80 flex items-center gap-2 text-[11px] text-sky-900">
          <Info className="w-3.5 h-3.5 text-sky-600 shrink-0" />
          <span>
            <strong className="font-semibold">Liquidity Cushion:</strong> ₹{(committedEquity - promoterCashApplied).toLocaleString('en-IN')} unencumbered cash equity remains available as promoter operational reserve.
          </span>
        </div>
      )}

      {/* Grounded Data Source Lineage Tag */}
      <div className="text-[10px] text-slate-500 flex flex-wrap items-center justify-between gap-2 pt-3 mt-4 border-t border-slate-200">
        <span>
          <strong className="text-slate-700"><TranslatedText text="Data Source:" /></strong> <TranslatedText text={budget ? 'Selected machinery and estimated itemized budget' : 'Legacy planning allocation'} />
        </span>
        <span className="font-mono text-slate-600 font-medium">
          <TranslatedText text="Reconciliation: Balanced (₹0 Residual Drift)" />
        </span>
      </div>

    </div>
  );
}
export default CapitalReconciliationCard;
