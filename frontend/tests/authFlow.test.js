import test from 'node:test';
import assert from 'node:assert/strict';
import { destinationAfterSignIn } from '../src/services/authNavigation.js';
import { authErrorMessage } from '../src/services/authErrorMessage.js';

test('returning users load businesses with their ID token and reach dashboard', async () => {
  let receivedToken;
  const destination = await destinationAfterSignIn({ token: 'firebase-id-token' }, async (token) => {
    receivedToken = token;
    return { hasBusinesses: true };
  });
  assert.equal(receivedToken, 'firebase-id-token');
  assert.equal(destination, '/dashboard');
});

test('new users reach onboarding; protected return paths are preserved', async () => {
  const load = async () => ({ hasBusinesses: false });
  assert.equal(await destinationAfterSignIn({ token: 'valid' }, load), '/onboarding');
  assert.equal(await destinationAfterSignIn({ token: 'valid' }, load, '/reports/123'), '/reports/123');
});

test('missing token or business API failure never counts as successful sign-in', async () => {
  let called = false;
  await assert.rejects(destinationAfterSignIn({}, async () => { called = true; }), /ID token/);
  assert.equal(called, false);
  const failure = Object.assign(new Error('Unavailable'), { status: 503 });
  await assert.rejects(destinationAfterSignIn({ token: 'valid' }, async () => ({ error: failure })), /Unavailable/);
});

test('provider, network and backend failures show useful safe messages', () => {
  assert.match(authErrorMessage({ code: 'auth/admin-restricted-operation' }, 'failed'), /not enabled/);
  assert.match(authErrorMessage(new TypeError('Failed to fetch'), 'failed'), /backend is running/);
  assert.match(authErrorMessage({ status: 503 }, 'failed'), /sign-in service/);
  assert.match(authErrorMessage({ code: 'auth/invalid-verification-code' }, 'failed', 'hi'), /कोड/);
});
