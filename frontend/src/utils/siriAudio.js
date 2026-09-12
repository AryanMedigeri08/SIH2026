/**
 * siriAudio.js
 * 
 * Synthesizes the iconic Siri dual-tone activation chime using the Web Audio API.
 * Operates with 0 external MP3 dependencies, ensuring instantaneous feedback,
 * 0 network latency, and 100% offline reliability.
 */

let sharedAudioCtx = null;

function getAudioContext() {
  if (typeof window === 'undefined') return null;
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return null;
  if (!sharedAudioCtx || sharedAudioCtx.state === 'closed') {
    sharedAudioCtx = new AudioCtx();
  }
  if (sharedAudioCtx.state === 'suspended') {
    sharedAudioCtx.resume().catch(() => {});
  }
  return sharedAudioCtx;
}

/**
 * Plays the Siri activation chime (D5 -> A5 tone sequence with gentle decay)
 */
export function playSiriActivationChime() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;

    // --- First Tone: ~587.33 Hz (D5) ---
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();

    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(587.33, now);

    gain1.gain.setValueAtTime(0.001, now);
    gain1.gain.linearRampToValueAtTime(0.28, now + 0.015);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.085);

    osc1.connect(gain1);
    gain1.connect(ctx.destination);

    osc1.start(now);
    osc1.stop(now + 0.09);

    // --- Second Tone: ~880.00 Hz (A5) ---
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();

    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(880.0, now + 0.09);

    gain2.gain.setValueAtTime(0.001, now + 0.09);
    gain2.gain.linearRampToValueAtTime(0.32, now + 0.105);
    gain2.gain.exponentialRampToValueAtTime(0.0001, now + 0.28);

    osc2.connect(gain2);
    gain2.connect(ctx.destination);

    osc2.start(now + 0.09);
    osc2.stop(now + 0.3);

    // Subtle warm harmonic overtone on Tone 2
    const oscHarmonic = ctx.createOscillator();
    const gainHarmonic = ctx.createGain();

    oscHarmonic.type = 'triangle';
    oscHarmonic.frequency.setValueAtTime(1760.0, now + 0.09); // octave harmonic
    gainHarmonic.gain.setValueAtTime(0.001, now + 0.09);
    gainHarmonic.gain.linearRampToValueAtTime(0.04, now + 0.105);
    gainHarmonic.gain.exponentialRampToValueAtTime(0.0001, now + 0.24);

    oscHarmonic.connect(gainHarmonic);
    gainHarmonic.connect(ctx.destination);

    oscHarmonic.start(now + 0.09);
    oscHarmonic.stop(now + 0.25);
  } catch (err) {
    console.warn('[SiriAudio] Could not play activation chime:', err);
  }
}

/**
 * Plays a soft deactivation tone when voice listening ends
 */
export function playSiriDeactivationChime() {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(880.0, now);
    osc.frequency.exponentialRampToValueAtTime(587.33, now + 0.12);

    gain.gain.setValueAtTime(0.001, now);
    gain.gain.linearRampToValueAtTime(0.18, now + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.14);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.15);
  } catch (err) {
    console.warn('[SiriAudio] Could not play deactivation chime:', err);
  }
}
