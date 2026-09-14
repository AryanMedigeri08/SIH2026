import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Bot, Mic, Volume2, Loader2, Sparkles, Zap } from 'lucide-react';
import { useChat } from '../../context/ChatContext';

/**
 * VoiceAgentWindow — Lightweight floating voice-agent status widget.
 * 
 * Appears below the Siri toggle when activated via "Hey Siri".
 * Shows a cute animated bot avatar that communicates the current voice state:
 * IDLE (hidden) | LISTENING | THINKING | SPEAKING | ACTION
 * 
 * Pure visual representation — speech capture is managed seamlessly by the
 * background speech recognition engine with 0 microphone device contention.
 */

// ─── Animated Bot SVG Avatar ───────────────────────────────────────
function BotAvatar({ state }) {
  const eyeScale = state === 'LISTENING' ? 1.3 : state === 'THINKING' ? 0.6 : 1;
  const mouthWidth = state === 'SPEAKING' ? 14 : 10;
  const mouthRy = state === 'SPEAKING' ? 4 : 2;

  return (
    <svg
      viewBox="0 0 80 80"
      className="w-20 h-20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Head - rounded rectangle with gradient */}
      <defs>
        <linearGradient id="botHeadGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="50%" stopColor="#8b5cf6" />
          <stop offset="100%" stopColor="#a78bfa" />
        </linearGradient>
        <linearGradient id="botFaceGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1e1b4b" />
          <stop offset="100%" stopColor="#312e81" />
        </linearGradient>
        <radialGradient id="eyeGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#67e8f9" />
          <stop offset="100%" stopColor="#22d3ee" />
        </radialGradient>
      </defs>

      {/* Antenna */}
      <line x1="40" y1="8" x2="40" y2="16" stroke="#a78bfa" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="40" cy="6" r="3.5" fill="#c4b5fd">
        <animate
          attributeName="r"
          values={state === 'LISTENING' ? '3.5;5.5;3.5' : state === 'THINKING' ? '3.5;4.5;3.5' : '3.5'}
          dur={state === 'LISTENING' ? '1.1s' : '2s'}
          repeatCount="indefinite"
        />
        <animate
          attributeName="fill"
          values={state === 'LISTENING' ? '#c4b5fd;#67e8f9;#c4b5fd' : '#c4b5fd'}
          dur="1.5s"
          repeatCount="indefinite"
        />
      </circle>

      {/* Head body */}
      <rect x="12" y="16" width="56" height="48" rx="16" ry="16" fill="url(#botHeadGrad)" />
      {/* Inner face panel */}
      <rect x="17" y="21" width="46" height="38" rx="12" ry="12" fill="url(#botFaceGrad)" opacity="0.9" />

      {/* Left Eye */}
      <ellipse cx="30" cy="36" rx="5" ry="5" fill="url(#eyeGlow)">
        <animateTransform
          attributeName="transform"
          type="scale"
          values={`${eyeScale};${eyeScale}`}
          dur="0.3s"
          fill="freeze"
        />
        {state === 'LISTENING' && (
          <animate attributeName="ry" values="5;6;5" dur="1.4s" repeatCount="indefinite" />
        )}
        {state === 'THINKING' && (
          <animate attributeName="ry" values="3;2;3" dur="1.8s" repeatCount="indefinite" />
        )}
      </ellipse>
      {/* Left pupil */}
      <circle cx="30" cy="36" r="2" fill="#0e1629">
        {state === 'THINKING' && (
          <animate attributeName="cx" values="29;31;29" dur="2s" repeatCount="indefinite" />
        )}
      </circle>

      {/* Right Eye */}
      <ellipse cx="50" cy="36" rx="5" ry="5" fill="url(#eyeGlow)">
        <animateTransform
          attributeName="transform"
          type="scale"
          values={`${eyeScale};${eyeScale}`}
          dur="0.3s"
          fill="freeze"
        />
        {state === 'LISTENING' && (
          <animate attributeName="ry" values="5;6;5" dur="1.4s" repeatCount="indefinite" />
        )}
        {state === 'THINKING' && (
          <animate attributeName="ry" values="3;2;3" dur="1.8s" repeatCount="indefinite" />
        )}
      </ellipse>
      {/* Right pupil */}
      <circle cx="50" cy="36" r="2" fill="#0e1629">
        {state === 'THINKING' && (
          <animate attributeName="cx" values="49;51;49" dur="2s" repeatCount="indefinite" />
        )}
      </circle>

      {/* Mouth */}
      <ellipse cx="40" cy="50" rx={mouthWidth / 2} ry={mouthRy} fill="#67e8f9" opacity="0.85">
        {state === 'SPEAKING' && (
          <animate attributeName="ry" values="2;5;3;5;2" dur="0.55s" repeatCount="indefinite" />
        )}
        {state === 'SPEAKING' && (
          <animate attributeName="rx" values="5;7;5;7;5" dur="0.55s" repeatCount="indefinite" />
        )}
      </ellipse>

      {/* Cheek blush */}
      <circle cx="20" cy="44" r="4" fill="#f472b6" opacity="0.2" />
      <circle cx="60" cy="44" r="4" fill="#f472b6" opacity="0.2" />
    </svg>
  );
}

