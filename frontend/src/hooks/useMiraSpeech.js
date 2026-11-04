import { useCallback, useEffect, useRef, useState } from 'react';
import { chatApi } from '../services/api';
import { useVoiceRecorder } from './useVoiceRecorder';

export function useMiraSpeech({ language='en',token,onTranscript,onFailure,onSilence,initialSilenceMs=null }) {
  const [speechError,setSpeechError]=useState('');
  const [transcribing,setTranscribing]=useState(false);
  const [speaking,setSpeaking]=useState(false);
  const audio=useRef(null), pending=useRef(null), generation=useRef(0), mounted=useRef(true);
  const callbacks=useRef({onTranscript,onFailure,onSilence});callbacks.current={onTranscript,onFailure,onSilence};
  const stopSpeaking=useCallback(()=>{
    generation.current++;audio.current?.pause();audio.current=null;
    pending.current?.(false);pending.current=null;window.speechSynthesis?.cancel();
    if(mounted.current)setSpeaking(false);
  },[]);
  const recorder=useVoiceRecorder({silenceThresholdMs:2000,initialSilenceMs,onSilence:()=>callbacks.current.onSilence?.(),
    onRecordingComplete:async blob=>{
      if(!mounted.current)return;
      const recordingGeneration=generation.current;
      setTranscribing(true);setSpeechError('');
      try {
        const result=await chatApi.transcribeAudio(blob,language);
        if(!mounted.current||recordingGeneration!==generation.current)return;
        if(!result.transcript?.trim())throw new Error('Empty transcript');
        await callbacks.current.onTranscript?.(result.transcript.trim());
      }catch(_){if(mounted.current&&recordingGeneration===generation.current){setSpeechError('The recording could not be understood. Please try again or type your answer.');callbacks.current.onFailure?.();}}
      finally{if(mounted.current)setTranscribing(false);}
    }});
  const speak=useCallback(async text=>{
    stopSpeaking();const id=generation.current;setSpeechError('');setSpeaking(true);
    const valid=()=>mounted.current&&id===generation.current;
    try {
      const result=await chatApi.generateTts(text,language,token);
      if(!valid())return false;
      if(!result.audio_base64)throw new Error('No audio');
      const source=result.audio_base64.startsWith('data:audio/')?result.audio_base64:`data:audio/mpeg;base64,${result.audio_base64}`;
      const player=new Audio(source);audio.current=player;
      const played=await new Promise((resolve,reject)=>{
        const timer=setTimeout(()=>{player.pause();done(false);},120000);
        const done=value=>{clearTimeout(timer);resolve(value);};
        const fail=error=>{clearTimeout(timer);reject(error);};
        pending.current=done;player.onended=()=>done(true);player.onerror=()=>fail(new Error('Playback failed'));
        player.play().catch(fail);
      });
      if(valid()){pending.current=null;setSpeaking(false);}
      return !!played&&valid();
    }catch(_){
      if(!valid())return false;
      if(!window.speechSynthesis){setSpeaking(false);setSpeechError('Audio is unavailable. You can type below.');return false;}
      return new Promise(resolve=>{
        const timer=setTimeout(()=>{window.speechSynthesis.cancel();finish(false);},120000);
        const utterance=new SpeechSynthesisUtterance(text);
        utterance.lang={en:'en-IN',hi:'hi-IN',mr:'mr-IN',ta:'ta-IN',te:'te-IN',kn:'kn-IN'}[language]||'en-IN';
        const finish=ok=>{clearTimeout(timer);if(valid()){setSpeaking(false);pending.current=null;if(!ok)setSpeechError('Audio is unavailable. You can type below.');}resolve(ok&&valid());};
        pending.current=finish;
        utterance.onend=()=>finish(true);utterance.onerror=()=>finish(false);
        window.speechSynthesis.speak(utterance);
      });
    }
  },[language,token,stopSpeaking]);
  const startRecording=async()=>{stopSpeaking();setSpeechError('');return recorder.startRecording();};
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;stopSpeaking();};},[stopSpeaking]);
  return {...recorder,startRecording,speak,stopSpeaking,speaking,transcribing,speechError:speechError||recorder.error};
}
