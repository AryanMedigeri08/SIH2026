import test from 'node:test';
import assert from 'node:assert/strict';
import { chooseRecordingFormat, transcribeOnboardingAudio } from '../src/services/onboardingAudio.js';

test('recording format uses a browser-supported codec', () => {
  const recorder = { isTypeSupported: type => type === 'audio/mp4' };
  assert.deepEqual(chooseRecordingFormat(recorder), { mimeType: 'audio/mp4', extension: 'm4a' });
});

test('onboarding sends the microphone recording to the transcription API as file', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/api/v2/chat/stt');
    assert.equal(options.method, 'POST');
    assert.equal(options.headers.Authorization, 'Bearer test-token');
    assert.equal(options.body.get('language'), 'hi');
    assert.equal(options.body.get('file').name, 'onboarding-recording.webm');
    assert.equal(options.body.get('file').size, 4);
    return { ok: true, json: async () => ({ transcript: '  paneer ki dukan  ' }) };
  };
  try {
    assert.equal(await transcribeOnboardingAudio(new Blob(['test']), { language: 'hi', token: 'test-token' }), 'paneer ki dukan');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('onboarding reports failed or empty transcription', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({ ok: false, status: 503, json: async () => ({ detail: 'ASR unavailable' }) });
  try {
    await assert.rejects(() => transcribeOnboardingAudio(new Blob(['voice'])), /ASR unavailable/);
    await assert.rejects(() => transcribeOnboardingAudio(new Blob([])), /No audio was recorded/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
