import { useState, useEffect, useRef, useCallback } from 'react';
import { chatApi } from '../services/api';

/**
 * Phonetic patterns to catch "Hey Siri" across diverse accents, speech speeds,
 * and speech-to-text interpretations.
 * Also accommodates trailing commands e.g. "Hey Siri what is dairy demand in Thane?"
 */
export const WAKE_WORD_REGEX = /\b(?:hey|hay|ay|hai|hi|hello|ok|okay|a)?[\s,.]*(?:siri|seeree|sery|ciri|serious|sarah|shiri|suri|series|cereal|ceri|cere|sorry|cyril|theory|city|sweetie|cd|see ree)\b/i;
export const SAATHI_ALIAS_REGEX = /\b(?:hey|namaste|hello|ok)?[\s,.]*(?:saathi|sathi|udyam)\b/i;

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
 *   Holds a persistent media stream so the browser microphone access NEVER flickers on/off.
 * - Engine B (Web Audio VAD + Groq Whisper): Universal fallback with micro-utterance transcription (Firefox & all modern browsers).
 */
export function useWakeWord({
  onWakeWordDetected,
  onSpeechRecognized,
  enabledByDefault = true,
  cooldownMs = 2000,
  minSpeechThreshold = 0.022,
  silenceThresholdMs = 650,
  maxUtteranceMs = 3500,
} = {}) {
  const [isEnabled, setIsEnabled] = useState(() => {
    try {
      const stored = localStorage.getItem('udyam_wake_word_siri_enabled_v2');
      if (stored !== null) return stored === 'true';
      return enabledByDefault;
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
  const onSpeechRecognizedRef = useRef(onSpeechRecognized);
  onSpeechRecognizedRef.current = onSpeechRecognized;

  // Persistent background stream to keep Chrome's microphone indicator steadily active
  const persistentMicStreamRef = useRef(null);

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
      localStorage.setItem('udyam_wake_word_siri_enabled_v2', String(isEnabled));
    } catch {
      // Storage ignored
    }
  }, [isEnabled]);

  // Unified detection trigger with cooldown
  const handleDetection = useCallback((transcript) => {
    if (!transcript) return;
    const now = Date.now();

    // Check if utterance contains wake word
    if (matchWakeWord(transcript)) {
      if (now - lastTriggerTimeRef.current < cooldownMs) {
        return;
      }

      lastTriggerTimeRef.current = now;
      const trailingQuery = extractTrailingPrompt(transcript);
      setLastDetected({
        timestamp: now,
        transcript,
        trailingQuery,
        engine: engineType,
      });

      console.info(`[useWakeWord] 🎙️ "Hey Siri" detected! Trailing prompt:`, trailingQuery || '(none)');

      if (onWakeWordRef.current) {
        onWakeWordRef.current({
          phrase: 'Hey Siri',
          transcript,
          trailingQuery,
          engine: engineType,
        });
      }
    } else {
      // Non-wake-word speech: notify follow-up handler if active
      if (onSpeechRecognizedRef.current) {
        onSpeechRecognizedRef.current(transcript);
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
    }
    vadAudioCtxRef.current = null;
    vadAnalyserRef.current = null;
    vadChunksRef.current = [];
    isCapturingRef.current = false;
  }, []);

  // ----------------------------------------------------
  // ENGINE A: Native Web Speech Recognition (Chrome/Edge/Safari)
  // ----------------------------------------------------
  useEffect(() => {
    if (!hasNativeSpeech) return;

    if (!isEnabled) {
      isStoppingRef.current = true;
      clearTimeout(restartTimerRef.current);
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {}
        recognitionRef.current = null;
      }
      if (persistentMicStreamRef.current) {
        persistentMicStreamRef.current.getTracks().forEach((t) => t.stop());
        persistentMicStreamRef.current = null;
      }
      setIsListening(false);
      return;
    }

    isStoppingRef.current = false;
    setIsListening(true);

    // Keep persistent audio track open so Chrome never switches the microphone on and off
    if (!persistentMicStreamRef.current && navigator?.mediaDevices?.getUserMedia) {
      navigator.mediaDevices
        .getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        })
        .then((stream) => {
          if (isStoppingRef.current) {
            stream.getTracks().forEach((t) => t.stop());
            return;
          }
          persistentMicStreamRef.current = stream;
        })
        .catch((err) => {
          console.debug('[useWakeWord] Persistent mic stream notice:', err?.message);
        });
    }

    // Factory to start fresh SpeechRecognition instance on every cycle
    const startRecognition = () => {
      if (!shouldListenRef.current || isStoppingRef.current) return;

      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {}
        recognitionRef.current = null;
      }

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) return;

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
      recognition.lang = (typeof navigator !== 'undefined' && navigator.language) ? navigator.language : 'en-US';
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
          console.warn('[useWakeWord] Microphone permission notice:', event.error);
          setError('Microphone permission required for "Hey Siri".');
          setIsListening(false);
          return;
        }
        if (event.error !== 'aborted') {
          console.debug('[useWakeWord] Native recognition notice:', event.error);
        }
      };

      recognition.onend = () => {
        recognitionRef.current = null;
        // Recreate new SpeechRecognition instance smoothly without dropping mic
        if (shouldListenRef.current && !isStoppingRef.current) {
          clearTimeout(restartTimerRef.current);
          restartTimerRef.current = setTimeout(() => {
            startRecognition();
          }, 150);
        }
      };

      try {
        recognition.start();
      } catch (err) {
        console.debug('[useWakeWord] Start notice:', err?.message);
        if (shouldListenRef.current && !isStoppingRef.current) {
          clearTimeout(restartTimerRef.current);
          restartTimerRef.current = setTimeout(() => {
            startRecognition();
          }, 600);
        }
      }
    };

    startRecognition();

    return () => {
      isStoppingRef.current = true;
      clearTimeout(restartTimerRef.current);
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {}
        recognitionRef.current = null;
      }
      if (persistentMicStreamRef.current) {
        persistentMicStreamRef.current.getTracks().forEach((t) => t.stop());
        persistentMicStreamRef.current = null;
      }
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
    setIsEnabled((prev) => {
      const next = !prev;
      shouldListenRef.current = next;
      return next;
    });
  }, []);

  const enableWakeWord = useCallback(() => {
    shouldListenRef.current = true;
    setIsEnabled(true);
  }, []);

  const disableWakeWord = useCallback(() => {
    shouldListenRef.current = false;
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
