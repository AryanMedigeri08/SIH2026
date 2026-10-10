import test from 'node:test';
import assert from 'node:assert/strict';
import { chooseRecordingFormat, classifyVoiceChoice, encodeWavSamples, prepareOnboardingAudio, transcribeOnboardingAudio } from '../src/services/onboardingAudio.js';

test('localized voice choices preserve yes/no intent and let negative corrections win', () => {
  for (const yes of ['yes', 'हाँ', 'होय', 'ಹೌದು', 'ஆம்', 'అవును']) {
    assert.equal(classifyVoiceChoice(yes), 'affirmative');
  }
  for (const no of ['no', 'नहीं', 'नाही', 'ಇಲ್ಲ', 'இல்லை', 'కాదు']) {
    assert.equal(classifyVoiceChoice(no), 'negative');
  }
  assert.equal(classifyVoiceChoice('yes, but no'), 'negative');
  assert.equal(classifyVoiceChoice('tailoring'), 'unknown');
});

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
    assert.equal(options.body.get('purpose'), 'onboarding');
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

test('onboarding produces mono PCM WAV for Bhashini when browser decoding is available', async () => {
  const oldAudioContext = globalThis.AudioContext;
  const oldOfflineAudioContext = globalThis.OfflineAudioContext;
  globalThis.AudioContext = class {
    async decodeAudioData() { return { duration: 0.001 }; }
    async close() {}
  };
  globalThis.OfflineAudioContext = class {
    constructor(channels, frames, rate) {
      assert.equal(channels, 1);
      assert.equal(rate, 16000);
      assert.equal(frames, 16);
      this.destination = {};
    }
    createBufferSource() { return { connect() {}, start() {} }; }
    async startRendering() { return { getChannelData: () => new Float32Array(16) }; }
  };
  try {
    const result = await prepareOnboardingAudio(new Blob(['recorded']), 'webm');
    assert.equal(result.extension, 'wav');
    assert.equal(result.blob.type, 'audio/wav');
    const header = new DataView(await result.blob.arrayBuffer());
    assert.equal(header.getUint32(24, true), 16000);
    assert.equal(header.getUint16(22, true), 1);
  } finally {
    globalThis.AudioContext = oldAudioContext;
    globalThis.OfflineAudioContext = oldOfflineAudioContext;
  }
});

test('WAV encoder writes a valid RIFF header', async () => {
  const blob = encodeWavSamples(new Float32Array([0, 0.5, -0.5]));
  const data = new Uint8Array(await blob.arrayBuffer());
  assert.equal(new TextDecoder().decode(data.slice(0, 4)), 'RIFF');
  assert.equal(new TextDecoder().decode(data.slice(8, 12)), 'WAVE');
  assert.equal(blob.size, 50);
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
