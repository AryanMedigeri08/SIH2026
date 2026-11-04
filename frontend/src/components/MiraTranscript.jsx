import React from 'react';
import { speechTokens } from '../services/spokenWords';

export function MiraTranscript({text,speech,dark=false}) {
  const active=speech?.speaking&&speech.spokenText===text?speech.activeWordIndex:-1;
  return <p className={`mira-transcript ${dark?'mira-transcript--dark':''}`} aria-live="polite" aria-atomic="true" data-timing={speech?.speechTiming}>
    {speechTokens(text).map((token,index)=><span key={index} className={token.wordIndex===active?'mira-word--active':''}>{token.text}</span>)}
  </p>;
}
