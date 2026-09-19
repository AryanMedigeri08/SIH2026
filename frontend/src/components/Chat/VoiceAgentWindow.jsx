import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { X } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';

/**
 * VoiceAgentWindow — Professional floating voice-agent widget.
 *
 * Redesigned with a minimal, premium, AI-native visual language.
 * Central audio-reactive orb replaces the old cartoon bot avatar.
 *
 * States: IDLE (hidden) | LISTENING | THINKING | SPEAKING | WAITING_FOR_USER
 *
 * Key design principles:
 * - Minimal, calm, professional
 * - Audio-reactive animations (not arbitrary timers)
 * - State-synchronized with real backend lifecycle
 * - Conversational loop: listen → process → speak → wait → listen again
 */

// ─── Language Display Names ────────────────────────────────────────
const LANG_NAMES = {
  hi: 'Hindi', 'hi-IN': 'Hindi',
  en: 'English', 'en-IN': 'English',
  te: 'Telugu', 'te-IN': 'Telugu',
  ta: 'Tamil', 'ta-IN': 'Tamil',
  kn: 'Kannada', 'kn-IN': 'Kannada',
  mr: 'Marathi', 'mr-IN': 'Marathi',
  bn: 'Bengali', 'bn-IN': 'Bengali',
  gu: 'Gujarati', 'gu-IN': 'Gujarati',
  ml: 'Malayalam', 'ml-IN': 'Malayalam',
  pa: 'Punjabi', 'pa-IN': 'Punjabi',
};

// ─── Audio-Reactive Orb ────────────────────────────────────────────
function VoiceOrb({ state, volume = 0 }) {
  const orbScale = useMemo(() => {
    if (state === 'LISTENING') return 1 + volume * 0.4;
    if (state === 'SPEAKING') return 1 + volume * 0.35;
    return 1;
  }, [state, volume]);

  const orbConfig = useMemo(() => {
    switch (state) {
      case 'LISTENING':
        return {
          bg: 'radial-gradient(circle, rgba(34,211,238,0.5) 0%, rgba(6,182,212,0.25) 50%, transparent 70%)',
          border: '2px solid rgba(34,211,238,0.5)',
          shadow: `0 0 ${20 + volume * 40}px rgba(34,211,238,${0.3 + volume * 0.4}), 0 0 ${40 + volume * 60}px rgba(34,211,238,${0.1 + volume * 0.2})`,
          animation: 'none',
        };
      case 'THINKING':
        return {
          bg: 'radial-gradient(circle, rgba(129,140,248,0.4) 0%, rgba(99,102,241,0.2) 50%, transparent 70%)',
          border: '2px solid rgba(129,140,248,0.35)',
          shadow: '0 0 24px rgba(129,140,248,0.25), 0 0 48px rgba(99,102,241,0.1)',
          animation: 'voiceOrbBreathe 2.5s ease-in-out infinite',
        };
      case 'SPEAKING':
        return {
          bg: 'radial-gradient(circle, rgba(52,211,153,0.45) 0%, rgba(16,185,129,0.2) 50%, transparent 70%)',
          border: '2px solid rgba(52,211,153,0.45)',
          shadow: `0 0 ${20 + volume * 35}px rgba(52,211,153,${0.3 + volume * 0.3}), 0 0 ${40 + volume * 50}px rgba(16,185,129,${0.1 + volume * 0.15})`,
          animation: 'none',
        };
      case 'WAITING_FOR_USER':
        return {
          bg: 'radial-gradient(circle, rgba(148,163,184,0.2) 0%, rgba(100,116,139,0.1) 50%, transparent 70%)',
          border: '2px solid rgba(148,163,184,0.2)',
          shadow: '0 0 16px rgba(148,163,184,0.1)',
          animation: 'voiceOrbIdle 3s ease-in-out infinite',
        };
      default:
        return {
          bg: 'transparent',
          border: '2px solid rgba(148,163,184,0.15)',
          shadow: 'none',
          animation: 'none',
        };
    }
  }, [state, volume]);

  return (
    <div className="relative flex items-center justify-center" style={{ width: '88px', height: '88px' }}>
      {/* Outer glow ring */}
      <div
        className="absolute rounded-full transition-all duration-200"
        style={{
          width: '88px',
          height: '88px',
          background: orbConfig.bg,
          boxShadow: orbConfig.shadow,
          transform: `scale(${orbScale})`,
          animation: orbConfig.animation,
        }}
      />
      {/* Inner core */}
      <div
        className="relative rounded-full transition-all duration-150"
        style={{
          width: '44px',
          height: '44px',
          background: state === 'LISTENING'
            ? 'radial-gradient(circle, #22d3ee 0%, #0891b2 100%)'
            : state === 'THINKING'
            ? 'radial-gradient(circle, #818cf8 0%, #6366f1 100%)'
            : state === 'SPEAKING'
            ? 'radial-gradient(circle, #34d399 0%, #10b981 100%)'
            : 'radial-gradient(circle, #94a3b8 0%, #64748b 100%)',
          border: orbConfig.border,
          transform: `scale(${state === 'LISTENING' ? 1 + volume * 0.15 : state === 'SPEAKING' ? 1 + volume * 0.12 : 1})`,
          boxShadow: state === 'LISTENING'
            ? '0 0 12px rgba(34,211,238,0.6), inset 0 0 8px rgba(34,211,238,0.3)'
            : state === 'SPEAKING'
            ? '0 0 12px rgba(52,211,153,0.5), inset 0 0 8px rgba(52,211,153,0.2)'
            : state === 'THINKING'
            ? '0 0 10px rgba(129,140,248,0.4), inset 0 0 6px rgba(129,140,248,0.2)'
            : '0 0 6px rgba(148,163,184,0.15)',
        }}
      />
      {/* Listening: subtle ripple rings */}
      {state === 'LISTENING' && volume > 0.03 && (
        <>
          {[0, 1].map((i) => (
            <div
              key={i}
              className="absolute rounded-full border border-cyan-400/20 pointer-events-none"
              style={{
                width: `${60 + i * 20}px`,
                height: `${60 + i * 20}px`,
                opacity: Math.max(0, 0.4 - i * 0.15) * Math.min(1, volume * 5),
                transform: `scale(${1 + volume * 0.3 * (i + 1)})`,
                transition: 'all 0.15s ease-out',
              }}
            />
          ))}
        </>
      )}
    </div>
  );
}

