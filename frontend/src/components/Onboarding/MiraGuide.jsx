import React from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import { useMiraSpeech } from './useMiraSpeech';
import { copy } from './copy';
import './mira.css';

export function MiraAvatar({ speaking = false }) {
  return <div className={`mira-avatar ${speaking ? 'mira-speaking' : ''}`} aria-hidden="true">
    <svg viewBox="0 0 240 240" role="presentation">
      <rect width="240" height="240" rx="56" fill="#f1eaff" />
      <path d="M36 238c0-54 33-73 84-73s84 19 84 73" fill="#5b21b6" />
      <path d="M71 133V83c0-67 101-67 101 0v64l-23 28H86z" fill="#27203b" />
      <path d="M99 156h42v29c-8 19-34 19-42 0" fill="#c17b51" />
      <ellipse cx="120" cy="105" rx="47" ry="61" fill="#e5a779" />
      <path d="M72 91c-5-55 59-79 94-30l8 34c-16-6-29-22-32-39-20 21-42 29-70 35" fill="#27203b" />
      <g className="mira-eyes" fill="#332330"><ellipse cx="102" cy="108" rx="4" ry="5" /><ellipse cx="138" cy="108" rx="4" ry="5" /></g>
      <path d="M116 111l-4 17h10" fill="none" stroke="#b46d4c" strokeWidth="3" strokeLinecap="round" />
      <path className="mira-mouth" d="M105 140q15 14 30 0" fill="#a14357" stroke="#a14357" strokeWidth="3" strokeLinecap="round" />
      <circle cx="120" cy="91" r="3" fill="#a14357" />
      <path d="M70 185l50 52 49-52" fill="none" stroke="#c4b5fd" strokeWidth="12" />
    </svg>
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
  </aside>;
}
