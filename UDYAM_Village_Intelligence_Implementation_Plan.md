# UDYAM Village Intelligence Engine
## Detailed Phase-by-Phase Implementation Specification for Opus 4.6

> **Purpose:** This document is the implementation handoff for building a scalable, evidence-based village-level MSME/competitor intelligence pipeline using the official UDYAM dataset and additional government/reference geographic data.
>
> **Primary instruction:** Do not optimize the system to make the Balanagar/Medak example look perfect. Medak/Balanagar is a stress-test benchmark used to expose general data-quality problems. Build generic components that work across states and districts, preserve uncertainty explicitly, and measure resolution quality instead of forcing every record into a precise geographic location.

---

# 0. Mission and Non-Negotiable Principles

## Objective

Build a reusable backend pipeline that can answer:

> Given an Indian village/locality and a proposed business category, identify existing MSMEs in the surrounding market, estimate competitive density/saturation, and eventually combine this with demand/economic indicators to produce an opportunity assessment.

The current implementation phase is **geographic intelligence only**.

**Do not implement the final opportunity score yet.**

## Core principles

The system must distinguish:

1. What the UDYAM data actually says.
2. What is inferred from the address.
3. What an external geographic source says.
4. What remains uncertain.

Never silently convert an uncertain inference into a fact.

---

# PHASE 1 — Freeze the Known UDYAM API Contract

## 1.1 Official dataset

Use the official data.gov.in resource:

**List of MSME Registered Units under UDYAM**

Resource ID:

`8b68ae56-84cf-4728-a0a6-1be11028dea7`

API endpoint:

`https://api.data.gov.in/resource/8b68ae56-84cf-4728-a0a6-1be11028dea7`

Known validated fields:

- `LG_ST_Code`
- `State`
- `LG_DT_Code`
- `District`
- `Pincode`
- `RegistrationDate`
- `EnterpriseName`
- `CommunicationAddress`
- `Activities`

Do not assume additional fields exist.

If the API schema changes, detect and report the change rather than silently breaking.

---

# PHASE 2 — Build a Robust UDYAM Retrieval Layer

Create a reusable `UdyamClient`.

Responsibilities:

- API authentication
- request construction
- filtering
- pagination
- retries
- rate limiting
- response validation
- caching
- diagnostics

Suggested interface:

```python
client.fetch_by_district(
    state="TELANGANA",
    district="MEDAK"
)

client.fetch_by_pincode(
    pincode="502117"
)

client.fetch_by_date(
    registration_date="2026-09-09"
)
```

## Geographic retrieval strategy

For a village query:

### Primary

Use:

`State + District`

and, where useful:

`Pincode`

### Secondary

Use additional filters only after validating their behavior against the current API.

### Never

Download the entire national UDYAM dataset merely to answer one village query.

The validated experiments showed that unrestricted deep offset pagination is not a reliable foundation for a national mirror.

## Pagination safeguards

Track:

- offset
- limit
- API-reported total
- records received
- pages fetched

Stop when:

- records received >= reported total, OR
- the API returns fewer records than requested.

Detect:

- repeated page content
- duplicate records
- unstable offsets
- HTTP errors
- rate limiting
- API totals changing during retrieval

Do not assume the live API total is an immutable snapshot.

## Cache raw API responses

Persist raw responses where practical.

Example structure:

```text
data/raw/udyam/
    YYYY/
        MM/
            DD/
                ...
```

Store retrieval metadata such as:

```json
{
  "resource_id": "...",
  "retrieved_at": "...",
  "state": "...",
  "district": "...",
  "pincode": "...",
  "offset": 0,
  "limit": 10000,
  "api_total": 33281
}
```

---

# PHASE 3 — Normalize UDYAM Records

Create a canonical internal schema.

Suggested fields:

- `enterprise_name_raw`
- `enterprise_name_normalized`
- `state_raw`
- `state_normalized`
- `district_raw`
- `district_normalized`
- `pincode_raw`
- `pincode_normalized`
- `registration_date_raw`
- `registration_date`
- `communication_address_raw`
- `communication_address_normalized`
- `activities_raw`
- `activities_parsed`

**Never overwrite raw government values.**

Retain raw and normalized representations side by side.

---

# PHASE 4 — Deterministic Record Identity

The validated UDYAM fields do not expose an obvious government-issued unique enterprise identifier.

Create a **local deterministic record fingerprint**.

Suggested canonical inputs:

- EnterpriseName
- CommunicationAddress
- Pincode
- RegistrationDate
- State
- District

