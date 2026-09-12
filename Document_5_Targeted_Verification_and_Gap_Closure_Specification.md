# Document 5 — Targeted Verification & Gap-Closure Specification
## Udyam Saathi — Interactive Business Ecosystem Intelligence Graph/Map

### Purpose

This is a **targeted verification pass for Document 5 only**.

Do not redesign the product. Do not restart Document 5. Do not replace the current architecture merely because the original concept mentioned Leaflet/D3 while the implementation uses HTML5 Canvas.

Inspect the actual implementation and determine whether the current graph/map satisfies the requirements. This is an engineering audit, not a test-count exercise.

---

# 1. Non-Negotiable Audit Principles

1. Inspect actual source code, not only previous reports or test names.
2. Do not infer implementation from filenames.
3. Passing tests proves software behavior against those tests; it does not by itself prove geographic, analytical, UX, or scientific validity.
4. Do not fabricate evidence.
5. Never convert approximate spatial information into exact coordinates.
6. Preserve Document 1 and Document 2 semantics.
7. The graph/map remains a read-model projection layer.
8. Classify every gate as:
   - PASS
   - PASS_WITH_LIMITATION
   - NEEDS_FIX
   - UNSUPPORTED_CLAIM
9. For every non-PASS finding, provide exact file/function, behavior, significance, and minimum corrective action.
10. Do not modify unrelated components.

---

# 2. Repository Inspection

Inspect at minimum:

```text
backend/app/core/intelligence/ecosystem_graph.py
backend/app/routers/market_intelligence.py
backend/app/models/schemas.py
frontend/src/components/Dashboard/EcosystemIntelligenceMap.jsx
frontend/src/services/api.js
frontend/src/pages/report/MarketDemandPage.jsx
tests/test_ecosystem_graph.py
docs/PHASE5_GRAPH_IMPLEMENTATION.md
docs/PHASE5_GRAPH_TEST_REPORT.md
```

Also inspect directly imported services required to establish provenance of coordinates, activity classification, competitor rules, supply-chain rules, opportunity metrics, HHI, temporal data, and catchment scoring.

Create:

```text
docs/PHASE5_TARGETED_VERIFICATION.md
```

---

# 3. Gate A — Geographic Mode

The original concept distinguishes a geographic map from a topological graph.

The implementation currently claims:

> Pure HTML5 Canvas + geodesic rings + center crosshair.

Determine whether Geographic Mode actually provides a **real geographic basemap**, or only a coordinate plot.

Inspect:
- real map tiles/vector basemap
- roads/boundaries/other geographic context
- map provider implementation
- latitude/longitude projection
- geographic center
- catchment rings tied to requested center/radius

If the result is only:

```text
blank canvas + lat/lon projection + rings + nodes
```

classify `PASS_WITH_LIMITATION` unless the product requirement was explicitly changed.

Required report:

```text
Geographic Mode:
[REAL_BASEMAP / COORDINATE_PLOT]

Evidence:
<file/function/component>

Finding:
<PASS / PASS_WITH_LIMITATION / NEEDS_FIX>
```

Do not claim “real GPS basemap” unless code proves it.

---

# 4. Gate B — Spatial Precision and Exact-Coordinate Semantics

The UDYAM seven-column dataset exposes:

- EnterpriseName
- RegistrationDate
- Activities/NIC
- Pincode
- CommunicationAddress
- State
- District

It does not provide enterprise-level GPS.

Trace:

```text
source record
→ normalized enterprise
→ geographic resolution
→ graph node
→ API response
→ frontend rendering
→ inspector / banker mode
```

Verify:
- what qualifies as `EXACT`
- whether `EXACT` means enterprise-level verified coordinates
- whether administrative/Census/geocoder sources are being incorrectly labelled exact
- whether pincode anchors disclose approximation
- whether Banker mode preserves spatial precision

If Banker mode says or implies “exact coordinates” for PINCODE/locality/village anchors, fix wording to something like:

> Spatial location / resolved coordinate

and expose:

```text
Spatial precision: PINCODE
Coordinate confidence: <value>
```

Do not alter coordinates merely to improve presentation.

---

# 5. Gate C — Geographic Truth Across Topological Projection

Verify that force-directed mode never overwrites geographic truth.

Conceptually retain:

```text
node.location
```

as immutable geographic/provenance data and use a separate visual layout position such as:

```text
node.renderPosition
```

or equivalent transient state.

Verify:
- force simulation does not mutate lat/lon
- switching back restores geographic positions
- API/state retains geographic coordinates
- disconnected components are allowed
- no fake edges are added to connect the graph

Result:

