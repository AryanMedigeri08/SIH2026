# MSME Market Intelligence & Opportunity Engine
## Document 2 — Detailed Implementation Specification for Opus 4.6

> **Purpose:** Define the intelligence layer built on top of the validated UDYAM/geographic pipeline.
>
> **Scope:** Business-category understanding, relevant competitor identification, supply-side concentration, demand-side signals, market gaps, opportunity indicators, explainable recommendations, and product/API outputs.
>
> **Important:** This document does not replace Document 1. Document 1 owns UDYAM ingestion, normalization, locality resolution, provenance, confidence, coordinates, and geographic market pools. Document 2 consumes those outputs.
>
> **Critical principle:** Do not manufacture certainty. Every intelligence output must be traceable to source data, deterministic transformations, documented inference rules, or explicitly labeled model predictions.

---

# 1. Position of Document 2

Document 1 produces:

```text
UDYAM records
    ↓
normalized enterprises
    ↓
resolved geography
    ↓
coordinates + confidence
    ↓
market radius
    ↓
candidate nearby MSMEs
    ↓
parsed activities
```

Document 2 starts here:

```text
Candidate MSMEs
        ↓
Business semantic understanding
        ↓
Category normalization
        ↓
Relevant competitor identification
        ↓
Market supply analysis
        ↓
Demand/economic context
        ↓
Gap/opportunity analysis
        ↓
Explainable recommendation
```

Do not duplicate the geographic engine inside Document 2.

---

# 2. Core Objective

Given:

```text
target village/locality
+
market radius
+
business intent/category
```

produce:

```text
existing relevant businesses
+
competitive intensity
+
category concentration
+
demand-side indicators
+
market gaps
+
opportunity indicators
+
explanation
+
data-quality limitations
```

The system should answer:

- What businesses already exist nearby?
- How many are relevant to the proposed business?
- How concentrated is the relevant category?
- How far away are the nearest relevant businesses?
- Is supply concentrated in the target village or nearby settlements?
- What demand/economic indicators support or weaken the opportunity?
- Which factors drive the recommendation?
- How confident is the recommendation?
- What evidence is missing?

---

# 3. Non-Negotiable Intelligence Principles

## 3.1 Nearby ≠ competitor

A nearby MSME is not automatically a competitor.

```text
nearby MSME
    ↓
business activity understood
    ↓
category mapped
    ↓
relevance evaluated
    ↓
potential competitor
```

## 3.2 Registration ≠ active business

Do not claim every UDYAM registration represents a currently operating enterprise.

Use terms such as:

- registered enterprise
- registered MSME
- UDYAM-listed enterprise

unless independent evidence supports operational status.

## 3.3 UDYAM ≠ complete business universe

UDYAM-derived counts represent businesses available in the UDYAM dataset, not every business operating in the market.

## 3.4 Category counts ≠ demand

Few businesses do not automatically imply high unmet demand.

Supply scarcity must be combined with independent demand/economic evidence.

## 3.5 No arbitrary scores

Every scoring component must have:

- definition
- source
- transformation
- rationale
- confidence
- limitation

---

# 4. Input Contract

Example:

```json
{
  "state": "TELANGANA",
  "district": "MEDAK",
  "village": "BALANAGAR",
  "radius_km": 10,
  "business_intent": "DAIRY"
}
```

Optional:

- subdistrict / mandal
- target coordinates
- business category
- business keywords
- analysis mode

Do not require users to provide a NIC code unless the product explicitly supports advanced use.

---

# 5. Business Intent Model

Create a structured representation.

Example:

```json
{
  "intent_id": "dairy",
  "display_name": "Dairy Business",
  "category": "DAIRY",
  "related_categories": [
    "MILK_RETAIL",
    "DAIRY_PROCESSING",
    "MILK_COLLECTION"
  ],
  "direct_categories": [
    "DAIRY"
  ]
}
```

Do not freeze a large taxonomy before examining real data across multiple districts/states.

---