Normalize first, then hash.

Example:

```python
record_fingerprint = sha256(
    canonical_string.encode()
).hexdigest()
```

Call this:

- `record_fingerprint`, or
- `local_record_hash`

**Never call it a UDYAM ID.**

It is an internal deduplication/change-detection mechanism.

---

# PHASE 5 — Address Normalization

Create:

```python
normalize_address()
```

Operations may include:

- uppercase/lowercase normalization
- whitespace normalization
- punctuation normalization
- repeated-space removal
- separator normalization
- Unicode normalization
- safe abbreviation normalization
- preservation of meaningful geographic tokens

Example:

```text
"3-26/3, Rajpally, Medak, Telangana"
```

may normalize to a consistent representation such as:

```text
3 26 3 RAJPALLY MEDAK TELANGANA
```

However:

**Do not aggressively remove geographic information.**

For example:

`S KONDAPUR`

must not automatically become:

`KONDAPUR`

because similar names can represent distinct places.

---

# PHASE 6 — Locality Extraction

This is the major scalability improvement over the Medak prototype.

Do **not** create giant hardcoded state/district-specific alias dictionaries.

Create:

```python
extract_geographic_candidates(address)
```

Return multiple candidate entities where appropriate.

Suggested entity types:

- village
- hamlet
- ward
- town
- taluka
- tehsil
- mandal
- block
- gram_panchayat
- post_office
- district
- state
- pincode

Example:

```json
{
  "candidates": [
    {
      "text": "RAJPALLY",
      "type": "LOCALITY",
      "position": 12,
      "method": "gazetteer_match"
    }
  ]
}
```

Do not immediately collapse multiple candidates into one geographic truth.

---

# PHASE 7 — Geographic Reference Database

Create a generic:

`locality_master`

Suggested schema:

```text
locality_id
state
district
subdistrict
block
taluka
mandal
gram_panchayat
village
normalized_name

latitude
longitude

source
source_url
source_record_id

coordinate_confidence
administrative_confidence

valid_from
valid_to
```

## Source hierarchy

Prefer, in order:

1. Government administrative/village datasets
2. Official district/state sources
3. Authoritative geographic datasets
4. OpenStreetMap/geographic databases
5. Geocoding services
6. Search-engine-derived secondary sources

Do not treat all sources as equivalent.

---

# PHASE 8 — Source Provenance

Every coordinate must have:

- `coordinate_source`
- `coordinate_source_url`
- `coordinate_confidence`

Example:

```text
source = official_district_dataset
confidence = HIGH
```

or:

```text
source = OSM-derived
confidence = MEDIUM
```

or:

```text
source = geocoder
confidence = LOW
```

If multiple sources disagree:

**Do not automatically average them.**

Create a conflict record and resolve only with evidence.

---

# PHASE 9 — Separate Locality Confidence from Coordinate Confidence

This is mandatory.

Do not use a single `geo_confidence` field.

Use:

- `locality_confidence`
- `coordinate_confidence`

Example:

```text
Locality:
S KONDAPUR
confidence: HIGH

Coordinate:
unknown
confidence: UNKNOWN
```

This is a valid state.

Another:

```text
Locality:
BALANAGAR
confidence: HIGH

Coordinate:
17.9276, 78.2344
confidence: HIGH
```

---

# PHASE 10 — Geographic Resolution Algorithm

For each UDYAM business:

### Step 1

Extract geographic candidates from the address.

### Step 2

Match candidates against the locality master.

### Step 3

Use administrative hierarchy to disambiguate.

For example:

```text
BALANAGAR
MEDAK
TELANGANA
```

is stronger than:

```text
BALANAGAR
```

alone.

### Step 4

Use PIN as a supporting signal.

**Critical rule: PIN is not equivalent to village.**

One PIN may cover multiple villages/localities.

Therefore:

```text
PIN → candidate geographic set
```

not:

```text
PIN → exact village
```

### Step 5

Assign locality and coordinate confidence separately.

---

# PHASE 11 — Confidence Model

Start with explicit deterministic rules, not an opaque ML model.

Suggested levels:

## HIGH

Exact locality identified and coordinate supported by an authoritative/verified source.

## MEDIUM

Locality identified but coordinate comes from a weaker or ambiguous source.

## LOW

Only broader geographic information is available.

Example:

```text
District known
Village unknown
```

## UNKNOWN

No defensible geographic assignment.

---

# PHASE 12 — Never Fabricate Coordinates

This is a hard requirement.

If:

