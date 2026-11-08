import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Mic, Square } from 'lucide-react';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { useLanguage } from '../../context/LanguageContext';
import { useAutoTranslate } from '../../hooks/useAutoTranslate';
import { chatApi } from '../../services/api';
import { copy } from './copy';

export function MiraAnswer({ onAnswer, disabled, stopSpeech, options = [], optional = false, initial = '', maxLength = 800 }) {
  const { language } = useLanguage();
  const [text, setText] = useState(initial);
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState('');
  const alive = useRef(true);
  const { translated: problem } = useAutoTranslate(error);
  const optionKey = JSON.stringify(options);
  const rawLabels = useMemo(() => options.map(item => item.label), [optionKey]);
  const { translated: labels } = useAutoTranslate(rawLabels);
  const recorder = useVoiceRecorder({ maxDurationMs: 45000, onRecordingComplete: async blob => {
    setTranscribing(true); setError('');
    try {
      const result = await chatApi.transcribeAudio(blob, language);
      if (alive.current) setText(result.transcript || '');
    } catch (err) { if (alive.current) setError(err.message); }
    finally { if (alive.current) setTranscribing(false); }
  } });
  useEffect(() => { alive.current = true; return () => { alive.current = false; recorder.cancelRecording(); }; }, []);
  const submit = event => {
    event.preventDefault(); stopSpeech?.();
    if (options.length) {
      const normalized = text.trim().toLocaleLowerCase().replace(/[.!।]/g, '');
      const index = Number(normalized) - 1;
      const match = options.find((option, i) => [String(option.value).toLocaleLowerCase(), option.label.toLocaleLowerCase(), String(labels[i]).toLocaleLowerCase()].includes(normalized));
      if (match) onAnswer(match.value);
      else if (Number.isInteger(index) && options[index]) onAnswer(options[index].value);
      else setError('Choose an option, or say or type its number.');
    } else onAnswer(text);
  };
  const busy = disabled || transcribing;
  const silenceMira = () => { stopSpeech?.(); window.dispatchEvent(new Event('mira:stop-speech')); };
  return <form onSubmit={submit} className="space-y-4">
    {options.length > 0 && <div className="grid gap-3 max-h-80 overflow-y-auto p-1">
      {options.map((option, i) => <button type="button" key={String(option.value)} disabled={busy || recorder.isRecording}
        onClick={() => { silenceMira(); onAnswer(option.value); }} className="mira-secondary text-left">
        <span className="mr-2 opacity-60">{i + 1}.</span>{labels[i] || option.label}
      </button>)}
    </div>}
    <label className="block space-y-2 font-semibold">
      <span>{copy('type', language)}</span>
      <textarea className="mira-input" rows={options.length ? 1 : 3} value={text} maxLength={maxLength}
        disabled={busy || recorder.isRecording} onFocus={silenceMira} onChange={event => setText(event.target.value)} />
    </label>
    <div className="flex flex-wrap gap-3">
      <button type="button" disabled={busy} aria-pressed={recorder.isRecording} className={`mira-secondary inline-flex items-center gap-2 ${recorder.isRecording ? '!border-rose-600 !text-rose-800' : ''}`}
        onClick={() => { silenceMira(); recorder.isRecording ? recorder.stopRecording() : recorder.startRecording(); }}>
        {recorder.isRecording ? <Square size={20} /> : <Mic size={20} />}{copy(recorder.isRecording ? 'stop' : 'speak', language)}
      </button>
      <button disabled={busy || recorder.isRecording || !text.trim()} className="mira-primary">{copy(busy ? 'waiting' : 'next', language)}</button>
      {optional && <button type="button" disabled={busy || recorder.isRecording} onClick={() => { stopSpeech?.(); onAnswer('unknown'); }} className="mira-secondary">{copy('unknown', language)}</button>}
    </div>
    {(error || recorder.error) && <p role="alert" className="mira-error">{problem || recorder.error}</p>}
    {transcribing && <p role="status">{copy('waiting', language)}</p>}
  </form>;
}
