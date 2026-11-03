# Mira conversational onboarding

`/wizard` and `/new-assessment` now open Mira. The original detailed appraisal form remains an explicit alternative, and its benchmark templates remain available in evaluator mode. Returning users keep their existing sign-in and project navigation; opening the new assessment route restores the saved plan.

## What was inspected and reused

The application uses React/Vite, Firebase Authentication, FastAPI, Neon PostgreSQL with a durable SQLite fallback, LGD administrative tables, and the existing appraisal and DPR pipeline. The comparison was `operation-goldrush` at `a978a800` against `recalculations-v3` at `cdd86b63`.

The email/password and Google flows, profile endpoints, and LGD location endpoints were identical on those revisions. Mira reuses the existing Firebase UI and session handoff, the LGD tables and identifiers, and the browser GPS/Nominatim approach. The business wizard from `recalculations-v3` was not ported. The existing speech providers, chat provider cascade, opportunity engine, business intent and NIC catalogues, ODOP registry, scheme ranking, bank and SCA calculations, project storage, and DPR generation are reused.

**Area classification difference:** `recalculations-v3` has a manual rural/urban radio control; its GPS handler expressly leaves the value unchanged. There is no automatic classifier on that branch. Mira reads authoritative rural/urban flags where present on the verified LGD row. If the directory has no flag, she asks for the original manual verification and stores the result with its provenance. There is no population threshold, postcode heuristic, GPS-based rural assumption, or synthetic locality fallback in this flow.

## How a conversation advances

- Registration guidance uses the existing Firebase form. Name, gender and scheme category can be reviewed and corrected; credentials stay in the form. Profile fields already known are reused. The category explanation says why the information is requested. Raw profile responses are excluded from Mira's business language prompt and speech logs do not contain transcript excerpts.
- `GET /api/v2/onboarding/session` reads the authenticated owner's draft. Text and reviewed transcripts both go to `/turn`. The session stores validated facts with their source, confirmation and dependency metadata, the latest question, and bounded conversation history. Revision checks protect concurrent tabs and request IDs make a repeated answer safe to retry.
- The business language service calls the existing Sarvam/Groq cascade for typed extraction. Each proposed fact needs supporting text from the latest statement. Monetary inputs must match amounts in that text; local parsing covers common spoken rupee amounts and rent periods. Unsupported outputs, including geographic classifications, subsidies and calculated figures, cannot enter the fact model. A conservative local parser and editable choices remain available if language services fail.
- The backend chooses a question based on current prerequisites. For example, a user who gives a dairy idea, owns land, and states ₹5 lakh in one answer proceeds to the missing product or operational details; the amount is not taken as personal contribution without evidence. Contradictory values are reviewed before replacing saved facts. A change invalidates its dependents: a new site requires location confirmation, suitability, rent where applicable, and new regional and financial outputs; a new idea leaves known capital and location intact.
- GPS only produces a candidate. A unique LGD match and explicit confirmation are needed before regional work. The directory cascades by state, district, development block and village code. Exact GPS coordinates and street addresses are not retained in the conversation. If GPS fails, the directory remains the recovery path.
- Business type is inferred from the explicit activity. The existing intent/NIC mappings and sector catalogue determine application IDs; ambiguous classifications are clarified and the user confirms the business summary. The existing village intelligence engine assesses the confirmed site. For users exploring ideas, the catalogue screens for regional affinity or district ODOP, stated interests and capital, then attaches village evidence when available. An unsupported match is omitted; an option with weak evidence is labelled as exploratory. No specific space or demand figure is invented.
- ODOP is introduced when the activity is understood. The offer requires a district/state match in the existing registry. Users can explore, keep the original idea or decline; declining carries through to the report. Sector overlap is a reason to investigate, not an eligibility decision.

## Financial handoff

Mira waits for the confirmed site, activity, product or service, operating scale and requirements, premises suitability, and rent or shared facility fee if applicable. Supported sector catalogue ranges provide a reference. Confirmed, applicable setup costs are summed on the backend, then used for appraisal and DPR itemization. Land purchase remains outside the financed project outlay under the existing model. Rent is an operating cost, and annual rent is converted to monthly rent before the existing engine uses it.

