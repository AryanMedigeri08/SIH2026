import React, { useEffect, useRef } from 'react';
import { Mic, Send, Volume2, VolumeX, RotateCcw, ChevronDown } from 'lucide-react';
import { MiraTranscript } from './MiraTranscript';
import { LanguageSelector } from './LanguageSelector';
import { miraCopy } from '../services/miraCopy';
import { TranslatedText as T } from './TranslatedText';
import './miraChat.css';

function PastMessage({ message }) {
  return <article className={`mira-chat-message mira-chat-message--${message.role}`}>
    <span className="mira-chat-speaker">{message.role === 'user' ? <T text="You" /> : 'Mira'}</span>
    <p>{message.role === 'user' ? message.text : <T text={message.text} />}</p>
  </article>;
}

export function MiraChatShell({ language, prompt, speech, busy, inputMode, input, onInput, onTyping, onMicrophone, onSend,
  audioEnabled, onAudioToggle, history = [], error, onRetry, children, dialogs }) {
  const copy = miraCopy(language), latest = useRef(null), composing = useRef(false);
  const composer = useRef(null), page = useRef(null), answer = useRef(null);
  const phase = busy || speech.transcribing || speech.audioLoading ? 'thinking' : speech.speaking ? 'speaking' : speech.isRecording ? 'listening' : 'idle';
  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    latest.current?.scrollIntoView({ behavior: reduced ? 'instant' : 'smooth', block: 'start' });
  }, [prompt]);
  useEffect(() => {
    const resize = new ResizeObserver(entries => page.current?.style.setProperty('--mira-composer-height', `${entries[0].target.getBoundingClientRect().height}px`));
    if (composer.current) resize.observe(composer.current);
    return () => resize.disconnect();
  }, []);
  useEffect(() => {
    if (answer.current) { answer.current.style.height = 'auto'; answer.current.style.height = `${Math.min(answer.current.scrollHeight, 140)}px`; }
  }, [input]);
  const previous = history.at(-1)?.role === 'assistant' ? history.slice(0, -1) : history;
  const lastUser = previous.at(-1)?.role === 'user' ? previous.at(-1) : null;
  const earlier = lastUser ? previous.slice(0, -1) : previous;
  return <main ref={page} className="mira-chat-page">
    <header className="mira-chat-header"><div className="mira-chat-identity"><img src="/mira-avatar.png" alt="Mira" />
      <div><strong>Mira</strong><span><T text="Your business helper" /></span></div></div><LanguageSelector /></header>
    <div className="mira-chat-thread">
      {earlier.length > 0 && <details className="mira-chat-history"><summary><ChevronDown size={18} /><T text="Earlier messages" /></summary>
        {earlier.map((message, index) => <PastMessage key={index} message={message} />)}</details>}
      {lastUser && <PastMessage message={lastUser} />}
      <article ref={latest} className="mira-chat-message mira-chat-message--assistant mira-chat-current">
        <div className="mira-chat-question-heading"><img className="mira-chat-avatar" src="/mira-avatar.png" alt="" /><span className="mira-chat-speaker">Mira</span>
          <span className="mira-chat-status" role="status"><span className={`mira-chat-status-dot ${phase}`} />{copy[phase]}</span></div>
        <MiraTranscript text={prompt} speech={speech} />
        <div className="mira-chat-audio-actions"><button type="button" onClick={speech.repeat} disabled={busy || !prompt} aria-label={copy.repeat}><RotateCcw size={17} /><T text="Listen again" /></button>
          <button type="button" onClick={onAudioToggle} aria-pressed={audioEnabled}>{audioEnabled ? <Volume2 size={17} /> : <VolumeX size={17} />}<T text={audioEnabled ? 'Sound on' : 'Sound off'} /></button></div>
      </article>
      <div className="mira-chat-insights">{children}</div>
      {(error || speech.error) && <div role="alert" className="mira-chat-error">{error || copy.voiceRecovery}<button type="button" onClick={onRetry} disabled={busy}>{copy.retry}</button></div>}
    </div>
    <footer ref={composer} className="mira-chat-composer"><form onSubmit={event => { event.preventDefault(); if (!composing.current && input.trim() && !busy) onSend(); }}>
      <textarea ref={answer} rows={2} aria-label={copy.placeholder} placeholder={copy.placeholder} value={input} disabled={busy} maxLength={3000}
        onCompositionStart={() => { composing.current = true; }} onCompositionEnd={() => { composing.current = false; }}
        onFocus={onTyping} onChange={event => { onTyping(); onInput(event.target.value); }}
        onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing && !composing.current) { event.preventDefault(); if (input.trim() && !busy) onSend(); } }} />
      <div className="mira-chat-compose-actions"><button className={`mira-chat-mic ${inputMode === 'voice' ? 'active' : ''}`} type="button" aria-label={copy.microphone} aria-pressed={inputMode === 'voice'} onClick={onMicrophone} disabled={busy}><Mic size={21} /><T text={inputMode === 'voice' ? 'Stop microphone' : 'Speak'} /></button>
        <button className="mira-chat-send" type="submit" aria-label={copy.send} disabled={busy || !input.trim()}><T text="Send" /><Send size={20} /></button></div>
    </form><p><T text={inputMode === 'voice' ? 'Listening. Tap Stop when you finish.' : 'Microphone off. Type here or tap Speak.'} /></p></footer>
    {dialogs}
  </main>;
}