// ─── State Label ───────────────────────────────────────────────────
function StateLabel({ state }) {
  const config = {
    LISTENING: { text: 'Listening...', color: 'text-cyan-400' },
    THINKING: { text: 'Thinking...', color: 'text-indigo-400' },
    SPEAKING: { text: 'Speaking...', color: 'text-emerald-400' },
    WAITING_FOR_USER: { text: 'Ready', color: 'text-slate-400' },
  };

  const info = config[state];
  if (!info) return null;

  return (
    <div className={`text-[11px] font-medium tracking-wider uppercase ${info.color} transition-colors duration-300`}>
      {info.text}
    </div>
  );
}

// ─── Main VoiceAgentWindow Component ───────────────────────────────
export function VoiceAgentWindow() {
  const {
    voiceAgentState,
    voiceSession,
    siriToggleRef,
    sendVoiceAgentAudio,
    endVoiceConversation,
    interruptVoiceAgent,
  } = useChat();

  const windowRef = useRef(null);
  const [position, setPosition] = useState({ top: 72, right: 24 });
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimatingOut, setIsAnimatingOut] = useState(false);
  const [micVolume, setMicVolume] = useState(0);

  const isActive = voiceAgentState && voiceAgentState !== 'IDLE';

  // Microphone recorder for conversational loop
  const {
    isRecording,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useVoiceRecorder({
    onRecordingComplete: sendVoiceAgentAudio,
    onVolumeChange: setMicVolume,
    silenceThresholdMs: 2000,
    maxDurationMs: 60000,
  });

  // Auto-start recording when entering LISTENING or WAITING_FOR_USER state
  useEffect(() => {
    if (voiceAgentState === 'LISTENING' || voiceAgentState === 'WAITING_FOR_USER') {
      if (!isRecording) {
        const timer = setTimeout(() => {
          startRecording();
        }, voiceAgentState === 'WAITING_FOR_USER' ? 400 : 100);
        return () => clearTimeout(timer);
      }
    } else if (voiceAgentState === 'THINKING' || voiceAgentState === 'SPEAKING') {
      if (isRecording) {
        cancelRecording();
      }
    }
  }, [voiceAgentState]); // eslint-disable-line react-hooks/exhaustive-deps

  // Position the window below the Siri toggle
  useEffect(() => {
    if (!siriToggleRef?.current || !isActive) return;

    const updatePosition = () => {
      const rect = siriToggleRef.current.getBoundingClientRect();
      if (!rect || (rect.width === 0 && rect.height === 0)) {
        setPosition({ top: 72, right: 24 });
        return;
      }
      setPosition({
        top: Math.max(10, rect.bottom + 8),
        right: Math.max(12, window.innerWidth - rect.right),
      });
    };

    updatePosition();
    window.addEventListener('resize', updatePosition);
    return () => window.removeEventListener('resize', updatePosition);
  }, [isActive, siriToggleRef]);

  // Handle visibility transitions
  useEffect(() => {
    if (isActive) {
      setIsAnimatingOut(false);
      requestAnimationFrame(() => setIsVisible(true));
    } else if (isVisible) {
      setIsAnimatingOut(true);
      if (isRecording) cancelRecording();
      const timer = setTimeout(() => {
        setIsVisible(false);
        setIsAnimatingOut(false);
      }, 280);
      return () => clearTimeout(timer);
    }
  }, [isActive]); // eslint-disable-line react-hooks/exhaustive-deps

  // Interruption: tap while speaking to interrupt
  const handleOrbClick = useCallback(() => {
    if (voiceAgentState === 'SPEAKING') {
      interruptVoiceAgent();
    } else if (voiceAgentState === 'LISTENING' && isRecording) {
      stopRecording();
    }
  }, [voiceAgentState, isRecording, interruptVoiceAgent, stopRecording]);

  const handleDismiss = useCallback(() => {
    if (isRecording) cancelRecording();
    endVoiceConversation();
  }, [isRecording, cancelRecording, endVoiceConversation]);

  // Detected language display
  const detectedLangDisplay = voiceSession?.detectedLanguage
    ? LANG_NAMES[voiceSession.detectedLanguage] || voiceSession.detectedLanguage
    : null;

  if (!isVisible && !isActive) return null;

  return (
    <>
      {/* CSS Keyframes */}
      <style>{`
        @keyframes voiceOrbBreathe {
          0%, 100% { transform: scale(1); opacity: 0.9; }
          50% { transform: scale(1.08); opacity: 1; }
        }
        @keyframes voiceOrbIdle {
          0%, 100% { transform: scale(1); opacity: 0.7; }
          50% { transform: scale(1.03); opacity: 0.85; }
        }
        @keyframes voiceWidgetEnter {
          0% { transform: scale(0.8) translateY(-10px); opacity: 0; }
          100% { transform: scale(1) translateY(0); opacity: 1; }
        }
        @keyframes voiceWidgetExit {
          0% { transform: scale(1) translateY(0); opacity: 1; }
          100% { transform: scale(0.8) translateY(-10px); opacity: 0; }
        }
      `}</style>

      <div
        ref={windowRef}
        className="fixed z-50"
        style={{
          top: `${position.top}px`,
          right: `${position.right}px`,
          animation: isAnimatingOut
            ? 'voiceWidgetExit 0.28s ease-in forwards'
            : 'voiceWidgetEnter 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
        }}
      >
        <div
          className="relative rounded-2xl overflow-hidden shadow-2xl"
          style={{
            width: '200px',
            background: 'linear-gradient(145deg, rgba(8,8,24,0.97), rgba(15,15,35,0.96))',
            backdropFilter: 'blur(32px)',
            border: '1px solid rgba(148,163,184,0.12)',
          }}
        >
          {/* Top accent line */}
          <div
            className="h-[1.5px] w-full"
            style={{
              background: voiceAgentState === 'LISTENING'
                ? 'linear-gradient(90deg, transparent, #22d3ee, transparent)'
                : voiceAgentState === 'THINKING'
                ? 'linear-gradient(90deg, transparent, #818cf8, transparent)'
                : voiceAgentState === 'SPEAKING'
                ? 'linear-gradient(90deg, transparent, #34d399, transparent)'
                : 'linear-gradient(90deg, transparent, rgba(148,163,184,0.3), transparent)',
            }}
          />

          {/* Close button */}
          <button
            type="button"
            onClick={handleDismiss}
            className="absolute top-2.5 right-2.5 w-6 h-6 flex items-center justify-center rounded-full bg-white/5 hover:bg-white/10 text-white/40 hover:text-white/80 transition-all z-10 cursor-pointer"
            title="End conversation"
            aria-label="End voice conversation"
          >
            <X className="w-3.5 h-3.5" />
          </button>

          {/* Main content */}
          <div className="flex flex-col items-center pt-6 pb-4 px-4">
            {/* Audio-reactive orb */}
            <button
              type="button"
              onClick={handleOrbClick}
              className="cursor-pointer focus:outline-none"
              aria-label={voiceAgentState === 'SPEAKING' ? 'Interrupt' : 'Voice control'}
            >
              <VoiceOrb state={voiceAgentState} volume={micVolume} />
            </button>

            {/* State label */}
            <div className="mt-3">
              <StateLabel state={voiceAgentState} />
            </div>

            {/* Detected language badge */}
            {detectedLangDisplay && (
              <div className="mt-2 px-2.5 py-0.5 rounded-full text-[10px] font-medium tracking-wide bg-white/5 text-white/50 border border-white/[0.08]">
                {detectedLangDisplay}
              </div>
            )}

            {/* Transcript snippet */}
            {voiceSession?.transcript && voiceAgentState !== 'LISTENING' && (
              <div className="mt-3 w-full px-1">
                <p className="text-[10px] text-white/30 text-center truncate leading-relaxed">
                  &ldquo;{voiceSession.transcript.length > 50
                    ? voiceSession.transcript.substring(0, 47) + '...'
                    : voiceSession.transcript}&rdquo;
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default VoiceAgentWindow;
