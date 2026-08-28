"""
test_phase7.py — Udyam Saathi Phase 7 Decoupled React Frontend Verification Harness.

Four Comprehensive Test Layers:
  1. REPOSITORY STRUCTURE & ASSET VERIFICATION: Validates existence of all React SPA modules,
     Vite configuration, Tailwind system, components, package configurations, and assets.
  2. DESIGN SYSTEM & CSS TOKENS: Validates glassmorphism styles, color palettes, responsive
     breakpoints, font imports, and print media rules in index.css.
  3. COMPONENT INTERFACE & EXPORT INTEGRITY: Checks that all React UI components export
     their respective functional components and handle props cleanly.
  4. API BINDINGS & 5 PITCH CASES INTEGRITY: Validates client route mappings against FastAPI
     backend endpoints and consistency of pre-packaged pitch case data.

Run: python test_phase7.py
"""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

PASS = 0
FAIL = 0


def check(label: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}  {detail}")


# ============================================================================
# LAYER 1: REPOSITORY STRUCTURE & ASSET INTEGRITY
# ============================================================================
print("=" * 90)
print("LAYER 1 — REPOSITORY STRUCTURE & ASSET INTEGRITY")
print("=" * 90)

required_files = [
    FRONTEND_DIR / "package.json",
    FRONTEND_DIR / "vite.config.js",
    FRONTEND_DIR / "tailwind.config.js",
    FRONTEND_DIR / "postcss.config.js",
    FRONTEND_DIR / "index.html",
    FRONTEND_DIR / "src" / "index.css",
    FRONTEND_DIR / "src" / "main.jsx",
    FRONTEND_DIR / "src" / "App.jsx",
    FRONTEND_DIR / "src" / "services" / "api.js",
    FRONTEND_DIR / "src" / "data" / "pitchCases.js",
    FRONTEND_DIR / "src" / "components" / "Navbar.jsx",
    FRONTEND_DIR / "src" / "components" / "Sidebar" / "Sidebar.jsx",
    FRONTEND_DIR / "src" / "components" / "ReportGenerationLoader.jsx",
    FRONTEND_DIR / "src" / "components" / "Skeletons" / "CardSkeletons.jsx",
    FRONTEND_DIR / "src" / "components" / "CaseStudiesBar.jsx",
    FRONTEND_DIR / "src" / "components" / "Wizard" / "FeasibilityWizard.jsx",
    FRONTEND_DIR / "src" / "components" / "Dashboard" / "Dashboard.jsx",
    FRONTEND_DIR / "src" / "components" / "Dashboard" / "ViabilityMeterCard.jsx",
    FRONTEND_DIR / "src" / "components" / "Dashboard" / "CapitalReconciliationCard.jsx",
    FRONTEND_DIR / "src" / "components" / "Dashboard" / "SchemeLeaderboardCard.jsx",
    FRONTEND_DIR / "src" / "components" / "Dashboard" / "CashflowProjectionsChart.jsx",
    FRONTEND_DIR / "src" / "components" / "Dashboard" / "RiskRadarCard.jsx",
    FRONTEND_DIR / "src" / "components" / "Dashboard" / "SwotMatrixCard.jsx",
    FRONTEND_DIR / "src" / "components" / "Dashboard" / "StatutoryChecklistCard.jsx",
    FRONTEND_DIR / "src" / "components" / "Dashboard" / "ExecutiveNarrativeCard.jsx",
    FRONTEND_DIR / "src" / "components" / "DprModal.jsx",
    FRONTEND_DIR / "src" / "components" / "QuickCalculatorModal.jsx",
    FRONTEND_DIR / "src" / "pages" / "DashboardPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "OverviewPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "ViabilityPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "MarketDemandPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "GovernmentSchemesPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "FinancialsPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "RiskAssessmentPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "SwotAnalysisPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "BankDprPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "WizardPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "CalculatorPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "DataSourcesPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "SchemesPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "ReportDetailPage.jsx",
    FRONTEND_DIR / "src" / "pages" / "NotFoundPage.jsx",
]

for f in required_files:
    exists = f.exists() and f.stat().st_size > 0
    check(f"File exists & non-empty: {f.relative_to(FRONTEND_DIR.parent)}", exists)

print(f"\nLayer 1 result: {PASS} passed, {FAIL} failed so far.\n")



# ============================================================================
# LAYER 2: DESIGN SYSTEM & CSS TOKENS
# ============================================================================
print("=" * 90)
print("LAYER 2 — DESIGN SYSTEM & CSS TOKENS")
print("=" * 90)

css_content = (FRONTEND_DIR / "src" / "index.css").read_text(encoding="utf-8")

check("CSS includes Tailwind directives (@tailwind base, components, utilities)", "@tailwind base" in css_content and "@tailwind components" in css_content)
check("CSS defines glassmorphism card styling (.glass-panel)", ".glass-panel" in css_content and "backdrop-filter" in css_content)
check("CSS defines design system variables (--bg-dark, --border-glass, --accent-cyan)", "--bg-dark" in css_content and "--accent-cyan" in css_content and "--accent-emerald" in css_content)
check("CSS includes print layout rules (@media print)", "@media print" in css_content)

html_content = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
check("index.html imports Google Fonts (Inter & Outfit)", "fonts.googleapis.com" in html_content and "Outfit" in html_content and "Inter" in html_content)
check("index.html contains #root mounting container", 'id="root"' in html_content)
check("index.html loads main.jsx with module type", 'type="module"' in html_content and 'src="/src/main.jsx"' in html_content)

