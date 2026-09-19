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

// ─── Audio-Reactive Mira Avatar ────────────────────────────────────
function VoiceOrb({ state, volume = 0 }) {
  const avatarScale = useMemo(() => {
    if (state === 'LISTENING') return 1 + volume * 0.35;
    if (state === 'SPEAKING') return 1 + volume * 0.3;
    return 1;
  }, [state, volume]);

  const glowConfig = useMemo(() => {
    switch (state) {
      case 'LISTENING':
        return {
          bg: 'radial-gradient(circle, rgba(34,211,238,0.45) 0%, rgba(6,182,212,0.2) 60%, transparent 75%)',
          border: '2px solid rgba(34,211,238,0.7)',
          ringColor: 'rgba(34,211,238,0.4)',
          shadow: `0 0 ${24 + volume * 45}px rgba(34,211,238,${0.4 + volume * 0.4}), 0 0 ${48 + volume * 60}px rgba(6,182,212,${0.2 + volume * 0.2})`,
          badgeColor: 'bg-cyan-400',
          badgePing: true,
          animation: 'none',
        };
      case 'THINKING':
        return {
          bg: 'radial-gradient(circle, rgba(129,140,248,0.4) 0%, rgba(99,102,241,0.15) 60%, transparent 75%)',
          border: '2px solid rgba(129,140,248,0.6)',
          ringColor: 'rgba(129,140,248,0.3)',
          shadow: '0 0 24px rgba(129,140,248,0.35), 0 0 48px rgba(99,102,241,0.15)',
          badgeColor: 'bg-indigo-400',
          badgePing: true,
          animation: 'voiceOrbBreathe 2.5s ease-in-out infinite',
        };
      case 'SPEAKING':
        return {
          bg: 'radial-gradient(circle, rgba(52,211,153,0.45) 0%, rgba(16,185,129,0.2) 60%, transparent 75%)',
          border: '2px solid rgba(52,211,153,0.7)',
          ringColor: 'rgba(52,211,153,0.4)',
          shadow: `0 0 ${24 + volume * 40}px rgba(52,211,153,${0.4 + volume * 0.35}), 0 0 ${48 + volume * 55}px rgba(16,185,129,${0.15 + volume * 0.2})`,
          badgeColor: 'bg-emerald-400',
          badgePing: true,
          animation: 'none',
        };
      case 'WAITING_FOR_USER':
        return {
          bg: 'radial-gradient(circle, rgba(148,163,184,0.2) 0%, rgba(100,116,139,0.08) 60%, transparent 75%)',
          border: '2px solid rgba(148,163,184,0.35)',
          ringColor: 'rgba(148,163,184,0.2)',
          shadow: '0 0 16px rgba(148,163,184,0.15)',
          badgeColor: 'bg-slate-400',
          badgePing: false,
          animation: 'voiceOrbIdle 3s ease-in-out infinite',
        };
      default:
        return {
          bg: 'transparent',
          border: '2px solid rgba(148,163,184,0.2)',
          ringColor: 'transparent',
          shadow: 'none',
          badgeColor: 'bg-slate-500',
          badgePing: false,
          animation: 'none',
        };
    }
  }, [state, volume]);

  return (
    <div className="relative flex items-center justify-center" style={{ width: '96px', height: '96px' }}>
      {/* Outer audio-reactive glow ring */}
      <div
        className="absolute rounded-full transition-all duration-200 pointer-events-none"
        style={{
          width: '96px',
          height: '96px',
          background: glowConfig.bg,
          boxShadow: glowConfig.shadow,
          transform: `scale(${avatarScale})`,
          animation: glowConfig.animation,
        }}
      />

      {/* Ripple rings when listening to speech */}
      {state === 'LISTENING' && volume > 0.03 && (
        <>
          {[0, 1].map((i) => (
            <div
              key={i}
              className="absolute rounded-full border border-cyan-400/30 pointer-events-none"
              style={{
                width: `${72 + i * 20}px`,
                height: `${72 + i * 20}px`,
                opacity: Math.max(0, 0.45 - i * 0.15) * Math.min(1, volume * 5),
                transform: `scale(${1 + volume * 0.35 * (i + 1)})`,
                transition: 'all 0.15s ease-out',
              }}
            />
          ))}
        </>
      )}

      {/* Speaking acoustic pulse rings */}
      {state === 'SPEAKING' && (
        <div
          className="absolute rounded-full border border-emerald-400/30 pointer-events-none animate-ping opacity-30"
          style={{ width: '80px', height: '80px' }}
        />
      )}

      {/* Central Mira Avatar Image */}
      <div
        className="relative rounded-full overflow-hidden transition-all duration-150 shrink-0 cursor-pointer shadow-lg group"
        style={{
          width: '68px',
          height: '68px',
          border: glowConfig.border,
          transform: `scale(${state === 'LISTENING' ? 1 + volume * 0.12 : state === 'SPEAKING' ? 1 + volume * 0.1 : 1})`,
          boxShadow: glowConfig.shadow,
        }}
      >
        <img
          src="/mira-avatar.png"
          alt="Mira Voice Assistant"
          className="w-full h-full object-cover object-top transition-transform duration-300 group-hover:scale-105"
        />
        {/* Subtle glass reflection overlay */}
        <div className="absolute inset-0 bg-gradient-to-tr from-black/20 via-transparent to-white/20 pointer-events-none" />
      </div>

      {/* Status indicator badge dot */}
      <div className="absolute bottom-2.5 right-2.5 flex items-center justify-center pointer-events-none">
        {glowConfig.badgePing && (
          <span className={`animate-ping absolute inline-flex h-3 w-3 rounded-full ${glowConfig.badgeColor} opacity-75`} />
        )}
        <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${glowConfig.badgeColor} border border-slate-900 shadow-sm`} />
      </div>
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
