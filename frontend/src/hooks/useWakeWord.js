import { useState, useEffect, useRef, useCallback } from 'react';
import { chatApi } from '../services/api';

/**
 * Phonetic patterns to catch "Hey Siri" across diverse accents and speech speeds.
 * Also accommodates trailing commands e.g. "Hey Siri what is dairy demand in Thane?"
 */
const WAKE_WORD_REGEX = /\b(?:hey|hay|ay|hello|hi|ok|okay)?\s*(?:siri|seeree|sery|ciri|serious|sarah)\b/i;
const SAATHI_ALIAS_REGEX = /\b(?:hey|namaste|hello|ok)?\s*(?:saathi|sathi|udyam)\b/i;

/**
 * Extracts any trailing prompt that follows the wake phrase in the same utterance.
 * e.g. "Hey Siri what is the feasibility of dairy in Pune" -> "what is the feasibility of dairy in Pune"
 */
export function extractTrailingPrompt(fullText) {
  if (!fullText) return '';
  let match = fullText.match(WAKE_WORD_REGEX);
  if (!match) {
    match = fullText.match(SAATHI_ALIAS_REGEX);
  }
  if (!match) return '';

  const matchEnd = match.index + match[0].length;
  const trailing = fullText.slice(matchEnd).replace(/^[,.\s]+/, '').trim();
  return trailing;
}

/**
 * Checks if a text utterance contains a wake-word trigger.
 */
export function matchWakeWord(text) {
  if (!text) return false;
  return WAKE_WORD_REGEX.test(text) || SAATHI_ALIAS_REGEX.test(text);
}

/**
 * Custom Hook: useWakeWord
 * 
 * Dual-Engine Background Wake-Word Detection:
 * - Engine A (Native SpeechRecognition): High-speed client-side matching (Chrome, Edge, Safari, Opera).
 * - Engine B (Web Audio VAD + Groq Whisper): Universal fallback with micro-utterance transcription (Firefox & all modern browsers).
 */
