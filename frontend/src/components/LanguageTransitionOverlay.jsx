/**
 * LanguageTransitionOverlay.jsx — Ethereal Pastel Aurora Transition Overlay.
 *
 * Recreates the dreamy pastel aura gradient (cyan, lavender, soft rose pink)
 * with 250-300 small shining dots and 4-point twinkling stars with subtle motion,
 * a frosted glassmorphic card, dynamic progress percentage, and dual-language pill.
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { useLanguage, LANGUAGES } from "../context/LanguageContext";

const TOTAL_PARTICLES = 280; // 200+ fine shining dots + ~60 4-point twinkling stars
const MIN_DISPLAY_MS = 6500; // 6.5s buffer to allow full batch translation
const MAX_DISPLAY_MS = 12000; // 12s safety timeout
const SETTLE_CHECK_INTERVAL = 300;
const FADE_DURATION_MS = 600;

export function LanguageTransitionOverlay() {
  // Do not show transition overlay during onboarding
  if (typeof window !== "undefined" && window.location.pathname.includes("onboarding")) {
    return null;
  }

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

  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);
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
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);

    progressIntervalRef.current = null;
    settleCheckRef.current = null;
    maxTimerRef.current = null;
    fadeTimerRef.current = null;
    animFrameRef.current = null;
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

  // Lifecycle & timing
  useEffect(() => {
    if (isTransitioning && fromLang && toLang) {
      setIsVisible(true);
      setIsFadingOut(false);
      setProgress(0);
      startTimeRef.current = Date.now();

      // Progress animation (smooth cubic ease up to 90%, then 100% on dismiss)
      progressIntervalRef.current = setInterval(() => {
        const elapsed = Date.now() - startTimeRef.current;
        const ratio = Math.min(elapsed / MIN_DISPLAY_MS, 1);
        const eased = 1 - Math.pow(1 - ratio, 3);
        setProgress(Math.min(Math.round(eased * 90), 90));
      }, 50);

      // Check for completion after minimum time
      settleCheckRef.current = setInterval(() => {
        const elapsed = Date.now() - startTimeRef.current;
        if (elapsed >= MIN_DISPLAY_MS) {
          const pending = pendingTranslationCount?.current ?? 0;
          if (pending <= 0) {
            cleanup();
            startFadeOut();
          }
        }
      }, SETTLE_CHECK_INTERVAL);

      // Max timeout fallback
      maxTimerRef.current = setTimeout(() => {
        cleanup();
        startFadeOut();
      }, MAX_DISPLAY_MS);

      return () => {
        cleanup();
      };
    }
  }, [isTransitioning, fromLang, toLang, pendingTranslationCount, cleanup, startFadeOut]);

  // Canvas starfield animation: 280 sparkling dots & 4-point twinkling stars
  useEffect(() => {
    if (!isVisible) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvasRef.current) return;
      width = canvasRef.current.width = window.innerWidth;
      height = canvasRef.current.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    // Initialize 280 particles
    const particles = [];
    const colors = [
      "rgba(255, 255, 255,", // Pure white sparkle
      "rgba(207, 250, 254,", // Soft Cyan aura (#cffafe)
      "rgba(233, 213, 255,", // Soft Lavender (#e9d5ff)
      "rgba(251, 207, 232,", // Soft Rose Pink (#fbcfe8)
      "rgba(254, 240, 138,", // Gentle Gold Stardust (#fef08a)
    ];

    for (let i = 0; i < TOTAL_PARTICLES; i++) {
      const isStar = i % 5 === 0; // ~56 are 4-pointed twinkling stars, rest are fine dots
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.35, // subtle horizontal drift
        vy: -0.15 - Math.random() * 0.45,  // gentle upward floating drift
        radius: isStar ? 1.8 + Math.random() * 2.4 : 0.6 + Math.random() * 1.6,
        colorPrefix: colors[Math.floor(Math.random() * colors.length)],
        isStar,
        twinkleSpeed: 0.02 + Math.random() * 0.05,
        twinklePhase: Math.random() * Math.PI * 2,
        baseAlpha: 0.35 + Math.random() * 0.55,
        rotation: Math.random() * Math.PI,
        rotationSpeed: (Math.random() - 0.5) * 0.015,
      });
    }

    // Helper: draw 4-pointed diamond star flare
    const drawFourPointStar = (cx, cy, spikes, outerRadius, innerRadius, alpha, colorPrefix) => {
      let rot = (Math.PI / 2) * 3;
      let x = cx;
      let y = cy;
      const step = Math.PI / spikes;

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(cx, cy - outerRadius);

      for (let i = 0; i < spikes; i++) {
        x = cx + Math.cos(rot) * outerRadius;
        y = cy + Math.sin(rot) * outerRadius;
        ctx.lineTo(x, y);
        rot += step;

        x = cx + Math.cos(rot) * innerRadius;
        y = cy + Math.sin(rot) * innerRadius;
        ctx.lineTo(x, y);
        rot += step;
      }
      ctx.lineTo(cx, cy - outerRadius);
      ctx.closePath();

      // Star Glow
      ctx.shadowBlur = outerRadius * 3;
      ctx.shadowColor = `${colorPrefix} ${alpha * 0.9})`;
      ctx.fillStyle = `${colorPrefix} ${alpha})`;
      ctx.fill();

      // Bright center core
      ctx.beginPath();
      ctx.arc(cx, cy, innerRadius * 0.8, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 255, 255, ${Math.min(alpha * 1.3, 1)})`;
      ctx.fill();
      ctx.restore();
    };

    let time = 0;
    const render = () => {
      ctx.clearRect(0, 0, width, height);
      time += 0.03;

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // Motion update
        p.x += p.vx;
        p.y += p.vy;
        p.rotation += p.rotationSpeed;
        p.twinklePhase += p.twinkleSpeed;

        // Wrap around boundaries smoothly
        if (p.x < -20) p.x = width + 20;
        if (p.x > width + 20) p.x = -20;
        if (p.y < -20) p.y = height + 20;
        if (p.y > height + 20) p.y = -20;

        // Pulsating twinkle alpha
        const twinkle = Math.sin(p.twinklePhase);
        const alpha = Math.max(0.1, Math.min(1.0, p.baseAlpha + twinkle * 0.45));

        if (p.isStar) {
          // Render 4-pointed star
          const currentOuter = p.radius * (1 + twinkle * 0.3);
          const currentInner = currentOuter * 0.28;
          ctx.save();
          ctx.translate(p.x, p.y);
          ctx.rotate(p.rotation);
          drawFourPointStar(0, 0, 4, currentOuter, currentInner, alpha, p.colorPrefix);
          ctx.restore();
        } else {
          // Render glowing round starlight dot
          ctx.save();
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius * (1 + twinkle * 0.2), 0, Math.PI * 2);
          ctx.shadowBlur = p.radius * 4;
          ctx.shadowColor = `${p.colorPrefix} ${alpha * 0.8})`;
          ctx.fillStyle = `${p.colorPrefix} ${alpha})`;
          ctx.fill();

          // Soft white center
          if (p.radius > 1.2) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius * 0.4, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${Math.min(alpha * 1.2, 1)})`;
            ctx.fill();
          }
          ctx.restore();
        }
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isVisible]);

  if (!isVisible) return null;

  return (
    <div
      className={`language-transition-overlay ${isFadingOut ? "fading-out" : "fading-in"}`}
      role="status"
      aria-live="polite"
      aria-label="Translating interface"
    >
      {/* Ethereal Pastel Aurora Animated Gradient Background */}
      <div className="lto-pastel-aurora-bg">
        <div className="lto-aurora-blob lto-blob-cyan" />
        <div className="lto-aurora-blob lto-blob-lavender" />
        <div className="lto-aurora-blob lto-blob-rose" />
        <div className="lto-aurora-blob lto-blob-magenta" />
        <div className="lto-frost-glass-layer" />
      </div>

      {/* 280 Canvas Shining Dots & Twinkling Stars Field */}
      <canvas ref={canvasRef} className="lto-starfield-canvas" />

      {/* Center Floating Glass Card */}
      <div className="lto-center-card">
        {/* Top Micro-Tag */}
        <div className="lto-top-sparkle-tag">
          <span className="lto-sparkle-dot animate-ping" />
          <svg className="w-3.5 h-3.5 text-cyan-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
          </svg>
          <span className="lto-tag-text">Real-Time Indic Localization</span>
        </div>

        {/* Dual Language Direction Badge */}
        <div className="lto-badge-container">
          <div className="lto-badge-pill">
            <span className="lto-lang-from">
              {fromLang?.native || fromLang?.label || "English"}
            </span>

            <div className="lto-arrow-wrapper">
              <svg className="lto-arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14" />
                <path d="m12 5 7 7-7 7" />
              </svg>
            </div>

            <span className="lto-lang-to">
              {toLang?.native || toLang?.label || "..."}
            </span>
          </div>
        </div>

        {/* Subtitle status with animated typing dots */}
        <div className="lto-status-line">
          <span className="lto-status-text">Translating entire appraisal workspace</span>
          <span className="lto-ellipsis-dots">
            <span>.</span>
            <span>.</span>
            <span>.</span>
          </span>
        </div>

        {/* Multi-Stop Pastel Rainbow Progress Bar */}
        <div className="lto-progress-box">
          <div className="lto-progress-track">
            <div
              className="lto-progress-fill"
              style={{ width: `${progress}%` }}
            >
              <div className="lto-progress-shimmer-sweep" />
            </div>
          </div>
          <div className="lto-progress-meta">
            <span className="lto-progress-count">
              {progress < 100 ? "Syncing dialect tokens..." : "Translations ready"}
            </span>
            <span className="lto-progress-pct">{progress}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LanguageTransitionOverlay;
