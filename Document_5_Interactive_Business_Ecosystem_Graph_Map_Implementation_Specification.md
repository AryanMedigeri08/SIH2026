# UDYAM SAATHI — DOCUMENT 5
# INTERACTIVE BUSINESS ECOSYSTEM GRAPH / MAP
# IMPLEMENTATION SPECIFICATION FOR OPUS 4.6

**Project:** Udyam Saathi — SIH 2026  
**Scope:** ONLY the Interactive Business Ecosystem Intelligence Graph/Map component  
**Primary implementation agent:** Opus 4.6  
**Reference:** `docs/ECOSYSTEM_GRAPH_CONTEXT_WINDOW.md`

---

## 0. EXECUTIVE INSTRUCTION

Implement the **Interactive Business Ecosystem Intelligence Graph/Map as a self-contained, reusable component/service boundary** that can be embedded into Udyam Saathi now or reused by other product surfaces later.

This document deliberately limits scope to the graph/map system.

### DO NOT expand scope into

- loan underwriting
- financial feasibility
- scheme recommendation
- business-plan generation
- chat/LLM features
- translation
- authentication redesign
- unrelated dashboard redesign
- new opportunity-scoring engines
- replacement of the existing MSME intelligence engine
- unrelated database migrations
- unrelated frontend refactors

The graph/map may **consume** existing intelligence outputs, but it must not silently replace or redefine them.

The implementation must first inspect the current repository and existing Documents 1–4 implementations before creating new services, models, API clients, scoring logic, or database structures.

> **Primary engineering rule:** reuse existing validated data/analytics contracts wherever possible. Build an adapter/read-model for visualization rather than duplicating the UDYAM ingestion and market-intelligence pipelines.

---

# 1. SOURCE OF TRUTH

The primary product/context source is:

`docs/ECOSYSTEM_GRAPH_CONTEXT_WINDOW.md`

It defines:

- analytical purpose of the graph/map
- zero-fabrication constraints
- micro-enterprise + macro-ecosystem architecture
- geographic and force-directed projections
- spatial catchments
- business nodes
- competitor/supply-chain relationship visualization
- KDE density layer
- opportunity/white-space layer
- temporal registration view
- interaction/state model
- beneficiary/banker rendering
- implementation roadmap

Do not silently replace the document's terminology.

This specification adds **engineering safety constraints** where the source wording could otherwise imply unsupported precision. These corrections are mandatory.

---

# 2. NON-NEGOTIABLE DATA-INTEGRITY CORRECTIONS

## 2.1 Pincode is NOT an enterprise GPS coordinate

Do not represent a pincode centroid as the exact physical location of an enterprise.

Use this hierarchy:

```text
Enterprise record
    |
    +-- exact GPS available?
    |       |
    |       +-- YES -> exact coordinate + HIGH spatial confidence
    |
    +-- village/locality successfully resolved?
    |       |
    |       +-- YES -> village/locality centroid + appropriate confidence
    |
    +-- only pincode available?
            |
            +-- pincode centroid ONLY as an approximate spatial anchor
                with explicit spatial precision/uncertainty
```

Every node must carry spatial metadata:

```json
{
  "latitude": 0.0,
  "longitude": 0.0,
  "spatialPrecision": "EXACT|LOCALITY|VILLAGE|PINCODE|UNMAPPED",
  "spatialConfidence": 0.0,
  "locationSource": "..."
}
```

If no defensible coordinate exists:

- do not invent one
- do not force the record onto the map
- place it in `unmappedEntities`
- expose an unmapped count where useful

---

## 2.2 Relationship edges are derived relationships, not observed transactions

### Competitor edge

Means:

> Two enterprises satisfy the deterministic competition rule based on activity/sector classification and spatial scope.

It does **not** mean they have transacted, share customers, have equal turnover, or compete commercially with certainty.

### Supply-chain edge

Means:

> Two activities match a deterministic complementary relationship rule from the configured activity matrix.

It does **not** mean a real supplier/buyer transaction, contract, or commercial relationship has been observed.

Use language such as:

- `Derived competitor relationship`
- `Potential supply-chain relationship`
- `Activity-based relationship`
- `Deterministic relationship`

Avoid:

