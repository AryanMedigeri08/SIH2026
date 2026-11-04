import React from 'react';
import { Mic,Keyboard,Send,SlidersHorizontal,MapPin,RotateCcw } from 'lucide-react';
import { MiraOrb } from './Orb/MiraOrb';
import { MiraTranscript } from './MiraTranscript';
import { miraCopy } from '../services/miraCopy';
import './orbOnboarding.css';

export function OrbOnboardingShell({language,prompt,speech,busy,inputMode,input,onInput,onTyping,onMicrophone,onSend,onDetails,onLocation,locationStep,error,onRetry,children,actions}) {
  const copy=miraCopy(language);
  const phase=busy||(inputMode==='voice'&&(speech.transcribing||speech.audioLoading))?'thinking':inputMode==='text'||speech.paused?'paused':speech.speaking?'speaking':speech.isRecording?'listening':'idle';
  return <main className="orb-onboarding" data-mode={inputMode} data-phase={phase}>
    <div className="orb-onboarding-status" role="status"><span className={`orb-status-dot orb-status-dot--${phase}`}/>{copy[phase]}</div>
    <div className="orb-onboarding-visual"><MiraOrb state={phase} volume={speech.volume}/></div>
    <div className="orb-onboarding-caption"><MiraTranscript text={prompt} speech={speech} dark/>{actions}</div>
    {(error||(inputMode==='voice'&&speech.error))&&<div role="alert" className="orb-onboarding-error">{error||copy.voiceRecovery}<button onClick={onRetry} type="button">{copy.retry}</button></div>}
    <footer className="orb-onboarding-controls"><div className="orb-control-row">
      <button className={`orb-control orb-control--mic ${phase==='listening'?'is-listening':''}`} type="button" aria-label={copy.microphone} aria-pressed={inputMode==='voice'&&!speech.paused} title={copy.microphone} onClick={onMicrophone}><Mic size={25}/></button>
      {inputMode==='text'?<form onSubmit={event=>{event.preventDefault();if(input.trim())onSend();}} className="orb-text-form"><input autoFocus aria-label={copy.placeholder} placeholder={copy.placeholder} value={input} onFocus={onTyping} onChange={event=>{onTyping();onInput(event.target.value);}} disabled={busy}/><button className="orb-control" disabled={busy||!input.trim()} aria-label={copy.send}><Send size={21}/></button></form>
        :<button className="orb-control" type="button" aria-label={copy.type} title={copy.type} onClick={onTyping}><Keyboard size={23}/></button>}
      {inputMode==='voice'&&<button className="orb-control orb-control--quiet" type="button" aria-label={copy.repeat} title={copy.repeat} onClick={speech.repeat}><RotateCcw size={19}/></button>}
      {locationStep&&<button className="orb-control" type="button" aria-label={copy.changeLocation} title={copy.changeLocation} onClick={onLocation}><MapPin size={21}/></button>}
      <button className="orb-control orb-control--quiet" type="button" aria-label={copy.details} title={copy.details} onClick={onDetails}><SlidersHorizontal size={21}/></button>
    </div></footer>{children}
  </main>;
}