// ─── Concentric Sound Rings (LISTENING state) ──────────────────────
function ListeningRings() {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="absolute rounded-full border-2 border-cyan-400/35"
          style={{
            width: `${92 + i * 28}px`,
            height: `${92 + i * 28}px`,
            animation: `voiceAgentPing ${1.8 + i * 0.3}s ease-out infinite`,
            animationDelay: `${i * 0.4}s`,
          }}
        />
      ))}
    </div>
  );
}

// ─── Thinking Shimmer Dots ─────────────────────────────────────────
function ThinkingDots() {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="absolute w-1.5 h-1.5 rounded-full bg-purple-400/70"
          style={{
            animation: `voiceAgentOrbit 2.4s linear infinite`,
            animationDelay: `${i * 0.4}s`,
            transformOrigin: '50% 50%',
            left: '50%',
            top: '50%',
            marginLeft: '-3px',
            marginTop: '-3px',
            transform: `rotate(${i * 60}deg) translateY(-46px)`,
          }}
        />
      ))}
    </div>
  );
}

// ─── Speaking Wave Bars ────────────────────────────────────────────
function SpeakingBars() {
  return (
    <div className="flex items-end justify-center gap-1 h-5 mt-1">
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="w-1 bg-gradient-to-t from-cyan-400 to-purple-400 rounded-full"
          style={{
            animation: `voiceAgentBar 0.8s ease-in-out infinite`,
            animationDelay: `${i * 0.12}s`,
            height: '4px',
          }}
        />
      ))}
    </div>
  );
}

// ─── State Label ───────────────────────────────────────────────────
function StateLabel({ state }) {
  const labels = {
    LISTENING: { text: 'Listening...', icon: Mic, color: 'text-cyan-300' },
    THINKING: { text: 'Thinking...', icon: Loader2, color: 'text-purple-300' },
    SPEAKING: { text: 'Speaking...', icon: Volume2, color: 'text-emerald-300' },
    ACTION: { text: 'On it...', icon: Zap, color: 'text-amber-300' },
  };

  const info = labels[state];
  if (!info) return null;

  const Icon = info.icon;
  return (
    <div className={`flex items-center justify-center gap-1.5 text-xs font-medium ${info.color}`}>
      <Icon className={`w-3 h-3 ${state === 'THINKING' ? 'animate-spin' : state === 'LISTENING' ? 'animate-pulse' : ''}`} />
      <span className="tracking-wide">{info.text}</span>
    </div>
  );
}