- `Confirmed supplier`
- `Actual buyer`
- `Transaction partner`
- `Guaranteed competitor`

unless future verified data explicitly supports them.

---

## 2.3 Workforce glyphs must not be fabricated

The source document proposes:

- Circle = Micro 1–5 workers
- Square = Small 6–9
- Diamond = Medium 10+

Do not infer these tiers from enterprise name, turnover, activity text, registration date, or another unsupported proxy.

Only render workforce-scale glyphs when validated workforce/employment-bracket data exists for that **individual enterprise**.

Otherwise:

```text
scaleTier = UNKNOWN
```

SHRUG village-level workforce brackets are macro aggregates and must not be assigned to individual named enterprises.

---

## 2.4 HHI semantics must match the existing intelligence engine

Do not implement a conventional revenue-market-share HHI if the existing Udyam Saathi engine uses a different definition.

Reuse the existing validated HHI metric/semantics.

In particular, preserve the distinction between:

- conventional firm revenue market-share HHI
- the project's **economic-sector diversification HHI**

Do not label sector-diversification HHI as revenue market-share HHI.

---

## 2.5 Temporal minimum year must be data-driven

The context document says the scrubber begins at 2018.

Do not hard-code 2018 as the earliest data year unless repository data proves that 2018 is the earliest supported graph year.

Compute:

```text
minYear = earliest valid RegistrationDate year
maxYear = latest valid RegistrationDate year
```

If 2018 is required as a display bound, distinguish:

- display range
- actual data availability

Never fabricate historical registrations.

---

## 2.6 Radius controls must not silently change the market-scoring engine

The graph specification includes:

- 3 km
- 5 km
- 10 km

The existing market-intelligence engine also supports analysis radii such as 5/10/15/20 km.

The graph may provide its own visualization radius controls.

However:

> Changing graph visualization radius must not silently recompute or reinterpret the existing opportunity score unless the existing backend explicitly supports that radius and semantic contract.

Separate:

```text
visualization catchment
```

from:

```text
market-analysis scoring catchment
```

---

# 3. ARCHITECTURAL OBJECTIVE

Build:

```text
Existing UDYAM / SHRUG / Census / government-data pipelines
                     |
                     v
        Existing validated backend models
                     |
                     v
        Graph/Map Adapter / Read Model
                     |
                     v
              Graph API Contract
                     |
          +----------+----------+
          |                     |
          v                     v
   Geographic Projection   Topological Projection
       Leaflet/Canvas         D3/WebGL
          |                     |
          +----------+----------+
                     |
                     v
            Shared Interaction State
                     |
                     v
      Node / Edge / Layer / Metric Details
```

The graph is a **consumer of validated analytical data**, not a second source of truth.

---

# 4. PHASE 0 — REPOSITORY INSPECTION FIRST

Before writing implementation code, inspect:

1. backend framework/routing
2. frontend framework
3. map libraries
4. graph libraries
5. state-management approach
6. existing UDYAM API client
7. normalized enterprise model
8. geography/location resolver
9. Haversine/geospatial utilities
10. existing market-intelligence API
11. existing HHI implementation
12. activity/NIC classification
13. competitor classification
14. supply-chain/activity matrix
15. provenance/confidence fields
16. caching
17. PostGIS/database structures
18. `ViewModeContext.jsx`, if present
19. existing tests
20. design system

Create:

`docs/PHASE5_GRAPH_REPOSITORY_AUDIT.md`

Use:

| Area | Existing implementation | Reusable? | Required change | Risk |
|---|---|---:|---|---|
| UDYAM ingestion | ... | YES/NO | ... | ... |
| Enterprise model | ... | YES/NO | ... | ... |
| Geography | ... | YES/NO | ... | ... |
| Market intelligence | ... | YES/NO | ... | ... |
| HHI | ... | YES/NO | ... | ... |
| Frontend map | ... | YES/NO | ... | ... |
| Graph library | ... | YES/NO | ... | ... |
| State | ... | YES/NO | ... | ... |
| Tests | ... | YES/NO | ... | ... |

Do not create duplicate implementations when existing code is suitable.

---

# 5. GRAPH DATA CONTRACT

Create a versioned graph-specific read model.

Suggested endpoint:

```http
GET /api/v1/ecosystem/catchment
```

