import React from 'react';
import { TranslatedText } from './TranslatedText';

export function MachineryCapacityCard({ plan }) {
  if (!plan?.selected_capacity_variant_id) return null;
  const money = value => Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });
  const selection = plan.capacity_selection || {};
  return (
    <div className="rounded-2xl border border-indigo-200 bg-indigo-50/60 p-4 space-y-2 text-sm">
      <div className="flex flex-wrap justify-between gap-2 font-bold text-indigo-950">
        <h4><TranslatedText text="Recommended machinery capacity" /></h4>
        <span><TranslatedText text={plan.typical_capacity} /></span>
      </div>
      <p><TranslatedText text="Estimated equipment cost" />: <strong>₹{money(plan.total_machinery_cost_inr)}</strong></p>
      <p className="text-xs text-slate-700"><TranslatedText text={selection.rationale} /></p>
      {selection.source === 'indicative_capacity_selection' && (
        <p className="text-xs text-amber-900"><TranslatedText text="Indicative starter option; AI sizing was unavailable." /></p>
      )}
      {plan.equipment_funding_gap_inr > 0 && (
        <p className="text-xs text-amber-900"><TranslatedText text="Additional equipment funding needed" />: ₹{money(plan.equipment_funding_gap_inr)}</p>
      )}
      <details className="text-xs text-slate-600">
        <summary className="cursor-pointer font-semibold"><TranslatedText text="Compare capacities and view estimate basis" /></summary>
        <p className="mt-2"><TranslatedText text={selection.demand_basis} /></p>
        {plan.equipment_budget_inr != null && <p className="mt-1"><TranslatedText text="Equipment budget after reserving 30% for other project costs" />: ₹{money(plan.equipment_budget_inr)}</p>}
        <ul className="mt-2 space-y-1">
          {(plan.capacity_variants || []).map(option => (
            <li key={option.variant_id} className={option.variant_id === plan.selected_capacity_variant_id ? 'font-bold text-indigo-900' : ''}>
              <TranslatedText text={option.typical_capacity} /> · ₹{money(option.total_machinery_cost_inr)}
              {option.variant_id === plan.selected_capacity_variant_id && <> · <TranslatedText text="Recommended" /></>}
            </li>
          ))}
        </ul>
        <p className="mt-2"><TranslatedText text={plan.variant_pricing?.basis} /></p>
        <p className="mt-1"><TranslatedText text={plan.variant_pricing?.notice} /></p>
      </details>
    </div>
  );
}
