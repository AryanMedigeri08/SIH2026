import React from 'react';
import { TranslatedText } from '../TranslatedText';
import { AverageSellingPriceDetails } from './AverageSellingPriceDetails';
import { DemandForecastDetails } from './DemandForecastDetails';

export function PlanningAssumptionsCard({ financialData }) {
  const model = financialData?.operating_model;
  const assumptions = financialData?.planning_assumptions;
  if (!model || !assumptions?.values) return null;
  const a = assumptions.values;
  const conversion = assumptions.conversion;
  const money = value => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 });
  return (
    <div className="glass-panel p-4 sm:p-6 bg-white border border-slate-200 rounded-xl space-y-3">
      <div className="flex flex-wrap justify-between gap-2">
        <h3 className="font-bold text-slate-900"><TranslatedText text="Sales & operating assumptions" /></h3>
        <span className="text-xs font-semibold text-sovereign-800"><TranslatedText text={assumptions.demand_forecast ? 'Provisional base planning scenario' : 'Optimistic planning estimate'} /></span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
        <div><p className="text-slate-500"><TranslatedText text="Estimated annual sales" /></p><strong>₹{money(model.annual_sales)}</strong></div>
        <div><p className="text-slate-500"><TranslatedText text={['llm_quantity_weighted', 'llm_mix_with_indicative_arithmetic'].includes(assumptions.pricing?.source) ? 'Average selling price' : 'Estimated selling price'} /></p><strong>₹{money(model.average_selling_price_inr ?? a.selling_price_inr)}/{a.output_unit}</strong></div>
        <div><p className="text-slate-500"><TranslatedText text="Variable cost" /></p><strong>₹{money(model.variable_cost_per_output_unit)}/{a.output_unit}</strong></div>
        <div><p className="text-slate-500"><TranslatedText text={assumptions.demand_forecast ? 'Base monthly sales estimate' : 'Monthly sales volume'} /></p><strong>{assumptions.demand_forecast ? `≈${Number(model.monthly_sales_units).toLocaleString('en-IN', { maximumSignificantDigits: 2 })}` : money(model.monthly_sales_units)} {a.output_unit}</strong></div>
      </div>
      {conversion?.saleable_unit_definition && (
        <p className="text-xs font-medium text-slate-700"><TranslatedText text="Saleable unit" />: <TranslatedText text={conversion.saleable_unit_definition} /></p>
      )}
      <p className="text-xs text-slate-600"><TranslatedText text={a.rationale} /></p>
      {!assumptions.demand_forecast && assumptions.demand_status && <p className="text-xs text-amber-900"><TranslatedText text="Indicative demand estimate; business-specific assumptions still require review" /></p>}
      <details className="text-xs text-slate-600">
        <summary className="cursor-pointer"><TranslatedText text="View calculation assumptions" /></summary>
        <p className="mt-2">{a.input_units_per_output_unit} {a.input_unit}/{a.output_unit} · ₹{money(a.raw_material_cost_per_input_unit_inr)}/{a.input_unit} · {Math.round(a.utilization * 100)}% <TranslatedText text="utilization" />{!assumptions.demand_forecast && <> · {Math.round(a.market_share * 100)}% <TranslatedText text="local market share" /></>}</p>
        <p className="mt-1"><TranslatedText text={assumptions.source_summary} /></p>
        {assumptions.capacity?.basis && <p className="mt-1"><TranslatedText text={assumptions.capacity.basis} /></p>}
        {conversion && <>
          <p className="mt-2"><TranslatedText text="Monthly production capacity" />: {money(model.monthly_saleable_capacity)} {a.output_unit} · <TranslatedText text="Estimated monthly gross sales" />: ₹{money(model.monthly_gross_sales)}</p>
          <p className="mt-1"><TranslatedText text={conversion.conversion_basis} /></p>
          {!assumptions.demand_forecast && <p className="mt-1"><TranslatedText text="Annual-average seasonality factor" />: {money(conversion.seasonality_factor)}</p>}
        </>}
        {financialData.financial_calculation_source === 'llm_calculated' && (
          <p className="mt-1"><TranslatedText text="Capacity, conversions and report calculations provided by AI" /></p>
        )}
        {financialData.financial_calculation_source === 'indicative_calculation_fallback' && (
          <p className="mt-1"><TranslatedText text="Financial calculations use the indicative fallback" /></p>
        )}
      </details>
      <AverageSellingPriceDetails pricing={assumptions.pricing} comparison={model.price_comparison} unit={a.output_unit} />
      <DemandForecastDetails forecast={assumptions.demand_forecast} userSalesOverride={model.sales_source === 'user_supplied'} />
    </div>
  );
}