The exact path may change if an existing compatible endpoint already exists.

Suggested query parameters:

```text
lat
lon
radius_km
pincode
from_year
to_year
sectors[]
scale_tiers[]
verified_only
```

Validate:

- latitude/longitude
- radius bounds
- year bounds
- sector identifiers
- scale-tier identifiers

Invalid input must produce structured 4xx errors rather than misleading empty data.

---

# 6. RESPONSE SCHEMA

Suggested:

```json
{
  "schemaVersion": "1.0",
  "catchment": {
    "center": {
      "latitude": 0.0,
      "longitude": 0.0,
      "source": "..."
    },
    "radiusKm": 5,
    "distanceMethod": "HAVERSINE"
  },
  "nodes": [],
  "edges": [],
  "unmappedEntities": [],
  "metrics": {},
  "temporal": {},
  "layers": {},
  "provenance": {},
  "warnings": []
}
```

---

# 7. NODE CONTRACT

Suggested:

```json
{
  "id": "stable-local-node-id",
  "enterpriseName": "Example Enterprise",
  "state": "Maharashtra",
  "district": "Satara",
  "pincode": "000000",
  "address": "...",
  "activities": [
    {
      "code": "...",
      "label": "...",
      "sector": "DAIRY"
    }
  ],
  "registrationDate": "2024-01-15",
  "location": {
    "latitude": 0.0,
    "longitude": 0.0,
    "precision": "PINCODE",
    "confidence": 0.0,
    "source": "..."
  },
  "scaleTier": "UNKNOWN",
  "scaleSource": null,
  "sector": "DAIRY",
  "distanceKm": 2.84,
  "dataQuality": {
    "verified": false,
    "warnings": []
  },
  "provenance": {
    "sources": []
  }
}
```

If the source has no government unique ID, use a stable local node ID and document its derivation. Never call it a government ID.

---

# 8. EDGE CONTRACT

Suggested:

```json
{
  "id": "edge-local-id",
  "source": "node-A",
  "target": "node-B",
  "relationshipType": "COMPETITOR|SUPPLY_CHAIN",
  "relationshipStatus": "DERIVED",
  "confidence": 0.0,
  "distanceKm": 2.84,
  "ruleId": "COMPETITOR_ACTIVITY_V1",
  "direction": "NONE|SOURCE_TO_TARGET",
  "evidence": {
    "sourceActivity": "...",
    "targetActivity": "...",
    "matchingRule": "...",
    "spatialRule": "..."
  }
}
```

Supply-chain direction may be rendered only when the configured activity matrix defines direction.

Do not infer direction from visual layout.

---

# 9. GEOGRAPHIC PROJECTION

Use the repository's existing mapping stack where possible.

Required:

- real geographic coordinates only
- 5 km ring
- 10 km ring
- node rendering
- optional relationships
- pan
- zoom
- node selection
- edge selection
- sector filtering
- layer toggles
- reset

Catchment rings must be geodesic/correctly projected. Do not use arbitrary pixel circles.

---

# 10. FORCE-DIRECTED TOPOLOGICAL PROJECTION

Implement a second projection over the same graph data.

Critical rule:

> Force-directed layout changes visual position, not geographic facts.

Preserve:

```text
latitude
longitude
distanceKm
spatialPrecision
```

Use separate render coordinates:

```text
node.location = geographic truth
node.renderPosition = projection-specific visual position
```

Force layout may use:

- competitor edges
- supply-chain edges
- sector clustering
- repulsion
- link distance
- collision handling

Do not create edges merely to make the graph visually connected.

Disconnected components are valid.

---

# 11. FIVE VISUAL LAYERS

## Layer 1 — Catchment Rings

Render 5 km and 10 km rings when a valid center exists.

## Layer 2 — Business Nodes

Render:

- sector/domain
- registration vintage
- spatial confidence
- scale tier only when supported

Never encode unsupported workforce values.

## Layer 3 — Economic Relationships

### Competitor

Existing activity/sector matching rule + spatial eligibility.

### Supply chain

Existing deterministic activity-complementarity matrix.

Both are derived relationships unless verified external transaction data exists.

## Layer 4 — Density

KDE/density is optional and must use real mapped observations.

