import React from 'react';
import { TranslatedText } from '../TranslatedText';

const money = (value) => `₹${Number(value ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
const quantity = (value) => Number(value ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });

export function AnnualSalesForecastCard({ forecast }) {
  if (!forecast) return null;
  const accepted = forecast.status === 'provisional';
  const plan = forecast.accepted_plan || {};
  const annual = forecast.annual_sales || {};
  return (
    <section className="rounded-2xl border border-sky-200 bg-white p-4 sm:p-6 space-y-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-900"><TranslatedText text="Estimated Year-1 Gross Sales" /></h2>
          <p className="text-sm text-slate-600">{accepted ? plan.business_classification : 'Entered estimate retained; automatic forecast was unavailable.'}</p>
        </div>
        <span className="rounded-full px-3 py-1 bg-amber-50 text-amber-900 text-xs font-semibold">
          <TranslatedText text={accepted ? 'Provisional forecast — verify local assumptions' : 'Manual fallback — demand not validated'} />
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {['conservative', 'base', 'optimistic'].filter(s => annual[s] != null).map(s => (
          <div key={s} className="rounded-xl bg-slate-50 border border-slate-200 p-3">
            <p className="text-xs capitalize text-slate-600">{s}</p>
            <p className="text-xl font-bold text-sky-900">{money(annual[s])}</p>
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-600"><TranslatedText text="Annual sales are the sum of twelve monthly forecasts. Prices and demand are estimates, not guaranteed sales. DSCR and expense formulas have not yet been revised." /></p>
      {forecast.review_required && <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">Review required: capacity, budget feasibility or weak demand assumptions materially limit this forecast.</p>}
      {(forecast.selected_equipment || []).length > 0 && (
        <div className="space-y-2">
          <h3 className="font-semibold text-sm"><TranslatedText text="Suggested machinery configuration" /></h3>
          {forecast.selected_equipment.map(item => (
            <div key={item.profile_id} className="rounded-xl border border-slate-200 p-3 text-sm">
              <p className="font-semibold">{item.business_name}</p>
              <p>{item.typical_capacity} · {money(item.total_machinery_cost_inr)}</p>
              <p className="text-xs text-amber-800">Indicative {item.cost_source === 'derived_catalogue_estimate' ? 'scaled catalogue' : 'catalogue'} estimate; supplier confirmation required.</p>
              <details className="mt-2"><summary className="cursor-pointer text-sky-800">Equipment included</summary>
                <ul className="list-disc pl-5">{(item.machine_costs || []).map((m, i) => <li key={i}>{m.quantity} × {m.machine_name} — {money(m.estimated_cost_inr)}</li>)}</ul>
              </details>
            </div>
          ))}
          <p className="text-xs">Equipment: {money(forecast.equipment_cost_inr)}. Reserved for setup and working capital: {money(forecast.non_machinery_budget_inr)}.</p>
        </div>
      )}
      {accepted && (
        <details>
          <summary className="cursor-pointer font-semibold text-sm text-sky-900">Monthly sales, capacity and assumptions</summary>
          <div className="overflow-x-auto mt-3">
            <table className="w-full text-xs text-left">
              <thead><tr>{['Month', 'Product / channel', 'Demand', 'Units sold', 'Daily sales', 'Average price', 'Sales', 'Utilisation'].map(h => <th key={h} className="p-2 border-b">{h}</th>)}</tr></thead>
              <tbody>{(forecast.monthly_scenarios?.base || []).flatMap(month => month.products.map(p => (
                <tr key={`${month.month}-${p.product_id}`} className="border-b border-slate-100">
                  <td className="p-2 whitespace-nowrap">{month.month}</td><td className="p-2">{p.name} / {p.channel} ({p.unit})</td>
                  <td className="p-2">{quantity(p.obtainable_demand)}</td><td className="p-2">{quantity(p.units_sold)}</td>
                  <td className="p-2">{quantity(p.daily_units_sold)}</td><td className="p-2">{money(p.average_selling_price)}</td>
                  <td className="p-2">{money(p.revenue)}</td><td className="p-2">{quantity(p.capacity_utilisation_pct)}%</td>
                </tr>
              )))}</tbody>
            </table>
          </div>
          {(plan.products || []).map(p => (
            <div key={p.product_id} className="mt-4 space-y-2 text-xs">
              <h4 className="font-semibold text-sm">{p.name} / {p.channel}</h4>
              <p>{p.method_reason}</p><p>Buyer definition: {p.buyer_definition}</p>
              <p>Monthly demand = {Object.keys(p.scenarios.base.drivers).join(' × ')}</p>
              <div className="overflow-x-auto"><table className="w-full text-left">
                <thead><tr>{['Assumption', 'Unit', 'Source / confidence', 'Reasoning'].map(h => <th key={h} className="p-2 border-b">{h}</th>)}</tr></thead>
                <tbody>{Object.entries({ ...p.assumptions, conversion: p.output_per_input, capacity: p.capacity_basis }).map(([key, source]) => (
                  <tr key={key} className="border-b border-slate-100"><td className="p-2">{key}{source.value != null ? `: ${quantity(source.value)}` : ''}</td><td className="p-2">{source.unit}</td>
                    <td className="p-2">{source.source_kind} / {source.confidence}{source.evidence_ref ? ` (${source.evidence_ref})` : ''}</td><td className="p-2">{source.reasoning}</td></tr>
                ))}</tbody>
              </table></div>
              <details><summary className="cursor-pointer">All scenario drivers and prices by month</summary><pre className="whitespace-pre-wrap break-words bg-slate-50 p-3">{JSON.stringify(p.scenarios, null, 2)}</pre></details>
            </div>
          ))}
          <details className="mt-4 text-xs"><summary className="cursor-pointer">Regional evidence and data limitations</summary><pre className="whitespace-pre-wrap break-words bg-slate-50 p-3">{JSON.stringify(forecast.evidence_snapshot?.evidence || {}, null, 2)}</pre></details>
        </details>
      )}
      <ul className="space-y-1 text-xs text-amber-900 list-disc pl-5">
        {[...(forecast.warnings || []), ...(forecast.limitations || [])].map((warning, i) => <li key={i}>{warning}</li>)}
      </ul>
    </section>
  );
}
