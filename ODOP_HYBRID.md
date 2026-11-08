# Optional ODOP hybrid step

Only the existing idea-plus-investment wizard adds this step, immediately after
Enterprise. The other two planning paths keep their direct-to-dashboard flow.
The wizard now has eight steps; financial calculations and final appraisal rules
are unchanged.

The step explains ODOP and possible branding, packaging, market-link and shared
service benefits, linking to the [official MoFPI overview](https://www.mofpi.gov.in/en/node/3285).
It loads the district product from the application's registry with an exact
state/district match. No fabricated product is used when a record is missing.

No skips AI evaluation and keeps the original idea. Yes explicitly sends only
enterprise name, idea, sector/type, location and server-sourced district ODOP
context to Groq. No phone, email, gender, caste or financial amounts are required
for this business-synergy check.

The server validates an integer score and assigns the recommendation:

| Score | Advice |
| --- | --- |
| 81–100 | Recommended combination |
| 60–80 | Could be a good combination |
| 0–59 | Poor synergy |

The result explains a proposed hybrid, practical steps, risks and missing facts.
The user then chooses Use this combination or Continue with my own idea. Nothing
is adopted automatically, including scores above 80. Adoption changes only the
enterprise name and primary idea; the original can be restored. Sector/type,
financial inputs and supplemental business background are preserved. Equipment
for the previous idea is discarded; the ordinary final appraisal refreshes it.
The selected primary idea and supplementary context reach the existing final
appraisal through its existing 1,000-character background field.

A score is advisory business synergy. It does not certify statutory ODOP alignment,
grant scheme eligibility, change subsidy rules or guarantee financial feasibility.
The final deterministic/XGBoost appraisal still evaluates the chosen business.

## Provider budget and persistence

- No model call on entry, No, financial edits, back navigation or unchanged cached
  results. A changed primary idea or location invalidates the displayed score.
- One model request on an explicit Yes. Existing Groq configuration is reused with
  zero SDK retries, a 12-second timeout and a 1,000-token output ceiling.
- Results for the owner's latest unchanged input are cached for 24 hours in a
  separate PostgreSQL/shared SQLite table. A request hash includes the district
  record, model and prompt version. The two deployed workers share the cache.
- Owner leases and a 30-second request interval prevent duplicate calls across
  workers. At most two ODOP model calls run per worker. A provider 429 adds a
  60-second local backoff, with no automatic retry.
- Provider failure, invalid JSON/score or unavailable credentials produce an
  unavailable state, never a fabricated score. Users can always keep their own idea.

Run `tests/test_odop_hybrid.py` with the existing planning/financial regressions,
the native Node checks in `odopHybridState.test.js`, and the frontend build.
The synthetic browser fixture supplies test-only ODOP responses without calling
real providers or connecting to production data.

Browser verification confirmed No made zero provider calls, Yes made one, and
revisiting the same result kept the total at one. Both adopting and restoring the
original idea worked. Editing the primary idea hid the stale score; supplementary
background edits progressed to the eighth-step review without another evaluation.