Requirements:

- no synthetic points
- clearly identify metric
- handle low sample sizes
- handle zero/missing data

If insufficient:

```text
densityLayer.status = "INSUFFICIENT_DATA"
```

Do not render a misleading heatmap.

## Layer 5 — Opportunity / White Space

Do not derive opportunity from visual emptiness alone.

Require defensible evidence such as:

- population/demand proxy
- infrastructure evidence
- observed enterprise supply
- confidence/coverage

If evidence is incomplete:

```text
status = "UNAVAILABLE"
```

No opportunity claim from absence of mapped nodes alone.

---

# 12. FILTERING

Implement composable filters:

```text
sector
relationship type
scale tier
verification/data quality
temporal range
radius
```

Use:

```text
rawGraphData
        |
        v
filterGraph()
        |
        v
visibleGraphData
        |
        v
projection
```

Do not mutate the original API response.

When filtering nodes, incompatible edges must also be hidden/removed from the render graph.

---

# 13. TEMPORAL SCRUBBER

Use `RegistrationDate`.

For selected year `Y`:

```text
visible nodes:
RegistrationDate.year <= Y
```

Missing/invalid dates:

- are not assigned a fabricated year
- are tracked in data-quality warnings/counts

Registration velocity must be based on actual registrations.

Use:

> Registration acceleration

rather than:

> Demand acceleration

unless an independent demand dataset supports the latter.

---

# 14. INTERACTION CONTRACT

## Node click

1. select node
2. de-emphasize unrelated nodes
3. highlight first-degree derived relationships
4. show node details
5. preserve current map/graph state

Reuse an existing enterprise detail component if available. Otherwise expose:

```javascript
onNodeSelect(node)
```

## Edge click

Show:

- relationship type
- distance
- rule ID
- participating activities
- relationship status
- confidence
- evidence/provenance

Never present a derived edge as a confirmed commercial relationship.

## Legend

Support:

- single-sector isolate
- multi-sector comparison
- restore all

Provide an accessible alternative if keyboard modifiers are unsuitable.

## Radius

Recompute graph catchment membership only.

Do not silently alter unrelated market scoring.

## Reset

Restore:

- full graph
- default filters
- default projection
- default camera
- cleared selection

---

# 15. STATE MODEL

Use graph-local state:

```javascript
{
  viewMode: "beneficiary" | "banker",
  projectionMode: "geographic" | "topological",

  catchment: {
    centerCoords: [lat, lon],
    radiusKm: 5
  },

  temporal: {
    minYear: null,
    maxYear: null,
    selectedMaxYear: null
  },

  activeFilters: {
    sectors: [],
    relationshipTypes: [],
    scaleTiers: [],
    verifiedOnly: false
  },

  activeLayers: {
    catchmentRings: true,
    nodes: true,
    relationships: true,
    heatmap: false,
    opportunities: false
  },

  selection: {
    selectedNodeId: null,
    selectedEdgeId: null
  }
}
```

Keep derived metrics out of mutable UI state when they can be calculated from validated data. Server-provided metrics must retain provenance and radius.

---

# 16. PERSONA MODES — GRAPH-ONLY

## Beneficiary

Emphasize:

- competitor count
- nearest derived competitor relationship
- nearby potential suppliers/partners
- simple radius control
- plain-language explanations

Avoid unexplained HHI and dense graph jargon.

## Banker

Emphasize:

- existing HHI
- sector concentration/diversification
- registration growth
- derived competitor network
- potential supply-chain network
- borrower-overlap/cannibalization only if an existing validated source supports it

Do not implement a new borrower-cannibalization engine inside this component.

---

# 17. METRICS

The graph may display existing validated:

- enterprise count
- competitor count
- supplier/potential-partner count
- sector distribution
- HHI
- registration velocity
- historical CAGR

Each metric must make clear:

1. definition
2. source
3. time period
4. radius
5. observed vs derived
6. confidence/coverage limitations

Example:

```json
{
  "name": "HHI",
  "value": 1640,
  "semanticDefinition": "existing-project-sector-diversification-HHI",
  "radiusKm": 5,
  "source": "market-intelligence-engine",
  "status": "AVAILABLE"
}
```

---

# 18. PROVENANCE AND WARNINGS