# 6. Business Category Ontology

Create a maintainable hierarchy.

Possible starting categories:

```text
FOOD_RETAIL
GENERAL_RETAIL
DAIRY
POULTRY
LIVESTOCK
TAILORING
APPAREL
TRANSPORT
CONSTRUCTION
MANUFACTURING
FOOD_PROCESSING
AGRICULTURE_SUPPORT
REPAIR_SERVICES
PERSONAL_SERVICES
PROFESSIONAL_SERVICES
EDUCATION
HEALTH
HOSPITALITY
OTHER
UNKNOWN
```

These are candidates, not final truth.

Support:

```text
parent_category
category
subcategory
aliases
NIC mappings
keyword mappings
confidence
```

---

# 7. NIC/Activity Interpretation

Input:

```text
NIC code
raw NIC description
activity description
```

Output:

```text
normalized_category
subcategory
mapping_confidence
mapping_source
```

Use official NIC documentation as the semantic authority where available.

Do not use an LLM alone as the source of truth for official NIC meanings.

---

# 8. Activity Normalization

One enterprise may have multiple activities.

Represent:

```text
enterprise
    ├── activity 1
    ├── activity 2
    └── activity 3
```

Each activity row should contain:

```text
record_fingerprint
nic_code
raw_description
normalized_category
subcategory
mapping_confidence
mapping_source
```

Do not collapse multiple activities into one arbitrary category.

---

# 9. Relevance Classification

For a requested business intent:

```text
DIRECT_COMPETITOR
RELATED_BUSINESS
INDIRECT_COMPETITOR
NON_RELEVANT
UNKNOWN
```

Definitions:

- **DIRECT_COMPETITOR:** same/substantially equivalent category.
- **RELATED_BUSINESS:** closely connected but not identical.
- **INDIRECT_COMPETITOR:** substitute or overlapping customer demand.
- **NON_RELEVANT:** no meaningful competitive relationship.
- **UNKNOWN:** insufficient evidence.

Never force an ambiguous enterprise into a competitor class.

---

# 10. Relevance Rules

Use deterministic rules first.

Evidence hierarchy:

```text
official NIC mapping
        ↓
activity/category mapping
        ↓
business-name/keyword evidence
        ↓
secondary semantic inference
```

Store the reason:

```json
{
  "classification": "DIRECT_COMPETITOR",
  "reason": "Same normalized business category",
  "confidence": "HIGH"
}
```

---

# 11. Competitor Record Model

Expose:

```text
enterprise_name
category
subcategory
distance_km
market_zone
locality
registration_date
activity
relevance_class
relevance_confidence
geographic_confidence
data_sources
```

Do not expose unsupported claims about:

- revenue
- employee count
- operating hours
- inventory
- sales
- customer volume

---

# 12. Supply-Side Metrics

For a target category calculate:

```text
N_total
N_relevant
N_direct
N_related
N_unknown
```

Never silently exclude unknowns.

---

# 13. Distance-Based Competition Metrics

Calculate:

```text
nearest_direct_competitor_km
nearest_related_business_km
median_direct_competitor_distance
```

And counts by market zone:

```text
direct_competitors_0_5km
direct_competitors_5_10km
```

Keep geographic confidence separate from relevance confidence.

---

# 14. Geographic Concentration

Calculate:

```text
share_of_direct_competitors_in_target_locality
```

and:

```text
share_by_market_zone
```

These are descriptive supply-distribution statistics, not demand estimates.

---

# 15. Category Concentration

Calculate:

```text
category_count
```

and:

```text
category_share =
category_count / all_resolved_enterprises
```

Optional concentration measures such as HHI should be introduced only if entity/category definitions are stable and the metric has a clear purpose.

---

# 16. Market Density

If reliable population data exists:

```text
businesses_per_1000_people
```

If population is unavailable, do not invent a population-adjusted density.

Descriptive supply metrics may still be reported.

---

# 17. Demand-Side Data Layer

