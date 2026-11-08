import React from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useMiraSpeech } from './useMiraSpeech';
import { copy } from './copy';
import './mira.css';

export function MiraAvatar({ speaking = false }) {
  return <div className={`mira-avatar ${speaking ? 'mira-speaking' : ''}`} aria-hidden="true">
    <img src="/images/mira-avatar.png" alt="" width="1135" height="1386" decoding="async" className="h-auto w-full object-contain" />
  </div>;
}

export function MiraGuide({ text, centered = false, enabled = true, onSpeechControl }) {
  const { language } = useLanguage();
  const speech = useMiraSpeech(text, language, enabled);
  React.useEffect(() => { onSpeechControl?.(speech.stop); }, [onSpeechControl, speech.stop]);
  return <aside className={`mira-guide ${centered ? 'mira-centered' : ''}`}>
    <MiraAvatar speaking={speech.speaking} />
    <p className="mira-name">Mira</p>
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