Expose warnings such as:

```json
{
  "code": "PINCODE_APPROXIMATION",
  "severity": "INFO",
  "message": "Some enterprise locations use pincode-level spatial anchors."
}
```

```json
{
  "code": "UNMAPPED_ENTERPRISES",
  "severity": "WARNING",
  "count": 12
}
```

```json
{
  "code": "INSUFFICIENT_DENSITY_DATA",
  "severity": "WARNING"
}
```

```json
{
  "code": "SUPPLY_CHAIN_IS_DERIVED",
  "severity": "INFO",
  "message": "Supply-chain links are activity-based inferred relationships, not observed transactions."
}
```

---

# 19. PERFORMANCE

Target the source document's 500+ node requirement, but benchmark before claiming performance.

Required:

- avoid O(N²) edge generation in the frontend
- perform expensive relationship construction server-side or with indexed/optimized structures
- batch Canvas/WebGL rendering where appropriate
- memoize stable graph transformations
- debounce expensive filter/layout operations
- avoid recreating the whole map on every state update
- clean up event listeners
- dispose graph/map instances correctly

Benchmark at:

```text
500 nodes  -> target smooth interaction
1000+      -> benchmark and document result
5000+      -> explicit degradation strategy
```

Never claim "high performance" without measurements.

---

# 20. ACCESSIBILITY

Graph/map interactions must not depend solely on color.

Provide:

- textual relationship labels
- keyboard-accessible controls
- visible focus states
- non-color distinction for competitor vs supply-chain edges
- meaningful ARIA labels where applicable
- textual representation of selected-node relationships
- selected-node details without requiring hover

---

# 21. RESPONSIVE/MOBILE

Only make this graph/map component responsive.

Required:

- collapsible controls
- touch-friendly selection
- zoom/pan gestures
- readable relationship details
- no critical information hidden only in hover tooltips
- selected-node information available without hover

Do not redesign the entire application.

---

# 22. API / CACHING

Reuse existing cache infrastructure.

If a graph-specific read-model cache is needed:

```text
cache key =
dataset version
+ geographic key
+ radius
+ temporal range
+ filter signature
```

Do not create a second UDYAM ingestion cache if Document 1 already provides a canonical cache.

Document TTL and invalidation.

Keep upstream API keys backend-only.

---

# 23. SECURITY

The graph component must:

- validate query parameters
- cap maximum radius
- cap maximum node count
- reject malformed coordinates
- prevent query injection
- avoid secrets in frontend code
- avoid unnecessary sensitive fields
- safely render enterprise names, addresses and activity text
- avoid unsafe HTML rendering

---

# 24. TEST PLAN

Create dedicated suites:

```text
tests/test_ecosystem_graph_api.py
tests/test_ecosystem_graph_geometry.py
tests/test_ecosystem_graph_relationships.py
tests/test_ecosystem_graph_temporal.py
tests/test_ecosystem_graph_provenance.py
tests/test_ecosystem_graph_performance.py

frontend tests:
EcosystemIntelligenceMap.test.*
graphState.test.*
graphFiltering.test.*
```

## Mandatory backend tests

### Geometry

- zero-distance pair
- known Haversine pair
- exact radius boundary
- just-inside radius
- just-outside radius
- invalid coordinates
- unmapped location

### Data integrity

- no coordinate fabrication
- pincode centroid marked approximate
- no workforce tier when absent
- no fake edge generation
- deterministic relationship rule
- stable local node IDs
- duplicate handling

### Relationships

- direct competitor
- non-competitor exclusion
- supply-chain rule
- no transaction claim
- directional edge only when matrix supports direction

### Temporal

- valid date inclusion
- upper-bound filtering
- missing date
- invalid date
- data-driven min/max year

### Filters

- sector
- relationship type
- scale tier
- verified-only
- combined filters

### Metrics

- radius-specific counts
- metric provenance
- HHI semantic label
- insufficient-data behavior

---

# 25. FRONTEND TESTS

Verify:

1. geographic mode renders
2. topological mode renders
3. projection switch preserves node identity
4. geographic coordinates remain unchanged by force layout
5. node selection works
6. edge selection works
7. unrelated nodes are de-emphasized
8. legend filtering works
9. reset works
10. temporal scrubber works
11. radius changes update graph membership
12. layer toggles work
13. unmapped warning appears
14. insufficient-data heatmap is not misleadingly rendered
15. keyboard interaction works
16. mobile layout remains usable