Demand must be independent of UDYAM supply data.

Potential sources:

```text
population
households
population growth
age distribution
literacy
agriculture
livestock
crop patterns
road connectivity
banking access
market infrastructure
schools
health facilities
electricity
internet/connectivity
other official economic indicators
```

Every dataset requires:

1. identifiable source
2. geographic join
3. temporal understanding
4. documented methodology
5. appropriate access/licensing

Do not add a dataset merely because it sounds relevant.

---

# 18. Demand Feature Store

Suggested fields:

```text
location_id
population
households
population_growth
agriculture_indicator
livestock_indicator
road_access_indicator
banking_access_indicator
infrastructure_indicators
data_year
source
source_url
confidence
```

Retain source values and derived values separately.

---

# 19. Temporal Alignment

Every demand/economic feature must carry:

```text
data_year
reference_period
```

Do not describe a historical census value as a current population measurement.

If temporal mismatch is unavoidable, label it in the analysis.

---

# 20. Geographic Joins

Preferred hierarchy:

```text
official geographic ID
    ↓
district/subdistrict/village hierarchy
    ↓
normalized name
    ↓
fuzzy matching
```

Do not rely solely on free-text village names when authoritative geographic IDs exist.

Every fuzzy match must have confidence/provenance.

---

# 21. Feature Engineering

Potential derived features:

```text
population_density
population_growth_rate
household_density
agriculture_intensity
livestock_intensity
infrastructure_access_score
distance_to_market
business_density
```

Every feature needs:

```text
formula
source variables
source years
interpretation
limitations
```

---

# 22. Avoid Leakage and Circular Reasoning

Do not use the same UDYAM count as both competition and independent demand evidence without justification.

Do not create:

```text
low businesses
→ low competition
→ high demand
→ high opportunity
```

That is circular reasoning.

---

# 23. Opportunity Indicators

Before a final score, calculate transparent indicators.

Examples:

### Supply gap

Few direct competitors relative to an established demand proxy.

### Accessibility gap

Target is relatively distant from relevant businesses.

### Demand support

Independent government indicators support potential demand.

### Growth support

Population/economic/activity growth supports future demand.

### Infrastructure constraint

Poor connectivity may reduce feasibility despite low competition.

Show indicators separately before combining them.

---

# 24. Opportunity Score

Only after indicators are validated.

Conceptually:

```text
Opportunity
=
Demand potential
+
Supply gap
+
Accessibility
+
Growth
-
Infrastructure constraints
```

Do not assign arbitrary weights.

Possible approaches:

### Rule-based baseline

Transparent deterministic score.

### Statistical model

Only if sufficient labeled historical data exists.

### ML ranking

Only if training/evaluation data supports it.

For the first SIH prototype, prefer a transparent rule-based baseline over an unexplained black box.

---

# 25. Confidence-Aware Scoring

Example:

```text
opportunity_score = 78
confidence = MEDIUM
```

because different evidence layers have different reliability.

Do not treat the numeric score as equally reliable for every village/category.

---

# 26. Missing Data

Never convert missing data to favorable assumptions.

For example:

```text
population = UNKNOWN
```

must not become:

```text
population = 0
```

Use explicit states such as:

```text
UNKNOWN
NOT_AVAILABLE
NOT_APPLICABLE
```

where useful.

---

# 27. Opportunity Explanation

Every recommendation must have an evidence trail.

Conceptual output:

```text
Recommendation:
DAIRY — PROMISING

Why:
1. X direct UDYAM-registered businesses identified within 10 km.
2. Nearest identified direct competitor is X km away.
3. Local livestock/agriculture indicator is above the comparison baseline.
4. Population/demand data supports the market size.

Cautions:
- UDYAM does not cover every business.
- Registration does not prove current operation.
- Geographic coverage is incomplete for X% of records.
- Population data is from YEAR.
```

Every number must come from actual data.

---

# 28. Explainability Contract

Every recommendation should be machine-reconstructable.

Example:

