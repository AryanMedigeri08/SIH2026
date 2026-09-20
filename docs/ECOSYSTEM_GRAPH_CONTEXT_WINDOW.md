# CONTEXT WINDOW: INTERACTIVE BUSINESS ECOSYSTEM INTELLIGENCE ENGINE

> **Purpose**: This document is a complete, self-contained context specification for LLMs (Claude, GPT, etc.) and engineering contributors. It records the entire problem evolution, roadblocks faced, datasets evaluated, architectural decisions made, and the final technical & UX specification for the **Interactive Business Ecosystem Intelligence Map & Graph Component** in project **Udyam Saathi (SIH 2026)**.

---

## Table of Contents
1. [Project Overview & Core Objective](#1-project-overview--core-objective)
2. [Guiding Principles & Non-Negotiable Constraints](#2-guiding-principles--non-negotiable-constraints)
3. [The Problem Evolution & Roadblocks Encountered (Issues Faced)](#3-the-problem-evolution--roadblocks-encountered-issues-faced)
4. [Datasets Evaluated & Breakthrough Ideas](#4-datasets-evaluated--breakthrough-ideas)
5. [The Hybrid Data Architecture: Micro-Entities + Macro-Demographics](#5-the-hybrid-data-architecture-micro-entities--macro-demographics)
6. [Component Architecture & Visualization Layers](#6-component-architecture--visualization-layers)
7. [Interaction & State Management Model](#7-interaction--state-management-model)
8. [Bi-Modal Experience: Beneficiary vs. Banker View](#8-bi-modal-experience-beneficiary-vs-banker-view)
9. [Data Requirements & Schema Mapping Matrix](#9-data-requirements--schema-mapping-matrix)
10. [6-Phase Implementation Roadmap](#10-6-phase-implementation-roadmap)
11. [Ready-to-Use Claude Context Injection Header](#11-ready-to-use-claude-context-injection-header)

---

## 1. Project Overview & Core Objective

### What is Udyam Saathi?
**Udyam Saathi** is an AI-powered credit underwriting, financial feasibility, and project appraisal platform designed for rural and semi-urban Indian micro-entrepreneurs and bank loan appraisal officers. It bridges the gap between grassroots loan applicants seeking government schemes (PMEGP, PMFME, MUDRA, Stand-Up India) and credit officers underwriting loans.

### What is the Ecosystem Intelligence Component?
The user requires an **Interactive Business Ecosystem Intelligence Map/Graph** embedded directly into the platform. 

**Primary Goal**: Turn rural enterprise and business data into an **interactive analytical decision-making workspace**, rather than a static map with passive markers. It models rural economies as dynamic, interconnected webs of competitors, supply chains, and market opportunities within **5 km and 10 km operational catchments**.

---

## 2. Guiding Principles & Non-Negotiable Constraints

1. **Analytical, Never Decorative**:
   * The visualization must *never feel static*.
   * Avoid decorative SVG animations, fake lines, or unclickable markers.
   * Every meaningful visual element (nodes, segments, clusters, legend chips, buffer rings) must trigger state changes and data drill-downs.
2. **Strict Data Integrity (Zero Hallucination / Zero Fake Data)**:
   * Do **NOT** fabricate synthetic business entities or fake relationships.
   * Clearly separate:
     * **Directly Available**: Real fields from registered datasets.
     * **Mathematically Derived**: Deterministic formulas (Haversine distances, HHI indices, decadal CAGRs).
     * **External Integrations Needed**: Fields requiring third-party CBS/GSTN integration.
3. **Bi-Modal Persona Separation**:
   * **Beneficiary View**: Simple, actionable, zero banking jargon, focused on walking radius competition and nearby buyers/suppliers.
   * **Banker View**: Deep credit appraisal workspace with Herfindahl-Hirschman Index (HHI) saturation gauges, decadal sectoral CAGR, cannibalization warnings, and ego-network drill-downs.
4. **Code Safety**:
   * Strictly do not modify application code until explicitly requested by the user.

---

## 3. The Problem Evolution & Roadblocks Encountered (Issues Faced)

Throughout the architectural discovery, several critical real-world challenges were identified and addressed:

### Roadblock 1: The MSME Microdata Privacy Wall
* **Issue**: The Indian Government (Ministry of MSME, Udyam Registration Portal) publishes enterprise statistics publicly **strictly aggregated at the State and District level**. Under the *Collection of Statistics Act (2008)*, individual micro-unit names, door numbers, and exact GPS coordinates from National Economic Censuses are legally anonymized to protect business privacy.
* **Impact**: We could not query a public API for "all fabrication shops on Main Street in Village Nimbut" using standard government aggregate dashboards.

### Roadblock 2: The Village-Level Granularity Dilemma
* **Issue**: District-level statistics (e.g., "85,000 MSMEs in Pune District") are useless for a rural borrower. A borrower operates within a hyper-local **5 km walking/cycle catchment** or a **10 km haat/market catchment**.
* **Impact**: We needed a dataset or mechanism with granular village-level economic counts (`pc11_village_id` or pincode level), not broad district summaries.

### Roadblock 3: The Danger of the "Decorative Map"
* **Issue**: Most fintech apps implement maps as passive eye candy—showing pins on Leaflet/Google Maps where clicking a pin just displays a name.
* **Impact**: The user explicitly rejected this: *"I do not want a static map or a decorative graph... It must allow users to explore the underlying data, change perspectives, isolate segments, inspect individual businesses, identify patterns, and derive useful insights."*

### Roadblock 4: The Cognitive Dichotomy Between Personas
* **Issue**: Showing complex topological network graphs, Herfindahl-Hirschman saturation metrics, or input-output matrices to a rural dairy farmer intimidates the applicant. Conversely, showing a banker only a green "Good Location" badge lacks the empirical rigor needed to sanction a ₹10 Lakh loan.
* **Impact**: Required strict state-driven dual-persona rendering from the exact same underlying catchment data.

---

## 4. Datasets Evaluated & Breakthrough Ideas

During exploration, four distinct technical approaches were investigated:

### Approach A: Spatial Gravity Downscaling (Huff's Model)
* **Concept**: Take district-level MSME counts and downscale them into 5 km and 10 km radial buffers around a village using Census 2011 village population weights.
* **Evaluation**: Methodologically sound for statistical estimation, but does not provide individual enterprise nodes or exact business identities.

### Approach B: OpenStreetMap (OSM / Overpass API) POI Extraction
* **Concept**: Query OpenStreetMap for real point-level features (`shop=dairy`, `craft=metal_construction`, `amenity=bank`).
* **Evaluation**: Provides real GPS coordinates and entity names, but coverage is highly uneven in India (dense in Tier 1/2 cities, but sparse in deep rural villages).

### Approach C: The SHRUG Dataset (Novosad & Asher / Development Data Lab)
* **Concept**: Socioeconomic High-resolution Rural-Urban Geographic Platform for India.
* **Data Available**:
  * Merges MoSPI's **6th Economic Census (EC13)**, **5th Economic Census (EC05)**, and **Population Census 2011 (PC11)** down to 600,000+ villages (`shrid`).
  * Exact village-level enterprise counts categorized by **3-digit NIC/SHRIC sector codes** (e.g., NIC 105 Dairy, NIC 251 Metal Fabrication, NIC 106 Grain Milling).
  * Employment brackets (own-account, 1–5 micro, 6–9 small, 10+ medium).
  * Infrastructure attributes: Electricity access of units, female ownership, SC/ST ownership.
  * Exact village centroid latitude and longitude.
* **Limitation**: MoSPI EC13 within SHRUG is legally anonymized—it gives exact enterprise counts and scales per village, but not proprietary shop names.

### Approach D: The Enterprise Registration API Breakthrough (The "Golden Gem")
* **Concept**: The user secured access to an API returning 7 specific real-world columns:
  1. **`State`**: State name (e.g., Maharashtra)
  2. **`District`**: District name (e.g., Pune)
  3. **`Pincode`**: 6-digit Postal PIN Code (e.g., 412205)
  4. **`RegistrationDate`**: Exact date of registration (e.g., 2021-06-15)
  5. **`EnterpriseName`**: Real business identity (e.g., "Mauli Agro Fabrication")
  6. **`CommunicationAddress`**: Hyper-local address (village, taluka, gat/survey no.)
  7. **`Activities`**: Operational activities & sector classification (NIC descriptions)

---

## 5. The Hybrid Data Architecture: Micro-Entities + Macro-Demographics

The breakthrough insight is to unite **Approach C (SHRUG)** and **Approach D (Enterprise API)** into a complementary two-tier architecture:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       TIER 1: MICRO-ENTERPRISE LAYER                    │
│                      (Supplied by the 7-Column API)                     │
│  • Real Enterprise Names ('EnterpriseName')                             │
│  • Exact Registration Vintage & Timeline ('RegistrationDate')           │
│  • Operational Activity Classification ('Activities' -> NIC 3-Digit)    │
│  • Spatial Anchor via Pincode Directory Centroids & Village Addresses    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ Joins via State + District + Pincode
┌────────────────────────────────────▼────────────────────────────────────┐
│                      TIER 2: MACRO-ECOSYSTEM BACKBONE                   │
│                       (Supplied by SHRUG + Census 2011)                 │
│  • Village Centroid GPS Coordinates ('shrug_spatial' / 'shrid')          │
│  • Total Informal + Formal Enterprise Baseline (MoSPI EC13 counts)      │
│  • 10-Year Decadal Sectoral Growth Trajectory (EC05 -> EC13 CAGR)       │
│  • Local Electrification Rates & Rural Infrastructure Scores (613 APIs) │
│  • Population & Catchment TAM (Census 2011 PC11 Village Demographics)  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Component Architecture & Visualization Layers

### 6.1 The 5 Visual Layers
1. **Layer 1 — Spatial Catchment Rings**: Concentric 5 km (primary hyper-local catchment) and 10 km (secondary transport catchment) geodesic buffer polygons centered on the applicant's location.
2. **Layer 2 — Business Nodes**:
   * Glyphs: Circle = Micro (1–5 workers), Square = Small (6–9 workers), Diamond = Medium (10+ workers).
   * Domain Color-Coded:
     * 🟢 **Dairy & Allied**: `#10B981`
     * 🟠 **Fabrication & Engineering**: `#F59E0B`
     * 🔵 **Agro-Processing & Milling**: `#0284C7`
     * 🟣 **Retail & Kirana**: `#6366F1`
     * ⚪ **Services & Maintenance**: `#8B5CF6`
3. **Layer 3 — Economic Segments (Edges)**:
   * **Competitor Links (Red/Orange)**: Connects enterprises sharing identical activities/sectors within the 5 km/10 km radius. Stroke weight is inversely proportional to distance (closer = thicker, higher competitive friction).
   * **Supply-Chain Links (Teal/Cyan)**: Connects complementary activities (e.g., Raw Milk Rearing $\leftrightarrow$ Chilling Plant $\leftrightarrow$ Retail Dairy). Dashed with directional indicators.
4. **Layer 4 — Saturation & Density Heatmap**: Dynamic Kernel Density Estimation (KDE) surface representing business concentration in the filtered sector.
5. **Layer 5 — Opportunity & White-Space Overlay**: Highlights underserved areas (high population + electricity access, but low competitor count).

### 6.2 Dual-Projection Modes
The component can smoothly transition between two projection styles:
* **Geographic Mode**: Nodes rendered on real GPS basemaps (Leaflet Canvas). Best for physical transport friction, road distance, and boundary analysis.
* **Force-Directed Topological Mode**: Nodes positioned using physics forces (D3 force layout / WebGL). Closely related competitors and supply-chain partners cluster together regardless of geographic distance. Best for detecting market cliques and ecosystem dependence.

### 6.3 Temporal Catchment Scrubber (Using `RegistrationDate`)
* Interactive timeline scrubber (from 2018 $\to$ Present).
* Visualizes how market competition grew year-by-year within the 5 km radius.
* Computes **Registration Velocity**: Highlights sudden acceleration in competitor registrations (saturation risk warning).

---

## 7. Interaction & State Management Model

### Interaction Matrix
* **Click Node**: Dims unrelated nodes to 15% opacity, highlights 1st-degree competitor & supplier edges, and opens the `<EnterpriseDetailDrawer />`.
* **Click Segment**: Shows a floating edge tooltip quantifying the relationship (e.g., *"Direct Competitor: 2.8 km away, Registered Nov 2021"*).
* **Click Dynamic Legend Chip**: Single-click isolates sector; Shift-click compares multiple sectors; Click again restores all.
* **Toggle 5 km / 10 km Buffer**: Recalculates HHI saturation index, counts, and supply-chain ratios in real time.
* **Reset View**: Restores full ecosystem context, clears active isolations, and resets camera.

### Unified State Schema
```json
{
  "viewMode": "banker", 
  "projectionMode": "geographic", 
  "catchment": {
    "centerCoords": [18.2341, 74.0125],
    "pincode": "412205",
    "radiusKm": 5
  },
  "temporal": {
    "minYear": 2018,
    "selectedMaxYear": 2026
  },
  "activeFilters": {
    "sectors": ["DAIRY", "FABRICATION"],
    "scaleTiers": ["MICRO_1_5", "SMALL_6_9"],
    "verifiedOnly": true
  },
  "activeLayers": {
    "catchmentRings": true,
    "nodes": true,
    "relationships": true,
    "heatmap": false,
    "opportunities": true
  },
  "selection": {
    "selectedNodeId": null,
    "selectedEdgeId": null
  },
  "metrics": {
    "hhiIndex": 1640,
    "competitorCount": 3,
    "supplierCount": 7,
    "saturationVerdict": "MODERATE_COMPETITION"
  }
}
```

---

## 8. Bi-Modal Experience: Beneficiary vs. Banker View

### 8.1 Beneficiary View (Rural Entrepreneur)
* **Philosophy**: Clear, human-language, decision-oriented guidance.
* **Features**:
  * **"My Competitor Radar"**:
    > *"Inside your 5 km circle, there are 3 registered competitors. The closest is Shree Ganesh Fabrication (1.8 km away, registered in 2021)."*
  * **1-Tap Radius Toggle**: Quickly switch between **3 km (Walking/Cycle)**, **5 km (Village Cluster)**, and **10 km (Market Town/Haat)**.
  * **Local Partner Matcher**:
    > *"4 registered steel raw-material suppliers found within 8 km."*
  * **Opportunity Badge**: 🟢 High Viability | 🟡 Moderate Competition | 🔴 Saturated Market.

### 8.2 Banker View (Credit Appraisal Officer)
* **Philosophy**: In-depth analytical workspace for underwriting and risk assessment.
* **Features**:
  * **Catchment HHI Saturation Gauge**:
    $$\text{HHI} = \sum s_i^2$$
    Classifies the catchment as Competitive ($<1500$), Moderate ($1500\text{--}2500$), or Saturated ($>2500$).
  * **Decadal Sectoral CAGR (EC05 $\to$ EC13)**:
    $$\text{CAGR} = \left(\frac{\text{Count}_{2013}}{\text{Count}_{2005}}\right)^{\frac{1}{8}} - 1$$
    Distinguishes structural sunrise trades from sunset categories.
  * **Loan Cannibalization & Overlap Alert**: Flags if branch borrowers in the same pincode/village are in the exact same business activity.
  * **Ego-Network Expansion**: Expand connections of a selected enterprise to see its supplier and buyer dependencies.

---

## 9. Data Requirements & Schema Mapping Matrix

| Engine Feature | Required Field | Source | Status |
| :--- | :--- | :--- | :---: |
| **Enterprise Identity** | `EnterpriseName` | 7-Column API | **Directly Available** |
| **Operational Sector** | `Activities` (NIC Code/Text) | 7-Column API | **Directly Available** |
| **Registration Vintage** | `RegistrationDate` | 7-Column API | **Directly Available** |
| **Hyper-local Address** | `CommunicationAddress` | 7-Column API | **Directly Available** |
| **Spatial Centroid** | `Pincode` (linked to Lat/Lon) | 7-Column API + PIN Directory | **Directly Available** |
| **5 km / 10 km Geodesic Rings** | Radial distance between coordinates | Haversine Formula | **Mathematically Derived** |
| **Competitor Segments** | Same activity within radius | Activity matching rule | **Mathematically Derived** |
| **Supply-Chain Edges** | Input-Output complementary activity pairs | Deterministic Activity Matrix | **Mathematically Derived** |
| **Catchment Saturation (HHI)** | Market share & density within radius | Mathematical HHI Formula | **Mathematically Derived** |
| **Historical Decadal Growth** | EC05 vs EC13 counts | SHRUG Dataset | **Directly Available** |
| **Village Population & TAM** | `pc11_pca_tot_p`, Households | Census 2011 (in repo db) | **Directly Available** |
| **Rural Amenities & Power** | Power hours, road connectivity | 613 Amenities APIs (in repo) | **Directly Available** |
| **Firm Financials & Balances** | Annual turnover, profit, GST | Private Bank LMS / GSTN | *Requires External CBS/GSTN* |

---

## 10. 6-Phase Implementation Roadmap

* **Phase 1: Ingestion & Spatial Catchment API**
  * Create `backend/app/core/ecosystem_service.py` to ingest and cache the 7-column API results.
  * Query by `pincode`, `district`, or `state` with a local SQLite/PostgreSQL caching layer.
  * Expose REST endpoint: `GET /api/v1/ecosystem/catchment?pincode=...&lat=...&lon=...&radius_km=...`.
* **Phase 2: Interactive Map Canvas Component**
  * Build `frontend/src/components/Dashboard/EcosystemIntelligenceMap.jsx`.
  * Render high-performance HTML5 Canvas / Leaflet layer with 5 km and 10 km concentric buffer rings.
  * Implement the dual-projection switcher (Geographic Map $\leftrightarrow$ Force-Directed Graph).
* **Phase 3: Composable Filters, Dynamic Legend & Timeline Scrubber**
  * Interactive multi-select legend (Dairy, Fabrication, Agro, Retail, Services).
  * Interactive relationship toggles: Competitor segments (red) vs. Supply-chain links (teal).
  * Timeline scrubber using `RegistrationDate`.
* **Phase 4: Banker Analytics Suite**
  * Dynamic HHI Saturation Gauge.
  * Decadal Sectoral Growth CAGR widget (SHRUG EC05 $\to$ EC13).
  * Borrower Cannibalization Warning alert.
* **Phase 5: Beneficiary Simplified Experience**
  * Integrate with existing `ViewModeContext.jsx` (`isBanker` vs `isEntrepreneur`).
  * 1-tap walking radius toggle (3 km / 5 km / 10 km).
  * Plain-language "Competitor Radar" and "Supplier Matcher" cards.
* **Phase 6: Verification, Performance & Mobile Polish**
  * Optimize with Canvas batching for 500+ nodes.
  * Verify responsive layouts across desktop and mobile screens.

---

## 11. Ready-to-Use Claude Context Injection Header

Copy and paste the snippet below into any new Claude or LLM prompt session:

```markdown
You are assisting with the implementation of the "Interactive Business Ecosystem Intelligence Engine" for Project Udyam Saathi (SIH 2026).
Refer to the complete technical and UX specification documented in:
`docs/ECOSYSTEM_GRAPH_CONTEXT_WINDOW.md`

Key context highlights:
1. Ground Truth Dataset: An API returning 7 columns (State, District, Pincode, RegistrationDate, EnterpriseName, CommunicationAddress, Activities) combined with SHRUG / Census 2011 macro-demographics.
2. Core Principle: An analytical decision-making workspace (not a decorative map). Zero synthetic/fake data.
3. Personas: Strict bi-modal rendering for Beneficiary (simple competitor radar, 1-tap radius) vs. Banker (HHI saturation, decadal CAGR, cannibalization alert, network drill-down).
4. Spatial Scope: 5 km and 10 km concentric geodesic buffer rings around the applicant's location.
5. Visualization: Dual-projection (Geographic Map <-> Force-Directed Graph) with 5 composable layers and timeline scrubber.
```
