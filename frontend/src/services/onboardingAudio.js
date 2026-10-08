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

export async function transcribeOnboardingAudio(blob, { language = 'hi', token, extension = 'webm' } = {}) {
  if (!blob?.size) throw new Error('No audio was recorded. Please try again.');
  const body = new FormData();
  body.append('file', blob, `onboarding-recording.${extension}`);
  body.append('language', language);

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