```json
{
  "recommendation": "PROMISING",
  "drivers": [
    {
      "feature": "direct_competitor_count",
      "value": 3,
      "interpretation": "Low observed registered supply",
      "confidence": "HIGH"
    }
  ],
  "limitations": [
    "UDYAM coverage is incomplete",
    "Some addresses are unresolved"
  ]
}
```

---

# 29. Comparative Baselines

Possible baselines:

```text
district average
mandal average
nearby villages
same-category market average
similar-population villages
```

Do not compare unrelated geographic scales without normalization.

---

# 30. Peer-Group Analysis

Eventually identify comparable villages based on measurable features:

```text
population
households
agriculture
connectivity
business density
geographic context
```

Use peer groups to determine whether a village is unusually underserved or saturated.

Do not create arbitrary peer groups.

---

# 31. Market Gap Detection

A market gap should require multiple signals.

Example:

```text
Low direct competitor supply
+
sufficient demand proxy
+
reasonable accessibility
=
candidate market gap
```

Never use:

```text
Low competitor count
=
market gap
```

by itself.

---

# 32. Negative Signals

The system must also identify reasons not to enter:

```text
high competitor concentration
low demand indicators
poor accessibility
very small market
weak infrastructure
insufficient evidence
```

It must be able to return:

> Insufficient evidence

instead of forcing a positive/negative recommendation.

---

# 33. Recommendation Classes

Start with:

```text
PROMISING
MODERATE
SATURATED
HIGH_RISK
INSUFFICIENT_DATA
```

Definitions must be documented and validated.

---

# 34. Scenario Analysis

Allow users to change:

```text
market radius
business category
comparison baseline
```

Example:

```text
5 km:
2 competitors

10 km:
7 competitors
```

This exposes sensitivity to market assumptions.

---

# 35. Sensitivity Analysis

For important recommendations calculate robustness to:

- radius
- uncertain geographic records
- category classification uncertainty
- old demand data
- alternative comparison baselines

Example:

```text
5 km  → PROMISING
10 km → MODERATE
15 km → SATURATED
```

This is more informative than one static score.

---

# 36. Uncertainty Propagation

If geographic confidence is low, downstream metrics must reflect it.

Example:

```text
Direct competitors:
HIGH-confidence = 3
possible additional = 2
```

Report:

```text
confirmed range: 3
possible range: 3–5
```

Do not pretend the count is exactly 5.

---

# 37. Market Count Presentation

Use:

```text
confirmed_count
possible_count
unknown_count
```

where appropriate.

Example:

```text
Direct competitors within 10 km:

Confirmed: 3
Potential: 2
Unresolved relevance: 1
```

---

# 38. Category-Level Market Report

Recommended output:

```text
Business Category
-------------------------
Existing registered supply
Direct competitors
Related businesses
Nearest competitor
Median competitor distance
5 km count
10 km count
Supply concentration
Demand indicators
Growth indicators
Infrastructure factors
Opportunity indicators
Confidence
Limitations
```

---

# 39. API Contract

Potential endpoint:

```http
POST /market-analysis
```

Request:

```json
{
  "state": "TELANGANA",
  "district": "MEDAK",
  "village": "BALANAGAR",
  "radius_km": 10,
  "business_category": "DAIRY"
}
```

Response:

```json
{
  "target": {},
  "market_definition": {},
  "supply": {},
  "demand": {},
  "competition": {},
  "opportunity": {},
  "confidence": {},
  "limitations": {},
  "evidence": []
}
```

Refine the schema after backend validation.

---

# 40. Evidence Object

Every major metric should be traceable.

Example:

```json
{
  "metric": "direct_competitor_count",
  "value": 3,
  "source_records": [
    "record_fingerprint_1",
    "record_fingerprint_2"
  ],
  "transformation": "distance <= 10km AND relevance = DIRECT_COMPETITOR",
  "confidence": "HIGH"
}
```

---

# 41. Data Lineage

For every derived metric maintain:

```text
source dataset
source record(s)
transformation
filters
date retrieved
algorithm version
```

This is mandatory for reproducibility.

---

# 42. Analysis Versioning

Store:

```text
analysis_run_id
pipeline_version
category_ontology_version
scoring_version
data_snapshot_date
```

A changed recommendation should be explainable through these versions.

---

# 43. Caching

Cache expensive intermediate outputs:

```text
geographic resolution
activity parsing
category mapping
market pools
demand features
```

Invalidate using source/data versions.

Do not blindly reuse stale analyses.

---

# 44. Database Models

Suggested intelligence tables:

```text
business_categories
category_aliases
nic_category_mapping
enterprise_category_assignments
market_analysis_runs
market_supply_metrics
market_demand_features
competition_metrics
opportunity_indicators
opportunity_scores
recommendation_evidence
```

Keep raw and derived layers separate.

---

# 45. PostGIS Integration

Consume a reproducible geographic market pool from Document 1.

Use spatial queries such as:

```text
target coordinate
        ↓
PostGIS ST_DWithin
        ↓
market pool
```

Avoid repeated external geocoding during every analysis request.

---

# 46. Frontend — Market Overview

Show:

```text
Target location
Selected category
Market radius
Registered supply
Direct competitors
Nearest competitor
Opportunity indicator
Confidence
```

Do not overwhelm the user with raw records before the decision summary.

---

# 47. Frontend — Map

Show:

- target location
- market boundary
- relevant businesses
- optional related businesses

Differentiate:

```text
direct
related
unknown
```

Represent uncertain geography visibly.

Do not show unresolved records as exact pins.

---

# 48. Frontend — Opportunity View

Show:

```text
Opportunity:
PROMISING

Key positive factors:
...

Key negative factors:
...

Evidence:
...

Confidence:
...

Limitations:
...
```

The user must be able to understand why the result was produced.

---

# 49. User-Selectable Analysis

Allow:

```text
business category
market radius
comparison baseline
```

Potential radius options:

```text
5 km
10 km
15 km
20 km
custom
```

---

# 50. Multi-Category Comparison

Eventually allow several categories for the same village.

Example:

```text
Category        Opportunity    Confidence
-------------------------------------------
Dairy           Promising       Medium
Poultry         Moderate        High
Tailoring       Saturated       High
Food Processing Insufficient    Low
```

Do not compare scores without explaining major differences in evidence availability.

---

# 51. Ranking

If categories are ranked, expose:

- score
- confidence
- drivers
- limitations

Never return only a ranked list without explanation.

---

# 52. Evaluation Dataset

Create a manually reviewed benchmark.

For each target village/category record:

```text
reviewed nearby businesses
reviewed category relevance
geographic correctness
```

Where possible, keep evaluation data independent from heuristic development.

---

# 53. Evaluation Metrics

## Competitor relevance

- precision
- recall
- F1

## Category mapping

- accuracy/F1 on reviewed mappings

## Market counts

Compare derived counts against reviewed ground truth.

## Opportunity model

If labeled outcome data eventually exists:

- precision
- recall
- calibration
- ranking metrics

Do not claim performance without labeled evaluation data.

---

# 54. Baseline Before ML

Build a deterministic baseline first.

Example:

```text
Direct competitor:
same validated category
AND
distance <= selected radius
AND
coordinate confidence >= threshold
```

Future ML should be evaluated against this baseline.

---

# 55. ML/LLM Use

LLMs may assist with:

- activity semantic normalization
- ambiguous descriptions
- category suggestions
- explanation generation

But LLM output must not silently become ground truth.

Store, where LLMs are used:

```text
model_name
model_version
prompt/version
input
output
confidence
validation_status
```

Prefer validated rules/reference data for production-critical deterministic decisions.

---

# 56. No Hallucinated Business Information

Never infer without evidence:

- revenue
- profit
- customer count
- employee count
- market share
- sales volume
- operational status