```text
locality = S KONDAPUR
coordinate = unresolved
```

then:

```text
lat = NULL
lon = NULL
```

Do not insert a guessed coordinate merely to make map/radius output complete.

Use:

`UNMAPPED`

when precise radius classification is impossible.

---

# PHASE 13 — Target Location Model

Create a reusable `TargetLocation` model.

Fields:

- name
- state
- district
- subdistrict/mandal
- latitude
- longitude
- source
- source_url
- confidence

The target village itself requires provenance.

---

# PHASE 14 — Distance Engine

Initially use Haversine distance.

Inputs:

- target latitude
- target longitude
- business latitude
- business longitude

Output:

- `distance_km`

If coordinates are missing:

`distance_km = NULL`

Do not calculate from incomplete coordinates.

---

# PHASE 15 — Market Zones

Initial configurable zones:

```text
CORE_5KM
NEARBY_10KM
OUTSIDE_10KM
UNMAPPED
```

Rules:

```text
distance <= 5
    CORE_5KM

5 < distance <= 10
    NEARBY_10KM

distance > 10
    OUTSIDE_10KM

coordinate unavailable
    UNMAPPED
```

The radius must remain configurable.

Do not permanently hardcode 5 km/10 km into the architecture.

---

# PHASE 16 — Do Not Call Radius Counts "Competitors" Yet

A business within 5 km is only:

`nearby_business`

It is not automatically a competitor.

A business becomes a potential competitor only after business-category relevance is established.

Pipeline:

```text
nearby businesses
        ↓
relevant businesses
        ↓
potential competitors
```

This distinction must be maintained in the data model and UI.

---

# PHASE 17 — Activity Parsing

`Activities` is a JSON-encoded string and may contain multiple activity records.

Create:

```python
parse_activities()
```

Normalize into rows such as:

```text
record_fingerprint
nic_code
nic_description_raw
activity_description
```

One enterprise may therefore produce multiple activity rows.

Do not confuse:

- enterprise count
- activity count

---

# PHASE 18 — NIC/Activity Validation

Some observed activity labels in the Medak experiment appeared semantically suspicious.

Therefore:

**Do not blindly trust raw activity descriptions for business intelligence.**

Store:

```text
nic_code
raw_description
normalized_category
category_confidence
validation_source
```

If the semantic mapping is uncertain:

```text
normalized_category = UNKNOWN
```

Do not invent a category from a suspicious label.

---

# PHASE 19 — Business Category Ontology

Create a separate category layer.

Potential initial categories include:

- FOOD_RETAIL
- GENERAL_RETAIL
- TAILORING
- DAIRY
- POULTRY
- GOAT_SHEEP
- TRANSPORT
- CONSTRUCTION
- MANUFACTURING
- SERVICES
- AGRICULTURE_SUPPORT

However:

**Do not freeze the final ontology before inspecting activity distributions across multiple districts/states.**

The ontology should be data-driven and extensible.

---

# PHASE 20 — Category Mapping

Use a hierarchy:

```text
NIC code
    ↓
official NIC meaning
    ↓
normalized business category
    ↓
user-selected business intent
```

Retain the original NIC information.

Do not replace official/raw values with our categories.

---

# PHASE 21 — Geographic + Category Intersection

Only after geographic resolution and category mapping:

```text
businesses within 5 km
AND
same/relevant category
```

Example structure:

```text
Target:
DAIRY

5 km:
10 nearby MSMEs

Dairy-related:
3

Potential direct competitors:
2
```

The numbers must always be calculated from actual data.

---

# PHASE 22 — Market Saturation

Do not label a simple business count as market saturation.

Potential later metric:

```text
category_business_count / market_population
```

But this requires reliable population data.

Before population integration, report descriptive metrics such as:

- category count
- category share of local MSMEs
- nearest relevant business distance

Do not manufacture a saturation score.

---

# PHASE 23 — Cross-State Evaluation

The exact same codebase must be tested across multiple geographic contexts.

## Benchmark A

```text
TELANGANA
MEDAK
BALANAGAR
```

This is the known stress-test benchmark.

## Benchmark B

Maharashtra:

- one rural district
- one village
- defensible government geographic reference
- sufficient UDYAM candidate data

Do not manually create a separate Maharashtra pipeline.

## Benchmark C

A third state with different geographic/address patterns.

Configuration may change; core code should not.

---

# PHASE 24 — Generalization Metrics

For each benchmark report:

