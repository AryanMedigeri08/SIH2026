import React from 'react';
import { TranslatedText } from '../TranslatedText';

export function AverageSellingPriceDetails({ pricing, comparison, unit }) {
  if (!pricing) return null;
  const money = value => Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 });
  return (
    <details className="text-xs text-slate-600">
      <summary className="cursor-pointer font-medium"><TranslatedText text="View selling price mix and comparison" /></summary>
      <p className="mt-2"><TranslatedText text={pricing.basis} /></p>
      {pricing.source === 'indicative_single_price' && <p className="mt-1"><TranslatedText text="Uniform-price fallback; a channel mix was not validated." /></p>}
      {pricing.source === 'llm_mix_with_indicative_arithmetic' && <p className="mt-1"><TranslatedText text="AI-estimated price mix with fallback arithmetic." /></p>}
      <div className="overflow-x-auto mt-2">
        <table className="w-full text-left">
          <thead><tr className="border-b border-slate-200">
            <th className="py-1"><TranslatedText text="Sales segment" /></th>
            <th><TranslatedText text="Quantity share" /></th>
            <th><TranslatedText text="Quoted price" /></th>
            <th><TranslatedText text="Realized price per unit" /></th>
          </tr></thead>
          <tbody>{(pricing.sales_mix || []).map((row, index) => <tr key={index} className="border-b border-slate-100">
            <td className="py-2 pr-2"><TranslatedText text={row.segment} /></td>
            <td>{money(row.quantity_share * 100)}%</td>
            <td>₹{money(row.quoted_price_inr)} / {money(row.output_units_per_quote)} {unit}<br />{money(row.discount_pct)}% <TranslatedText text="discount" /></td>
            <td>₹{money(row.realized_unit_price_inr)}/{unit}</td>
          </tr>)}</tbody>
        </table>
      </div>
      {comparison && <div className="mt-3 rounded-lg bg-slate-50 border border-slate-200 p-3 space-y-1">
        <p className="font-semibold"><TranslatedText text="Price comparison at the same sales volume" /></p>
        <p><TranslatedText text="Reference single price" />: ₹{money(comparison.reference_unit_price_inr)}/{unit} · <TranslatedText text="Annual sales" />: ₹{money(comparison.reference_annual_sales)}</p>
        <p><TranslatedText text="Weighted average price" />: ₹{money(comparison.average_selling_price_inr)}/{unit} · <TranslatedText text="Annual sales" />: ₹{money(comparison.weighted_annual_sales)}</p>
        <p><TranslatedText text="Annual sales difference" />: ₹{money(comparison.annual_sales_difference)} ({money(comparison.annual_sales_change_pct)}%)</p>
        <p><TranslatedText text="Reference-price scenario, not a previous saved report." /></p>
      </div>}
    </details>
  );
}