```text
Geographic coordinates immutable across projection changes:
PASS / PASS_WITH_LIMITATION / NEEDS_FIX
```

---

# 6. Gate D — Competitor Edge Semantics

Competitor edges must be derived analytical relationships, not observed commercial relationships.

For each edge verify:

```text
relationshipType = COMPETITOR
evidenceType = DERIVED
ruleId = deterministic configured rule
```

Generation must use activity/NIC/category classification and configured rules, not:
- inferred transactions
- arbitrary LLM reasoning
- visual proximity alone
- fabricated relationships

Test:
1. same valid sector
2. unknown sector
3. unrelated sectors
4. duplicate/bidirectional pair
5. evidence wording contains no transaction claim

---

# 7. Gate E — Supply-Chain Edge Semantics

Supply-chain edges must come from a deterministic documented complementarity matrix.

For every edge inspect:

```text
relationshipType
sourceCategory
targetCategory
ruleId
direction
evidenceType
```

Direction may only be shown when the matrix defines direction.

Do not turn sector complementarity into a confirmed supplier/customer claim.

If direction is not established, use wording such as:

> potential supply-chain complementarity

---

# 8. Gate F — Layer 4 KDE / Density Heatmap

Inspect actual implementation. Do not accept a layer-status flag as proof.

Classify the implementation as:

A. Actual KDE / mathematically defined spatial density surface → `PASS`

B. Point density / grid aggregation / clustering visualization → `PASS_WITH_LIMITATION` if honestly documented

C. Only a status flag, no actual visualization → `NEEDS_FIX` if Layer 4 is required

Verify low-sample behavior. If threshold is >=10 nodes, ensure insufficient data does not produce a misleading heatmap.

---

# 9. Gate G — Layer 5 Opportunity / White-Space Overlay

Inspect actual implementation.

Opportunity overlay must derive from Document 2 analytical evidence, such as:
- opportunity score
- supply gap
- accessibility gap
- demand support
- growth support
- infrastructure penalty
- confidence
- guardrail status

It must NOT infer opportunity from visual emptiness or low node count alone.

Required behavior:

```text
sufficient analytical evidence → overlay available
insufficient evidence → unavailable / insufficient data
SATURATED_MARKET → must not be presented as attractive white space
CONSTRAINED_MARKET → must not be presented as attractive white space
```

---

# 10. Gate H — Temporal Scrubber

Verify actual `RegistrationDate` usage.

Required:
- data-derived min year
- data-derived max year
- missing/malformed dates tracked
- no hardcoded 2018
- visualization filtering does not alter upstream scoring
- single-year, missing-date, multi-year, invalid/future-date, and empty datasets behave safely

---

# 11. Gate I — Radius Independence

Keep these concepts separate:

```text
analytical/scoring radius
visualization radius
```

Changing visualization radius must not alter:
- opportunity score
- HHI
- upstream demand metrics
- analytical catchment definition

unless a separate analytical-radius parameter is explicitly changed.

Also verify beneficiary radius options against the existing graph specification.

---

# 12. Gate J — Frontend Performance

The reported:

```text
500 nodes + 46,625 edges → 0.375 seconds
```

is a backend transformation benchmark, not a browser rendering benchmark.

Where feasible, run the actual frontend component with:

```text
A: 500 nodes / ~46,625 edges
B: 1,000 nodes
C: 5,000 nodes
```

Measure:
- initial render
- zoom/pan latency
- projection-switch latency
- filter latency
- timeline scrub latency
- memory behavior
- browser responsiveness

If browser instrumentation is unavailable:

```text
Frontend performance evidence: NOT MEASURED
```

Do not invent measurements.

---

# 13. Gate K — Canvas Rendering / Edge Explosion

Inspect:
- whether all edges render simultaneously
- whether filtered edges are skipped
- off-screen culling if applicable
- unnecessary animation
- force simulation convergence
- batching/throttling

Treat 46,625 edges as an actual rendering concern, not merely a backend concern.

---

# 14. Gate L — Accessibility

Inspect actual JSX.

Verify:
- keyboard access for major controls
- accessible labels for icon-only controls
- readable contrast
- non-color-only relationship/sector distinctions
- accessible selected-node information
- timeline accessibility
- reset/zoom accessibility
- textual alternative through inspector/unmapped views for Canvas content

Do not claim accessibility without evidence.

---

# 15. Gate M — Mobile / Responsive Behavior

Inspect or test:
- narrow viewport
- touch pan/zoom
- inspector
- legend
- timeline
- unmapped drawer
- clipping/overflow

If runtime mobile testing was not performed:

