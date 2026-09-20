# Document 6 — Udyam Saathi Cross-Component Integration & End-to-End Consistency Audit

## 0. Execution Contract

This is an **integration/audit specification**, not a request to redesign the existing intelligence engines.

Audit and implement only what is required to prove that the existing Udyam Saathi components work together consistently:

```text
UDYAM / Government Data
        ↓
Village Intelligence Engine
        ↓
Market Intelligence & Opportunity Engine
        ↓
Ecosystem Graph / Map Read Model
        ↓
Decision / Recommendation Layer
        ↓
Beneficiary / Banker UI
```

### Primary objective

Verify consistency of:
- enterprise identity
- geographic identity
- category/activity semantics
- market-radius semantics
- competitor semantics
- scoring semantics
- confidence semantics
- provenance
- guardrails
- temporal behavior
- API contracts
- frontend/backend behavior

### Explicit scope boundary

Do NOT use this document to:
- rebuild Documents 1–5
- redesign the existing opportunity formula
- redesign the ecosystem graph
- add unrelated product features
- claim the existing Canvas coordinate plot is a real geographic basemap
- add satellite/street tiles unless separately authorized
- replace deterministic decisions with LLM-generated decisions
- fabricate coordinates, demand, transactions, suppliers, customers, revenue, or market shares
- silently change existing metric definitions

A real Leaflet/street/satellite basemap is a later UI enhancement. The existing graph may remain a Canvas coordinate plot.

---

# 1. Repository and Architecture Audit

Inspect the actual repository before changing code. Do not assume filenames.

Map the real implementations of:
1. UDYAM ingestion/cache
2. Village Intelligence
3. Market Intelligence
4. Ecosystem Graph
5. frontend API/client
6. beneficiary flow
7. banker flow
8. LLM/recommendation layer, if present
9. shared schemas/utilities

Create:

`docs/PHASE6_INTEGRATION_REPOSITORY_AUDIT.md`

For every component record:
- actual module/file
- public interface
- upstream dependency
- downstream consumer
- source-of-truth status
- duplicated logic
- risks
- classification: PASS / PASS_WITH_LIMITATION / NEEDS_FIX / UNSUPPORTED_CLAIM

---

# 2. Integration Invariants

## I1 — Enterprise identity

The same enterprise must not become multiple logical businesses because of formatting, retrieval path, or address differences.

The existing deterministic fingerprint may be used for local identity/deduplication.

It is NOT a government-issued enterprise ID.

Do not invent a government identifier.

## I2 — Geographic identity

Use the established precision hierarchy:

```text
EXACT
LOCALITY
VILLAGE
PINCODE
UNMAPPED
```

`EXACT` is reserved strictly for verified enterprise GPS or verified/manual survey GPS.

Administrative, census, village-centroid, or pincode anchors must not be upgraded to EXACT.

Mandatory rule:

```text
PINCODE ≠ exact enterprise location
```

If two components resolve the same enterprise/locality to conflicting coordinates, classify it as an integration finding.

---

# 3. Coordinate Integrity

For every graph node with coordinates, verify:

```text
source coordinate
→ resolution method
→ precision class
→ resolved coordinate
→ display coordinate
```

Prove that:
- no coordinate is fabricated for visual completeness
- unresolved records remain unresolved
- precision class is retained
- display coordinates do not overwrite analytical coordinates
- projection does not mutate source geographic coordinates

Create a deterministic fixture containing:
- verified GPS
- locality anchor
- village centroid
- pincode anchor
- unmapped enterprise

Expected precision:

```text
verified GPS       → EXACT
locality anchor    → LOCALITY
village centroid   → VILLAGE
pincode anchor     → PINCODE
no resolution      → UNMAPPED
```

---

# 4. Category / Activity Consistency

The category interpretation used by:
- Market Intelligence
- competitor classification
- supply-chain edges
- graph filtering
- opportunity analysis
- recommendation logic

must originate from a common semantic source.

Verify:

```text
raw Activities / NIC
        ↓
normalization
        ↓
canonical activity/category
        ↓
relevance classification
        ↓
market-analysis category
        ↓
graph category
```

The same enterprise must not be DIRECT in one component and NON_RELEVANT in another without an explicit documented rule.

Unexplained mismatch = `NEEDS_FIX`.

---

# 5. Competitor Semantics

Preserve the existing definition:

```text
COMPETITOR
= DERIVED relationship based on deterministic activity/category rules
```

It does NOT mean confirmed rivalry, transaction, or physical co-location.

Verify:
- same canonical category/activity semantics
- graph competitor population can reconcile with Market Intelligence
- UI does not imply observed rivalry
- derivation rule remains available

Expected metadata:

