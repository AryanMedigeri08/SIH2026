# Phase 6 Integration Test Report
## Udyam Saathi — Cross-Component End-to-End Consistency

**Test Suite:** [`tests/test_integration_consistency.py`](file:///c:/SIH2026/tests/test_integration_consistency.py)  
**Execution Date:** 2026-09-12  
**Python Environment:** `c:\SIH2026\venv\Scripts\python.exe` (Python 3.10)  
**Total Tests Run:** 23  
**Passed:** 23  
**Failed:** 0  
**Errors:** 0  
**Execution Latency:** 0.598 seconds  
**Test Success Rate:** **100%**

---

## 1. Test Execution Breakdown

| # | Test Method Name | Invariant / Gate Covered | Execution Time | Verdict |
|:---:|:---|:---|:---:|:---:|
| 1 | `test_gate_b_identity_stability_and_no_government_id_invention` | Invariant I1 (Enterprise Identity, SHA-256 Stability) | 0.002s | **PASS** |
| 2 | `test_gate_b_graph_node_id_derived_from_fingerprint` | Gate B (Node ID Derivation from Fingerprint) | 0.001s | **PASS** |
| 3 | `test_gate_c_no_coordinate_fabrication_for_unmapped` | Invariant I2 (Zero Coordinate Fabrication) | 0.002s | **PASS** |
| 4 | `test_gate_d_precision_hierarchy_exact_reserved_strictly_for_gps` | Gate D (Spatial Precision Hierarchy Semantics) | 0.001s | **PASS** |
| 5 | `test_gate_d_fixture_nodes_reflect_exact_precision_classes` | Gate D (Graph Nodes Spatial Precision Mapping) | 0.002s | **PASS** |
| 6 | `test_gate_e_canonical_categories_shared_across_engines` | Gate E (Category Ontology Shared Consistency) | 0.002s | **PASS** |
| 7 | `test_gate_e_relevance_classification_consistency` | Gate E (5-Level Competitor Relevance Mapping) | 0.002s | **PASS** |
| 8 | `test_gate_f_competitor_edges_are_derived_without_transaction_claims` | Gate F (Competitor Edge Semantics & DERIVED flag) | 0.003s | **PASS** |
| 9 | `test_gate_g_supply_chain_edges_are_derived_without_transaction_claims` | Gate G (Supply-Chain Complementarity Matrix & DERIVED flag) | 0.003s | **PASS** |
| 10 | `test_gate_h_hhi_retains_sector_diversification_semantics` | Gate H (HHI Economic Sector Diversification Definition) | 0.001s | **PASS** |
| 11 | `test_gate_i_visual_radius_does_not_alter_analytical_scoring` | Gate I (Scoring vs Visualization Radius Independence) | 0.008s | **PASS** |
| 12 | `test_gate_j_opportunity_score_consumed_directly_from_report` | Gate J (Opportunity Score Direct Consumption) | 0.001s | **PASS** |
| 13 | `test_gate_k_saturation_and_constrained_guardrail_suppression` | Gate K (Guardrail Propagation: Saturated/Constrained Markets) | 0.004s | **PASS** |
| 14 | `test_gate_l_high_confidence_with_low_opportunity_is_valid` | Gate L (Confidence vs Opportunity Independence) | 0.002s | **PASS** |
| 15 | `test_gate_m_provenance_lineage_and_engine_versions_present` | Gate M (Provenance & Lineage Metadata Attachment) | 0.001s | **PASS** |
| 16 | `test_gate_n_temporal_min_max_and_malformed_date_handling` | Gate N (Temporal Metadata Dynamic Extraction & Out-of-Range Date Tracking) | 0.003s | **PASS** |
| 17 | `test_gate_o_unmapped_entities_tracked_with_explicit_disclaimer` | Gate O (Unmapped Entities Segregation & Warning) | 0.002s | **PASS** |
| 18 | `test_gate_p_api_request_validation` | Gate P (Ecosystem Graph API Request Bounding Validation) | 0.001s | **PASS** |
| 19 | `test_gate_p_pydantic_schema_serialization` | Gate P (Pydantic V2 Response Schema Serialization) | 0.003s | **PASS** |
| 20 | `test_gate_r_and_s_bi_modal_data_contract_completeness` | Gates R & S (Beneficiary vs Banker Persona Data Support) | 0.002s | **PASS** |
| 21 | `test_gate_t_llm_boundary_no_metric_or_guardrail_override` | Gate T (LLM Advisory Layer Isolation from Scoring) | 0.001s | **PASS** |
| 22 | `test_gate_w_transformation_performance_and_edge_capping` | Gate W (500+ Node Transformation Performance < 1.0s) | 0.313s | **PASS** |
| 23 | `test_section_14_competitor_reconciliation` | Section 14 (Exact Competitor Reconciliation: Market vs Graph) | 0.002s | **PASS** |

---

## 2. Performance Analysis

- **Total Execution Time:** 0.598s
- **500-Node Transformation Latency:** **0.313s** (Target: < 1.0s)
- **Node-Building Throughput:** > 1,500 nodes / second
- **Edge Derivation Throughput:** > 40,000 edge evaluations / second

---

## 3. Key Findings & Invariant Confirmations

1. **Enterprise Identity (Invariant I1):** Verified that enterprise identity is computed using SHA-256 fingerprinting over normalized names and addresses. Casing and whitespace variances do not create duplicate entities. No synthetic government IDs are created.
2. **Geographic Precision (Invariant I2):** `EXACT` precision is reserved exclusively for verified GPS (`verified_gps`, `manual_survey_gps`). Census and administrative sources resolve strictly to `LOCALITY` or `VILLAGE` centroids. Unmapped entities retain `None` coordinates.
3. **Reconciliation Integrity (Section 14):** Mathematical comparison between the Market Intelligence competitor set ($A$) and Graph competitor nodes ($B$) confirmed zero unexplained discrepancies ($A \Delta B = \emptyset$ for in-catchment mapped nodes).
4. **Guardrail Propagation (Gate K):** Confirmed that `SATURATED_MARKET` and `CONSTRAINED_MARKET` verdicts strictly suppress the Layer 5 opportunity overlay (`status: "UNAVAILABLE"`).
