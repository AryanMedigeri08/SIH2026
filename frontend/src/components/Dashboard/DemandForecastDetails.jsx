import React from 'react';
import { TranslatedText } from '../TranslatedText';

export function DemandForecastDetails({ forecast, userSalesOverride = false }) {
  if (!forecast?.scenarios) return null;
  const approx = value => value == null ? '—' : Number(value).toLocaleString('en-IN', { maximumSignificantDigits: 2 });
  const names = ['conservative', 'base', 'optimistic'];
  return <div className="border-t border-slate-200 pt-3 space-y-2 text-xs text-slate-700">
    <h4 className="font-bold text-slate-900"><TranslatedText text="Business-specific demand forecast" /></h4>
    <p><TranslatedText text={forecast.business_model} /> · <TranslatedText text={forecast.product_service} /> · <TranslatedText text={forecast.sales_channel} /></p>
    <p><TranslatedText text={forecast.method_reason} /></p>
    <p><TranslatedText text="Forecast method" />: <TranslatedText text={forecast.method?.replaceAll('_', ' ') || 'Business-specific method'} /></p>
    <p className="font-mono break-words"><TranslatedText text={forecast.equation_with_units} /></p>
    <p><TranslatedText text={forecast.provisional ? 'Provisional scenario range; numerical assumptions are hypotheses, not verified sales' : 'Forecast based on supplied business evidence'} /></p>
    {userSalesOverride && <p><TranslatedText text="The financial projections use your explicit annual sales input; these demand scenarios are a separate comparison" /></p>}
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead><tr>{['Scenario', 'Monthly demand', 'Realized monthly sales', 'Demand active buyers', 'Demand transactions', 'Daily sales', 'Monthly revenue', 'Effective capacity used'].map(label => <th key={label} className="p-2 whitespace-nowrap"><TranslatedText text={label} /></th>)}</tr></thead>
        <tbody>{names.map(name => {
          const s = forecast.scenarios[name];
          return <tr key={name} className="border-t border-slate-100">
            <td className="p-2 font-semibold"><TranslatedText text={name} /></td>
            <td className="p-2">≈{approx(s.monthly_demand_units)} {forecast.output_unit}</td>
            <td className="p-2">≈{approx(s.realized_monthly_units)} {forecast.output_unit}</td>
            <td className="p-2">{approx(s.monthly_active_buyers)}</td>
            <td className="p-2">{approx(s.monthly_transactions)}</td>
            <td className="p-2">≈{approx(s.daily_unit_sales)}</td>
            <td className="p-2">≈₹{approx(s.monthly_revenue_inr)}</td>
            <td className="p-2">{approx(s.capacity_utilization_pct)}%</td>
          </tr>;
        })}</tbody>
      </table>
    </div>
    <p><TranslatedText text="Buyer and transaction counts describe obtainable demand before the capacity limit; realized sales and revenue apply that limit" /></p>
    <p><TranslatedText text="Effective monthly capacity" />: ≈{approx(forecast.effective_monthly_capacity)} {forecast.output_unit} · <TranslatedText text={forecast.period?.replaceAll('_', ' ') || 'monthly'} /></p>
    {forecast.warnings?.length > 0 && <ul className="list-disc pl-4 text-amber-900">{forecast.warnings.map((warning, i) => <li key={i}><TranslatedText text={warning} /></li>)}</ul>}
    {forecast.review_status === 'review_required' && <p className="font-semibold text-amber-900"><TranslatedText text="Demand assumptions still require review; report figures are provisional" /></p>}
    <details>
      <summary className="cursor-pointer font-semibold"><TranslatedText text="Demand assumptions, evidence and reality checks" /></summary>
      <p className="mt-2"><TranslatedText text="Target customers" />: <TranslatedText text={forecast.target_customer} /> · <TranslatedText text={forecast.buyer_base} /></p>
      <p><TranslatedText text={forecast.location} /> · <TranslatedText text={forecast.maturity} /> · <TranslatedText text={forecast.buying_cycle} /></p>
      <p><TranslatedText text={forecast.acquisition_constraints} /></p>
      {[...names.map(name => ({ name, inputs: forecast.scenarios[name].inputs })), ...['category_demand', 'independent_cross_check'].filter(key => forecast[key]).map(key => ({ name: key, inputs: forecast[key].inputs }))].map(({ name, inputs }) => <div key={name} className="mt-3 overflow-x-auto">
        <strong><TranslatedText text={name} /></strong>
        <table className="w-full text-xs text-left"><thead><tr>{['Input', 'Value and units', 'Period', 'Source', 'Confidence', 'Justification'].map(label => <th key={label} className="p-1"><TranslatedText text={label} /></th>)}</tr></thead>
          <tbody>{inputs.map(input => <tr key={input.role} className="border-t border-slate-100">
            <td className="p-1"><TranslatedText text={input.role.replaceAll('_', ' ')} /></td>
            <td className="p-1">{Number(input.value).toLocaleString('en-IN', { maximumFractionDigits: 8 })} {input.units}</td>
            <td className="p-1"><TranslatedText text={input.reference_period.replaceAll('_', ' ')} /></td>
            <td className="p-1"><TranslatedText text={input.source_kind.replaceAll('_', ' ')} />: <TranslatedText text={input.source} />{input.evidence_path && <span> ({input.evidence_path})</span>}</td>
            <td className="p-1"><TranslatedText text={input.confidence} /></td>
            <td className="p-1"><TranslatedText text={input.reasoning} /></td>
          </tr>)}</tbody>
        </table>
      </div>)}
      <p className="mt-2"><TranslatedText text={forecast.reality_review} /></p>
      <p><TranslatedText text={forecast.reconciliation} /></p>
      {['category_demand', 'independent_cross_check'].map(key => forecast[key] && <p key={key}><TranslatedText text={key.replaceAll('_', ' ')} />: ≈{approx(forecast[key].monthly_demand_units)} {forecast.output_unit}/<TranslatedText text="month" />. <TranslatedText text={forecast[key].equation_with_units} />. <TranslatedText text={forecast[key].basis} /></p>)}
      {['uncertainty_drivers', 'limitations', 'missing_data'].map(key => forecast[key]?.length > 0 && <p key={key}><strong><TranslatedText text={key.replaceAll('_', ' ')} />: </strong>{forecast[key].map((item, i) => <span key={i}><TranslatedText text={item} />{i < forecast[key].length - 1 ? '; ' : ''}</span>)}</p>)}
    </details>
  </div>;
}
