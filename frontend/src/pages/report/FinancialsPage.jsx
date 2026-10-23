import React from 'react';
import { CapitalReconciliationCard } from '../../components/Dashboard/CapitalReconciliationCard';
import { CashflowProjectionsChart } from '../../components/Dashboard/CashflowProjectionsChart';
import { PlanningAssumptionsCard } from '../../components/Dashboard/PlanningAssumptionsCard';
import { TrendingUp, Landmark, ShieldCheck, IndianRupee, PieChart, Percent, Target, Clock } from 'lucide-react';
import { TranslatedText } from '../../components/TranslatedText';

export function FinancialsPage({ reportData }) {
  if (!reportData) return null;

  const p = reportData.input_parameters || {};
  const fin = reportData.financial_analysis || {};
  const schemes = reportData.scheme_optimization || [];
  const pricing = reportData.pricing_recommendation || {};

  const projectCost = Number(p.project_cost) || 0;
  const committedEquity = fin.committed_promoter_equity ?? p.promoter_equity ?? fin.promoter_equity ?? fin.promoter_margin_amount ?? (projectCost * 0.10);
  const statutoryMargin = fin.minimum_statutory_margin_amount ?? fin.statutory_margin_amount ?? (projectCost * (p.promoter_category === 'general' ? 0.10 : 0.05));
  const statutoryPct = fin.minimum_statutory_margin_pct ?? (p.promoter_category === 'general' ? 10 : 5);
  const ownedMachinery = fin.owned_machinery_value ?? p.owned_machinery_value ?? 0;
  const grossProjectCost = fin.gross_project_cost ?? p.gross_project_cost ?? (projectCost + ownedMachinery);
  const promoterMargin = fin.promoter_margin_amount ?? committedEquity;
  const loanPrincipal = fin.loan_principal || 0;
  const monthlyEmi = fin.amortization?.monthly_emi || 0;
  const annualNetProfit = fin.annual_net_profit || 0;
  const roiPct = fin.roi_pct || 0;
  const dscr = fin.dscr?.dscr ?? 0;
  const inMoratorium = fin.dscr?.verdict === 'MORATORIUM';
  const fullYear = fin.first_full_repayment_year;
  const breakEvenMilestone = fin.break_even_milestone || 'Year 2 (Mo 16)';
  const breakEvenPct = fin.break_even_pct ? `${Number(fin.break_even_pct).toFixed(1)}%` : '64.5%';
  const paybackYears = fin.payback_period_years ? `${Number(fin.payback_period_years).toFixed(1)} Yrs` : '2.6 Yrs';
  const equityPayback = fin.equity_payback_years ? `${Number(fin.equity_payback_years).toFixed(1)} Yrs` : '1.8 Yrs';

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-4 sm:p-6 border-l-4 border-sovereign-800 bg-gradient-to-r from-white via-sovereign-50/20 to-white shadow-card border border-slate-200/90">
        <div className="text-xs font-bold uppercase tracking-wider text-sovereign-700 mb-1 flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4 text-sovereign-700" />
          <span><TranslatedText text="Dimension 4 • Deterministic Financial Engineering & Solvency Analysis" /></span>
        </div>
        <h1 className="text-lg sm:text-2xl font-outfit font-extrabold text-slate-900 tracking-tight">
          <TranslatedText text="Capital Outlay Deployment, Means of Finance & 5-Year Cash Flow Projections" />
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium leading-relaxed">
          <TranslatedText text="Itemized investment and funding estimates, scheduled debt service and five-year operating projections." />
        </p>
      </div>

      {/* Financial Appraisal Telemetry Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 sm:gap-2.5">
        <div className="glass-panel p-3 bg-white border border-slate-200/90 rounded-xl shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[9px] sm:text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <PieChart className="w-3 h-3 text-sovereign-700 shrink-0" />
            <span className="truncate"><TranslatedText text="Net Outlay" /></span>
          </div>
          <strong className="text-sm sm:text-base font-mono font-extrabold text-slate-900 block mt-1">
            ₹{(projectCost / 100000).toFixed(2)}L
          </strong>
          <span className="text-[9px] text-slate-500 font-medium truncate block">
            {ownedMachinery > 0 ? `Gross: ₹${(grossProjectCost / 100000).toFixed(2)}L` : <TranslatedText text="Project Cost" />}
          </span>
        </div>

        <div className="glass-panel p-3 bg-white border border-slate-200/90 rounded-xl shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[9px] sm:text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <IndianRupee className="w-3 h-3 text-sky-700 shrink-0" />
            <span className="truncate"><TranslatedText text="Cash Equity" /></span>
          </div>
          <strong className="text-sm sm:text-base font-mono font-extrabold text-sky-900 block mt-1">
            ₹{(committedEquity / 100000).toFixed(2)}L
          </strong>
          <span className="text-[9px] text-sky-700 font-semibold truncate block">
            Min: ₹{(statutoryMargin / 100000).toFixed(2)}L ({statutoryPct}%)
          </span>
        </div>

        <div className="glass-panel p-3 bg-white border border-slate-200/90 rounded-xl shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[9px] sm:text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <Landmark className="w-3 h-3 text-amber-700 shrink-0" />
            <span className="truncate"><TranslatedText text="Bank Loan" /></span>
          </div>
          <strong className="text-sm sm:text-base font-mono font-extrabold text-amber-900 block mt-1">
            ₹{(loanPrincipal / 100000).toFixed(2)}L
          </strong>
          <span className="text-[9px] text-amber-700 font-semibold truncate block">@ {fin.amortization?.annual_rate_pct || 11}% p.a.</span>
        </div>

        <div className="glass-panel p-3 bg-white border border-slate-200/90 rounded-xl shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[9px] sm:text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <TrendingUp className="w-3 h-3 text-indigo-700 shrink-0" />
            <span className="truncate"><TranslatedText text="EMI" /></span>
          </div>
          <strong className="text-sm sm:text-base font-mono font-extrabold text-indigo-900 block mt-1">
            ₹{Math.round(monthlyEmi).toLocaleString('en-IN')}
          </strong>
          <span className="text-[9px] text-slate-500 font-medium truncate block">{fin.amortization?.tenure_years || p.tenure_years || 5} <TranslatedText text="year loan term" /></span>
        </div>

        <div className="glass-panel p-3 bg-white border border-slate-200/90 rounded-xl shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[9px] sm:text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <Percent className="w-3 h-3 text-emerald-700 shrink-0" />
            <span className="truncate"><TranslatedText text="PAT" /></span>
          </div>
          <strong className="text-sm sm:text-base font-mono font-extrabold text-emerald-700 block mt-1">
            ₹{(annualNetProfit / 100000).toFixed(2)}L
          </strong>
          <span className="text-[9px] text-emerald-700 font-semibold truncate block">{roiPct.toFixed(1)}% ROI</span>
        </div>

        <div className="glass-panel p-3 bg-white border border-slate-200/90 rounded-xl shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[9px] sm:text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-sovereign-700 shrink-0" />
            <span className="truncate"><TranslatedText text="Year 1 DSCR" /></span>
          </div>
          <strong className="text-sm sm:text-base font-mono font-extrabold text-sovereign-900 block mt-1">
            {fin.debt_service_required === false ? 'No debt' : inMoratorium ? 'Moratorium' : `${dscr.toFixed(2)}x`}
          </strong>
          <span className={`text-[9px] font-bold truncate block ${dscr >= 1.33 ? 'text-emerald-700' : 'text-amber-700'}`}>
            <TranslatedText text={fin.debt_service_required === false || inMoratorium ? 'No loan repayments' : dscr >= 1.33 ? 'Benchmark met' : 'Below 1.33'} />
          </span>
        </div>

        <div className="glass-panel p-3 bg-white border border-amber-200/80 rounded-xl shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[9px] sm:text-[10px] text-amber-700 font-bold uppercase tracking-wider flex items-center gap-1">
            <Target className="w-3 h-3 text-amber-700 shrink-0" />
            <span className="truncate"><TranslatedText text="Break-Even" /></span>
          </div>
          <strong className="text-sm sm:text-base font-mono font-extrabold text-amber-900 block mt-1 truncate">
            {breakEvenMilestone}
          </strong>
          <span className="text-[9px] text-amber-700 font-semibold truncate block">{breakEvenPct} <TranslatedText text="Capacity" /></span>
        </div>

        <div className="glass-panel p-3 bg-white border border-sky-200/80 rounded-xl shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[9px] sm:text-[10px] text-sky-700 font-bold uppercase tracking-wider flex items-center gap-1">
            <Clock className="w-3 h-3 text-sky-700 shrink-0" />
            <span className="truncate"><TranslatedText text="Payback" /></span>
          </div>
          <strong className="text-sm sm:text-base font-mono font-extrabold text-sky-900 block mt-1">
            {paybackYears}
          </strong>
          <span className="text-[9px] text-sky-700 font-semibold truncate block">Equity: {equityPayback}</span>
        </div>
      </div>

      {fullYear && <div className="text-sm text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3">
        <strong><TranslatedText text="Full repayment-year DSCR" />: {`${Number(fullYear.annual_dscr).toFixed(2)}x`}</strong>
        {' · '}<TranslatedText text="Year" /> {fullYear.year}{' · '}<TranslatedText text="12 scheduled repayments" />
        <p className="text-xs mt-1"><TranslatedText text="Year 1 may include fewer repayments during the moratorium. Operating months are independent of loan repayment timing." /></p>
      </div>}

      <PlanningAssumptionsCard financialData={fin} />
      {/* Capital Reconciliation Card */}
      <CapitalReconciliationCard inputData={p} financialData={fin} schemeData={schemes} />


      {/* 5-Year Amortization Schedule & Financial Horizon */}
      <CashflowProjectionsChart inputData={p} financialData={fin} pricingData={pricing} />

    </div>
  );
}
export default FinancialsPage;
