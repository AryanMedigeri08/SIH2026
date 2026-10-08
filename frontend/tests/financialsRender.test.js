import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToString } from 'react-dom/server';
import { createServer } from 'vite';

test('financials route component renders its full telemetry cards', async () => {
  const values = new Map();
  globalThis.localStorage = {
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: key => values.delete(key),
  };
  const vite = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'error' });
  try {
    const { AuthProvider } = await vite.ssrLoadModule('/src/context/AuthContext.jsx');
    const { LanguageProvider } = await vite.ssrLoadModule('/src/context/LanguageContext.jsx');
    const { FinancialsPage } = await vite.ssrLoadModule('/src/pages/report/FinancialsPage.jsx');
    const html = renderToString(
      React.createElement(AuthProvider, null,
        React.createElement(LanguageProvider, null,
          React.createElement(FinancialsPage, {
            reportData: {
              input_parameters: { project_cost: 500000, promoter_equity: 100000 },
              financial_analysis: {
                loan_principal: 400000, annual_net_profit: 80000, roi_pct: 16,
                dscr: { dscr: 1.5 }, amortization: { monthly_emi: 9000 },
              },
              scheme_optimization: [], pricing_recommendation: {},
            },
          }),
        ),
      ),
    );
    assert.match(html, /Break-Even/);
    assert.match(html, /Payback/);
    assert.match(html, /Capital Outlay/);
  } finally {
    await vite.close();
    delete globalThis.localStorage;
  }
});
