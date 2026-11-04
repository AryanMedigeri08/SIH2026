import { useEffect, useRef, useState } from 'react';
import { useMiraSpeech } from './useMiraSpeech';
import { VoiceConversation } from '../services/voiceConversation';

export function useMiraConversation({language,token,prompt,questionKey,field,enabled,busy,onAnswer}) {
  const [status,setStatus]=useState('paused');
  const [error,setError]=useState('');
  const [paused,setPaused]=useState(false);
  const loop=useRef(null);
  const answer=useRef(onAnswer);answer.current=onAnswer;
  const speech=useMiraSpeech({language,token,onTranscript:value=>loop.current?.answer(value),
    onFailure:()=>loop.current?.failure(),onSilence:()=>loop.current?.failure(),initialSilenceMs:10000});
  const transport=useRef(speech);transport.current=speech;
  if(!loop.current)loop.current=new VoiceConversation({
    speak:text=>transport.current.speak(text),listen:()=>transport.current.startRecording(),
    stop:()=>{transport.current.stopSpeaking();transport.current.cancelRecording();},
    answer:text=>answer.current(text),status:setStatus,error:setError,paused:()=>setPaused(true),
  });
  useEffect(()=>{loop.current.update({key:questionKey,field,prompt,enabled:enabled&&!paused,busy});},[questionKey,field,prompt,enabled,paused,busy,language]);
  useEffect(()=>()=>loop.current.dispose(),[]);
  const resume=()=>{setError('');setPaused(false);loop.current.activeKey=null;loop.current.failures=0;loop.current.update({key:questionKey,field,prompt,enabled,busy});};
  const pause=()=>{setPaused(true);loop.current.update({key:questionKey,field,prompt,enabled:false,busy});};
  const repeat=()=>{loop.current.cancel();resume();};
  return {status,error:error||speech.speechError,paused,resume,pause,repeat,speaking:speech.speaking,isRecording:speech.isRecording,transcribing:speech.transcribing,
    stopSpeaking:()=>loop.current.cancel(),speak:repeat};
}
