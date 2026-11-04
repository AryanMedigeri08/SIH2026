import { useCallback, useEffect, useRef, useState } from 'react';
import { chatApi } from '../services/api';
import { useVoiceRecorder } from './useVoiceRecorder';
import { wordAtPlayback,wordAtBoundary,speechTokens } from '../services/spokenWords';

export function useMiraSpeech({ language='en',token,onTranscript,onFailure,onSilence,initialSilenceMs=null }) {
  const [speechError,setSpeechError]=useState('');
  const [transcribing,setTranscribing]=useState(false);
  const [speaking,setSpeaking]=useState(false);
  const [audioLoading,setAudioLoading]=useState(false);
  const [spokenText,setSpokenText]=useState('');
  const [activeWordIndex,setActiveWordIndex]=useState(-1);
  const [speechTiming,setSpeechTiming]=useState('playback_estimate');
  const progressFrame=useRef(null),activeWord=useRef(-1);
  const audio=useRef(null), pending=useRef(null), generation=useRef(0), mounted=useRef(true);
  const callbacks=useRef({onTranscript,onFailure,onSilence});callbacks.current={onTranscript,onFailure,onSilence};
  const stopSpeaking=useCallback(()=>{
    cancelAnimationFrame(progressFrame.current);progressFrame.current=null;activeWord.current=-1;
    generation.current++;audio.current?.pause();audio.current=null;
    pending.current?.(false);pending.current=null;window.speechSynthesis?.cancel();
    if(mounted.current){setSpeaking(false);setTranscribing(false);setAudioLoading(false);setActiveWordIndex(-1);setSpokenText('');}
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
    stopSpeaking();const id=generation.current;setSpeechError('');setAudioLoading(true);
    const valid=()=>mounted.current&&id===generation.current;
    const mark=index=>{if(valid()&&activeWord.current!==index){activeWord.current=index;setActiveWordIndex(index);}};
    const track=(read,timing)=>{
      setSpokenText(text);setSpeechTiming(timing);mark(0);
      const frame=()=>{if(!valid())return;const index=read();if(index!=null)mark(index);progressFrame.current=requestAnimationFrame(frame);};
      progressFrame.current=requestAnimationFrame(frame);
    };
    const stopProgress=()=>{cancelAnimationFrame(progressFrame.current);progressFrame.current=null;if(valid()){mark(-1);setAudioLoading(false);setSpeaking(false);}};
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
        player.onplay=()=>{if(valid()){setAudioLoading(false);setSpeaking(true);track(()=>wordAtPlayback(text,player.currentTime,player.duration),'playback_estimate');}};
        player.play().catch(fail);
      });
      if(valid()){pending.current=null;stopProgress();}
      return !!played&&valid();
    }catch(_){
      if(!valid())return false;
      cancelAnimationFrame(progressFrame.current);progressFrame.current=null;
      if(!window.speechSynthesis){stopProgress();setSpeechError('Audio is unavailable. You can type below.');return false;}
      return new Promise(resolve=>{
        const timer=setTimeout(()=>{window.speechSynthesis.cancel();finish(false);},120000);
        const utterance=new SpeechSynthesisUtterance(text);
        utterance.lang={en:'en-IN',hi:'hi-IN',mr:'mr-IN',ta:'ta-IN',te:'te-IN',kn:'kn-IN'}[language]||'en-IN';
        let boundarySeen=false;
        utterance.onstart=()=>{if(valid()){setAudioLoading(false);setSpeaking(true);const start=performance.now();const duration=Math.max(1,speechTokens(text).filter(token=>token.wordIndex>=0).length/2.4);track(()=>boundarySeen?null:wordAtPlayback(text,(performance.now()-start)/1000,duration),'native_estimate');}};
        utterance.onboundary=event=>{if(valid()&&event.name==='word'){boundarySeen=true;setSpeechTiming('native_boundary');mark(wordAtBoundary(text,event.charIndex));}};
        const finish=ok=>{clearTimeout(timer);if(valid()){stopProgress();pending.current=null;if(!ok)setSpeechError('Audio is unavailable. You can type below.');}resolve(ok&&valid());};
        pending.current=finish;
        utterance.onend=()=>finish(true);utterance.onerror=()=>finish(false);
        window.speechSynthesis.speak(utterance);
      });
    }
  },[language,token,stopSpeaking]);
  const startRecording=async()=>{stopSpeaking();setSpeechError('');return recorder.startRecording();};
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;stopSpeaking();};},[stopSpeaking]);
  return {...recorder,startRecording,speak,stopSpeaking,speaking,audioLoading,spokenText,activeWordIndex,speechTiming,transcribing,speechError:speechError||recorder.error};
}