// ─── Main VoiceAgentWindow Component ───────────────────────────────
export function VoiceAgentWindow() {
  const {
    voiceAgentState,
    siriToggleRef,
    dismissVoiceAgent,
  } = useChat();

  const windowRef = useRef(null);
  const [position, setPosition] = useState({ top: 72, right: 24 });
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimatingOut, setIsAnimatingOut] = useState(false);

  const isActive = voiceAgentState && voiceAgentState !== 'IDLE';

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
      const timer = setTimeout(() => {
        setIsVisible(false);
        setIsAnimatingOut(false);
      }, 280);
      return () => clearTimeout(timer);
    }
  }, [isActive, isVisible]);

  const handleDismiss = useCallback(() => {
    dismissVoiceAgent?.();
  }, [dismissVoiceAgent]);

  if (!isVisible && !isActive) return null;

  return (
    <>
      {/* CSS Keyframes for animations */}
      <style>{`
        @keyframes voiceAgentPing {
          0% { transform: scale(0.8); opacity: 0.6; }
          100% { transform: scale(1.4); opacity: 0; }
        }
        @keyframes voiceAgentOrbit {
          0% { opacity: 0.3; }
          50% { opacity: 1; }
          100% { opacity: 0.3; }
        }
        @keyframes voiceAgentBar {
          0%, 100% { height: 4px; }
          50% { height: 16px; }
        }
        @keyframes voiceAgentEnter {
          0% { transform: scale(0.7) translateY(-12px); opacity: 0; }
          100% { transform: scale(1) translateY(0); opacity: 1; }
        }
        @keyframes voiceAgentExit {
          0% { transform: scale(1) translateY(0); opacity: 1; }
          100% { transform: scale(0.7) translateY(-12px); opacity: 0; }
        }
        @keyframes voiceAgentGlow {
          0%, 100% { box-shadow: 0 0 20px rgba(139, 92, 246, 0.18), 0 0 40px rgba(34, 211, 238, 0.1); }
          50% { box-shadow: 0 0 32px rgba(139, 92, 246, 0.3), 0 0 65px rgba(34, 211, 238, 0.2); }
        }
        @keyframes voiceAgentBreathe {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.04); }
        }
      `}</style>

      <div
        ref={windowRef}
        className="fixed z-50"
        style={{
          top: `${position.top}px`,
          right: `${position.right}px`,
          animation: isAnimatingOut
            ? 'voiceAgentExit 0.28s ease-in forwards'
            : 'voiceAgentEnter 0.32s cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
        }}
      >
        <div
          className="relative w-[180px] h-[200px] rounded-2xl overflow-hidden shadow-2xl"
          style={{
            background: 'linear-gradient(135deg, rgba(15, 12, 41, 0.96), rgba(48, 16, 85, 0.94), rgba(13, 22, 42, 0.96))',
            backdropFilter: 'blur(24px)',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            animation: voiceAgentState === 'LISTENING'
              ? 'voiceAgentGlow 2s ease-in-out infinite'
              : voiceAgentState === 'SPEAKING'
              ? 'voiceAgentGlow 1.5s ease-in-out infinite'
              : 'none',
          }}
        >
          {/* Top accent bar */}
          <div className="h-[2px] w-full bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400" />

          {/* Close / dismiss button */}
          <button
            type="button"
            onClick={handleDismiss}
            className="absolute top-2 right-2 w-5 h-5 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 text-white/50 hover:text-white/90 transition-all z-10 text-[10px] leading-none cursor-pointer"
            title="Dismiss voice agent"
            aria-label="Dismiss voice agent"
          >
            ×
          </button>

          {/* Main content area */}
          <div className="flex flex-col items-center justify-center h-full pt-1 pb-3 px-3 relative">

            {/* State-specific background effects */}
            {voiceAgentState === 'LISTENING' && <ListeningRings />}
            {voiceAgentState === 'THINKING' && <ThinkingDots />}

            {/* Bot Avatar */}
            <div
              className="relative z-10"
              style={{
                animation: voiceAgentState === 'LISTENING'
                  ? 'voiceAgentBreathe 2s ease-in-out infinite'
                  : voiceAgentState === 'SPEAKING'
                  ? 'voiceAgentBreathe 1.2s ease-in-out infinite'
                  : 'none',
              }}
            >
              <BotAvatar state={voiceAgentState} />
            </div>

            {/* Speaking wave bars */}
            {voiceAgentState === 'SPEAKING' && <SpeakingBars />}

            {/* State label */}
            <div className="mt-2 relative z-10">
              <StateLabel state={voiceAgentState} />
            </div>
          </div>

          {/* Bottom subtle glow */}
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-24 h-8 bg-purple-500/15 blur-xl rounded-full pointer-events-none" />
        </div>
      </div>
    </>
  );
}

export default VoiceAgentWindow;