---

# 26. GOLDEN DATASET

Create a deterministic **test-only** fixture containing:

- several sectors
- one direct competitor relationship
- one non-competitor
- one potential supply-chain relationship
- one unmapped enterprise
- one pincode-level enterprise
- one exact/locality-level enterprise if repository supports it
- multiple registration years
- missing registration date
- unknown workforce scale

Mark it explicitly:

```text
TEST FIXTURE — NOT REAL BUSINESS DATA
```

Synthetic records are acceptable inside automated tests only. They must never enter production graph responses.

---

# 27. VISUAL QA

If repository architecture permits, create a development-only fixture/demo route.

It must make it easy to verify:

- catchment rings
- nodes
- edges
- filters
- timeline
- map ↔ topology switch
- selected node
- selected edge
- warnings

Do not add fake production records.

---

# 28. ERROR STATES

Implement:

```text
LOADING
READY
EMPTY
PARTIAL_DATA
INVALID_LOCATION
NO_VALID_COORDINATES
INSUFFICIENT_DATA
API_ERROR
TIMEOUT
```

### Empty

> No mapped enterprises were found in this catchment.

Do not say:

> There are no businesses in this area.

### Partial

> 12 enterprises were found, but 4 could not be placed accurately on the map.

### Opportunity unavailable

> Opportunity overlay unavailable because required demand/infrastructure evidence is incomplete.

---

# 29. EXACT LANGUAGE RULES

### Allowed

- "3 registered enterprises were mapped within 5 km."
- "2 derived competitor relationships were identified."
- "Potential supply-chain relationship based on activity classification."
- "Location represented using pincode-level spatial approximation."
- "Registration activity increased between 2022 and 2025."

### Not allowed

- "There are definitely only 3 businesses here."
- "This company supplies that company."
- "This is the exact location of the enterprise." when only pincode/locality data exists
- "Demand increased" based only on registrations
- "High opportunity" based only on visual whitespace
- "Market share HHI" if the metric is not market-share HHI

---

# 30. DELIVERABLES

## Documentation

```text
docs/PHASE5_GRAPH_REPOSITORY_AUDIT.md
docs/PHASE5_GRAPH_IMPLEMENTATION.md
docs/PHASE5_GRAPH_TEST_REPORT.md
```

## Backend

Use existing structure. Likely responsibilities:

```text
graph read-model adapter
catchment query
node transformation
edge transformation
provenance
metrics adapter
```

Do not duplicate existing UDYAM ingestion.

## Frontend

Use the repository's appropriate location. Likely:

```text
frontend/src/components/Dashboard/EcosystemIntelligenceMap.jsx
```

Recommended decomposition:

```text
EcosystemIntelligenceMap
├── GeographicProjection
├── TopologicalProjection
├── CatchmentRings
├── GraphControls
├── GraphLegend
├── GraphTimeline
├── GraphLayerControls
├── NodeDetails
├── EdgeDetails
├── GraphWarnings
└── graphState / selectors / utilities
```

Do not force every subcomponent if the existing architecture supports a cleaner smaller design.

---

# 31. IMPLEMENTATION DOCUMENTATION

`docs/PHASE5_GRAPH_IMPLEMENTATION.md` must explain:

1. architecture
2. consumed data sources
3. API contract
4. node schema
5. edge schema
6. spatial precision
7. relationship semantics
8. temporal logic
9. projection behavior
10. filters
11. state management
12. performance strategy
13. caching
14. error handling
15. provenance
16. known limitations
17. test execution
18. future integration

---

# 32. FINAL VALIDATION MATRIX

Produce:

