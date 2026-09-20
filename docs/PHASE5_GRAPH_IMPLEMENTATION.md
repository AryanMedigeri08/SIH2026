# Document 5: Interactive Business Ecosystem Intelligence Graph/Map Implementation

## Executive Summary

The Interactive Business Ecosystem Intelligence Graph/Map is a read-model projection layer over the validated outputs of the `MarketOpportunityEngine` (Document 2) and `VillageIntelligencePipeline` (Document 1). It enables dual-projection visualization (Geographic and Topological force-directed) of micro, small, and medium enterprise (MSME) networks within a defined spatial catchment radius.

## Architectural Principles & Strict Guarantees

1. **Read-Model Consumer**: Consumes validated analytical data; never acts as a secondary source of truth or creates competing market scoring pipelines.
2. **Zero Coordinate Fabrication**: Enterprises without defensible spatial coordinates are routed to `unmappedEntities` with spatial approximation disclaimers. Pincode-level anchors carry explicit warnings. Coordinates represent resolved spatial coordinates rather than exact geocodes unless spatial precision == EXACT.
3. **Derived Relationships**: Relationship edges between nodes (Competitor and Supply Chain) are explicitly flagged as `DERIVED` based on deterministic activity/NIC classification and configured complementarity matrices. No confirmed commercial transactions are claimed.
4. **Scale Tier Integrity**: Workforce scale tier defaults to `UNKNOWN` unless validated employment/investment data exists.
5. **HHI Semantic Preservation**: Herfindahl-Hirschman Index (HHI) retains the platform's standardized economic-sector diversification definition.
6. **Visual Catchment Independence**: Adjusting the visualization radius dynamically filters rendered nodes without altering upstream market-opportunity scoring semantics.
7. **Bi-Modal Persona Adaptation**: Dynamically switches vocabulary and disclosure depth between Beneficiary (`Business Neighborhood Map`, simplified labels) and Banker (`Ecosystem Intelligence Graph`, resolved spatial coordinates (with `EXACT` reserved strictly for verified enterprise GPS), HHI values, layer health diagnostics).

## Core Components

### 1. Backend Adapter (`backend/app/core/intelligence/ecosystem_graph.py`)
- `EcosystemGraphAdapter`: Transforms `MarketOpportunityReport` outputs into a versioned data contract (`v1.0`).
- `_build_graph_node`: Projects enterprise entities with 5-tier spatial precision hierarchy (`EXACT`, `LOCALITY`, `VILLAGE`, `PINCODE`, `UNMAPPED`).
- `_build_edges`: Generates deterministic competitor and supply-chain linkages.
- `_build_temporal_metadata`: Dynamically calculates min/max registration years from actual date fields without hardcoding.
- `_build_metrics`: Compiles radius-specific counts, sector distributions, and HHI indices.
- `_build_warnings`: Issues data quality disclaimers for unmapped records and inferred edges.

### 2. REST API Endpoints (`backend/app/routers/market_intelligence.py`)
- `POST /api/v2/market-analysis/ecosystem-graph`:
  - Request: `EcosystemGraphRequest` (state, district, village, coordinates, business_intent, radius_km, visualization_radius_km, snapshot_id)
  - Response: `EcosystemGraphResponse` (schemaVersion, catchment, nodes, edges, unmappedEntities, metrics, temporal, layers, provenance, warnings)

### 3. Frontend Visualization Component (`frontend/src/components/Dashboard/EcosystemIntelligenceMap.jsx`)
- Pure HTML5 Canvas + Lucide-React implementation (zero heavy external GIS/mapping dependencies).
- Dual-projection engine:
  - **Geographic Mode**: Projects latitude/longitude coordinates onto scaled geodesic rings with center crosshair.
  - **Topological Mode**: Force-directed layout using iterative spring-electrical repulsion and attraction simulation.
- Interactive Features:
  - Zoom & Pan controls with reset.
  - Composable sector and edge visibility filters.
  - Dynamic legend with count metrics.
  - Temporal scrubber slider.
  - Enterprise inspection panel with data quality and provenance disclosure.
  - Unmapped entity drawer.

### 4. Page Integration (`frontend/src/pages/report/MarketDemandPage.jsx`)
- Directly integrated into `MarketDemandPage` under Dimension 2.
- Handles automated fetching with fallback from `reportData.input_parameters`.