```text
total UDYAM records
unique normalized localities
localities resolved
localities unresolved
records with coordinates
records without coordinates

HIGH locality confidence
MEDIUM locality confidence
LOW locality confidence
UNKNOWN

HIGH coordinate confidence
MEDIUM coordinate confidence
LOW coordinate confidence
UNKNOWN

CORE_5KM
NEARBY_10KM
OUTSIDE_10KM
UNMAPPED
```

Also measure:

- API requests
- execution time
- cache hits
- manual corrections

---

# PHASE 25 — Manual Intervention Metric

Track every manual correction.

Example:

```text
manual_resolution_count = 7
```

Then:

```text
manual_resolution_rate =
    manual_resolution_count / unique_localities
```

The goal is not necessarily zero manual intervention.

The goal is:

> The system should degrade gracefully instead of requiring manual investigation of every locality.

---

# PHASE 26 — Evaluation Against Ground Truth

For a representative subset, manually establish correct locality labels.

Then calculate:

- precision
- recall
- F1

For coordinate assignment, measure:

- correct locality coordinate
- incorrect coordinate
- unresolved

Do not report an accuracy percentage without an actual ground-truth sample.

---

# PHASE 27 — Error Taxonomy

Every unresolved or incorrect result should have an explicit reason.

Suggested categories:

```text
UNKNOWN_LOCALITY
MULTIPLE_LOCALITY_MATCHES
PIN_MULTIPLE_VILLAGES
GEOCODER_AMBIGUITY
MISSING_COORDINATE
CONFLICTING_SOURCES
ADDRESS_TOO_SPARSE
ADMINISTRATIVE_MISMATCH
PARSING_FAILURE
API_DATA_QUALITY
```

This will make debugging and SIH documentation much stronger.

---

# PHASE 28 — Observability

Every pipeline run should generate a diagnostic report.

Example structure:

```text
========================================
GEOGRAPHIC RESOLUTION REPORT
========================================

Target:
Balanagar, Medak, Telangana

UDYAM records:
381

Unique localities:
23

Localities resolved:
18
Unresolved:
5

Coordinate confidence:
HIGH      ...
MEDIUM    ...
LOW       ...
UNKNOWN   ...

Market:
<= 5 km       ...
5–10 km       ...
> 10 km       ...
UNMAPPED      ...
```

All values must be calculated.

Never hardcode benchmark numbers.

---

# PHASE 29 — Testing Strategy

Create unit tests for:

## Address normalization

Test known spelling variations, but only normalize them when supported by the locality master/context.

## Ambiguous locality

For example:

```text
KONDAPUR
```

must not automatically resolve to an arbitrary location.

## PIN ambiguity

A PIN covering multiple villages must remain a candidate pool, not a village identity.

## Missing coordinate

Must produce:

```text
UNMAPPED
```

## Boundary tests

Test:

```text
4.999 km
5.000 km
5.001 km

9.999 km
10.000 km
10.001 km
```

## Duplicate records

Same fingerprint must be detected.

## Multiple activities

One enterprise with multiple activities remains one enterprise and multiple activity rows.

---

# PHASE 30 — Integration Tests

Run the full pipeline for:

### Test A
Medak/Balanagar.

### Test B
Maharashtra rural village.

### Test C
Third-state rural village.

Pipeline:

```text
retrieve
→ normalize
→ resolve
→ coordinate
→ distance
→ classify
→ parse activities
→ generate report
```

Do not introduce state-specific code between tests unless the external source genuinely requires a configurable adapter.

---

# PHASE 31 — Database Architecture

Once notebook validation passes, move to PostgreSQL/PostGIS.

Suggested tables:

```text
udyam_enterprises
udyam_activities
locality_master
locality_aliases
locality_sources
geographic_resolution
target_locations
pipeline_runs
resolution_errors
```

PostGIS should eventually handle spatial queries.

---

# PHASE 32 — Spatial Query Architecture

Eventually use:

```text
target village coordinate
        ↓
PostGIS ST_DWithin
        ↓
businesses within radius
```

This avoids repeatedly recalculating distances for the same spatial queries.

Use spatial indexes.

---

# PHASE 33 — API Layer

After backend validation, expose a service such as:

```http
POST /market-analysis
```

Example request:

```json
{
  "state": "TELANGANA",
  "district": "MEDAK",
  "village": "BALANAGAR",
  "radius_km": 10,
  "business_category": "DAIRY"
}
```

Response should include:

```json
{
  "target": {},
  "geographic_quality": {},
  "market_summary": {},
  "business_categories": [],
  "competitors": [],
  "limitations": []
}
```

