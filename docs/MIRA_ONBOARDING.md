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
uses existing STT. Mira requests Bhashini with `gender=female` exclusively;
Bhashini failure leaves readable text and an explicit replay control, rather than
silently changing the voice. Other existing chat TTS clients retain auto fallback.
Microphone stays off until selected. Speech is canceled on navigation and input.
Resume sessions are owner-scoped and must not replay a submitted calculation.

Required QA: registration field order/validation, bad/expired OTP, denied GPS,
ambiguous location, six language catalogues, all three cases, stale ODOP results,
unknown/zero cash, numeric units, duplicate submit, saved appraisal handoff, and
existing financial snapshot tests. Synthetic fixtures must make no real SMS or
paid provider calls.

## Implemented routes and presentation

Landing Register opens `/register`: language, typed name, gender, social category,
phone and six-digit SMS code, one field at a time. `/register?signin=1` supports
returning phone users. Email/Google/evaluator sign-in remains available at `/login`.
Registration finishes at `/onboarding`, with centered animated Mira and three
journey cards. GPS resolution runs against backend location records; the selected
business location is confirmed once before questions. Missing/inexact GPS matches
show cascading manual state/district/block/village selection without a fabricated
first-result substitute. When the LGD service is unavailable, real postal locality
records are labelled as postal/taluk provenance; the existing rural planning default
is unverified in that fallback, not a new amenities/population classification model.

The supplied female portrait is integrated at `frontend/public/images/mira-avatar.png`
with RGBA transparency, also reused by both dashboard assistant surfaces. Existing
word highlighting follows audio playback progress: Bhashini's current response has
no word timestamps, so this is proportional highlighting, not forced alignment.
Speech promises are bounded/cached, canceled on navigation/input, and never run once
per word. Static questions/readbacks have six-language templates. Dynamic reports,
catalogue labels and provider explanations use the existing translation service.

`/api/v2/onboarding/session`, `/question`, `/answer`, `/interpret`, and location
endpoints are authenticated. No OTP, phone number or audio enters onboarding drafts
or idea interpretation. The draft survives process restarts with PostgreSQL/SQLite.
Interpretation is optional and bounded (one 700-token attempt, no SDK retries,
10-second owner interval, at most two active requests per worker). Its failure
leaves manual business selection available. Existing ODOP/planning limits remain.

Cases 2/3 use the existing planning batch/appraisal/accept endpoints. Owner-scoped
preview replay does not call providers, XGBoost or financial evaluation. Case 1
uses existing machinery and create-and-analyze services; existing turnover constants
are shared with the legacy wizard. Explicit zero contribution is now retained by
project-to-pipeline mapping rather than being replaced by an unknown value. No
financial equations, subsidy rules or viability thresholds were changed.

## Verification and deployment

Run `tests/test_mira_onboarding.py` alongside the planning, ODOP, provider budget,
financial baseline and SCA suites. Run native Node tests in Onboarding/Planning/
Wizard and `npm run build`. The synthetic browser fixture verified Hindi
registration field progression, manual location confirmation, ODOP evaluation and
adoption, unknown investment, three appraised project sizes, explicit funding/risk
acknowledgements and direct dashboard handoff. No real SMS was sent during QA.

Real phone delivery requires Firebase Phone auth and authorized domains; Bhashini
requires its existing configured credentials/pipeline. Restart the backend to apply
additive user-column migrations and register the new endpoints. Do not enable fake
OTP or development-token fallback for phone auth. Synthetic preview servers must
not be deployed in place of the real backend.

## Choice-first UX and navigation

Fixed-choice questions use selectable radio cards and an explicit Continue action.
They have no textarea. Free-form idea, money and background questions retain text
and opt-in voice input. Spoken choices resolve to a single available option and
are confirmed with Continue; ambiguous speech never silently chooses an option.

The server returns the actual question sequence and completed count. The progress
bar includes these answers plus appraisal and acceptance, with no simulated timer.
Conditional rent/custom-business questions change the sequence. Milestone hints
use the six-language catalogue, without extra LLM calls.

Back reviews saved answers without deleting them. Continuing an unchanged answer
makes no interpretation, appraisal or revision request. Changed answers use the
authenticated revision endpoint: investment edits require contribution confirmation;
business edits invalidate ODOP context; affected previews and final confirmation
are invalidated while unrelated answers remain. Reviewing an ODOP choice can keep
the saved choice without requesting another evaluation.

Mira's portrait glow, status and sound bars follow actual playback, recording and
answer-processing state. Reduced-motion preferences disable these animations.
The browser fixture confirmed selection/Continue, restored choices through Back,
conditional rent removal, zero textareas on option-only screens, and no horizontal
overflow at phone width. Fixture audio is intentionally muted; real Bhashini speech
availability was not inferred from this browser check.
