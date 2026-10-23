import React from 'react';
import { TranslatedText } from '../TranslatedText';

export function PlanningAssumptionsCard({ financialData }) {
  const model = financialData?.operating_model;
  const assumptions = financialData?.planning_assumptions;
  if (!model || !assumptions?.values) return null;
  const a = assumptions.values;
  const money = value => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 });
  return (
    <div className="glass-panel p-4 sm:p-6 bg-white border border-slate-200 rounded-xl space-y-3">
      <div className="flex flex-wrap justify-between gap-2">
        <h3 className="font-bold text-slate-900"><TranslatedText text="Sales & operating assumptions" /></h3>
        <span className="text-xs font-semibold text-sovereign-800"><TranslatedText text="Optimistic planning estimate" /></span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
        <div><p className="text-slate-500"><TranslatedText text="Estimated annual sales" /></p><strong>₹{money(model.annual_sales)}</strong></div>
        <div><p className="text-slate-500"><TranslatedText text="Selling price" /></p><strong>₹{money(a.selling_price_inr)}/{a.output_unit}</strong></div>
        <div><p className="text-slate-500"><TranslatedText text="Variable cost" /></p><strong>₹{money(model.variable_cost_per_output_unit)}/{a.output_unit}</strong></div>
        <div><p className="text-slate-500"><TranslatedText text="Monthly sales volume" /></p><strong>{money(model.monthly_sales_units)} {a.output_unit}</strong></div>
      </div>
      <p className="text-xs text-slate-600"><TranslatedText text={a.rationale} /></p>
      <details className="text-xs text-slate-600">
        <summary className="cursor-pointer"><TranslatedText text="View calculation assumptions" /></summary>
        <p className="mt-2">{a.input_units_per_output_unit} {a.input_unit}/{a.output_unit} · ₹{money(a.raw_material_cost_per_input_unit_inr)}/{a.input_unit} · {Math.round(a.utilization * 100)}% <TranslatedText text="utilization" /> · {Math.round(a.market_share * 100)}% <TranslatedText text="local market share" /></p>
        <p className="mt-1"><TranslatedText text={assumptions.source_summary} /></p>
      </details>
    </div>
  );
}
