import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import { renderToString } from 'react-dom/server';
import { createServer } from 'vite';
import { resolve } from 'node:path';

test('registration and login render every supported language, Mira, and secure choices', async () => {
  const values = new Map();
  globalThis.localStorage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
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
    const { RegisterPage } = await vite.ssrLoadModule('/src/pages/RegisterPage.jsx');
    const { LoginPage } = await vite.ssrLoadModule('/src/pages/LoginPage.jsx');
    const expected = {
      en: ['Create your account', 'Mobile number'],
      hi: ['अपना खाता बनाएँ', 'मोबाइल नंबर'],
      mr: ['खाते तयार करा', 'मोबाइल क्रमांक'],
      te: ['ఖాతా సృష్టించండి', 'మొబైల్ నంబర్'],
      ta: ['கணக்கு உருவாக்குங்கள்', 'கைபேசி எண்'],
      kn: ['ಖಾತೆ ತೆರೆಯಿರಿ', 'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ'],
    };
    for (const [language, [title, phone]] of Object.entries(expected)) {
      values.set('udyam_saathi_ui_language', language);
      const wrap = (page) => renderToString(
        React.createElement(MemoryRouter, null,
          React.createElement(AuthProvider, null,
            React.createElement(LanguageProvider, null,
              React.createElement(BusinessProvider, null, React.createElement(page)),
            ),
          ),
        ),
      );
      const register = wrap(RegisterPage);
      const login = wrap(LoginPage);
      assert.match(register, /mira-avatar\.png/);
      assert.match(register, new RegExp(title));
      assert.match(register, new RegExp(phone));
      assert.match(register, /type="tel"/);
      assert.match(register, /type="email"/);
      assert.match(login, /mira-avatar\.png/);
      assert.match(login, /Face ID/);
      assert.match(login, /login-recaptcha/);
    }
  } finally {
    await vite.close();
    delete globalThis.localStorage;
  }
});
