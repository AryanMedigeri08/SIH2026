import { useCallback, useEffect, useRef, useState } from 'react';
import { chatApi } from '../../services/api';
const speechCache = new Map();

export function useMiraSpeech(text, language, enabled = true) {
  const [word, setWord] = useState(-1);
  const [speaking, setSpeaking] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const current = useRef(0);
  const audio = useRef(null);
  const stop = useCallback(() => {
    current.current += 1;
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
        setUnavailable(false);
        let request = speechCache.get(key);
        if (!request) {
          request = chatApi.generateTts(text, language, null, { provider: 'bhashini' });
          speechCache.set(key, request);
          if (speechCache.size > 50) speechCache.delete(speechCache.keys().next().value);
        }
        const result = await request;
        if (id !== current.current) return;
        if (!result.audio_base64) { speechCache.delete(key); setUnavailable(true); return finish(); }
        const player = new Audio(result.audio_base64.startsWith('data:') ? result.audio_base64 : `data:audio/${result.audio_format || 'mp3'};base64,${result.audio_base64}`);
        audio.current = player;
        // Bhashini returns no word timestamps. Highlight according to playback
        // progress without making one synthesis request per word.
        player.ontimeupdate = () => {
          if (id === current.current && player.duration > 0) setWord(indexAt(Math.floor(text.length * player.currentTime / player.duration)));
        };
        player.onended = finish; player.onerror = () => { if (id === current.current) setUnavailable(true); finish(); };
        await player.play();
        if (id === current.current) { setSpeaking(true); setWord(0); }
      } catch {
        speechCache.delete(`${language}:${text}`);
        if (id === current.current) setUnavailable(true);
        finish();
      }
    };
    await provider();
  }, [text, language, stop]);
  useEffect(() => { if (enabled) speak(); else stop(); return stop; }, [speak, stop, enabled]);
  useEffect(() => { window.addEventListener('mira:stop-speech', stop); return () => window.removeEventListener('mira:stop-speech', stop); }, [stop]);
  return { word, speaking, speak, stop, unavailable };
}
