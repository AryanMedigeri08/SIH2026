import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToString } from 'react-dom/server';
import { createServer } from 'vite';

test('financial report renders estimated sales, persisted projections and losses', async () => {
  globalThis.localStorage = { getItem: () => null, setItem() {}, removeItem() {} };
  const vite = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'error' });
  try {
    const { AuthProvider } = await vite.ssrLoadModule('/src/context/AuthContext.jsx');
    const { LanguageProvider } = await vite.ssrLoadModule('/src/context/LanguageContext.jsx');
    const { FinancialsPage } = await vite.ssrLoadModule('/src/pages/report/FinancialsPage.jsx');
    const reportData = {
      input_parameters: { project_cost: 500000, annual_turnover_estimate: 72000 },
      financial_analysis: {
        loan_principal: 300000, dscr: { dscr: -.5 }, amortization: { monthly_emi: 4000 },
        operating_model: { annual_sales: 72000, monthly_sales_units: 100, monthly_gross_sales: 6000, monthly_saleable_capacity: 200, variable_cost_per_output_unit: 65 },
        planning_assumptions: { source_summary: 'Indicative planning estimate', conversion: {
          saleable_unit_definition: '1 kg of finished product', seasonality_factor: .7,
          conversion_basis: 'One kg sold from 1.1 kg input; 25 operating days.',
        }, values: {
          selling_price_inr: 60, output_unit: 'kg', input_unit: 'kg', input_units_per_output_unit: 1.1,
          raw_material_cost_per_input_unit_inr: 50, utilization: .75, market_share: .25,
          rationale: 'Optimistic estimate using the village catchment.',
        } },
        five_year_projections: [{ year: 1, capacity_utilization_pct: 75, gross_turnover: 72000,
          total_operating_expenses: 80000, depreciation: 1000, bank_interest: 1000,
          profit_after_tax: -10000, total_debt_service: 16000, annual_dscr: -.5 }],
      }, pricing_recommendation: {}, scheme_optimization: [],
    };
    const render = data => renderToString(React.createElement(AuthProvider, null,
      React.createElement(LanguageProvider, null, React.createElement(FinancialsPage, { reportData: data }))));
    const html = render(reportData);
    assert.match(html, /Optimistic planning estimate/);
    assert.match(html, /72,000/);
    assert.match(html, /-10,000/);
    assert.match(html, /-0.50/);
    assert.match(html, /1 kg of finished product/);
    assert.match(html, /Monthly production capacity/);
    assert.match(html, /Estimated monthly gross sales/);
    assert.match(html, /6,000/);
    assert.match(html, /One kg sold from 1.1 kg input/);
    assert.doesNotMatch(html, /cannot be predicted|insufficient numbers|9,50,000/i);
    const noDebt = render({ ...reportData, financial_analysis: { ...reportData.financial_analysis,
      debt_service_required: false, dscr: { dscr: 0, verdict: 'NO DEBT' } } });
    assert.match(noDebt, /No loan repayments/);
  } finally {
    await vite.close();
    delete globalThis.localStorage;
  }
});
