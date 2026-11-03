import { useCallback, useEffect, useRef, useState } from 'react';
import { chatApi } from '../services/api';
import { useVoiceRecorder } from './useVoiceRecorder';

// Speech is a transport. Transcripts go through the same reviewed text turn as typing.
export function useMiraSpeech({ language = 'en', token, onTranscript }) {
  const [speechError, setSpeechError] = useState('');
  const [transcribing, setTranscribing] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const audioRef = useRef(null);
  const generation = useRef(0);
  const mounted = useRef(true);
  const callback = useRef(onTranscript);
  callback.current = onTranscript;
  const stopSpeaking = useCallback(() => {
    generation.current += 1;
    audioRef.current?.pause();
    audioRef.current = null;
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  }, []);
  const recorder = useVoiceRecorder({
    silenceThresholdMs: 3000,
    onRecordingComplete: async blob => {
      if (!mounted.current) return;
      setTranscribing(true);
      setSpeechError('');
      try {
        const result = await chatApi.transcribeAudio(blob, language);
        if (!mounted.current) return;
        if (!result.transcript?.trim()) throw new Error('I couldn’t hear words. Please try again or type your answer.');
        callback.current?.(result.transcript.trim());
      } catch (error) {
        if (mounted.current) setSpeechError('Mira couldn’t turn that recording into text. Try again or type your answer.');
      } finally {
        if (mounted.current) setTranscribing(false);
      }
    },
  });
  const speak = useCallback(async text => {
    stopSpeaking();
    const id = generation.current;
    setSpeechError('');
    setSpeaking(true);
    try {
      const result = await chatApi.generateTts(text, language, token);
      if (!mounted.current || generation.current !== id) return;
      if (!result.audio_base64) throw new Error('Speech unavailable');
      const source = result.audio_base64.startsWith('data:audio/') ? result.audio_base64 : `data:audio/mpeg;base64,${result.audio_base64}`;
      const player = new Audio(source);
      audioRef.current = player;
      player.onended = () => setSpeaking(false);
      player.onerror = () => { setSpeaking(false); setSpeechError('Audio could not play. The question is available as text.'); };
      await player.play();
    } catch (_) {
      if (!mounted.current || generation.current !== id) return;
      if (window.speechSynthesis) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = { en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN', ta: 'ta-IN', te: 'te-IN', kn: 'kn-IN' }[language];
        utterance.onend = () => setSpeaking(false);
        utterance.onerror = () => { setSpeaking(false); setSpeechError('Audio is unavailable. You can read and type below.'); };
        window.speechSynthesis.speak(utterance);
      } else {
        setSpeaking(false);
        setSpeechError('Audio is unavailable. You can read and type below.');
      }
    }
  }, [language, token, stopSpeaking]);
  const startRecording = async () => { stopSpeaking(); setSpeechError(''); await recorder.startRecording(); };
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; stopSpeaking(); };
  }, [stopSpeaking]);
  return { ...recorder, startRecording, speak, stopSpeaking, speaking, transcribing,
    speechError: speechError || recorder.error };
}
