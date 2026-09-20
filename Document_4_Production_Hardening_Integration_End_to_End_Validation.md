# Document 4 — Production Hardening, Integration & End-to-End Validation

## Udyam Saathi — Direct Implementation Specification for Opus 4.6

### Mission
Documents 1, 2 and 3 are implemented. This phase is final hardening and integration—not another intelligence layer.

Objective: make the existing platform internally consistent, independently reproducible, secure, robust to upstream failures, performant enough for the SIH demonstration, correctly integrated frontend→backend→data, deployable, and demonstrably reliable end-to-end.

### Non-negotiable
Do not add arbitrary ML, synthetic demand, guessed coordinates, fake revenue, unsupported subsidy claims, opaque LLM scoring, or hidden score adjustments. The deterministic engine remains the source of truth.

## Critical audit correction
The 105-record confusion matrix has 79 exact matches:
- DIRECT→DIRECT: 34
- RELATED→RELATED: 17
- INDIRECT→INDIRECT: 2
- NON_RELEVANT→NON_RELEVANT: 14
- UNKNOWN→UNKNOWN: 12

Therefore overall 5-class exact-match accuracy is **79/105 = 75.24%**.

The valid class-specific claim is:
- DIRECT_COMPETITOR precision = 100%
- DIRECT_COMPETITOR recall = 100%

Never report the five-class classifier as 100% accurate. Preserve this distinction in audit reports, API documentation, frontend copy, README and SIH material. Do not change rules merely to improve this metric.

## Phase 1 — Codebase integrity review
Inspect the complete repository before modifying behavior. Produce `PHASE4_CODEBASE_REVIEW.md`.

Inventory backend/frontend entrypoints, routers, services, intelligence modules, adapters, models, migrations, cache, snapshots, telemetry, configuration, tests and deployment files. For each critical component record file, responsibility, inputs, outputs, dependencies, test coverage and production status. Do not assume a documented feature is wired into the running application.

## Phase 2 — Configuration and secrets
Audit environment variables, `.env`, `.env.example`, Docker/deployment configuration, frontend environment variables, API keys, database credentials and third-party secrets.

Secrets must never be hard-coded, committed, returned by APIs, exposed in frontend bundles or printed in logs. UDYAM/Data.gov.in credentials must remain backend-only. Add safe startup validation for required production configuration without printing secret values.

## Phase 3 — Database integrity
Verify all migrations from a clean database and from an existing database. Check primary/foreign keys, unique constraints, indexes, spatial indexes, nullability and transaction boundaries. No destructive migration without explicit justification.

## Phase 4 — Snapshot and replay
For one fixed benchmark, pin snapshot, engine version, ontology version, gazetteer version, government source versions and parameters. Replaying at least three times must reproduce score, recommendation, confidence and evidence. Changing source snapshots must change snapshot identity; changing engine parameters must change analysis identity.

## Phase 5 — UDYAM upstream failure testing
Simulate timeout, connection failure, HTTP 429/500, malformed JSON, missing fields, schema changes, HTTP 200 with zero records, partial responses and rate-limit delays.

Required behavior: controlled error or explicitly labelled degraded/cached result. Never fabricate fallback numbers. Cached data must expose retrieval timestamp/source status.

## Phase 6 — Data quality and reconciliation
For each dataset track raw count, normalized count, deduplicated count, mapped count and unmapped count. Geographic populations must reconcile where definitions match: `mapped + unmapped = total`. Flag invalid dates, coordinates, pincodes, duplicate fingerprints, empty activities and suspicious NICs. Do not silently discard bad records; retain a reason such as `invalid_date`, `unknown_locality`, `duplicate` or `schema_error`.

## Phase 7 — Geographic production validation
Enforce `PIN ≠ Village` and `address ≠ coordinate`. Every coordinate needs source, source_reference, confidence and resolution_level. Test multi-locality pincodes, same-name villages, spelling variants, Gram Panchayat/revenue-village mismatch, unresolved addresses and conflicting evidence. Never infer a coordinate solely from a pincode.

## Phase 8 — Competitor classification validation
Use the 105-record gold set and report overall exact-match accuracy 75.24%, DIRECT precision 100%, DIRECT recall 100%. Also calculate per-class precision/recall, macro precision/recall and confusion matrix. Do not change rules solely to improve metrics. Store classifier version and reviewer rationale for debatable classifications.

## Phase 9 — Opportunity mathematics
Independently reproduce Supply Gap, Accessibility Gap, Demand Support, Growth Support and Infrastructure Penalty outside the production implementation. Verify formulas, ranges, weights, normalization, rounding, missing-data behavior and guardrail precedence. Test normal, zero-competitor, high-competition, missing-demand, severe-infrastructure and all-unmapped cases. No NaN, infinity or impossible negative scores.

## Phase 10 — Confidence and uncertainty
Keep `Opportunity Score = market assessment` separate from `Confidence = evidence quality`. Confidence must not silently inflate the market score. Run unmapped scenarios at 0%, 15%, 50% and 100%; record score, recommendation, confidence and direct-competitor count. If recommendations change under plausible uncertainty, disclose the sensitivity.

## Phase 11 — Explainability contract
Every recommendation must expose recommendation, score, confidence, positive drivers, risk factors, missing evidence, limitations, source references and calculation/version metadata. Every displayed number must trace UI→API→calculation→feature→source snapshot. Generated explanations must never introduce unsupported numbers.