Business-name semantics alone do not support financial or operational claims.

---

# 57. Data Quality Dashboard

Expose:

```text
UDYAM records analyzed
geographically resolved
geographically unresolved
category-mapped
category-unknown
direct competitors confirmed
possible competitors
demand datasets available
stale demand datasets
```

This allows users to understand evidence quality.

---

# 58. Recommendation Guardrails

If:

```text
geographic coverage < threshold
```

or:

```text
category mapping confidence too low
```

or:

```text
demand data unavailable
```

downgrade confidence or return:

```text
INSUFFICIENT_DATA
```

Do not force a recommendation.

Thresholds should be configurable and empirically validated.

---

# 59. Government Dataset Adapter Architecture

Use adapters:

```python
class GovernmentDatasetAdapter:
    def fetch(...)
    def normalize(...)
    def validate(...)
    def map_geography(...)
    def expose_features(...)
```

Potential adapters:

```text
PopulationAdapter
AgricultureAdapter
InfrastructureAdapter
BankingAdapter
LivestockAdapter
```

Do not tightly couple the intelligence engine to one provider.

---

# 60. Source Registry

Create:

```text
data_sources
```

Suggested fields:

```text
source_id
dataset_name
publisher
url
coverage
geographic_level
time_period
license/access
last_checked
schema_version
notes
```

Every feature must point to its source.

---

# 61. Temporal Refresh Strategy

Define refresh policies per dataset.

Example:

```text
UDYAM:
frequent/daily refresh

Population:
according to official release cycle

Infrastructure:
according to source update cycle
```

Do not claim all datasets are real-time.

---

# 62. Reproducible Analysis Snapshot

Every analysis should reference:

```text
analysis_run_id
data_snapshot
target_location
radius
category ontology version
scoring version
```

A previous result should be reproducible from stored inputs.

---

# 63. Logging

Log:

```text
analysis start/end
target
radius
category
records considered
records excluded
classification counts
data sources
warnings
errors
```

Never log secrets/API keys.

---

# 64. Security

Never expose API keys or credentials to the frontend.

Use environment variables or a secrets manager.

Sanitize user input before constructing API queries.

---

# 65. Performance

Avoid:

```text
one external request per business
```

Prefer:

```text
bulk retrieval
cache
batch classification
precomputed geographic pools
database indexes
```

For repeated category analyses, reuse the market pool.

---

# 66. Cost Control

Do not invoke an LLM/geocoder for every record by default.

Prefer:

```text
deterministic normalization
→ reference lookup
→ rule-based classification
→ expensive processing only for ambiguous cases
```

Use an ambiguity-first architecture.

---

# 67. Ambiguity Queue

Create explicit queues:

```text
ambiguous_activity_records
ambiguous_category_records
ambiguous_geography_records
```

Workflow:

```text
automatic resolution
        ↓
high confidence → accept
        ↓
medium confidence → secondary resolver/review
        ↓
low/unknown → preserve uncertainty
```

A small ambiguous subset must not block the full pipeline.

---

# 68. Market Analysis Workflow

```text
User selects village
        ↓
Target location resolved
        ↓
User selects category
        ↓
User selects radius
        ↓
Retrieve/reuse geographic market pool
        ↓
Filter businesses with sufficient geographic evidence
        ↓
Parse/normalize activities
        ↓
Map categories
        ↓
Classify relevance
        ↓
Calculate supply metrics
        ↓
Load demand/economic features
        ↓
Calculate opportunity indicators
        ↓
Apply validated scoring model
        ↓
Confidence assessment
        ↓
Generate evidence-backed explanation
        ↓
Return API response
```

---

# 69. Failure Modes

Handle:

```text
UDYAM API unavailable
unexpected API response
missing activities
malformed Activities JSON
unknown NIC code
ambiguous category
missing coordinates
conflicting geographic sources
missing demand data
outdated demand data
insufficient market records
```

Each should produce a controlled state.

---

# 70. Graceful Degradation

