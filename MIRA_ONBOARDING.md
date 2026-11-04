# Audio-first registration and adaptive Mira onboarding

The default `/onboarding`, `/wizard` and `/new-assessment` routes now use one authenticated, resumable conversation. The screen keeps Mira’s current question prominent, with voice, typing, simple choices, optional details and correction controls. It does not expose a fixed business-question script.

## Registration and sign-in

The first interaction selects one of six languages. Mira then speaks, waits for playback to finish, listens, validates through the backend and automatically asks name → gender → category → phone → optional email. There are no per-field Speak or Next buttons. Pause/resume, repeat, explicit corrections and typing remain available. Silence and invalid answers pause after three attempts; denied microphone access pauses immediately. Interrupted or obsolete speech/transcription cannot answer a later question. No surname-based category inference is performed. Registration values remain transient until Firebase phone OTP succeeds; the authenticated backend then persists them. OTPs and credentials remain in secure sign-in controls, outside speech recognition. Skipped optional email is remembered.

Google, phone, passkey and existing email sign-in retain Firebase authentication. Every successful sign-in returns the token to navigation, and authenticated UI state is published only after the backend accepts the same identity. OAuth failures never create unsigned fallback identities. Local document navigation from `127.0.0.1` redirects to `localhost`, which the configured Firebase project authorizes. This redirect also applies to Vite preview; APIs do not redirect. The configured project currently does not authorize `127.0.0.1`.

One-click evaluator access uses a backend-created random identity and opaque 256-bit bearer token. Only its hash is persisted, with an eight-hour expiry. Existing owner checks isolate each evaluator's profiles, projects and conversations. Logout revokes access; passkey enrollment is unavailable for evaluator identities. The endpoint limits session creation to ten attempts per minute per client IP. Evaluator tokens are held only in sessionStorage; personal information is not cached with them. `ALLOW_TEST_AUTH=False` remains the production setting, and unsigned test tokens remain rejected. This endpoint requires working persistent storage; it does not silently fall back to a shared guest identity.

Passkey challenges and public credentials persist in PostgreSQL or SQLite. Challenges expire, are consumed once, require user verification and validate relying-party origin/hostname. Firebase remains the issuer of the resulting session. `webauthn==3.0.1` is included in requirements.

Deployment must enable Firebase Phone Authentication, Google sign-in and the actual authorized frontend domain. Firebase anonymous authentication is not required for evaluator access. Set `PASSKEY_RP_ID` and `PASSKEY_ORIGIN` to the actual frontend hostname and origin; the defaults are localhost. Live account OAuth completion, SMS OTP, real-device passkeys and microphone recognition require a device/account check; automated tests do not use personal credentials or record the user's microphone. Speech providers must be configured for live STT/TTS; browser speech synthesis is the TTS fallback.

Adaptive API responses redact personal profile values and mask profile turns in conversation history. Demographics and contact details do not enter general-purpose business-understanding prompts. Auth/onboarding responses use no-store headers. Profile writes fail visibly when PostgreSQL is unavailable. Personal questions have deterministic prompts in all six languages; dynamic business questions use the existing translation service and pause voice if a translation is unavailable, instead of speaking English under another language setting. The beneficiary dashboard hides personal category details and folds secondary tools into optional sections.

## How Mira decides what to ask

The server owns the confirmed facts, pending corrections, location, classification, regional evidence, cost proposals and financing results. A single answer can satisfy multiple dependencies. Missing facts determine the next question. Every typed or transcribed answer uses the same revision-checked API; retries are deduplicated, answers persist and report completion is idempotent.

- With an idea and no known investment, Mira clarifies activity, product and intended capacity, confirms her interpretation, checks the region and offers an applicable reference setup estimate for review. Personal cash is asked separately after the cost is understood.
- With an idea and budget, Mira distinguishes personal savings from total project budget or borrowing. Known answers survive; she asks only for missing business, site, rent and funding details.
- With a budget and no idea, Mira asks about interests/skills, then screens up to three catalogue candidates against budget and regional evidence. Saturated or constrained candidates are filtered. Insufficient evidence is labelled provisional rather than declared feasible.
- An adverse regional result offers alternative ideas or explicit continuation with those risks.
- ODOP is offered while shaping the idea. Exploring a connection does not silently replace the business or establish subsidy eligibility.
- Premises and actual monthly/annual rent are collected before financial assessment. A rent planning suggestion can be explicitly accepted or replaced.
- Setup outlay, own cash, remaining funding need, conditional subsidy and promoter-margin shortfall remain separate. Users can increase funds, explore the existing normal loan, or explore SCA margin assistance when a margin gap exists. Normal and SCA servicing use the existing calculators.
- Enterprise naming follows the settled business/funding draft. Type and sector are derived on the backend. Users can review or correct inputs before generating the existing saved project/report/DPR.