```text
edgeType: COMPETITOR
relationshipType: DERIVED
ruleId: COMPETITOR_ACTIVITY_V1
```

---

# 6. Supply-Chain Semantics

Supply-chain edges remain derived.

Expected representation:

```text
edgeType: SUPPLY_CHAIN
relationshipType: DERIVED
ruleId: SUPPLY_CHAIN_ACTIVITY_MATRIX_V1
direction: NONE
```

Never claim:
- confirmed supplier
- confirmed customer
- observed trade
- contract
- actual procurement flow

Verify that graph and Market Intelligence use the same complementarity matrix.

---

# 7. HHI Semantic Integrity

Preserve the project's existing definition:

> **Economic Sector Diversification HHI**

Do not silently convert it into revenue-based market-share HHI.

Audit every downstream display, API field, tooltip, and explanation.

Where ambiguity is possible, explicitly label it as sector diversification HHI.

---

# 8. Market Radius Consistency

Keep:

```text
scoringRadiusKm
visualization radiusKm
```

separate.

Changing visualization radius must NOT silently recompute opportunity scoring.

Test the same locality/business intent with:
- identical scoring radius
- different visualization radius

Expected:
- opportunity score identical
- guardrail identical
- demand evidence identical
- only displayed graph population changes

---

# 9. Opportunity Score Integrity

The graph must consume the validated Market Intelligence result.

Do NOT recreate the opportunity formula inside the graph.

Canonical flow:

```text
Market Intelligence
        ↓
validated composite_score
        ↓
guardrail
        ↓
recommendation
        ↓
Graph opportunity layer
```

Do not infer opportunity from:
- visual emptiness
- low node count alone
- graph sparsity
- edge absence
- visual distance

---

# 10. Guardrail Propagation

These must survive every API/UI boundary:

```text
SATURATED_MARKET
CONSTRAINED_MARKET
INSUFFICIENT_DATA
```

Verify that graph filters, radius changes, and LLM explanations cannot turn a guarded market into a positive recommendation.

A visual filter may change visibility, never analytical truth.

---

# 11. Confidence Propagation

Confidence is data quality, not opportunity quality.

Preserve distinction between:
- source confidence
- geographic confidence
- analytical confidence
- evidence confidence

Example:

```text
HIGH confidence + SATURATED_MARKET
```

is valid.

Do not map HIGH confidence to HIGH opportunity.

---

# 12. Provenance Propagation

Decision-relevant outputs must retain:
- source dataset/lineage
- engine/version
- calculation timestamp
- geographic scope
- data-quality warnings
- derivation rule where applicable

Observed/direct and derived relationships must remain distinguishable.

---

# 13. Temporal Consistency

RegistrationDate handling must remain consistent.

Audit:
- minimum year
- maximum year
- malformed dates
- missing dates
- out-of-range dates
- visual temporal filtering

Changing the graph timeline must not silently alter the Market Intelligence score unless an explicitly versioned temporal analytical mode exists.

---

# 14. Graph ↔ Market Intelligence Reconciliation

For a fixed fixture calculate:

```text
A = Market Intelligence competitor set
B = Graph competitor set
```

Report:
- A count
- B count
- intersection
- A - B
- B - A

Differences are acceptable only when explicitly explained by:
- visualization clipping
- visualization radius
- pagination
- display cap
- unresolved coordinates
- graph filters

Unexplained mismatch = `NEEDS_FIX`.

Perform analogous reconciliation for relevant supply-chain relationships where applicable.

---

# 15. Unmapped Data

Unmapped businesses must not disappear silently.

Expected:

```text
UNMAPPED
    ↓
not spatially rendered where necessary
    +
unmapped count/list
    +
warning/disclosure
```

The user must be able to distinguish:

```text
no businesses exist
```

from:

```text
businesses exist but could not be spatially resolved
```

---

# 16. Ecosystem Graph API Audit

Verify the existing endpoint:

`POST /api/v2/market-analysis/ecosystem-graph`

Audit:
- request validation
- coordinate bounds
- radius bounds
- invalid locality
- invalid intent
- insufficient data
- deterministic ordering
- stable IDs
- response version
- backward compatibility
- error format

Expected response structure remains conceptually:

```text
version
catchment
nodes
edges
unmapped
metrics
temporal
layers
provenance
warnings
```

Do not break existing consumers.

---

# 17. Frontend Contract Audit

Inspect the actual API client/components.

Verify:
- request parameters are correct
- frontend does not recompute backend analytics
- loading/error/empty states
- insufficient-data handling
- unmapped handling
- provenance/warnings
- guardrails
- confidence
- derived-edge labels
- stable IDs

---

# 18. Beneficiary End-to-End Journey

Test:

