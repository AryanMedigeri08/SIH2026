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
    const { ProductPricingCard } = await vite.ssrLoadModule('/src/components/Dashboard/ProductPricingCard.jsx');
    const reportData = {
      input_parameters: { project_cost: 500000, annual_turnover_estimate: 72000 },
      financial_analysis: {
        loan_principal: 300000, dscr: { dscr: -.5 }, amortization: { monthly_emi: 4000 },
        operating_model: { annual_sales: 72000, monthly_sales_units: 100, monthly_gross_sales: 6000, monthly_saleable_capacity: 200, variable_cost_per_output_unit: 65,
          average_selling_price_inr: 60, price_comparison: { reference_unit_price_inr: 70, average_selling_price_inr: 60,
            reference_annual_sales: 84000, weighted_annual_sales: 72000, annual_sales_difference: -12000, annual_sales_change_pct: -14.29 } },
        planning_assumptions: { source_summary: 'Indicative planning estimate', pricing: {
          source: 'llm_quantity_weighted', reference_selling_price_inr: 70,
          basis: 'Synthetic quantity-weighted retail/wholesale price assumption.', sales_mix: [
            { segment: 'Retail', quantity_share: .5, quoted_price_inr: 70, output_units_per_quote: 1, discount_pct: 0, realized_unit_price_inr: 70 },
            { segment: 'Wholesale', quantity_share: .5, quoted_price_inr: 500, output_units_per_quote: 10, discount_pct: 0, realized_unit_price_inr: 50 },
          ],
        }, conversion: {
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
      }, pricing_recommendation: { average_selling_price_inr: 60, expected_monthly_units: 100,
        recommended_selling_price_band_low: 100, recommended_selling_price_band_high: 120 }, scheme_optimization: [],
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
    assert.match(html, /Average selling price/);
    assert.match(html, /Quantity share/);
    assert.match(html, /Price comparison at the same sales volume/);
    assert.match(html, /84,000/);
    assert.match(html, /-12,000/);
    assert.match(html, /Reference-price scenario, not a previous saved report/);
    const simulatorHtml = renderToString(React.createElement(AuthProvider, null,
      React.createElement(LanguageProvider, null, React.createElement(ProductPricingCard, { reportData }))));
    assert.match(simulatorHtml, /Average realized price per unit/);
    assert.match(simulatorHtml, /value="60"/);
    assert.match(simulatorHtml, /monthly sales volume is held fixed/);
    assert.doesNotMatch(html, /cannot be predicted|insufficient numbers|9,50,000/i);
    const item = (amount_inr, basis) => ({ amount_inr, basis });
    const budgetReport = structuredClone(reportData);
    Object.assign(budgetReport.financial_analysis, {
      gross_project_cost: 600000, owned_machinery_value: 100000,
      committed_promoter_equity: 200000, promoter_margin_amount: 200000,
      potential_scheme_subsidy: 175000,
      funding_plan: { upfront_subsidy: 0, basis: 'Borrowing before unconfirmed subsidy' },
      first_full_repayment_year: { year: 2, annual_dscr: 1.1 },
      project_budget: { source: 'llm_itemized_budget', equipment_total: 350000, owned_machinery_credit: 100000,
        startup: { installation: item(20000, 'Installer allowance'), premises_deposit_and_fitout: item(30000, 'Workspace deposit'),
          utility_connections: item(10000, 'Connection costs'), licences_and_launch: item(10000, 'Launch costs'),
          initial_working_capital: item(150000, 'Inventory and cash cycle'), contingency: item(30000, 'Startup buffer') },
        monthly: { wages: item(12000, 'One paid assistant'), rent: item(4000, 'Workspace rent') } },
    });
    budgetReport.scheme_optimization = [{ eligible: true, subsidy_grant_amount: 175000 }];
    const budgetHtml = render(budgetReport);
    assert.match(budgetHtml, /Full repayment-year DSCR/);
    assert.match(budgetHtml, /1\.10x/);
    assert.match(budgetHtml, /Accounting Balanced/);
    assert.match(budgetHtml, /AI estimated budget/);
    assert.match(budgetHtml, /One paid assistant/);
    assert.match(budgetHtml, /2,50,000/);
    assert.match(budgetHtml, /Borrowing before unconfirmed subsidy/);
    const graceReport = structuredClone(budgetReport);
    graceReport.financial_analysis.dscr = { dscr: 0, verdict: 'MORATORIUM' };
    assert.match(render(graceReport), /Moratorium/);
    const noDebt = render({ ...reportData, financial_analysis: { ...reportData.financial_analysis,
      debt_service_required: false, dscr: { dscr: 0, verdict: 'NO DEBT' } } });
    assert.match(noDebt, /No loan repayments/);
  } finally {
    await vite.close();
    delete globalThis.localStorage;
  }
});
