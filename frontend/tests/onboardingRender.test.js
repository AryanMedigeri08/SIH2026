import test from 'node:test';
import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import React from 'react';
import { renderToString } from 'react-dom/server';
import { createServer } from 'vite';

test('language selection renders all supported choices and Mira artwork', async () => {
  const values = new Map();
  globalThis.localStorage = {
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: key => values.delete(key),
  };
  const vite = await createServer({
    resolve: { alias: { 'react-router-dom': resolve('node_modules/react-router-dom/dist/index.mjs') } },
    server: { middlewareMode: true, hmr: false }, appType: 'custom', logLevel: 'error',
  });
  try {
    const { MemoryRouter } = await vite.ssrLoadModule('/node_modules/react-router-dom/dist/index.mjs');
    const { AuthProvider } = await vite.ssrLoadModule('/src/context/AuthContext.jsx');
    const { LanguageProvider } = await vite.ssrLoadModule('/src/context/LanguageContext.jsx');
    const { BusinessProvider } = await vite.ssrLoadModule('/src/context/BusinessContext.jsx');
    const { OnboardingPage } = await vite.ssrLoadModule('/src/pages/OnboardingPage.jsx');
    const html = renderToString(
      React.createElement(MemoryRouter, null,
        React.createElement(AuthProvider, null,
          React.createElement(LanguageProvider, null,
            React.createElement(BusinessProvider, null, React.createElement(OnboardingPage)),
          ),
        ),
      ),
    );
    for (const language of ['Hindi', 'English', 'Marathi', 'Telugu', 'Tamil', 'Kannada']) {
      assert.match(html, new RegExp(`Continue in ${language}`));
    }
    assert.match(html, /mira-avatar\.png/);
    assert.match(html, /Choose your language/);
  } finally {
    await vite.close();
    delete globalThis.localStorage;
  }
});
