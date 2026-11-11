import React, { useEffect, useId, useMemo, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, Check, Mic, Square } from 'lucide-react';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { useLanguage } from '../../context/LanguageContext';
import { useAutoTranslate } from '../../hooks/useAutoTranslate';
import { chatApi } from '../../services/api';
import { copy } from './copy';
import { resolveSpokenChoice } from './answerChoices';

export function MiraAnswer({ onAnswer, onBack, disabled, stopSpeech, options = [], optional = false, initial = '', maxLength = 800 }) {
  const { language } = useLanguage();
  const groupId = useId();
  const [text, setText] = useState(initial == null ? '' : String(initial));
  const [selected, setSelected] = useState(() => options.find(option => option.value === initial)?.value);
  const [transcript, setTranscript] = useState('');
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState('');
  const alive = useRef(true);
  const { translated: problem } = useAutoTranslate(error);
  const optionKey = JSON.stringify(options);
  const rawLabels = useMemo(() => options.map(item => item.label), [optionKey]);
  const { translated: labels } = useAutoTranslate(rawLabels);
  const hasOptions = options.length > 0;
  const silenceMira = () => { stopSpeech?.(); window.dispatchEvent(new Event('mira:stop-speech')); };
  const recorder = useVoiceRecorder({ maxDurationMs: 45000, onRecordingComplete: async blob => {
    setTranscribing(true); setError('');
    try {
      const result = await chatApi.transcribeAudio(blob, language);
      if (!alive.current) return;
      if (hasOptions) {
        const choice = resolveSpokenChoice(result.transcript, options, labels);
        setTranscript(result.transcript || ''); setSelected(choice);
        if (choice === undefined) setError('Please tap an option, or say its number.');
      } else setText(result.transcript || '');
    } catch (err) { if (alive.current) setError(err.message); }
    finally { if (alive.current) setTranscribing(false); }
  } });
  useEffect(() => { alive.current = true; return () => { alive.current = false; recorder.cancelRecording(); }; }, []);
  useEffect(() => {
    window.dispatchEvent(new CustomEvent('mira:answer-state', { detail: recorder.isRecording ? 'listening' : transcribing || disabled ? 'thinking' : 'idle' }));
    return () => window.dispatchEvent(new CustomEvent('mira:answer-state', { detail: 'idle' }));
  }, [recorder.isRecording, transcribing, disabled]);
  const busy = disabled || transcribing;
  const submit = event => {
    event.preventDefault(); silenceMira();
    if (busy || recorder.isRecording || (hasOptions ? selected === undefined : !text.trim())) return;
    onAnswer(hasOptions ? selected : text);
  };
  return <form onSubmit={submit} className="space-y-5">
    {hasOptions ? <fieldset className={`mira-choices ${options.length <= 4 ? 'mira-choices-short' : 'mira-choices-long'}`} disabled={busy || recorder.isRecording}>
      <legend className="mb-3 text-sm font-semibold text-slate-600">{copy('chooseOne', language)}</legend>
      {options.map((option, i) => <label key={String(option.value)} className={`mira-choice ${selected === option.value ? 'mira-choice-selected' : ''}`}>
        <input type="radio" name={groupId} value={String(i)} checked={selected === option.value} onChange={() => {
          silenceMira(); setSelected(option.value); setError(''); setTranscript('');
        }} />
        <span className="mira-choice-number" aria-hidden="true">{i + 1}</span>
        <span className="mira-choice-label">{labels[i] || option.label}</span>
        <span className="mira-choice-check" aria-hidden="true">{selected === option.value && <Check size={18} />}</span>
      </label>)}
    </fieldset> : <label className="block space-y-2 font-semibold">
      <span>{copy('type', language)}</span>
      <textarea className="mira-input" rows={3} value={text} maxLength={maxLength}
        disabled={busy || recorder.isRecording} onFocus={silenceMira} onChange={event => setText(event.target.value)} />
    </label>}
    {transcript && <p role="status" className="mira-transcript">{copy('heard', language)} <span className="font-semibold">{transcript}</span></p>}
    <div className="flex flex-wrap items-center gap-3">
      <button type="button" disabled={busy} aria-pressed={recorder.isRecording} className={`mira-voice-button ${recorder.isRecording ? 'mira-recording' : ''}`}
        onClick={() => { silenceMira(); recorder.isRecording ? recorder.stopRecording() : recorder.startRecording(); }}>
        {recorder.isRecording ? <Square size={19} /> : <Mic size={19} />}{copy(recorder.isRecording ? 'stopRecording' : 'speak', language)}
      </button>
      {optional && <button type="button" disabled={busy || recorder.isRecording} onClick={() => { silenceMira(); onAnswer('unknown'); }} className="mira-voice-button">{copy('unknown', language)}</button>}
    </div>
    <div className="mira-navigation">
      {onBack && <button type="button" disabled={busy || recorder.isRecording} onClick={() => { silenceMira(); onBack(); }} className="mira-secondary inline-flex items-center justify-center gap-2"><ArrowLeft size={19} />{copy('back', language)}</button>}
      <button disabled={busy || recorder.isRecording || (hasOptions ? selected === undefined : !text.trim())} className="mira-primary ml-auto inline-flex items-center justify-center gap-2">
        {copy(busy ? 'waiting' : 'next', language)}<ArrowRight size={19} />
      </button>
    </div>
    {(error || recorder.error) && <p role="alert" className="mira-error">{problem || recorder.error}</p>}
    {transcribing && <p role="status">{copy('waiting', language)}</p>}
  </form>;
}
