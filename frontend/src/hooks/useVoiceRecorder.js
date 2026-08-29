import { useState, useRef, useEffect, useCallback } from 'react';

/**
 * useVoiceRecorder — Custom Hook for Dynamic Voice Recording & Real-Time Silence Detection (VAD).
 * 
 * Automatically detects when the user stops speaking (dynamic silence detection)
 * while providing manual stop/cancel controls and live audio volume levels for animated waveforms.
 */
export function useVoiceRecorder({ onRecordingComplete, silenceThresholdMs = 1600, minSpeechThreshold = 0.025 } = {}) {
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [volume, setVolume] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);
  const animFrameRef = useRef(null);
  const timerIntervalRef = useRef(null);

  const chunksRef = useRef([]);
  const hasSpokenRef = useRef(false);
  const silenceStartRef = useRef(null);
  const isCancelledRef = useRef(false);
  const startTimeRef = useRef(0);

  // Clean up all audio nodes and tracks
  const cleanupAudio = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      try {
        audioContextRef.current.close();
      } catch (e) {}
      audioContextRef.current = null;
    }
    analyserRef.current = null;
  }, []);

  // Stop recording and process audio blob
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {}
    }
    setIsRecording(false);
    setIsSpeaking(false);
    setVolume(0);
    cleanupAudio();
  }, [cleanupAudio]);

  // Cancel recording without submitting
  const cancelRecording = useCallback(() => {
    isCancelledRef.current = true;
    stopRecording();
  }, [stopRecording]);

  // Start recording with dynamic VAD
  const startRecording = useCallback(async () => {
    setError(null);
    isCancelledRef.current = false;
    hasSpokenRef.current = false;
    silenceStartRef.current = null;
    chunksRef.current = [];
    setDuration(0);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      // Audio Context for VAD and Volume Visualizer
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.4;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Select supported MediaRecorder MIME type
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        if (MediaRecorder.isTypeSupported('audio/webm')) {
          mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        } else {
          mimeType = '';
        }
      }

      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        if (!isCancelledRef.current && chunksRef.current.length > 0) {
          const finalBlob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
          if (onRecordingComplete) {
            onRecordingComplete(finalBlob);
          }
        }
        cleanupAudio();
      };

      recorder.start(100); // collect 100ms chunks
      startTimeRef.current = Date.now();
      setIsRecording(true);

      // Duration counter
      timerIntervalRef.current = setInterval(() => {
        setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000));
      }, 200);

      // Dynamic Silence Detection Loop (VAD)
      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const checkAudioLevel = () => {
        if (!analyserRef.current || !streamRef.current) return;

        analyserRef.current.getByteFrequencyData(dataArray);

        // Calculate Root Mean Square Volume
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i] * dataArray[i];
        }
        const rms = Math.sqrt(sum / dataArray.length) / 255;
        setVolume(rms);

        const now = Date.now();
        const elapsed = now - startTimeRef.current;

        if (rms > minSpeechThreshold) {
          hasSpokenRef.current = true;
          setIsSpeaking(true);
          silenceStartRef.current = null; // reset silence timer while user is speaking
        } else {
          setIsSpeaking(false);
          // If speech was detected previously, monitor how long the silence lasts
          if (hasSpokenRef.current) {
            if (!silenceStartRef.current) {
              silenceStartRef.current = now;
            } else {
              const silentDuration = now - silenceStartRef.current;
              // User has finished their sentence and remained silent for silenceThresholdMs -> Auto-stop!
              if (silentDuration >= silenceThresholdMs && elapsed > 800) {
                stopRecording();
                return;
              }
            }
          }
        }

        // Safety max duration cap (30 seconds)
        if (elapsed > 30000) {
          stopRecording();
          return;
        }

        animFrameRef.current = requestAnimationFrame(checkAudioLevel);
      };

      animFrameRef.current = requestAnimationFrame(checkAudioLevel);
    } catch (err) {
      console.error('Microphone access failed:', err);
      setError(err.message || 'Microphone access denied. Please grant permission in your browser.');
      setIsRecording(false);
      cleanupAudio();
    }
  }, [minSpeechThreshold, silenceThresholdMs, onRecordingComplete, stopRecording, cleanupAudio]);

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      cleanupAudio();
    };
  }, [cleanupAudio]);

  return {
    isRecording,
    isSpeaking,
    volume,
    duration,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}
export default useVoiceRecorder;
