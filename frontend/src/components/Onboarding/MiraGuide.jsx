import React from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useMiraSpeech } from './useMiraSpeech';
import { copy } from './copy';
import './mira.css';

export function MiraAvatar({ speaking = false, state = speaking ? 'speaking' : 'idle' }) {
  return <div className={`mira-avatar mira-${state}`} aria-hidden="true">
    <img src="/images/mira-avatar.png" alt="" width="1135" height="1386" decoding="async" className="h-auto w-full object-contain" />
  </div>;
}

export function MiraGuide({ text, centered = false, enabled = true, onSpeechControl }) {
  const { language } = useLanguage();
  const speech = useMiraSpeech(text, language, enabled);
  const [answerState, setAnswerState] = React.useState('idle');
  React.useEffect(() => {
    const update = event => setAnswerState(event.detail);
    window.addEventListener('mira:answer-state', update);
    return () => window.removeEventListener('mira:answer-state', update);
  }, []);
  const state = answerState === 'listening' ? 'listening' : speech.speaking ? 'speaking' : answerState;
  React.useEffect(() => { onSpeechControl?.(speech.stop); }, [onSpeechControl, speech.stop]);
  return <aside className={`mira-guide ${centered ? 'mira-centered' : ''}`}>
    <MiraAvatar state={state} />
    <div className="mira-status" data-state={state}><span className="mira-sound-bars" aria-hidden="true">{[0,1,2,3,4].map(i => <i key={i} style={{ '--bar': i }} />)}</span><span>{copy(`mira_${state}`, language)}</span></div>
    <p className="mira-caption" aria-live="polite" aria-atomic="true">
      {text.split(/(\s+)/u).map((part, i, all) => {
        const index = all.slice(0, i).filter(p => p.trim()).length;
        return part.trim() ? <span key={i} className={index === speech.word ? 'mira-active-word' : ''}>{part}</span> : part;
      })}
    </p>
    <button type="button" onClick={speech.speaking ? speech.stop : speech.speak} className="mira-secondary inline-flex items-center justify-center gap-2">
      {speech.speaking ? <VolumeX size={20} /> : <Volume2 size={20} />}{copy(speech.speaking ? 'stop' : 'repeat', language)}
    </button>
    {speech.unavailable && <p role="status" className="mt-3 text-sm leading-relaxed text-slate-600">{copy('audioUnavailable', language)}</p>}
  </aside>;
}