The existing project outlay and loan functions retain their original behavior for legacy inputs. Only the new confirmed-cost path supplies the actual equipment amount and outlay instead of the legacy allocation percentages. Personal contribution, total budget, borrowing capacity, remaining funding need, statutory equity gap, candidate SCA and candidate subsidy are distinct. The user chooses a path to explore; that choice and its existing-engine reference are saved separately from the standard scheme appraisal. No loan or subsidy is applied or approved by onboarding.

`POST /api/v2/onboarding/complete` validates the saved revision, generates the existing report/DPR and persists it as an owner-scoped project. An unchanged retry reuses the project ID. Completion requires a confirmed enterprise name. Starting another plan preserves the profile and offers the previous location for fresh confirmation.

## Code map and verification

| Area | Files |
| --- | --- |
| Session, evidence and decisions | `backend/app/models/onboarding.py`, `backend/app/core/onboarding.py`, `backend/app/core/onboarding_understanding.py`, `backend/app/routers/onboarding.py` |
| Location and persistence | `backend/app/core/onboarding_location.py`, `backend/app/database.py` |
| Existing auth and voice integration | `backend/app/routers/auth.py`, `backend/app/routers/chat.py`, `backend/app/core/audio_chat_service.py`, `frontend/src/context/AuthContext.jsx`, `frontend/src/components/MiraRegistrationGuide.jsx` |
| Appraisal and project handoff | `backend/app/core/financial_calculator.py`, `backend/app/core/dpr_generator.py`, `backend/app/models/schemas.py`, `backend/app/routers/feasibility.py`, `backend/app/routers/projects.py` |
| Screens and shared controls | `frontend/src/pages/WizardPage.jsx`, `frontend/src/components/Wizard/MiraOnboarding.jsx`, `frontend/src/components/Wizard/BusinessLocationPicker.jsx`, `frontend/src/hooks/useMiraSpeech.js`, `frontend/src/services/api.js` |

`tests/test_mira_onboarding.py` covers the requested idea/budget scenarios, location and idea changes, owned and rented premises, reviewed speech rent, both ODOP choices, ambiguity and multi-field extraction, voice/text switching, pause/resume, owner isolation, stale revisions, invalid values, and report creation for normal and SCA paths. Its golden finance comparison uses values captured from the pre-change implementation. The onboarding and SCA suites passed 44 tests; `tests/test_phase2.py` passed 57 checks across banking math, schemes, pitch cases and the no-network invariant.

The broader graph suite passed 22 checks and missed its 1-second performance target once in the isolated final run. That timing failure also reproduced on the untouched baseline. Seven tests in the older dashboard voice suite likewise failed on both revisions; the new onboarding speech handoff passes its own test.

For a local UI smoke run, start `venv\Scripts\python.exe scripts\preview_mira_onboarding.py`, then run `npm run dev` from `frontend`. Open `/register` and use the evaluator entry. The fixture binds to localhost, uses an in-memory database and clearly marked test geography, and replaces live regional and speech calls. It is not a deployment configuration.

## Deployment and verification limits

- The deployer needs access to the existing LGD database and permission to add the `onboarding_sessions` table and the additive user profile columns. SQLite preserves drafts, but does not provide authoritative LGD hierarchy; Mira stops location confirmation when the directory is unavailable.
- The repository catalogue is not a vendor quote database. Unsupported or custom ventures need the user's itemized estimates; a catalogue range is labelled as a reference. When village data or premises requirements are missing, suitability and local demand remain unverified.
- Live Firebase signup, live Neon persistence, GPS resolution against production data, and live microphone and provider playback require an environment smoke test. Local browser checks used synthetic geography; automated speech tests use a mocked provider and actual API handoff. Unsigned evaluator tokens are disabled by default; set `ALLOW_TEST_AUTH=True` only for an isolated synthetic test instance. The preview and pytest fixtures enable it explicitly.
