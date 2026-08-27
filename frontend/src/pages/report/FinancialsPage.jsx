import React from 'react';
import { CapitalReconciliationCard } from '../../components/Dashboard/CapitalReconciliationCard';
import { DscrGaugeChart } from '../../components/Dashboard/DscrGaugeChart';
import { CashflowProjectionsChart } from '../../components/Dashboard/CashflowProjectionsChart';
import { TrendingUp, Landmark, ShieldCheck } from 'lucide-react';

export function FinancialsPage({ reportData }) {
  if (!reportData) return null;

  const p = reportData.input_parameters || {};
  const fin = reportData.financial_analysis || {};
  const schemes = reportData.scheme_optimization || [];
  const pricing = reportData.pricing_recommendation || {};

  return (
    <div className="space-y-6">
      
      {/* Header Banner */}
      <div className="glass-panel p-6 border-l-4 border-sovereign-800 bg-white shadow-card border border-slate-200">
        <div className="text-xs font-bold uppercase tracking-wider text-sovereign-700 mb-1 flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4" />
          <span>Dimension 4 • Deterministic Financial Engineering & Solvency Analysis</span>
        </div>
        <h1 className="text-2xl font-outfit font-extrabold text-slate-900">
          Capital Outlay Deployment, Means of Finance & 5-Year Cash Flow Projections
        </h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl font-medium">
          Zero-drift capital outlay sizing, statutory promoter margin reconciliation, RBI-compliant Debt Service Coverage Ratio (DSCR) testing, and 5-year capacity ramp projections with tax depreciation.
        </p>
      </div>

      {/* Capital Reconciliation Card */}
      <CapitalReconciliationCard inputData={p} financialData={fin} schemeData={schemes} />

      {/* Banking Solvency DSCR Gauge */}
      <DscrGaugeChart dscrInfo={fin.dscr} projections={fin.five_year_projections} />

      {/* 5-Year Amortization Schedule & Financial Horizon */}
      <CashflowProjectionsChart inputData={p} financialData={fin} pricingData={pricing} />

    </div>
  );
}
export default FinancialsPage;
