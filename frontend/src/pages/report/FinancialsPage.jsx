import React from 'react';
import { CapitalReconciliationCard } from '../../components/Dashboard/CapitalReconciliationCard';
import { CashflowProjectionsChart } from '../../components/Dashboard/CashflowProjectionsChart';
import { TrendingUp, Landmark, ShieldCheck, IndianRupee, PieChart, Percent, CheckCircle2, ArrowUpRight } from 'lucide-react';
import { TranslatedText } from '../../components/TranslatedText';

export function FinancialsPage({ reportData }) {
  if (!reportData) return null;

  const p = reportData.input_parameters || {};
  const fin = reportData.financial_analysis || {};
  const schemes = reportData.scheme_optimization || [];
  const pricing = reportData.pricing_recommendation || {};

  const capStruct = reportData.capital_structure || fin.capital_structure || null;
  const projectCost = Number(capStruct?.true_project_outlay || capStruct?.project_cost || p.project_cost) || 0;
  const promoterMargin = capStruct?.available_promoter_cash !== undefined
    ? capStruct.available_promoter_cash
    : (capStruct?.effective_promoter_cash !== undefined 
        ? capStruct.effective_promoter_cash 
        : (fin.promoter_margin_amount || (projectCost * (p.promoter_category === 'general' ? 0.10 : 0.05))));
  const scaBridge = capStruct?.sca_soft_loan_eligible_amount || capStruct?.sca_soft_loan_bridge || 0;
  const totalMargin = promoterMargin + scaBridge;
  const loanPrincipal = capStruct?.bank_term_loan !== undefined 
    ? capStruct.bank_term_loan 
    : (fin.loan_principal || 0);
  const monthlyEmi = fin.amortization?.monthly_emi || 0;
  const annualNetProfit = fin.annual_net_profit || 0;
  const roiPct = fin.roi_pct || 0;
  const dscr = fin.dscr?.dscr ?? 1.33;

  return (
    <div className="space-y-6">
      {reportData.financing_selection && <div className="rounded-2xl border border-sovereign-200 bg-sovereign-50 p-4 space-y-2">
        <h2 className="font-bold">Your selected financing exploration: {({ normal: 'normal bank loan', sca: 'SCA margin assistance', self: 'own funds' })[reportData.financing_selection.choice]}</h2>
        <p className="text-sm">Own contribution: ₹{Number(reportData.financing_selection.personal_contribution || 0).toLocaleString('en-IN')} · Remaining funding need: ₹{Number(reportData.financing_selection.remaining_funding_need || 0).toLocaleString('en-IN')}</p>
        <p className="text-xs text-slate-600">{reportData.financing_selection.notice}</p>
      </div>}
      
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
          <TranslatedText text="Zero-drift capital outlay sizing, statutory promoter margin reconciliation, RBI-compliant Debt Service Coverage Ratio (DSCR) testing, and 5-year capacity ramp projections with tax depreciation." />
        </p>
      </div>

      {/* Financial Appraisal Telemetry Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3">
        <div className="glass-panel p-3.5 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <PieChart className="w-3 h-3 text-sovereign-700" />
            <span><TranslatedText text="Project Cost" /></span>
          </div>
          <strong className="text-base sm:text-lg font-mono font-extrabold text-slate-900 block mt-1">
            ₹{(projectCost / 100000).toFixed(2)}L
          </strong>
          <span className="text-[10px] text-slate-500 font-medium"><TranslatedText text="Total Outlay" /></span>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <IndianRupee className="w-3 h-3 text-sky-700" />
            <span><TranslatedText text="Promoter Equity" /></span>
          </div>
          <strong className="text-base sm:text-lg font-mono font-extrabold text-sky-900 block mt-1">
            ₹{(totalMargin / 100000).toFixed(2)}L
          </strong>
          <span className="text-[10px] text-sky-700 font-semibold">
            {scaBridge > 0 ? (
              <span>₹{(promoterMargin / 100000).toFixed(2)}L Cash + ₹{(scaBridge / 100000).toFixed(2)}L SCA</span>
            ) : (
              <span>{projectCost > 0 ? ((promoterMargin / projectCost) * 100).toFixed(0) : '10'}% <TranslatedText text="Margin" /></span>
            )}
          </span>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <Landmark className="w-3 h-3 text-amber-700" />
            <span><TranslatedText text="Bank Term Loan" /></span>
          </div>
          <strong className="text-base sm:text-lg font-mono font-extrabold text-amber-900 block mt-1">
            ₹{(loanPrincipal / 100000).toFixed(2)}L
          </strong>
          <span className="text-[10px] text-amber-700 font-semibold">@ {fin.amortization?.annual_rate_pct || 11}% p.a.</span>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <TrendingUp className="w-3 h-3 text-indigo-700" />
            <span><TranslatedText text={scaBridge > 0 ? "Total Debt Service" : "Monthly EMI"} /></span>
          </div>
          <strong className="text-base sm:text-lg font-mono font-extrabold text-indigo-900 block mt-1">
            ₹{Math.round(monthlyEmi + (capStruct?.sca_monthly_emi || (scaBridge > 0 ? (scaBridge * 0.03 / 12) / (1 - Math.pow(1 + 0.03/12, -60)) : 0))).toLocaleString('en-IN')}
          </strong>
          <span className="text-[10px] text-slate-500 font-medium">
            {scaBridge > 0 ? (
              <span>Bank: ₹{Math.round(monthlyEmi).toLocaleString('en-IN')} + SCA: ₹{Math.round(capStruct?.sca_monthly_emi || ((scaBridge * 0.03 / 12) / (1 - Math.pow(1 + 0.03/12, -60))))}</span>
            ) : (
              <span>5-Yr Amortized</span>
            )}
          </span>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <Percent className="w-3 h-3 text-emerald-700" />
            <span><TranslatedText text="Annual PAT" /></span>
          </div>
          <strong className="text-base sm:text-lg font-mono font-extrabold text-emerald-700 block mt-1">
            ₹{(annualNetProfit / 100000).toFixed(2)}L
          </strong>
          <span className="text-[10px] text-emerald-700 font-semibold">{roiPct.toFixed(1)}% ROI</span>
        </div>

        <div className="glass-panel p-3.5 bg-white border border-slate-200/90 shadow-card hover:shadow-card-hover transition-all">
          <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-sovereign-700" />
            <span><TranslatedText text="DSCR Solvency" /></span>
          </div>
          <strong className="text-base sm:text-lg font-mono font-extrabold text-sovereign-900 block mt-1">
            {dscr.toFixed(2)}x
          </strong>
          <span className={`text-[10px] font-bold ${dscr >= 1.33 ? 'text-emerald-700' : 'text-amber-700'}`}>
            <TranslatedText text={dscr >= 1.33 ? 'RBI Compliant' : 'Below 1.33'} />
          </span>
        </div>
      </div>

      {/* Capital Reconciliation Card */}
      <CapitalReconciliationCard reportData={reportData} inputData={p} financialData={fin} schemeData={schemes} />


      {/* 5-Year Amortization Schedule & Financial Horizon */}
      <CashflowProjectionsChart inputData={p} financialData={fin} pricingData={pricing} />

    </div>
  );
}
export default FinancialsPage;