## Location and area classification

The browser supplies GPS only with permission. The backend reverse-geocodes it and verifies a unique village through the official State → District → Development block → Village joins. Registration GPS can be reused briefly in the same browser; it is not treated as a confirmed business address. Failed, ambiguous or denied detection opens four cascading dropdowns. State/district changes clear dependent selections.

`Refactor-wizard-aryan` did not actually contain an automatic backend rural/urban classifier. This implementation first uses official LGD flags, then an exact census code match and its official area/administrative-level fields. Manual verification is offered only if authoritative data is missing. Unknown status is never silently converted to rural. The configured database hostname could not be resolved during this session, so live location/census coverage remains unverified.

## Estimates and calculation protection

The reference equipment data comes from `Refactor-wizard-aryan` commit `919a0d7`. Only business descriptions, search terms, reference capacity and equipment estimates were imported; none of that branch’s price-scaling or financial formulas were imported. Reference costs are not supplier quotations or verified matches to the user’s requested capacity. Retail/distribution does not inherit a processing plant. Unsupported cases ask for applicable user/supplier estimates.

The current Goldrush capital calculator and DPR allocations build a reviewable setup draft; the user must accept it or edit the costs. Land purchase remains outside the existing financed outlay, and recurring rent remains an operating expense. Confirmed components are summed deterministically. Category/contribution rules, scheme ranking, EMI/SCA servicing and DPR generation stay in their existing modules. An explicit zero own contribution is preserved rather than treated as missing.

## Code map and verification

- `frontend/src/pages/OnboardingPage.jsx`: voice/text conversation and review.
- `frontend/src/components/LanguageGate.jsx`, `frontend/src/pages/RegisterPage.jsx`: language-first sequential registration.
- `frontend/src/services/voiceConversation.js`, `frontend/src/hooks/useMiraConversation.js`, `useMiraSpeech.js`, `useVoiceRecorder.js`: cancellable speech/listening state machine and bounded recovery.
- `backend/app/core/profile_conversation.py`, `backend/app/routers/auth.py`: explicit multilingual profile validation and scoped evaluator issuance.
- `frontend/src/components/AuthExperience.jsx`, account pages, `AuthContext.jsx`: source-branch account experience with Firebase transport.
- `backend/app/core/adaptive_onboarding.py`: dependency-led conversation policy and reviewable estimates.
- `backend/app/routers/onboarding.py`: owner-scoped persistence, corrections, commands, retry safety and report handoff.
- `backend/app/core/onboarding_location.py`: official hierarchy and area evidence.
- `backend/app/routers/passkeys.py` and persistent database methods: WebAuthn transport.

Tests cover the three main cases, multiple facts per answer, spoken/typed switching, regional rejection, owned/rented premises, normal/SCA/increased contribution, corrections, saved-session recovery, passkey replay/signature checks and actual report/DPR generation with external data/narrative providers stubbed. Golden finance snapshots verify that the underlying existing numerical rules have not changed. `scripts/preview_mira_onboarding.py` supplies an isolated UI fixture with synthetic geography and blocked live speech providers.

Authentication/voice verification: `tests/test_auth_voice_registration.py` covers evaluator expiry, revocation, isolation, forged-token rejection, unavailable storage, rate limiting, native digits/categories, profile persistence/redaction, optional email and corrections. `node --test src/services/authVoice.test.js` checks automatic audio ordering, transitions, bounded retries, interruption, repeat, duplicate callbacks, token handoff and canonical development origin. Browser checks verify language-first rendering, Hindi field order, invalid-phone retry and one-click evaluator onboarding. Production build and the 75-test targeted backend suite pass; the 11 frontend transport tests pass.