## Phase 12 — FastAPI contract testing
Test:
- `POST /api/v2/market-analysis/opportunity`
- `POST /api/v2/market-analysis/compare`
- `GET /api/v2/market-analysis/intents`
- `GET /api/v2/market-analysis/sources`

Cover valid/invalid requests, missing fields, invalid types, empty values, unsupported intent/location, oversized input, malformed JSON, upstream timeout/429 and internal exceptions. Verify stable schemas, correct status codes, useful errors, no stack traces/secrets, and correlation IDs.

## Phase 13 — Frontend/backend integration
Test the actual flow: location→business→intent→analysis→competitors→map→demand→opportunity→guardrails→evidence→sensitivity. Frontend labels must match backend semantics. Do not call projected population “current population”; do not call Economic Sector Diversification HHI simply “Market HHI”.

## Phase 14 — Performance
Benchmark single village, pincode market, district market, single intent, multi-category comparison, cold cache and warm cache. Measure P50/P95/P99 latency, memory, CPU, DB time, upstream time and cache hit rate. Define targets after measuring actual behavior.

## Phase 15 — Caching
Cache only when snapshot and relevant parameters are identical. Cache keys must include location, intent, source snapshot IDs, engine version, ontology version, gazetteer version and relevant parameters. Never present stale results as current.

## Phase 16 — Telemetry
Verify `X-Correlation-ID` and `X-Response-Time-ms`. Internally capture analysis ID, request ID, engine version, snapshot IDs, duration, cache status, source failures and warnings. Verify PII sanitization. Never log API keys, passwords or authorization headers.

## Phase 17 — Deployment rehearsal
Run from a clean environment: install dependencies→configure environment→database migration→start backend→start frontend→health check→analysis request→end-to-end validation.

Create `DEPLOYMENT_RUNBOOK.md` containing prerequisites, environment variables, DB setup, migrations, startup, health checks, smoke tests, rollback and troubleshooting.

## Phase 18 — Failure recovery
Test database unavailable, UDYAM unavailable, government adapter unavailable, cache unavailable, invalid source data and frontend API unavailable. Fail gracefully. `Unavailable evidence ≠ fabricated evidence`. Degraded results must identify what is unavailable.

## Phase 19 — Regression
Run the complete existing master suite and new Phase 4 tests. Existing expected result: 18/18 pass. Add regression coverage for every bug found. Do not delete failing tests merely to make the suite pass. If a test encoded a wrong assumption, replace it with a corrected test and document the reason.

## Phase 20 — SIH end-to-end acceptance
Run one controlled benchmark, preferably Balanagar, Medak, Telangana / Dairy Processing, using a pinned snapshot. Validate location resolution, retrieval, geography, classification, demand evidence, score, guardrails, explanation, uncertainty and frontend rendering. Capture screenshots, request/response IDs, snapshot ID, engine version and source versions without exposing secrets.

## Phase 21 — Production readiness checklist
### Data
- [ ] source validation
- [ ] schema validation
- [ ] snapshotting
- [ ] refresh strategy
- [ ] reconciliation

### Geography
- [ ] no guessed coordinates
- [ ] coordinate provenance
- [ ] multi-locality handling
- [ ] spatial tests

### Intelligence
- [ ] gold-set validation
- [ ] per-class metrics
- [ ] independent score reproduction
- [ ] guardrails
- [ ] uncertainty

### Explainability
- [ ] evidence traceability
- [ ] limitations
- [ ] confidence reasons
- [ ] source lineage

### Engineering
- [ ] migrations
- [ ] API contracts
- [ ] upstream failure handling
- [ ] caching
- [ ] telemetry
- [ ] performance measurements
- [ ] security

### Deployment
- [ ] clean deployment rehearsal
- [ ] environment configuration
- [ ] health check
- [ ] smoke test
- [ ] rollback

### SIH
- [ ] complete user journey
- [ ] screenshots
- [ ] reproducible benchmark
- [ ] no secret exposure
- [ ] graceful failure

## Required deliverables
Create/update:
- `PHASE4_CODEBASE_REVIEW.md`
- `DEPLOYMENT_RUNBOOK.md`
- `PHASE4_FINAL_REPORT.md`
- `AUDIT_FINAL_MATRIX.md`
- `README.md` where necessary

`PHASE4_FINAL_REPORT.md` must include: executive summary, audited scope, changes, unchanged areas, security findings, data/geography findings, classification metrics, score validation, reproducibility, API validation, performance, deployment, failure recovery, SIH result, limitations, remaining risks and final status.

## Final status rules
Use exactly one:
- `PRODUCTION READY`
- `PRODUCTION READY WITH DOCUMENTED LIMITATIONS`
- `BLOCKED — HIGH SEVERITY FINDINGS`

Any unresolved Critical/High security issue means BLOCKED.

## Final instruction to Opus 4.6
Do not make the system larger. Make it harder to break and easier to trust. Inspect the actual codebase first. Implement only changes justified here. Run tests and independent calculations. Do not claim validation without evidence. Do not hide limitations or fabricate missing data. Preserve geographic and evidence safeguards.

At completion return a walkthrough containing: files inspected, files changed, files created, findings, fixes, tests added, complete test results, performance measurements, deployment result, SIH end-to-end result, remaining limitations and final production-readiness status.