If demand data is unavailable:

```text
Supply analysis:
AVAILABLE

Demand analysis:
UNAVAILABLE

Opportunity:
INSUFFICIENT_DATA
```

Do not infer demand from competition alone.

---

# 71. Auditability

For every recommendation, a developer should be able to trace:

```text
recommendation
↓
score
↓
indicators
↓
metrics
↓
business records/features
↓
raw datasets
```

This is a core requirement.

---

# 72. SIH Demonstration Flow

Eventually:

```text
1. User selects village
        ↓
2. System identifies target market
        ↓
3. Nearby MSMEs appear
        ↓
4. User selects business category
        ↓
5. System identifies relevant registered businesses
        ↓
6. Competition metrics appear
        ↓
7. Government demand indicators appear
        ↓
8. Opportunity analysis generated
        ↓
9. Evidence + confidence shown
```

The demo should emphasize decision support, not guaranteed prediction.

---

# 73. Example Final User-Facing Output

Conceptually:

```text
DAIRY BUSINESS — PROMISING

Market:
10 km

Observed UDYAM supply:
X registered enterprises

Direct competitors:
Y

Nearest identified competitor:
Z km

Demand signals:
• ...
• ...

Positive factors:
• ...
• ...

Risks:
• ...
• ...

Confidence:
MEDIUM

Why:
The recommendation is driven by observed registered supply,
distance to identified competitors, and independent demand indicators.

Limitations:
UDYAM does not represent every operating business.
Some geographic records remain unresolved.
Demand data may not be current.
```

All values must be calculated from actual sources.

---

# 74. Definition of Done

## Category intelligence

- [ ] Activity JSON parsed
- [ ] NIC mappings validated
- [ ] Category ontology implemented
- [ ] Category confidence implemented
- [ ] Multiple activities supported

## Competition

- [ ] Nearby businesses separated from competitors
- [ ] Direct/related/indirect relevance implemented
- [ ] Relevance confidence implemented
- [ ] Distance-aware metrics implemented
- [ ] Geographic uncertainty propagated

## Demand

- [ ] Government data adapter architecture implemented
- [ ] Geographic joins validated
- [ ] Data years tracked
- [ ] Temporal mismatch handled
- [ ] Missing data handled

## Opportunity

- [ ] Transparent indicators implemented
- [ ] Negative signals implemented
- [ ] Confidence implemented
- [ ] Evidence trail implemented
- [ ] Recommendation guardrails implemented
- [ ] No unsupported claims

## Evaluation

- [ ] Reviewed benchmark created
- [ ] Category metrics measured
- [ ] Competitor relevance metrics measured
- [ ] Market count evaluation performed
- [ ] Cross-state validation performed

---

# 75. Implementation Order for Opus

Do not implement all components simultaneously.

## Stage A — Consume Document 1

Verify the exact output contract from the geographic pipeline.

Do not duplicate geographic logic.

## Stage B — Activity parser

Implement:

```text
Activities JSON
→ normalized activity rows
```

## Stage C — Minimal category ontology

Implement only what is needed for the initial validated tests.

## Stage D — Category mapping

Map NIC/activity → category with confidence/provenance.

## Stage E — Relevance engine

Implement:

```text
DIRECT
RELATED
INDIRECT
NON_RELEVANT
UNKNOWN
```

## Stage F — Competition metrics

Implement:

```text
counts
distance
nearest competitor
zone distribution
concentration
```

## Stage G — Government demand adapters

Add one demand dataset at a time.

Validate geographic joins and temporal coverage before adding another.

## Stage H — Opportunity indicators

Implement transparent indicators.

## Stage I — Baseline opportunity model

Build a transparent rule-based baseline only after inputs are validated.

## Stage J — Explainability

Generate evidence-backed explanations from structured metrics.

## Stage K — Cross-state validation

Test the same engine on:

```text
Telangana
Maharashtra
Third state
```

## Stage L — Evaluation

Measure performance and error modes.

## Stage M — Productionization

