import React, { useEffect, useRef } from 'react';
import { Mic, Send, Volume2, VolumeX, RotateCcw } from 'lucide-react';
import { MiraTranscript } from './MiraTranscript';
import { LanguageSelector } from './LanguageSelector';
import { miraCopy } from '../services/miraCopy';
import { TranslatedText as T } from './TranslatedText';
import './miraChat.css';

export function MiraChatShell({ language, prompt, speech, busy, inputMode, input, onInput, onTyping, onMicrophone, onSend,
  audioEnabled, onAudioToggle, history = [], error, onRetry, children, dialogs }) {
  const copy = miraCopy(language), latest = useRef(null), composing = useRef(false);
  const phase = busy || speech.transcribing || speech.audioLoading ? 'thinking' : speech.speaking ? 'speaking' : speech.isRecording ? 'listening' : 'idle';
  useEffect(() => { latest.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, [prompt]);
  // The latest assistant reply is rendered below with live word cues rather than twice.
  const previous = history.at(-1)?.role === 'assistant' ? history.slice(0, -1) : history;
  return <main className="mira-chat-page">
    <header className="mira-chat-header"><div className="mira-chat-identity"><img src="/mira-avatar.png" alt="Mira" />
      <div><strong>Mira</strong><span><T text="Your business, one conversation at a time" /></span></div></div><LanguageSelector /></header>
    <div className="mira-chat-thread">
      <div className="mira-chat-intro"><T text="Let’s find a business that works for you" /><p><T text="Speak when you choose, or write in your own language. Your progress is saved." /></p></div>
      {previous.map((message, index) => <article key={index} className={`mira-chat-message mira-chat-message--${message.role}`}>
        <span className="mira-chat-speaker">{message.role === 'user' ? <T text="You" /> : 'Mira'}</span><p>{message.role==='user'?message.text:<T text={message.text}/>}</p></article>)}
      <article ref={latest} className="mira-chat-message mira-chat-message--assistant mira-chat-current">
        <img className="mira-chat-avatar" src="/mira-avatar.png" alt="" /><span className="mira-chat-speaker">Mira</span>
        <MiraTranscript text={prompt} speech={speech} />
        <div className="mira-chat-status" role="status"><span className={`mira-chat-status-dot ${phase}`} />{copy[phase]}
          <button type="button" aria-label={copy.repeat} title={copy.repeat} onClick={speech.repeat} disabled={busy || !prompt}><RotateCcw size={15} /></button></div>
      </article>
      <div className="mira-chat-insights">{children}</div>
      {(error || speech.error) && <div role="alert" className="mira-chat-error">{error || copy.voiceRecovery}<button type="button" onClick={onRetry}>{copy.retry}</button></div>}
    </div>
    <footer className="mira-chat-composer"><form onSubmit={event => { event.preventDefault(); if (!composing.current && input.trim() && !busy) onSend(); }}>
      <button className={`mira-chat-mic ${inputMode === 'voice' ? 'active' : ''}`} type="button" aria-label={copy.microphone} aria-pressed={inputMode === 'voice'} title={copy.microphone} onClick={onMicrophone} disabled={busy}><Mic size={22} /></button>
      <textarea rows={1} aria-label={copy.placeholder} placeholder={copy.placeholder} value={input} disabled={busy} maxLength={3000}
        onCompositionStart={() => { composing.current = true; }} onCompositionEnd={() => { composing.current = false; }}
        onFocus={onTyping} onChange={event => { onTyping(); onInput(event.target.value); }}
        onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing && !composing.current) { event.preventDefault(); if (input.trim() && !busy) onSend(); } }} />
      <button className="mira-chat-audio" type="button" aria-label={audioEnabled ? 'Mute Mira' : 'Hear Mira'} title={audioEnabled ? 'Mute Mira' : 'Hear Mira'} onClick={onAudioToggle}>{audioEnabled ? <Volume2 size={20} /> : <VolumeX size={20} />}</button>
      <button className="mira-chat-send" type="submit" aria-label={copy.send} disabled={busy || !input.trim()}><Send size={21} /></button>
    </form><p><T text={inputMode === 'voice' ? 'Microphone enabled for this answer. Tap again to stop.' : 'Microphone off · Tap the microphone whenever you want to speak'} /></p></footer>
    {dialogs}
  </main>;
}