```text
Select locality
      ↓
Describe/select business idea
      ↓
Market analysis
      ↓
Opportunity result
      ↓
Why?
      ↓
Competitor/ecosystem view
      ↓
Demand/infrastructure evidence
      ↓
Risks / constraints
      ↓
Recommendation
```

The graph must not contradict the primary recommendation without an explicit explanation.

Example:

```text
SATURATED_MARKET
+
many direct dairy businesses
```

is consistent.

Visual sparsity alone must never be presented as proof of opportunity.

---

# 19. Banker End-to-End Journey

Verify banker mode emphasizes:
- sector diversification HHI
- growth indicators
- concentration
- ecosystem structure
- cannibalization where implemented
- ego-network where implemented
- confidence
- limitations
- provenance

Do not represent derived graph edges as verified commercial relationships.

Do not represent approximate coordinates as exact enterprise addresses.

---

# 20. LLM / Recommendation Boundary

If an LLM is present, audit its position.

Correct:

```text
Structured evidence
       ↓
Deterministic analytics
       ↓
Guardrails
       ↓
Recommendation policy
       ↓
LLM explanation
```

Forbidden:

```text
Raw data
   ↓
LLM
   ↓
market score / competitor count / demand claim
```

The LLM must not:
- invent businesses
- invent suppliers/customers
- invent demand/revenue
- invent coordinates
- override SATURATED_MARKET
- override CONSTRAINED_MARKET
- convert uncertainty into certainty
- create unsupported financial projections

If no LLM exists, do not add one in this phase. Record it as a future integration point.

---

# 21. Deterministic E2E Fixture

Create one small synthetic fixture containing:
- target locality
- direct competitor
- related business
- indirect business
- non-relevant business
- UNKNOWN classification
- multiple geographic precision classes
- at least one unmapped enterprise
- multiple sectors
- temporal registration dates
- government demand/infrastructure inputs required by the existing engine

The fixture is synthetic and must never be presented as real government data.

Validate:

```text
input
 ↓
normalization
 ↓
geography
 ↓
classification
 ↓
market metrics
 ↓
opportunity
 ↓
graph
 ↓
frontend
```

---

# 22. Golden Assertions

For the deterministic fixture, assert exact expected values for:
- enterprise identity
- geographic precision
- distances
- competitor classification
- supply-chain classification
- competitor counts
- sector counts
- HHI
- opportunity features
- composite score
- guardrail
- recommendation
- confidence
- unmapped count
- graph node count
- graph edge count
- temporal bounds

Prefer exact assertions over tolerances when deterministic.

---

# 23. Regression

Run all existing suites before and after changes.

Minimum:

```text
Document 1 tests → PASS
Document 2 tests → PASS
Document 3 audit tests → PASS
Document 4 hardening tests → PASS
Document 5 graph tests → PASS
Document 6 integration tests → PASS
frontend build → PASS
```

Report:
- total suites
- passed
- failed
- skipped
- new tests
- regressions

Do not report only the new test count.

---

# 24. Performance

Separate:
### Backend
- query
- transformation
- graph construction
- serialization

from:

### Browser
- first render
- interaction latency
- Canvas frame rate
- filter response
- timeline response
- memory

Do not claim 60 FPS on low-end mobile unless actually measured.

The existing graph edge cap may remain as a rendering-cost control.

---

# 25. Error-State Matrix

Test at minimum:

| Scenario | Expected behavior |
|---|---|
| invalid locality | validation/error |
| no businesses | empty state, not opportunity claim |
| many unmapped businesses | warning + count |
| insufficient density data | layer unavailable |
| saturated market | opportunity overlay suppressed/guarded |
| constrained market | opportunity overlay suppressed/guarded |
| missing demand evidence | confidence/data limitation |
| invalid radius | validation error |
| API failure | recoverable UI error |
| malformed date | excluded from temporal calculation + warning |
| missing coordinates | no fabricated position |

---

# 26. No Silent Semantic Changes

Do not silently:
- replace the project's HHI definition
- upgrade approximate coordinates to EXACT
- redefine competitor
- turn derived supply-chain edges into observed relationships
- make visualization radius equal scoring radius
- replace opportunity guardrails
- turn confidence into opportunity
- use graph emptiness as proof of white space

If a conflict is discovered, stop and report it.

---

# 27. Audit Matrix

Create:

`docs/PHASE6_INTEGRATION_AUDIT_MATRIX.md`

Use these gates:

| Gate | Area |
|---|---|
| A | repository/component inventory |
| B | enterprise identity |
| C | geographic identity |
| D | coordinate precision |
| E | category semantics |
| F | competitor semantics |
| G | supply-chain semantics |
| H | HHI semantics |
| I | radius independence |
| J | opportunity propagation |
| K | guardrails |
| L | confidence |
| M | provenance |
| N | temporal consistency |
| O | unmapped handling |
| P | API contract |
| Q | frontend contract |
| R | beneficiary journey |
| S | banker journey |
| T | LLM boundary |
| U | golden fixture |
| V | regression |
| W | performance |
| X | error states |
| Y | final E2E replay |

