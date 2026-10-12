import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToString } from 'react-dom/server';
import { createServer } from 'vite';
import { resolve } from 'node:path';

test('report marketing does not invent an ODOP product when the registry has no match', async () => {
  globalThis.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
  const vite = await createServer({
    resolve: { alias: { 'react-router-dom': resolve('node_modules/react-router-dom/dist/index.mjs') } },
    server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'error',
  });
  try {
    const { MemoryRouter } = await vite.ssrLoadModule('/node_modules/react-router-dom/dist/index.mjs');
    const { AuthProvider } = await vite.ssrLoadModule('/src/context/AuthContext.jsx');
    const { LanguageProvider } = await vite.ssrLoadModule('/src/context/LanguageContext.jsx');
    const { MarketingPage } = await vite.ssrLoadModule('/src/pages/report/MarketingPage.jsx');
    const html = renderToString(
      React.createElement(MemoryRouter, { initialEntries: ['/marketing?tab=odop'] },
        React.createElement(AuthProvider, null,
          React.createElement(LanguageProvider, null,
            React.createElement(MarketingPage, {
              reportData: {
                input_parameters: { district_name: 'Bankura', state_name: 'West Bengal', enterprise_name: 'Test Dairy' },
                odop_alignment: { has_odop_record: false, is_aligned: false, odop_product: 'District General MSME' },
                pricing_recommendation: {},
              },
            }),
          ),
        ),
      ),
    );
    assert.match(html, /No verified district ODOP mapping/);
    assert.doesNotMatch(html, /Panchmura terracotta artisans/);
  } finally {
    await vite.close();
    delete globalThis.localStorage;
  }
});
