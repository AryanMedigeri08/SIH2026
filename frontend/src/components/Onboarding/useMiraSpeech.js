import { useCallback, useEffect, useRef, useState } from 'react';
import { chatApi } from '../../services/api';

export function useMiraSpeech(text, language, enabled = true) {
  const [word, setWord] = useState(-1);
  const [speaking, setSpeaking] = useState(false);
  const current = useRef(0);
  const audio = useRef(null);
  const cache = useRef(new Map());
  const stop = useCallback(() => {
    current.current += 1;
    window.speechSynthesis?.cancel();
    if (audio.current) { audio.current.pause(); audio.current.src = ''; audio.current = null; }
    setSpeaking(false); setWord(-1);
  }, []);
  const speak = useCallback(async () => {
    stop();
    if (!text?.trim()) return;
    const id = current.current;
    const words = [...text.matchAll(/\S+/gu)];
    const indexAt = offset => Math.max(0, words.findIndex((w, i) => offset < (words[i + 1]?.index ?? Infinity)));
    const finish = () => { if (id === current.current) { setSpeaking(false); setWord(-1); } };
    const provider = async () => {
      try {
        const key = `${language}:${text}`;
        let result = cache.current.get(key);
        if (!result) {
          result = await chatApi.generateTts(text, language);
          cache.current.set(key, result);
          if (cache.current.size > 30) cache.current.delete(cache.current.keys().next().value);
        }
        if (id !== current.current) return;
        if (!result.audio_base64) return finish();
        const player = new Audio(`data:audio/${result.audio_format || 'mp3'};base64,${result.audio_base64}`);
        audio.current = player;
        // Provider responses have no word timestamps. Track playback proportionally;
        // native voices below use actual word-boundary events where available.
        player.ontimeupdate = () => {
          if (id === current.current && player.duration > 0) setWord(indexAt(Math.floor(text.length * player.currentTime / player.duration)));
        };
        player.onended = finish; player.onerror = finish;
        await player.play();
        if (id === current.current) { setSpeaking(true); setWord(0); }
      } catch { finish(); }
    };
    const voice = window.speechSynthesis?.getVoices().find(v => v.lang.toLowerCase().startsWith(language));
    if (!voice) { await provider(); return; }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = voice; utterance.lang = voice.lang; utterance.rate = 0.88;
    utterance.onstart = () => { if (id === current.current) { setSpeaking(true); setWord(0); } };
    utterance.onboundary = event => { if (id === current.current) setWord(indexAt(event.charIndex)); };
    utterance.onend = finish;
    utterance.onerror = event => { if (id === current.current && !['canceled', 'interrupted'].includes(event.error)) provider(); };
    window.speechSynthesis.speak(utterance);
  }, [text, language, stop]);
  useEffect(() => { if (enabled) speak(); else stop(); return stop; }, [speak, stop, enabled]);
  return { word, speaking, speak, stop };
}