The actual response schema can be refined after the backend evaluation.

---

# PHASE 34 — Frontend Integration

Only after backend validation.

UI should show:

- target village
- state/district
- configurable market radius
- business/category distribution
- map
- confidence indicators
- unresolved/missing-data indicators

Do not display uncertain businesses as precise map pins without representing the uncertainty.

---

# PHASE 35 — Government Data Fusion

Only after the UDYAM geographic layer is stable.

Potential layers:

```text
UDYAM
+
Population
+
Agriculture
+
Infrastructure
+
Banking
+
Road/connectivity
+
Local economic indicators
```

Every additional dataset must undergo:

```text
source verification
→ schema validation
→ geographic key matching
→ temporal alignment
→ provenance
→ missing-value analysis
```

Do not add datasets merely because they appear relevant.

---

# PHASE 36 — Opportunity Scoring

Do this last.

Do not begin with an arbitrary formula such as:

```text
Opportunity = 0.4 demand + 0.3 competition + ...
```

First establish measurable variables.

Potential variables:

- population
- population growth
- existing category count
- category density
- nearest competitor distance
- agricultural activity
- economic proxies
- infrastructure
- market accessibility
- other validated demand/supply indicators

Only then design and justify the scoring model.

---

# PHASE 37 — Required Limitations

The system documentation must explicitly state:

## UDYAM is not the complete universe of businesses

The result represents registered UDYAM businesses identifiable through the dataset, not every business physically operating in a market.

## Registration does not automatically prove current operating status

A registration record alone does not establish current operational activity.

## Address does not equal exact operating coordinates

Communication addresses can be incomplete or ambiguous.

## NIC/activity is not perfect semantic classification

Raw activity data requires validation before high-confidence category analysis.

## PIN is not equivalent to village

A PIN may cover multiple villages/localities.

## Radius is an analytical approximation

A 5 km/10 km radius is not necessarily the true economic/customer catchment.

---

# PHASE 38 — What Opus Must NOT Do

Do not:

- download the entire national UDYAM dataset
- create a separate custom pipeline for every state
- create hundreds of manually curated village aliases
- assume PIN uniquely identifies a village
- trust one geocoder blindly
- fabricate missing coordinates
- call every nearby MSME a competitor
- interpret suspicious NIC descriptions without validation
- silently discard unresolved records
- overwrite raw government data
- call the local fingerprint a government identifier
- present illustrative values as measured results
- build the opportunity score before validating geography/category data
- add external datasets without recording provenance
- replace the official UDYAM source merely because another source is easier
- tune the architecture specifically to Balanagar
- hide uncertainty merely to increase apparent coverage
- silently average conflicting coordinates
- treat secondary-source coordinates as government-certified truth

---

# PHASE 39 — Recommended Repository Structure

Adapt this to the existing codebase rather than blindly creating a parallel application.

```text
project/
│
├── src/
│   ├── udyam/
│   │   ├── client.py
│   │   ├── pagination.py
│   │   ├── models.py
│   │   └── cache.py
│   │
│   ├── geography/
│   │   ├── normalization.py
│   │   ├── extraction.py
│   │   ├── resolver.py
│   │   ├── confidence.py
│   │   ├── distance.py
│   │   └── gazetteer.py
│   │
│   ├── activities/
│   │   ├── parser.py
│   │   ├── nic_mapper.py
│   │   └── categories.py
│   │
│   ├── analysis/
│   │   ├── market.py
│   │   └── competitors.py
│   │
│   └── evaluation/
│       ├── metrics.py
│       └── reports.py
│
├── data/
│   ├── raw/
│   ├── reference/
│   ├── processed/
│   └── cache/
│
├── tests/
│   ├── test_udyam.py
│   ├── test_normalization.py
│   ├── test_resolution.py
│   ├── test_distance.py
│   └── test_integration.py
│
├── notebooks/
│   └── geographic_validation.ipynb
│
└── docs/
    ├── data_sources.md
    ├── architecture.md
    └── limitations.md
```

---

# PHASE 40 — Definition of Done

Do not move to the next stage until the following are true.

## Data

- [ ] Official UDYAM API integrated
- [ ] Raw data preserved
- [ ] Pagination validated
- [ ] API caching implemented
- [ ] Record fingerprint implemented

## Geography

- [ ] Address normalization implemented
- [ ] Generic locality extraction implemented
- [ ] Geographic master implemented
- [ ] Source provenance implemented
- [ ] Locality confidence implemented
- [ ] Coordinate confidence implemented
- [ ] Ambiguity handling implemented
- [ ] Missing coordinates handled safely
- [ ] PIN/village distinction enforced
- [ ] Distance engine implemented
- [ ] Configurable market radius implemented

