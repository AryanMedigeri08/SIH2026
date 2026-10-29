import assert from 'node:assert/strict';
import test from 'node:test';
import { createRequire } from 'node:module';
import path from 'node:path';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { build } from 'esbuild';

const result = await build({
  entryPoints: ['src/components/Dashboard/AnnualSalesForecastCard.jsx'], bundle: true,
  platform: 'node', format: 'cjs', write: false, external: ['react'],
  plugins: [{ name: 'offline-translations', setup(b) {
    b.onLoad({ filter: /[\\/]TranslatedText\.jsx$/ }, () => ({
      contents: "import React from 'react'; export function TranslatedText({text}) { return React.createElement('span', null, text); }", loader: 'jsx',
    }));
  } }],
});
const require = createRequire(import.meta.url);
const Module = require('node:module');
const mod = new Module(path.resolve('tests/forecast-render.cjs'));
mod.filename = path.resolve('tests/forecast-render.cjs');
mod.paths = Module._nodeModulePaths(process.cwd());
mod._compile(result.outputFiles[0].text, mod.filename);
const { AnnualSalesForecastCard } = mod.exports;
const render = forecast => renderToStaticMarkup(React.createElement(AnnualSalesForecastCard, { forecast }));

test('historical reports do not acquire a fabricated forecast', () => {
  assert.equal(render(null), '');
});

test('zero forecast and its uncertainty remain visible', () => {
  const html = render({ status: 'provisional', annual_sales: { conservative: 0, base: 0, optimistic: 1000 },
    accepted_plan: { business_classification: 'Synthetic milk business', products: [] },
    monthly_scenarios: { base: [] }, warnings: ['Requires local validation.'] });
  assert.match(html, /₹0/);
  assert.match(html, /Provisional forecast/);
  assert.match(html, /Requires local validation/);
  assert.match(html, /DSCR and expense formulas have not yet been revised/);
});

test('fallback is explicitly unvalidated and model text is escaped', () => {
  const html = render({ status: 'manual_fallback', annual_sales: { base: 900000 }, warnings: ['<script>alert(1)</script>'] });
  assert.match(html, /Manual fallback/);
  assert.match(html, /₹9,00,000/);
  assert.ok(!html.includes('<script>'));
  assert.match(html, /&lt;script&gt;/);
});
