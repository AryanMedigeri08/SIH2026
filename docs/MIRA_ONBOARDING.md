# Mira registration and conversational onboarding

Implement on `operation-still-alive` with focused commits for each completed unit.

1. Profile contracts, category persistence and authenticated phone registration.
2. Owner-scoped onboarding drafts and backend location resolution.
3. Six-language question catalogue and persistent language selection.
4. Cancelable speech, synchronized word highlighting and animated Mira.
5. Language-first, one-field-at-a-time phone registration.
6. Location confirmation/manual LGD hierarchy and three journey choices.
7. Validated conversational question state, text/voice input and corrections.
8. Optional ODOP before appraisal for the two idea paths.
9. Existing financial adapters, pre-appraised recommendations and dashboard handoff.
10. Contract, financial parity, conversation and browser verification.

Preserve financial equations, category policy, XGBoost thresholds, rate limits and
existing appraisal/selection eligibility. Unknown money is not zero. Every amount
is confirmed; loan assistance is never fabricated as available cash. Record user
location with its source and explicit confirmation; never invent an LGD match.

Phone authentication uses Firebase reCAPTCHA and SMS confirmation. Never invent
an OTP or use development token fallback for phone verification. Codes remain in
memory, outside speech/LLM payloads and saved drafts. Firebase Console must enable
Phone auth and authorize the deployment domain for real SMS delivery.

Routine questions use translated templates without chat-model calls. Speech input
uses existing STT; TTS failure falls back to browser speech or readable text.
Microphone stays off until selected. Speech is canceled on navigation and input.
Resume sessions are owner-scoped and must not replay a submitted calculation.

Required QA: registration field order/validation, bad/expired OTP, denied GPS,
ambiguous location, six language catalogues, all three cases, stale ODOP results,
unknown/zero cash, numeric units, duplicate submit, saved appraisal handoff, and
existing financial snapshot tests. Synthetic fixtures must make no real SMS or
paid provider calls.