```text
Mobile runtime evidence: NOT MEASURED
```

---

# 16. Gate N — MarketDemandPage Integration

Inspect the exact changes to:

```text
frontend/src/pages/report/MarketDemandPage.jsx
```

Verify:
- correct Dimension 2 placement
- correct API input context
- graph failure does not break the page
- fallback is honest
- no unrelated business logic changes
- no duplicate opportunity scoring
- no duplicate UDYAM retrieval

Produce a concise integration diff summary.

---

# 17. Gate O — API Contract

Inspect:

```text
EcosystemGraphRequest
EcosystemGraphResponse
```

Verify:
- schema version
- constrained enums
- coordinate validation
- radius bounds
- optional coordinate behavior
- snapshot semantics
- provenance
- warnings
- unmapped entities
- temporal metadata
- layer status
- spatial precision cannot silently disappear

---

# 18. Gate P — Provenance / Evidence Integrity

Every graph metric and important derived relationship must be traceable to:

```text
source
definition
radius
snapshot/version where relevant
ruleId for derived edges
spatial precision for mapped nodes
```

Never present:
- derived competitor as observed competitor
- derived complementarity as confirmed supplier/customer

---

# 19. Gate Q — Test Quality

Review the actual 55 tests, not just their count.

For each requirement classify:

```text
tested directly
tested indirectly
not tested
```

Create this matrix:

| Requirement | Test Evidence | Code Evidence | Status |
|---|---|---|---|
| No coordinate fabrication | | | |
| Spatial precision hierarchy | | | |
| Pincode disclosure | | | |
| Exact-coordinate semantics | | | |
| Geographic projection | | | |
| Topological projection | | | |
| Immutable geographic truth | | | |
| Competitor derivation | | | |
| Supply-chain derivation | | | |
| No transaction claim | | | |
| Temporal metadata | | | |
| Radius independence | | | |
| HHI semantics | | | |
| KDE/density | | | |
| Opportunity overlay | | | |
| Insufficient-data handling | | | |
| API validation | | | |
| Frontend integration | | | |
| Frontend performance | | | |
| Accessibility | | | |
| Mobile behavior | | | |

---

# 20. Fix Policy

Only make changes for findings classified:

```text
NEEDS_FIX
```

Do not perform speculative redesign.

Priority:

### P0 — Semantic correctness
- false exact-coordinate claims
- fabricated geography
- false transaction/supplier claims
- unsupported opportunity claims
- mutation of analytical truth during projection

### P1 — Required feature correctness
- missing required layer
- incorrect radius semantics
- broken temporal behavior
- broken API contract

### P2 — UX/performance
- rendering bottlenecks
- accessibility
- mobile issues

---

# 21. Required Final Report

Create:

```text
docs/PHASE5_TARGETED_VERIFICATION.md
```

with exactly:

```text
# Phase 5 Targeted Verification

## 1. Executive Verdict

## 2. Repository Evidence Reviewed

## 3. Gate Results
### Gate A — Geographic Mode
### Gate B — Spatial Precision
### Gate C — Projection Integrity
### Gate D — Competitor Semantics
### Gate E — Supply-Chain Semantics
### Gate F — KDE/Density
### Gate G — Opportunity Overlay
### Gate H — Temporal
### Gate I — Radius Independence
### Gate J — Frontend Performance
### Gate K — Canvas Rendering
### Gate L — Accessibility
### Gate M — Mobile
### Gate N — MarketDemandPage Integration
### Gate O — API Contract
### Gate P — Provenance
### Gate Q — Test Quality

## 4. Critical Findings

## 5. Required Fixes

## 6. Limitations That Are Safe to Document

## 7. Claims That Must NOT Be Made

## 8. Final Audit Matrix

## 9. Final Production Readiness Classification
```

---

# 22. Final Classification Rules

### PRODUCTION READY
Only if all critical semantic gates pass and there are no material unsupported claims.

### PRODUCTION READY WITH DOCUMENTED LIMITATIONS
Use when core analytical semantics are correct, no hallucinated/fabricated data exists, limitations are explicitly disclosed, and missing functionality does not invalidate the core graph/map.

### NEEDS FIX
Use when any P0/P1 issue materially affects correctness.

### UNSUPPORTED
Use when the implementation claims functionality that code/evidence does not demonstrate.

Never use “100% verified” simply because 20/20 test suites pass.

---

# 23. Final User-Facing Summary

After the audit, report:
1. final classification
2. P0 findings
3. P1 findings
4. P2 findings
5. exact files changed
6. tests run/results
7. whether Document 5 can be closed

Do not claim a requirement is implemented unless source inspection supports it.