Move validated logic into PostgreSQL/PostGIS/backend APIs.

---

# 76. What Opus Must NOT Do

Do not:

- call every nearby UDYAM registration a competitor
- claim UDYAM covers every business
- claim registration proves current operation
- infer revenue/profit/customer count without evidence
- use arbitrary scoring weights
- use competitor scarcity alone as proof of demand
- treat missing data as zero
- silently discard unknown classifications
- fabricate category mappings
- fabricate demand
- use stale government data as current without labeling its year
- mix datasets with incompatible geographic levels without validation
- hide confidence/limitations
- call an opportunity prediction a guaranteed outcome
- introduce ML merely for novelty
- invoke an LLM for every record when deterministic rules can solve it
- make state-specific copies of the intelligence engine
- duplicate the geographic resolver from Document 1
- create unsupported market-share claims
- report accuracy without a ground-truth benchmark
- optimize the intelligence layer specifically for Balanagar

---

# 77. Recommended Repository Structure

Adapt to the existing codebase:

```text
src/
├── intelligence/
│   ├── intents.py
│   ├── ontology.py
│   ├── nic_mapping.py
│   ├── relevance.py
│   ├── competition.py
│   ├── supply.py
│   ├── demand.py
│   ├── opportunity.py
│   ├── confidence.py
│   ├── explainability.py
│   └── scenarios.py
│
├── datasets/
│   ├── registry.py
│   ├── population.py
│   ├── agriculture.py
│   ├── infrastructure.py
│   └── ...
│
└── api/
    └── market_analysis.py
```

---

# 78. Final Architecture

```text
                    USER
                     │
                     ▼
             Target village
                     │
                     ▼
          ┌─────────────────────┐
          │ Geographic Engine   │
          │   DOCUMENT 1        │
          └─────────────────────┘
                     │
                     ▼
              Market Pool
                     │
                     ▼
          ┌─────────────────────┐
          │ Activity/NIC Layer  │
          └─────────────────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ Category Ontology   │
          └─────────────────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ Relevance Engine    │
          └─────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   Supply/Competition       Demand Data
          │                     │
          └──────────┬──────────┘
                     ▼
          ┌─────────────────────┐
          │ Opportunity Engine  │
          └─────────────────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ Confidence +        │
          │ Explainability      │
          └─────────────────────┘
                     │
                     ▼
                    API
                     │
                     ▼
                 Frontend
```

---

# 79. Final Product Principle

The system is a decision-support engine, not an oracle.

It should say:

> Based on the available registered MSME supply, geographic evidence, and independent government demand indicators, this category appears promising/moderate/saturated — with this confidence level and these limitations.

It must never imply:

> This business will definitely succeed.

---

# 80. Final Instruction to Opus 4.6

Implement Document 2 only after understanding and validating Document 1.

Do not duplicate the geographic pipeline.

Do not optimize for one village or one state.

Do not manufacture business categories, demand, competition, or opportunity.

Build the smallest deterministic intelligence baseline first.

Every derived metric must have:

```text
source
→ transformation
→ value
→ confidence
→ limitation
```

Every recommendation must be explainable.

Every uncertainty must remain visible.

Every cross-state test must use the same core intelligence engine.

Prioritize:

```text
EVIDENCE
+
TRACEABILITY
+
GENERALIZATION
+
EXPLAINABILITY
+
GRACEFUL UNCERTAINTY
```

over:

```text
APPARENT PRECISION
+
COMPLEXITY
+
BLACK-BOX SCORING
```

## Immediate milestone

After Document 1 is validated:

```text
1. Parse Activities
2. Build minimal category ontology
3. Map NIC/activity → category
4. Classify relevance
5. Calculate competition metrics
6. Add one government demand dataset
7. Validate geographic joins
8. Build transparent opportunity indicators
9. Build explainability
10. Validate on Telangana + Maharashtra + third state
```

Do not proceed to sophisticated ML until this baseline is measured and understood.
