import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToString } from 'react-dom/server';
import { createServer } from 'vite';

test('onboarding shows recommended capacity, derived price, alternatives and funding gap', async () => {
  globalThis.localStorage = { getItem: () => null, setItem() {}, removeItem() {} };
  const vite = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'error' });
  try {
    const { AuthProvider } = await vite.ssrLoadModule('/src/context/AuthContext.jsx');
    const { LanguageProvider } = await vite.ssrLoadModule('/src/context/LanguageContext.jsx');
    const { MachineryCapacityCard } = await vite.ssrLoadModule('/src/components/MachineryCapacityCard.jsx');
    const plan = { selected_capacity_variant_id: 'small', typical_capacity: '250 litres milk input/day',
      total_machinery_cost_inr: 400000, equipment_funding_gap_inr: 50000, equipment_budget_inr: 350000,
      capacity_selection: { source: 'indicative_capacity_selection', rationale: 'Sized for the local paneer demand.', demand_basis: '100 households with 20% headroom.' },
      capacity_variants: [{ variant_id: 'starter', typical_capacity: '100 litres milk input/day', total_machinery_cost_inr: 300000 },
        { variant_id: 'small', typical_capacity: '250 litres milk input/day', total_machinery_cost_inr: 400000 }],
      variant_pricing: { basis: 'Reference cost with fixed equipment retained.', notice: 'Indicative estimate, not a supplier quotation.' } };
    const html = renderToString(React.createElement(AuthProvider, null,
      React.createElement(LanguageProvider, null, React.createElement(MachineryCapacityCard, { plan }))));
    for (const text of ['250 litres', '100 litres', '4,00,000', '50,000', 'paneer demand', '20% headroom', 'AI sizing was unavailable', 'not a supplier quotation']) {
      assert.ok(html.includes(text), `Missing ${text}`);
    }
    assert.equal(renderToString(React.createElement(MachineryCapacityCard, { plan: {} })), '');
  } finally {
    await vite.close();
    delete globalThis.localStorage;
  }
});
