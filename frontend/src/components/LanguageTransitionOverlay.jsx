/**
 * LanguageTransitionOverlay.jsx — Cinematic full-screen transition overlay
 * that appears during language switches with 200 fine starlight particles,
 * a blurred backdrop, language transition badge, and animated progress bar.
 *
 * Minimum display: 6 seconds. Maximum hard cap: 12 seconds.
 * The overlay waits for all pending translations to settle before dismissing
 * (after the minimum time has elapsed).
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { useLanguage, LANGUAGES } from "../context/LanguageContext";

/** Generate deterministic particle data for 200 starlight dots */
function generateStarlightParticles(count = 200) {
  const particles = [];
  // Use a seeded pseudo-random for consistent SSR/CSR
  let seed = 42;
  const rand = () => {
    seed = (seed * 16807 + 0) % 2147483647;
    return (seed - 1) / 2147483646;
  };
  for (let i = 0; i < count; i++) {
    particles.push({
      id: i,
      x: rand() * 100,        // % position
      y: rand() * 100,
      size: 1 + rand() * 2.5,  // Very fine dots: 1px - 3.5px
      delay: rand() * 6,       // Staggered animation delay (0-6s)
      duration: 2 + rand() * 4, // Pulse cycle 2-6s
      opacity: 0.15 + rand() * 0.6, // Base opacity 0.15-0.75
      hue: 190 + rand() * 40,  // Cyan-blue range (190-230)
    });
  }
  return particles;
}

const STARLIGHT_PARTICLES = generateStarlightParticles(200);

const MIN_DISPLAY_MS = 6000;   // 6 seconds minimum
const MAX_DISPLAY_MS = 12000;  // 12 seconds hard cap
const SETTLE_CHECK_INTERVAL = 300; // Check pending translations every 300ms
const FADE_DURATION_MS = 600;  // Fade-out animation

export function LanguageTransitionOverlay() {
  const {
    isTransitioning,
    previousLanguage,
    language,
    dismissTransition,
    pendingTranslationCount,
  } = useLanguage();

  const [isVisible, setIsVisible] = useState(false);
  const [isFadingOut, setIsFadingOut] = useState(false);
  const [progress, setProgress] = useState(0);
  const startTimeRef = useRef(null);
  const progressIntervalRef = useRef(null);
  const settleCheckRef = useRef(null);
  const maxTimerRef = useRef(null);
  const fadeTimerRef = useRef(null);

  const fromLang = useMemo(() => {
    if (!previousLanguage) return null;
    return LANGUAGES.find((l) => l.code === previousLanguage);
  }, [previousLanguage]);

  const toLang = useMemo(() => {
    return LANGUAGES.find((l) => l.code === language);
  }, [language]);

  const cleanup = useCallback(() => {
    if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
    if (settleCheckRef.current) clearInterval(settleCheckRef.current);
    if (maxTimerRef.current) clearTimeout(maxTimerRef.current);
    if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current);
    progressIntervalRef.current = null;
    settleCheckRef.current = null;
    maxTimerRef.current = null;
    fadeTimerRef.current = null;
  }, []);

  const startFadeOut = useCallback(() => {
    setIsFadingOut(true);
    setProgress(100);
    fadeTimerRef.current = setTimeout(() => {
      setIsVisible(false);
      setIsFadingOut(false);
      setProgress(0);
      cleanup();
      dismissTransition();
    }, FADE_DURATION_MS);
  }, [cleanup, dismissTransition]);

  useEffect(() => {
    if (isTransitioning && fromLang && toLang) {
      // Start the overlay
      setIsVisible(true);
      setIsFadingOut(false);
      setProgress(0);
      startTimeRef.current = Date.now();

      // Animated progress bar: smooth interpolation over MIN_DISPLAY_MS
      // Goes from 0% to ~85% during the minimum period, then jumps to 100% on dismiss
      progressIntervalRef.current = setInterval(() => {
        const elapsed = Date.now() - startTimeRef.current;
        const ratio = Math.min(elapsed / MIN_DISPLAY_MS, 1);
        // Ease-out cubic for smooth deceleration: progress reaches ~85% at min time
        const eased = 1 - Math.pow(1 - ratio, 3);
        setProgress(Math.min(Math.round(eased * 88), 88)); // Cap at 88% until dismiss
      }, 50);

      // After minimum display time, start checking if translations settled
      settleCheckRef.current = setInterval(() => {
        const elapsed = Date.now() - startTimeRef.current;
        if (elapsed >= MIN_DISPLAY_MS) {
          const pending = pendingTranslationCount?.current ?? 0;
          if (pending <= 0) {
            // Translations settled! Start fade-out
            cleanup();
            startFadeOut();
          }
        }
      }, SETTLE_CHECK_INTERVAL);

      // Hard cap — force dismiss even if translations are still pending
      maxTimerRef.current = setTimeout(() => {
        cleanup();
        startFadeOut();
      }, MAX_DISPLAY_MS);

      return () => {
        cleanup();
      };
    }
  }, [isTransitioning, fromLang, toLang, pendingTranslationCount, cleanup, startFadeOut]);

  if (!isVisible) return null;

  return (
    <div
      className={`language-transition-overlay ${isFadingOut ? "fading-out" : "fading-in"}`}
      role="status"
      aria-live="polite"
      aria-label="Translating interface"
    >
      {/* Blurred backdrop */}
      <div className="lto-backdrop" />

      {/* Starlight particles field */}
      <div className="lto-particles">
        {STARLIGHT_PARTICLES.map((p) => (
          <div
            key={p.id}
            className="lto-star"
            style={{
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: `${p.size}px`,
              height: `${p.size}px`,
              opacity: p.opacity,
              animationDelay: `${p.delay}s`,
              animationDuration: `${p.duration}s`,
              "--star-hue": p.hue,
            }}
          />
        ))}
      </div>

      {/* Center content */}
      <div className="lto-center">
        {/* Language transition badge */}
        <div className="lto-badge">
          <span className="lto-lang-from">{fromLang?.native || fromLang?.label || "..."}</span>
          <span className="lto-arrow">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14" />
              <path d="m12 5 7 7-7 7" />
            </svg>
          </span>
          <span className="lto-lang-to">{toLang?.native || toLang?.label || "..."}</span>
        </div>

        {/* Subtitle */}
        <p className="lto-subtitle">Translating interface...</p>

        {/* Progress bar */}
        <div className="lto-progress-container">
          <div className="lto-progress-track">
            <div
              className="lto-progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="lto-progress-label">{progress}%</span>
        </div>
      </div>
    </div>
  );
}

export default LanguageTransitionOverlay;