## Activities

- [ ] Activities JSON parsed
- [ ] Multiple activities supported
- [ ] Raw NIC information preserved
- [ ] Category mapping separated from raw NIC

## Validation

- [ ] Medak benchmark passes
- [ ] Maharashtra benchmark passes
- [ ] Third-state benchmark passes
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual intervention measured
- [ ] Error taxonomy generated
- [ ] No fabricated coordinates
- [ ] No unsupported claims

---

# PHASE 41 — Exact Implementation Order

Do not implement everything simultaneously.

```text
PHASE 1
Existing codebase audit
        ↓
PHASE 2
UDYAM client + caching
        ↓
PHASE 3
Canonical data model
        ↓
PHASE 4
Address normalization
        ↓
PHASE 5
Generic locality extraction
        ↓
PHASE 6
Geographic master + provenance
        ↓
PHASE 7
Resolution + confidence engine
        ↓
PHASE 8
Distance + market zones
        ↓
PHASE 9
Activity/NIC parser
        ↓
PHASE 10
Medak regression benchmark
        ↓
PHASE 11
Maharashtra cross-state benchmark
        ↓
PHASE 12
Third-state benchmark
        ↓
PHASE 13
Evaluation + error analysis
        ↓
PHASE 14
PostgreSQL/PostGIS productionization
        ↓
PHASE 15
API
        ↓
PHASE 16
Frontend
        ↓
PHASE 17
Additional government datasets
        ↓
PHASE 18
Opportunity intelligence
```

---

# PHASE 42 — How Opus Must Work

## Step 1 — Audit first

Before modifying code:

- inspect the existing repository
- identify existing UDYAM/API code
- identify current data models
- identify existing notebooks/scripts
- identify current dependencies
- identify existing frontend/backend structure
- identify what can be reused
- identify what should be replaced
- identify assumptions already embedded in the code

Do not create duplicate implementations without reason.

## Step 2 — Implement only Phases 1–8 initially

Build:

- UDYAM client
- caching
- canonical records
- normalization
- locality extraction
- geographic master integration
- provenance
- confidence
- distance
- market zones

## Step 3 — Run Medak regression

Use the existing Medak/Balanagar experiment as a benchmark.

Compare:

- record counts
- locality resolution
- coordinate resolution
- confidence distribution
- 5 km count
- 10 km count
- unmapped count
- errors

Do not force the new engine to reproduce every manually resolved Medak record if that requires non-generalizable special cases.

## Step 4 — Fix generic problems

If Medak exposes a problem, improve the generic algorithm.

Do not create:

```text
if district == "MEDAK":
    special_case()
```

unless there is a documented external-data requirement.

## Step 5 — Cross-state test

Run the unchanged core engine against Maharashtra.

Then a third state.

## Step 6 — Only after cross-state validation

Proceed to activity/category intelligence.

---

# Final Architectural Principle

The final system should optimize for:

```text
CORRECTNESS
+
TRACEABILITY
+
GENERALIZATION
+
GRACEFUL UNCERTAINTY
+
SCALABILITY
```

not:

```text
100% apparent geographic coverage
```

A result of:

```text
85% confidently resolved
15% explicitly unresolved
```

is preferable to:

```text
100% resolved using guessed coordinates
```

because the former is auditable and defensible.

---

# Final Instruction to Opus 4.6

Build this as a **generic geographic intelligence engine**, not a Balanagar-specific demonstration.

Use the existing Medak/Balanagar work as a regression/stress-test dataset.

Do not spend excessive implementation effort manually perfecting individual Medak localities unless the resulting solution generalizes to other districts/states.

Every inference must be traceable to:

- raw UDYAM data,
- a geographic reference source,
- a deterministic transformation,
- or an explicitly documented inference rule.

When evidence is insufficient, preserve `UNKNOWN`/`UNMAPPED`.

Never fabricate precision.

Do not proceed to the final opportunity-scoring layer until the geographic and category layers have been validated across multiple states.

**First milestone:** a working, generic geographic engine that can take:

```text
state
district
target village
target coordinates
radius
```

and produce a reproducible, provenance-aware market candidate dataset with confidence scores.

**Second milestone:** prove that the same implementation works on Medak + Maharashtra + a third state without state-specific hardcoded logic.

**Only then:** proceed to business-category intelligence and opportunity analysis.