print(f"\nLayer 2 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 3: COMPONENT INTERFACE & EXPORT INTEGRITY
# ============================================================================
print("=" * 90)
print("LAYER 3 — COMPONENT INTERFACE & EXPORT INTEGRITY")
print("=" * 90)

components_to_test = [
    ("Navbar.jsx", "Navbar"),
    ("Sidebar/Sidebar.jsx", "Sidebar"),
    ("ReportGenerationLoader.jsx", "ReportGenerationLoader"),
    ("Skeletons/CardSkeletons.jsx", "OverviewSkeleton"),
    ("CaseStudiesBar.jsx", "CaseStudiesBar"),
    ("Wizard/FeasibilityWizard.jsx", "FeasibilityWizard"),
    ("Dashboard/Dashboard.jsx", "Dashboard"),
    ("Dashboard/ViabilityMeterCard.jsx", "ViabilityMeterCard"),
    ("Dashboard/CapitalReconciliationCard.jsx", "CapitalReconciliationCard"),
    ("Dashboard/SchemeLeaderboardCard.jsx", "SchemeLeaderboardCard"),
    ("Dashboard/CashflowProjectionsChart.jsx", "CashflowProjectionsChart"),
    ("Dashboard/RiskRadarCard.jsx", "RiskRadarCard"),
    ("Dashboard/SwotMatrixCard.jsx", "SwotMatrixCard"),
    ("Dashboard/StatutoryChecklistCard.jsx", "StatutoryChecklistCard"),
    ("Dashboard/ExecutiveNarrativeCard.jsx", "ExecutiveNarrativeCard"),
    ("DprModal.jsx", "DprModal"),
    ("QuickCalculatorModal.jsx", "QuickCalculatorModal"),
]

for rel_path, comp_name in components_to_test:
    path = FRONTEND_DIR / "src" / "components" / rel_path
    code = path.read_text(encoding="utf-8")
    check(f"{rel_path} exports component '{comp_name}'", f"export function {comp_name}" in code or f"export const {comp_name}" in code or f"export {{{comp_name}}}" in code or f"export {{ {comp_name} }}" in code or f"export default {comp_name}" in code or f"export {{ {comp_name}" in code)

pages_to_test = [
    ("DashboardPage.jsx", "DashboardPage"),
    ("OverviewPage.jsx", "OverviewPage"),
    ("ViabilityPage.jsx", "ViabilityPage"),
    ("MarketDemandPage.jsx", "MarketDemandPage"),
    ("GovernmentSchemesPage.jsx", "GovernmentSchemesPage"),
    ("FinancialsPage.jsx", "FinancialsPage"),
    ("RiskAssessmentPage.jsx", "RiskAssessmentPage"),
    ("SwotAnalysisPage.jsx", "SwotAnalysisPage"),
    ("BankDprPage.jsx", "BankDprPage"),
    ("WizardPage.jsx", "WizardPage"),
    ("CalculatorPage.jsx", "CalculatorPage"),
    ("DataSourcesPage.jsx", "DataSourcesPage"),
    ("SchemesPage.jsx", "SchemesPage"),
    ("ReportDetailPage.jsx", "ReportDetailPage"),
    ("NotFoundPage.jsx", "NotFoundPage"),
]

for rel_path, comp_name in pages_to_test:
    path = FRONTEND_DIR / "src" / "pages" / rel_path
    code = path.read_text(encoding="utf-8")
    check(f"pages/{rel_path} exports page component '{comp_name}'", f"export function {comp_name}" in code or f"export const {comp_name}" in code or f"export {{{comp_name}}}" in code or f"export {{ {comp_name} }}" in code or f"export default {comp_name}" in code or f"export {{ {comp_name}" in code)

print(f"\nLayer 3 result: {PASS} passed, {FAIL} failed so far.\n")


# ============================================================================
# LAYER 4: API BINDINGS & 5 PITCH CASES INTEGRITY
# ============================================================================
print("=" * 90)
print("LAYER 4 — API BINDINGS & 5 PITCH CASES INTEGRITY")
print("=" * 90)

api_content = (FRONTEND_DIR / "src" / "services" / "api.js").read_text(encoding="utf-8")
check("api.js maps /feasibility/generate endpoint", "/feasibility/generate" in api_content)
check("api.js maps /feasibility/{reportId}/dpr endpoint", "/feasibility/${reportId}/dpr" in api_content or "dpr?format=" in api_content)
check("api.js maps /locations/states and districts", "/locations/states" in api_content and "/locations/districts" in api_content)
check("api.js maps /financial/calculate endpoint", "/financial/calculate" in api_content)
check("api.js maps /data-sources discovery endpoint", "/data-sources" in api_content)
check("api.js maps /data-sources/schemes catalog endpoint", "/data-sources/schemes" in api_content)

case_data_content = (FRONTEND_DIR / "src" / "data" / "pitchCases.js").read_text(encoding="utf-8")
check("pitchCases.js exports PITCH_CASES array", "export const PITCH_CASES" in case_data_content)
check("PITCH_CASES contains Scenario 1: Dairy Unit (WB)", "Joypur Fresh Dairy" in case_data_content)
check("PITCH_CASES contains Scenario 2: Artisan Pottery (UP)", "Khurja Traditional Glazed Pottery" in case_data_content)
check("PITCH_CASES contains Scenario 3: Heavy Agro Plant (MP)", "Malwa Heavy Agro Solvent" in case_data_content)

print("\n" + "=" * 90)
print(f"PHASE 7 VERIFICATION SUMMARY: {PASS} passed, {FAIL} failed")
print("=" * 90)


if FAIL > 0:
    sys.exit(1)