| Gate | Result | Evidence |
|---|---|---|
| Repository audit | PASS / ... | ... |
| Existing UDYAM pipeline reused | PASS / ... | ... |
| No duplicate ingestion | PASS / ... | ... |
| Spatial precision enforced | PASS / ... | ... |
| No fake production entities | PASS / ... | ... |
| No fake production edges | PASS / ... | ... |
| Competitor semantics correct | PASS / ... | ... |
| Supply-chain semantics correct | PASS / ... | ... |
| Workforce tier integrity | PASS / ... | ... |
| Geographic projection | PASS / ... | ... |
| Topological projection | PASS / ... | ... |
| Geographic truth preserved | PASS / ... | ... |
| Catchment rings | PASS / ... | ... |
| Filters | PASS / ... | ... |
| Timeline | PASS / ... | ... |
| HHI semantics | PASS / ... | ... |
| Provenance | PASS / ... | ... |
| Error states | PASS / ... | ... |
| Accessibility | PASS / ... | ... |
| Mobile behavior | PASS / ... | ... |
| Performance benchmark | PASS / ... | ... |
| Automated tests | PASS / ... | ... |
| Integration boundary | PASS / ... | ... |

---

# 33. DEFINITION OF DONE

- [ ] repository inspected first
- [ ] existing UDYAM/data/market-intelligence infrastructure reused where possible
- [ ] graph data has a documented versioned contract
- [ ] geographic coordinates carry precision/confidence metadata
- [ ] pincode centroid is never represented as exact enterprise GPS
- [ ] unmapped records are explicitly handled
- [ ] competitor relationships are deterministic and labelled derived
- [ ] supply-chain relationships are deterministic and labelled potential/derived
- [ ] no production fake entities or relationships
- [ ] workforce glyphs only used when supported
- [ ] geographic mode works
- [ ] topological mode works
- [ ] topology does not overwrite geographic truth
- [ ] 5 km and 10 km rings work
- [ ] filters work
- [ ] timeline works from actual available data
- [ ] radius changes do not silently alter unrelated scoring semantics
- [ ] HHI uses the existing validated definition
- [ ] density layer handles insufficient data honestly
- [ ] opportunity overlay does not infer opportunity from emptiness alone
- [ ] provenance and warnings are exposed
- [ ] backend/frontend tests pass
- [ ] performance is measured
- [ ] accessibility addressed
- [ ] mobile behavior validated
- [ ] implementation documentation complete
- [ ] no unrelated Udyam Saathi component modified without necessity

---

# 34. OPUS 4.6 EXECUTION ORDER

Follow exactly:

```text
1. Read this document.
2. Read docs/ECOSYSTEM_GRAPH_CONTEXT_WINDOW.md.
3. Inspect the repository.
4. Review existing Documents 1–4 implementations.
5. Produce PHASE5_GRAPH_REPOSITORY_AUDIT.md.
6. Identify reusable existing services/models/utilities.
7. Design graph adapter/read-model around existing contracts.
8. Implement backend graph data contract.
9. Implement geographic projection.
10. Implement topological projection.
11. Implement graph-local state and interactions.
12. Implement filtering and timeline.
13. Implement provenance/warnings/error states.
14. Add automated tests.
15. Run the relevant complete test suite.
16. Run performance checks.
17. Perform visual/manual QA.
18. Produce PHASE5_GRAPH_IMPLEMENTATION.md.
19. Produce PHASE5_GRAPH_TEST_REPORT.md.
20. Produce a final walkthrough listing:
    - files changed
    - files created
    - tests run
    - test results
    - benchmark results
    - known limitations
    - assumptions requiring human approval.
```

## STOP CONDITIONS

Stop and report instead of guessing if:

- an existing data contract conflicts with this specification
- a required coordinate cannot be defensibly resolved
- a proposed relationship requires unsupported business knowledge
- an existing metric's semantics are unclear
- a missing dependency would materially change architecture
- a feature would require changing an unrelated Udyam Saathi component
- production data would need to be fabricated

Never solve an evidence gap by inventing data.

---

# 35. FINAL PRINCIPLE

The graph/map is not a decoration layer.

It is a **visual analytical projection of validated Udyam Saathi data**.

```text
No evidence
    ↓
No claim

No coordinate
    ↓
No fabricated point

No observed transaction
    ↓
No confirmed supply-chain claim

No workforce field
    ↓
No workforce-tier inference

No demand dataset
    ↓
No demand-growth claim

No sufficient evidence
    ↓
No opportunity claim
```

The component should be impressive because it exposes the structure of the data and analytics—not because it visually invents structure that the data does not contain.