export function useWakeWord({
  onWakeWordDetected,
  enabledByDefault = false,
  cooldownMs = 2500,
  minSpeechThreshold = 0.022,
  silenceThresholdMs = 650,
  maxUtteranceMs = 3500,
} = {}) {
  const [isEnabled, setIsEnabled] = useState(() => {
    try {
      return localStorage.getItem('udyam_wake_word_siri_enabled') === 'true' || enabledByDefault;
    } catch {
      return enabledByDefault;
    }
  });

  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState(null);
  const [lastDetected, setLastDetected] = useState(null);

  // Engine capability detection
  const hasNativeSpeech = typeof window !== 'undefined' && 
    Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
  const hasMediaDevices = typeof window !== 'undefined' && 
    Boolean(navigator?.mediaDevices?.getUserMedia);
  const isSupported = hasNativeSpeech || hasMediaDevices;
  const engineType = hasNativeSpeech ? 'native_webspeech' : 'groq_whisper_vad';

  // Refs for state coordination
  const shouldListenRef = useRef(isEnabled);
  const lastTriggerTimeRef = useRef(0);
  const onWakeWordRef = useRef(onWakeWordDetected);
  onWakeWordRef.current = onWakeWordDetected;

  // Engine A (Native Speech) Refs
  const recognitionRef = useRef(null);
  const restartTimerRef = useRef(null);
  const isStoppingRef = useRef(false);

  // Engine B (VAD + Whisper) Refs
  const vadStreamRef = useRef(null);
  const vadAudioCtxRef = useRef(null);
  const vadAnalyserRef = useRef(null);
  const vadMediaRecorderRef = useRef(null);
  const vadAnimFrameRef = useRef(null);
  const vadChunksRef = useRef([]);
  const isCapturingRef = useRef(false);
  const captureStartTimeRef = useRef(0);
  const silenceStartRef = useRef(null);
  const isTranscribingRef = useRef(false);

  // Sync isEnabled to localStorage and ref
  useEffect(() => {
    shouldListenRef.current = isEnabled;
    try {
      localStorage.setItem('udyam_wake_word_siri_enabled', String(isEnabled));
    } catch {
      // Storage ignored
    }
  }, [isEnabled]);

  // Unified detection trigger with cooldown
  const handleDetection = useCallback((transcript) => {
    const now = Date.now();
    if (now - lastTriggerTimeRef.current < cooldownMs) {
      return;
    }

    if (matchWakeWord(transcript)) {
      lastTriggerTimeRef.current = now;
      const trailingQuery = extractTrailingPrompt(transcript);
      setLastDetected({
        timestamp: now,
        transcript,
        trailingQuery,
        engine: engineType,
      });

      console.info(`[useWakeWord] 🎙️ "Hey Siri" detected via [${engineType}]! Trailing prompt:`, trailingQuery || '(none)');

      if (onWakeWordRef.current) {
        onWakeWordRef.current({
          phrase: 'Hey Siri',
          transcript,
          trailingQuery,
          engine: engineType,
        });
      }
    }
  }, [cooldownMs, engineType]);

  // Clean up Engine B (VAD) resources
  const cleanupVadResources = useCallback(() => {
    if (vadAnimFrameRef.current) {
      cancelAnimationFrame(vadAnimFrameRef.current);
      vadAnimFrameRef.current = null;
    }
    if (vadMediaRecorderRef.current && vadMediaRecorderRef.current.state !== 'inactive') {
      try {
        vadMediaRecorderRef.current.stop();
      } catch (e) {}
    }
    vadMediaRecorderRef.current = null;
    if (vadStreamRef.current) {
      vadStreamRef.current.getTracks().forEach((t) => t.stop());
      vadStreamRef.current = null;
    }
    if (vadAudioCtxRef.current && vadAudioCtxRef.current.state !== 'closed') {
      try {
        vadAudioCtxRef.current.close();
      } catch (e) {}
      vadAudioCtxRef.current = null;
    }
    vadAnalyserRef.current = null;
    vadChunksRef.current = [];
    isCapturingRef.current = false;
  }, []);

  // ----------------------------------------------------
  // ENGINE A: Native Web Speech Recognition (Chrome/Edge/Safari)
  // ----------------------------------------------------
  useEffect(() => {
    if (!hasNativeSpeech) return; // Skip if in Firefox/Safari without SpeechRecognition

    if (!isEnabled) {
      if (recognitionRef.current) {
        isStoppingRef.current = true;
        try {
          recognitionRef.current.stop();
        } catch {
          // ignore
        }
      }
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;

    try {
      recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
    } catch (err) {
      setError(err?.message || 'Failed to initialize SpeechRecognition');
      return;
    }

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      isStoppingRef.current = false;
      setIsListening(true);
      setError(null);
    };

    recognition.onresult = (event) => {
      if (!shouldListenRef.current) return;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result && result[0]) {
          const transcript = result[0].transcript || '';
          handleDetection(transcript);
        }
      }
    };

    recognition.onerror = (event) => {
      if (event.error === 'no-speech') return;
      if (event.error === 'not-allowed' || event.error === 'permission-denied') {
        setError('Microphone permission was denied for Wake Word.');
        setIsEnabled(false);
        shouldListenRef.current = false;
        return;
      }
      if (event.error !== 'aborted') {
        console.warn('[useWakeWord] Native recognition notice:', event.error);
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      if (shouldListenRef.current && !isStoppingRef.current) {
        clearTimeout(restartTimerRef.current);
        restartTimerRef.current = setTimeout(() => {
          if (shouldListenRef.current && recognitionRef.current) {
            try {
              recognitionRef.current.start();
            } catch (e) {
              console.debug('[useWakeWord] Restart attempt:', e?.message);
            }
          }
        }, 300);
      }
    };

    try {
      recognition.start();
    } catch (err) {
      console.warn('[useWakeWord] Initial start failed:', err);
    }

    return () => {
      isStoppingRef.current = true;
      clearTimeout(restartTimerRef.current);
      if (recognition) {
        try {
          recognition.abort();
        } catch {
          // ignore
        }
      }
      recognitionRef.current = null;
    };
  }, [isEnabled, hasNativeSpeech, handleDetection]);

  // ----------------------------------------------------
  // ENGINE B: Universal Web Audio VAD + Groq Whisper (Firefox / Fallback)
  // ----------------------------------------------------
  useEffect(() => {
    if (hasNativeSpeech) return; // Only run Engine B when native speech recognition is not available

    if (!isEnabled) {
      cleanupVadResources();
      setIsListening(false);
      return;
    }

    let isCancelled = false;

    async function initVad() {
      try {
        setError(null);
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });
        if (isCancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        vadStreamRef.current = stream;
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        const audioCtx = new AudioCtx();
        vadAudioCtxRef.current = audioCtx;

        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.3;
        source.connect(analyser);
        vadAnalyserRef.current = analyser;

        setIsListening(true);

        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        // Continuous VAD listening loop
        const vadLoop = () => {
          if (!shouldListenRef.current || isCancelled) return;

          analyser.getByteTimeDomainData(dataArray);
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) {
            const val = (dataArray[i] - 128) / 128;
            sum += val * val;
          }
          const rms = Math.sqrt(sum / dataArray.length);
          const now = Date.now();

          // Check for speech onset
          if (rms > minSpeechThreshold) {
            silenceStartRef.current = null;

            // Start recording audio utterance snippet if not already
            if (!isCapturingRef.current && !isTranscribingRef.current) {
              isCapturingRef.current = true;
              captureStartTimeRef.current = now;
              vadChunksRef.current = [];

              try {
                const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                  ? 'audio/webm;codecs=opus'
                  : 'audio/webm';
                const recorder = new MediaRecorder(stream, { mimeType: mime });
                vadMediaRecorderRef.current = recorder;

                recorder.ondataavailable = (e) => {
                  if (e.data && e.data.size > 0) {
                    vadChunksRef.current.push(e.data);
                  }
                };

                recorder.onstop = async () => {
                  const chunks = vadChunksRef.current;
                  vadChunksRef.current = [];
                  isCapturingRef.current = false;

                  if (chunks.length > 0 && shouldListenRef.current && !isCancelled) {
                    const audioBlob = new Blob(chunks, { type: mime });
                    // Transcribe snippet with fast Groq Whisper
                    if (audioBlob.size > 2000) {
                      isTranscribingRef.current = true;
                      try {
                        const sttResult = await chatApi.transcribeAudio(audioBlob, 'en');
                        const transcript = sttResult?.transcript || sttResult?.text || '';
                        if (transcript.trim()) {
                          handleDetection(transcript.trim());
                        }
                      } catch (err) {
                        console.debug('[useWakeWord VAD] Transcription error:', err?.message);
                      } finally {
                        isTranscribingRef.current = false;
                      }
                    }
                  }
                };

                recorder.start(150);
              } catch (recErr) {
                console.warn('[useWakeWord VAD] Recorder failed:', recErr);
                isCapturingRef.current = false;
              }
            }
          } else if (isCapturingRef.current) {
            // Speech was detected, monitor silence pause
            if (!silenceStartRef.current) {
              silenceStartRef.current = now;
            } else {
              const silenceDuration = now - silenceStartRef.current;
              const totalUtterance = now - captureStartTimeRef.current;

              if (silenceDuration >= silenceThresholdMs || totalUtterance >= maxUtteranceMs) {
                // Pause detected or max length reached -> finalize snippet
                if (vadMediaRecorderRef.current && vadMediaRecorderRef.current.state === 'recording') {
                  try {
                    vadMediaRecorderRef.current.stop();
                  } catch (e) {}
                }
              }
            }
          }

          vadAnimFrameRef.current = requestAnimationFrame(vadLoop);
        };

        vadAnimFrameRef.current = requestAnimationFrame(vadLoop);
      } catch (err) {
        if (!isCancelled) {
          setError('Microphone permission required for voice wake-word.');
          setIsEnabled(false);
          setIsListening(false);
        }
      }
    }

    initVad();

    return () => {
      isCancelled = true;
      cleanupVadResources();
    };
  }, [
    isEnabled,
    hasNativeSpeech,
    minSpeechThreshold,
    silenceThresholdMs,
    maxUtteranceMs,
    handleDetection,
    cleanupVadResources,
  ]);

  const toggleWakeWord = useCallback(() => {
    setIsEnabled((prev) => !prev);
  }, []);

  const enableWakeWord = useCallback(() => {
    setIsEnabled(true);
  }, []);

  const disableWakeWord = useCallback(() => {
    setIsEnabled(false);
  }, []);

  return {
    isSupported,
    isEnabled,
    isListening,
    error,
    lastDetected,
    engineType,
    toggleWakeWord,
    enableWakeWord,
    disableWakeWord,
  };
}

export default useWakeWord;
