# Enterprise planning: appraise once, select, open dashboard

The existing idea-plus-investment application keeps its wizard. Budget-only and
idea-only paths generate candidates, appraise them before displaying recommendations,
and open the dashboard directly after selection. They do not reopen the wizard or
appraise the selected project again.

## Generation and appraisal

Budget-only inputs use the current category-based budget tiers. One Groq batch
proposes three location/ODOP-aware businesses at the server-defined costs.
Idea-only inputs use the supported business reference bands or current custom-idea
tiers. The same bounded batch proposes configurations of that idea. Local
configurations are used if the provider is unavailable.

Before comparison, idea-only users can evaluate ODOP synergy using the same
optional check as the existing wizard. They explicitly keep their idea or adopt
the proposed hybrid, then run the ordinary planning appraisal. Skipping requires
no synergy model call. Adopting changes the submitted idea/name, including local
fallback, while preserving the original catalogue ID and cost-sizing rules.
The shared ODOP endpoint retains its own cache, cooldown and provider limits;
the subsequent planning batch and all financing formulas remain unchanged.

The LLM describes candidates; it does not supply authoritative financial or
feasibility results. Generated tier indexes, sectors, business types and duplicate
names are validated. Project costs come from server tiers. Each candidate runs
through the existing regional engine and full feasibility pipeline, including
XGBoost inference, deterministic financial and scheme rules, machinery allocation,
risk assessment and DPR compilation.

The pipeline's optional use_ai=False mode uses existing local machinery and
narrative fallbacks. Financial formulas and model inference are unchanged.
Ordinary wizard/report calls retain their AI-enabled default. Forced local
synthesis uses a separate cache key so it does not replace AI-enabled results.

Only healthy appraisals with a SUITABLE business verdict, sufficient declared
contribution when known, and no constrained/saturated regional verdict are
recommended. Up to three passing candidates are ranked. If fewer pass, the UI
shows fewer, including an empty state when none pass. Failed appraisals cannot be
selected by accepting risks. No extra LLM batch fills missing slots.

Costs and forecasts remain estimates. Incomplete regional evidence is labelled
and requires acknowledgement. Card details distinguish XGBoost results from the
existing backup rules when the trained model is unavailable. These appraisals do
not establish verified customer orders or loan approval.

## Rate limits

Each comparison uses at most one idea-generation LLM call with the existing
2,500-token output ceiling and 12-second timeout. SDK retries are disabled; errors,
including rate limits, use local fallback. There are no per-candidate machinery or
executive-synthesis LLM calls. At most three candidates are evaluated, preserving
the previous regional-request bound. Existing per-worker concurrency and ten-second
resubmit controls remain.

Selection and selection retries make zero LLM, model-inference, regional-analysis
or financial pipeline calls. They reuse the stored result.

## Selection and persistence

Shared owner-scoped drafts store the exact report and full DPR for each passing
candidate under a private _evaluations key. Public responses omit that cache.
Drafts expire after 30 minutes and re-evaluation replaces the owner's earlier
preview. PostgreSQL/shared SQLite storage supports both deployed workers.
Only isolated fixtures without an initialized database use memory fallback.

Selection validates ownership, expiry, appraisal eligibility, estimate/risk
acknowledgements and cached DPR presence. Older previews without a cached appraisal
require a new comparison. The server creates an already-analyzed project and saves
the cached report/DPR through existing database methods. A deterministic
owner/draft/proposal project ID makes selection retries idempotent. The frontend
adopts this saved project into BusinessContext and navigates to /dashboard, without
calling create-and-analyze.

Unknown cash is appraised up front using a contribution assumption returned by
the existing capital-structure helper. Conservative category/gender compatibility
is retained. Users must confirm they can arrange the displayed contribution.
Known zero remains distinct from unknown and cannot make an unfunded candidate
eligible. Confirming the assumption does not require another financial calculation.

## Verification

Run the planning, provider-budget, financial-baseline and SCA tests with pytest; run the frontend
planningHandoff.test.js checks with node --test; build the frontend with npm run build.
Tests cover financial snapshot parity, one LLM batch, provider failure, candidate
rejection, one inference per candidate, private caches, ownership, expiry, legacy
drafts, idempotent selection, no repeat pipeline, cached report/DPR equality and
cross-worker draft storage.

scripts/preview_enterprise_planner.py provides synthetic evidence and ephemeral
projects for browser QA. It must not be deployed publicly or pointed at real
provider accounts or a production database.
