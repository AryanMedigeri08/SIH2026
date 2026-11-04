import React from 'react';
import { Mic,Keyboard,RotateCcw } from 'lucide-react';
import { MiraTranscript } from './MiraTranscript';
import { miraCopy } from '../services/miraCopy';
import './miraExperience.css';

export function GuidedRegistrationPanel({language,prompt,speech,mode,onMicrophone,onTyping,children}) {
  const copy=miraCopy(language);
  const status=mode==='text'?'paused':speech.transcribing||speech.audioLoading?'thinking':speech.speaking?'speaking':speech.isRecording?'listening':speech.paused?'paused':'idle';
  return <div className="guided-registration">
    <aside className="registration-guide"><img className="registration-mira-photo" src="/mira-avatar.png" alt="Mira"/>
      <div className="registration-guide-caption"><span className="registration-eyebrow">Mira</span><MiraTranscript text={prompt} speech={speech}/>
        <p className="registration-status" role="status">{copy[status]}</p>
        <div className="registration-guide-actions"><button type="button" aria-label={copy.microphone} title={copy.microphone} onClick={onMicrophone}><Mic size={20}/></button>
          <button type="button" aria-label={copy.type} title={copy.type} onClick={onTyping}><Keyboard size={20}/></button>
          <button type="button" aria-label={copy.repeat} title={copy.repeat} onClick={speech.repeat}><RotateCcw size={18}/></button></div>
      </div>
    </aside>
    <div className="registration-form-panel">{children}</div>
  </div>;
}
