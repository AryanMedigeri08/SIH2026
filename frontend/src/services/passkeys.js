import { passkeyApi } from './api';

const fromBase64url = (value) => Uint8Array.from(
  atob(value.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - value.length % 4) % 4)),
  (character) => character.charCodeAt(0)
);
const toBase64url = (buffer) => btoa(String.fromCharCode(...new Uint8Array(buffer)))
  .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

function requirePasskeys() {
  if (!window.PublicKeyCredential || !navigator.credentials) {
    throw new Error('This browser does not support passkeys. Use phone verification or Google instead.');
  }
}

export async function enrollPasskey(token) {
  requirePasskeys();
  const { challenge_id, credential } = await passkeyApi.registerOptions(token);
  const publicKey = {
    ...credential,
    challenge: fromBase64url(credential.challenge),
    user: { ...credential.user, id: fromBase64url(credential.user.id) },
    excludeCredentials: (credential.excludeCredentials || []).map((item) => ({ ...item, id: fromBase64url(item.id) })),
  };
  const created = await navigator.credentials.create({ publicKey });
  if (!created) throw new Error('Passkey creation was cancelled.');
  return passkeyApi.registerVerify(token, {
    challenge_id,
    credential: {
      id: created.id,
      rawId: toBase64url(created.rawId),
      type: created.type,
      authenticatorAttachment: created.authenticatorAttachment,
      response: {
        clientDataJSON: toBase64url(created.response.clientDataJSON),
        attestationObject: toBase64url(created.response.attestationObject),
        transports: created.response.getTransports?.() || [],
      },
      clientExtensionResults: created.getClientExtensionResults(),
    },
  });
}

export async function authenticateWithPasskey() {
  requirePasskeys();
  const { challenge_id, credential } = await passkeyApi.authenticateOptions();
  const publicKey = {
    ...credential,
    challenge: fromBase64url(credential.challenge),
    allowCredentials: (credential.allowCredentials || []).map((item) => ({ ...item, id: fromBase64url(item.id) })),
  };
  const assertion = await navigator.credentials.get({ publicKey });
  if (!assertion) throw new Error('Passkey sign-in was cancelled.');
  return passkeyApi.authenticateVerify({
    challenge_id,
    credential: {
      id: assertion.id,
      rawId: toBase64url(assertion.rawId),
      type: assertion.type,
      response: {
        clientDataJSON: toBase64url(assertion.response.clientDataJSON),
        authenticatorData: toBase64url(assertion.response.authenticatorData),
        signature: toBase64url(assertion.response.signature),
        userHandle: assertion.response.userHandle ? toBase64url(assertion.response.userHandle) : null,
      },
      clientExtensionResults: assertion.getClientExtensionResults(),
    },
  });
}