Each row must contain:
- result
- evidence
- risk
- required action

Allowed classifications:

```text
PASS
PASS_WITH_LIMITATION
NEEDS_FIX
UNSUPPORTED_CLAIM
```

---

# 28. Stop Conditions

Stop implementation and report the issue if:
1. enterprise identities conflict
2. geographic precision is upgraded without evidence
3. competitor semantics differ across components
4. category semantics differ across components
5. visualization radius changes analytical score
6. graph filters change recommendation
7. guardrails can be bypassed
8. unmapped records disappear without disclosure
9. derived relationships are represented as observed
10. coordinates are fabricated
11. HHI semantics change silently
12. previous tests regress
13. frontend invents backend metrics
14. LLM can generate unsupported decision facts

---

# 29. Required Artifacts

Produce:

```text
docs/PHASE6_INTEGRATION_REPOSITORY_AUDIT.md
docs/PHASE6_INTEGRATION_AUDIT_MATRIX.md
docs/PHASE6_INTEGRATION_TEST_REPORT.md
docs/PHASE6_E2E_VALIDATION_REPORT.md
```

If code changes are made, also produce:

```text
docs/PHASE6_CHANGELOG.md
```

The changelog must state:
- file changed
- reason
- old behavior
- new behavior
- tests added/modified
- regression impact

---

# 30. Final Acceptance Criteria

Document 6 is complete only if:

### Architecture
- major components are mapped
- source-of-truth boundaries are explicit
- duplicated analytical logic is identified

### Data
- enterprise identity is consistent
- geographic identity is consistent
- coordinate precision is preserved
- category semantics are consistent
- unmapped records remain visible

### Analytics
- competitor definitions reconcile
- supply-chain definitions reconcile
- HHI semantics remain unchanged
- scoring radius remains independent
- opportunity score is consumed, not reimplemented
- guardrails propagate
- confidence remains distinct from opportunity

### Graph
- graph reflects validated analytics
- derived relationships remain derived
- temporal behavior is consistent
- density/opportunity layers respect guardrails
- no real geographic basemap is falsely claimed

### Frontend
- API contracts are correct
- beneficiary flow is coherent
- banker flow is coherent
- errors/insufficient data are handled
- provenance/warnings reach the UI

### AI
- LLM, if present, cannot override deterministic truth
- unsupported claims are blocked
- explanations are grounded in supplied evidence

### Validation
- golden fixture passes
- previous suites remain green
- E2E replay passes
- backend/browser performance are reported separately

---

# 31. Final Status Rules

## PRODUCTION READY
Only if all critical gates pass, no unsupported claims remain, no regression exists, and E2E replay passes.

## PRODUCTION READY WITH DOCUMENTED LIMITATIONS
Use when the core system is integrated and reliable and remaining limitations are explicitly disclosed and non-fatal.

A missing real geographic basemap can remain a documented limitation if the analytical coordinate plot is clearly labeled.

## NEEDS_FIX
Use when integration semantics conflict, analytical truth can be changed by UI behavior, guardrails/provenance fail, regressions exist, or E2E results cannot reconcile.

## UNSUPPORTED_CLAIM
Use for capabilities not actually demonstrated, including:
- exact enterprise GPS
- real-time tracking
- observed supplier/customer relationships
- confirmed transactions
- satellite/street basemap
- guaranteed business success
- white-space opportunity based only on graph sparsity

---

# 32. Critical Language Rules

Use:
- “derived competitor relationship”, not “confirmed competitor”
- “derived supply-chain relationship”, not “supplier/customer relationship”
- “resolved spatial coordinate”, not “exact location” unless precision is EXACT
- “Canvas geographic coordinate plot”, not “interactive geographic map” unless a real geographic basemap exists
- “sector diversification HHI”, not “market-share HHI”
- “evidence-supported opportunity”, not “guaranteed business opportunity”

---

# 33. Final Instruction to Implementer

Treat this document as an **integration consistency gate**.

Do not optimize for a positive audit result.

If the existing system is inconsistent, report it.

If a capability is absent, report it.

If a claim cannot be demonstrated, classify it as `UNSUPPORTED_CLAIM`.

If a limitation is acceptable, document it.

The objective is to establish that:

> **Udyam Saathi's existing intelligence components form one consistent, reproducible, evidence-backed analytical system from source data to final user-facing output.**

Only after this audit should the project proceed to substantial new decision/recommendation intelligence or major UI enhancements such as a true Leaflet-based geographic basemap.
