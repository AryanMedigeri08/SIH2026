const AUDIO_FORMATS = [
  { mimeType: 'audio/webm;codecs=opus', extension: 'webm' },
  { mimeType: 'audio/webm', extension: 'webm' },
  { mimeType: 'audio/mp4', extension: 'm4a' },
];

export function chooseRecordingFormat(recorderClass = globalThis.MediaRecorder) {
  if (!recorderClass) throw new Error('Voice recording is not supported by this browser.');
  return AUDIO_FORMATS.find(({ mimeType }) => recorderClass.isTypeSupported?.(mimeType))
    || { mimeType: '', extension: 'webm' };
}

export function classifyVoiceChoice(transcript) {
  const heard = String(transcript || '').trim();
  const negative = /\b(no|nope|change|different|skip|keep|original)\b|नहीं|बदल|नको|नाही|ಬೇಡ|ಇಲ್ಲ|இல்லை|வேண்டாம்|కాదు|వద్దు/i.test(heard);
  if (negative) return 'negative';
  const affirmative = /\b(yes|continue|correct|same|sure|check|align)\b|हाँ|हां|सही|होय|बरोबर|ಹೌದು|ಸರಿ|ஆம்|ஆமாம்|అవును|సరే/i.test(heard);
  return affirmative ? 'affirmative' : 'unknown';
}

export function encodeWavSamples(samples, sampleRate = 16000) {
  const bytes = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(bytes);
  const writeText = (offset, value) => {
    for (let i = 0; i < value.length; i += 1) view.setUint8(offset + i, value.charCodeAt(i));
  };
  writeText(0, 'RIFF');
  view.setUint32(4, bytes.byteLength - 8, true);
  writeText(8, 'WAVE');
  writeText(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeText(36, 'data');
  view.setUint32(40, samples.length * 2, true);
  samples.forEach((sample, index) => {
    const clamped = Math.max(-1, Math.min(1, sample));
    view.setInt16(44 + index * 2, clamped < 0 ? clamped * 32768 : clamped * 32767, true);
  });
  return new Blob([bytes], { type: 'audio/wav' });
}

export async function prepareOnboardingAudio(blob, extension = 'webm') {
  if (extension === 'wav') return { blob, extension };
  const AudioContextClass = globalThis.AudioContext || globalThis.webkitAudioContext;
  const OfflineContextClass = globalThis.OfflineAudioContext || globalThis.webkitOfflineAudioContext;
  if (!AudioContextClass || !OfflineContextClass) return { blob, extension };
  const context = new AudioContextClass();
  try {
    const decoded = await context.decodeAudioData(await blob.arrayBuffer());
    const offline = new OfflineContextClass(1, Math.ceil(decoded.duration * 16000), 16000);
    const source = offline.createBufferSource();
    source.buffer = decoded;
    source.connect(offline.destination);
    source.start();
    const rendered = await offline.startRendering();
    return { blob: encodeWavSamples(rendered.getChannelData(0)), extension: 'wav' };
  } catch {
    // Browser codec decoding can fail; preserve the original for Groq fallback.
    return { blob, extension };
  } finally {
    await context.close().catch(() => {});
  }
}

export async function transcribeOnboardingAudio(blob, { language = 'hi', token, extension = 'webm' } = {}) {
  if (!blob?.size) throw new Error('No audio was recorded. Please try again.');
  const prepared = await prepareOnboardingAudio(blob, extension);
  const body = new FormData();
  body.append('file', prepared.blob, `onboarding-recording.${prepared.extension}`);
  body.append('language', language);
  body.append('purpose', 'onboarding');

  const response = await fetch('/api/v2/chat/stt', {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Speech recognition failed (${response.status}). Please try again.`);
  }
  const payload = await response.json();
  const transcript = String(payload.transcript || '').trim();
  if (!transcript) throw new Error('I could not hear any words. Please try recording again.');
  return transcript;
}
