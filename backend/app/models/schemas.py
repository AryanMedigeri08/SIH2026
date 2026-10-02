"""
schemas.py — Pydantic v2 Request & Response Data Schemas for Udyam Saathi REST API.
"""

from __future__ import annotations
from typing import Optional, Union, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Health & Status
# ---------------------------------------------------------------------------
class HealthStatus(BaseModel):
    status: str = "healthy"
    app_name: str
    version: str
    timestamp_utc: str
    database_connected: bool
    ai_synthesizer_active: bool
    ml_classifier_loaded: bool


# ---------------------------------------------------------------------------
# User Authentication & Profile Schemas
# ---------------------------------------------------------------------------
class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Full Name of Entrepreneur")
    gender: Optional[str] = Field("Unspecified", description="Male | Female | Other | Unspecified")
    phone: Optional[str] = Field(None, description="Mobile / Contact number")
    additional_business_details: Optional[str] = Field(None, max_length=1000, description="Optional free-text context for AI narrative")
    latitude: Optional[float] = Field(None, description="Browser auto-detected GPS latitude")
    longitude: Optional[float] = Field(None, description="Browser auto-detected GPS longitude")


class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    gender: Optional[str] = None
    phone: Optional[str] = None
    additional_business_details: Optional[str] = Field(None, max_length=1000)
    preferred_language: Optional[str] = Field(None, pattern="^(en|hi|mr|ta|te|kn)$")


class UserProfileResponse(BaseModel):
    firebase_uid: str
    name: str
    email: str
    gender: Optional[str] = "Unspecified"
    auth_provider: str = "email"
    phone: Optional[str] = None
    additional_business_details: Optional[str] = None
    preferred_language: str = "en"
    projects_count: int = 0
    created_at: str
    updated_at: str
    last_login_at: Optional[str] = None


# ---------------------------------------------------------------------------
# LGD Location Schemas
# ---------------------------------------------------------------------------
class StateInfo(BaseModel):
    state_code: int
    state_name: str
    state_or_ut: str
    census_2011_code: Optional[int] = None


class DistrictInfo(BaseModel):
    district_code: int
    district_name: str
    state_code: int
    census_2011_code: Optional[int] = None


class BlockInfo(BaseModel):
    development_block_code: int
    development_block_name: str
    district_code: int


class VillageInfo(BaseModel):
    id: Optional[int] = None
    village_code: int
    village_name: str
    subdistrict_code: Optional[int] = None
    district_code: Optional[int] = None
    state_code: Optional[int] = None
    pincode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    taluk: Optional[str] = None


# ---------------------------------------------------------------------------
# Feasibility Input & Output Schemas
# ---------------------------------------------------------------------------
class UserInput(BaseModel):
    enterprise_name: str = Field("Micro Enterprise Unit", description="Commercial name of the enterprise")
    business_category: str = Field("manufacturing", description="manufacturing | service")
    sector: str = Field("dairy", description="dairy | food_processing | repair | apparel | fabrication | artisan_trades | general")
    promoter_name: str = Field("Promoter", description="Main promoter name")
    promoter_category: str = Field("general", description="general | sc | st | obc | women | artisan | women_shg")
    gender: str = Field("Unspecified", description="Male | Female | Other | Unspecified")
    state_name: str = Field(..., description="Indian State Name (e.g. West Bengal, Karnataka, Uttar Pradesh)")
    district_name: str = Field(..., description="District Name")
    block_name: str = Field("N/A", description="Block / Tehsil Name")
    village_name: str = Field("N/A", description="Village Name")
    is_rural: bool = Field(True, description="True if rural, False if urban")
    project_cost: float = Field(..., gt=0, description="Total capital outlay in INR (₹)")
    annual_turnover_estimate: Optional[float] = Field(None, description="Estimated annual gross sales/turnover in INR (₹). If omitted, smartly computed from machinery capacity, Census TAM, and RBI debt solvency.")
    tenure_years: float = Field(5.0, gt=0, le=15, description="Requested bank loan repayment tenure in years")
    moratorium_months: int = Field(6, ge=0, le=36, description="Moratorium grace period in months")
    expected_monthly_units: Optional[float] = Field(None, description="Expected monthly production / service units")
    infrastructure_score: Optional[float] = Field(None, ge=0, le=10, description="Optional site infrastructure score (0-10)")
    promoter_equity: Optional[float] = Field(None, description="Promoter equity capital contribution (INR)")
    gross_project_cost: Optional[float] = Field(None, description="Total benchmarked capital outlay before deductions (INR)")
    owned_machinery_value: Optional[float] = Field(None, description="Valuation of existing machinery credited as in-kind asset (INR)")
    promoter_margin_pct: Optional[float] = Field(None, description="Promoter margin benchmark percentage")
    cpi_inflation_pct: Optional[float] = Field(None, description="Optional state CPI inflation override (%)")
    weather_risk_score: Optional[float] = Field(None, ge=0, le=1, description="Optional weather disruption score (0-1)")
    monthly_net_operating_income_override: Optional[float] = Field(None, description="Optional monthly net profit override (₹)")
    additional_business_details: Optional[str] = Field(None, max_length=1000, description="Optional supplemental narrative background")
    language: str = Field("en", description="Target language: en | hi | mr | ta | te | kn")
    latitude: Optional[float] = Field(None, description="Target GPS latitude if auto-detected or mapped")
    longitude: Optional[float] = Field(None, description="Target GPS longitude if auto-detected or mapped")


class FeasibilityReport(BaseModel):
    report_id: str
    generated_at_utc: str
    input_parameters: UserInput
    market_demographics: dict[str, Any]
    financial_analysis: dict[str, Any]
    scheme_optimization: list[dict[str, Any]]
    ml_viability: dict[str, Any]
    risk_assessment: dict[str, Any]
    swot_matrix: dict[str, Any]
    pricing_recommendation: dict[str, Any]
    executive_synthesis: dict[str, Any]
    data_sources_used: Optional[list[dict[str, Any]]] = Field(default_factory=list, description="Audit lineage of database tables, APIs and ML models queried")
    odop_alignment: Optional[dict[str, Any]] = Field(default=None, description="One District One Product (ODOP) alignment and PMFME/DPIIT cluster incentives")
    location: Optional[dict[str, Any]] = Field(default=None, description="Resolved geographic coordinates and locality info")
    ecosystem_graph: Optional[dict[str, Any]] = Field(default=None, description="Document 5 ecosystem graph data contract if pre-calculated")


class ODOPLookupResponse(BaseModel):
    has_odop_record: bool
    district_name: str
    state_name: str
    odop_product: str
    secondary_product: Optional[str] = None
    category: str
    matching_sectors: list[str] = Field(default_factory=list)
    pmfme_eligible: bool = False
    gem_category: Optional[str] = ""
    cfc_available: Optional[bool] = False
    key_benefits: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Project Persistence & Business Status Schemas
# ---------------------------------------------------------------------------
class BusinessStatus(BaseModel):
    code: str = Field("draft", description="Status code: healthy | reconsideration | critical | draft")
    label: str = Field("Draft Assessment", description="Human-readable business status label")
    severity: str = Field("neutral", description="Severity level: positive | warning | critical | neutral")
    color: str = Field("slate", description="Color token: emerald | amber | rose | slate")
    dscr: Optional[float] = None
    ml_verdict: Optional[str] = None
    ml_confidence_pct: Optional[float] = None
    reason: str = ""


def compute_business_status(analysis_result: Optional[dict[str, Any]]) -> BusinessStatus:
    """
    Computes institutional health, solvency, and viability status for a business
    based on deterministic DSCR math, supervised ML inference, and risk matrix.
    """
    if not analysis_result or not isinstance(analysis_result, dict):
        return BusinessStatus(
            code="draft",
            label="Draft Assessment",
            severity="neutral",
            color="slate",
            reason="Enterprise parameters recorded; credit feasibility appraisal pending.",
        )

    report = analysis_result.get("report", {})
    fin = report.get("financial_analysis", {})
    dscr_data = fin.get("dscr", {})
    dscr_val = dscr_data.get("dscr")
    dscr_verdict = str(dscr_data.get("verdict", "")).upper()

    ml = report.get("ml_viability", {})
    ml_verdict = str(ml.get("verdict", "")).upper()
    ml_conf = ml.get("confidence_pct", 0.0)

    risks = report.get("risk_assessment", {})
    avg_risk = risks.get("average_risk_score", 3.0)

    # 1. Critical Solvency / Default Risk Check
    if (dscr_val is not None and dscr_val < 1.0) or ml_verdict in ["RECONSIDER", "UNSUITABLE"] or dscr_verdict in ["UNVIABLE", "CRITICAL"] or avg_risk >= 7.5:
        reason_parts = []
        if dscr_val is not None and dscr_val < 1.0:
            reason_parts.append(f"DSCR {dscr_val:.2f} is below 1.0 (Debt obligations exceed operating surplus)")
        if ml_verdict in ["RECONSIDER", "UNSUITABLE"]:
            reason_parts.append(f"ML Viability model rated enterprise as {ml_verdict} ({ml_conf:.1f}% confidence)")
        if avg_risk >= 7.5:
            reason_parts.append(f"High composite risk score ({avg_risk:.1f}/10)")
        
        reason_str = " • ".join(reason_parts) if reason_parts else "Elevated credit risk requiring structural restructuring."
        return BusinessStatus(
            code="critical",
            label="Critical / Solvency Risk",
            severity="critical",
            color="rose",
            dscr=dscr_val,
            ml_verdict=ml_verdict or "RECONSIDER",
            ml_confidence_pct=ml_conf,
            reason=reason_str,
        )

    # 2. Reconsideration / Attention Required Check
    if (dscr_val is not None and 1.0 <= dscr_val < 1.33) or ml_verdict in ["CAUTION", "MARGINAL"] or (5.0 <= avg_risk < 7.5):
        reason_parts = []
        if dscr_val is not None and dscr_val < 1.33:
            reason_parts.append(f"DSCR {dscr_val:.2f} satisfies break-even but is below the RBI 1.33 benchmark")
        if ml_verdict in ["CAUTION", "MARGINAL"]:
            reason_parts.append(f"ML Viability flagged CAUTION ({ml_conf:.1f}% confidence)")
        if 5.0 <= avg_risk < 7.5:
            reason_parts.append(f"Moderate operational/market risk ({avg_risk:.1f}/10)")

        reason_str = " • ".join(reason_parts) if reason_parts else "Requires operational review & contingency capital before credit submission."
        return BusinessStatus(
            code="reconsideration",
            label="Requires Reconsideration",
            severity="warning",
            color="amber",
            dscr=dscr_val,
            ml_verdict=ml_verdict or "CAUTION",
            ml_confidence_pct=ml_conf,
            reason=reason_str,
        )

    # 3. Healthy / Bank Viable Check
    reason_str = f"Bank Viable: DSCR of {dscr_val:.2f} clears RBI benchmark (1.33) with {ml_conf:.1f}% ML SUITABLE confidence." if dscr_val is not None else "Enterprise satisfies statutory credit criteria."
    return BusinessStatus(
        code="healthy",
        label="Healthy / Bank Viable",
        severity="positive",
        color="emerald",
        dscr=dscr_val,
        ml_verdict=ml_verdict or "SUITABLE",
        ml_confidence_pct=ml_conf,
        reason=reason_str,
    )


class ProjectCreate(BaseModel):
    business_name: str
    business_category: str
    sector: str
    investment_amount: float
    annual_turnover_estimate: float
    state_name: str
    district_name: str
    block_name: str = "N/A"
    village_name: str = "N/A"
    promoter_name: str = "Enterprise Promoter"
    promoter_category: str = "general"
    gender: str = "Unspecified"
    is_rural: bool = True
    tenure_years: float = 5.0
    moratorium_months: int = 6
    expected_monthly_units: Optional[float] = None
    infrastructure_score: Optional[float] = None
    promoter_equity: Optional[float] = None
    gross_project_cost: Optional[float] = None
    owned_machinery_value: Optional[float] = None
    promoter_margin_pct: Optional[float] = None
    language: str = "en"
    additional_business_details: Optional[str] = None
    monthly_net_operating_income_override: Optional[float] = None
    auto_analyze: bool = False


class ProjectUpdate(BaseModel):
    business_name: Optional[str] = None
    investment_amount: Optional[float] = None
    annual_turnover_estimate: Optional[float] = None
    tenure_years: Optional[float] = None
    moratorium_months: Optional[int] = None
    expected_monthly_units: Optional[float] = None
    infrastructure_score: Optional[float] = None
    promoter_equity: Optional[float] = None
    gross_project_cost: Optional[float] = None
    owned_machinery_value: Optional[float] = None
    promoter_margin_pct: Optional[float] = None
    language: Optional[str] = None
    additional_business_details: Optional[str] = None
    monthly_net_operating_income_override: Optional[float] = None


class ProjectModel(BaseModel):
    project_id: str
    user_id: str
    business_name: str
    business_category: str
    sector: str
    investment_amount: float
    annual_turnover_estimate: float
    state_name: str
    district_name: str
    block_name: str
    village_name: str
    promoter_name: str
    promoter_category: str
    gender: str
    is_rural: bool
    tenure_years: float
    moratorium_months: int
    expected_monthly_units: Optional[float] = None
    infrastructure_score: Optional[float] = None
    promoter_equity: Optional[float] = None
    gross_project_cost: Optional[float] = None
    owned_machinery_value: Optional[float] = None
    promoter_margin_pct: Optional[float] = None
    language: str
    additional_business_details: Optional[str] = None
    monthly_net_operating_income_override: Optional[float] = None
    status: str = "draft"  # draft | analyzed
    business_status: Optional[BusinessStatus] = None
    analysis_result: Optional[dict[str, Any]] = None
    created_at: str
    updated_at: str

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.business_status is None:
            self.business_status = compute_business_status(self.analysis_result)


# ---------------------------------------------------------------------------
# Standalone Financial Calculator Schemas
# ---------------------------------------------------------------------------
class FinancialCalcRequest(BaseModel):
    project_cost: float = Field(..., gt=0)
    annual_turnover: float = Field(..., gt=0)
    sector: str = "dairy"
    business_category: str = "manufacturing"
    promoter_category: str = "general"
    is_rural: bool = True
    tenure_years: float = 5.0
    interest_rate_pct: float = 11.0
    moratorium_months: int = 6


class FinancialCalcResponse(BaseModel):
    project_cost: float
    top_scheme_id: str
    top_scheme_name: str
    subsidy_grant_amount: float
    loan_principal: float
    monthly_emi: float
    total_interest_payable: float
    total_repayment: float
    working_capital_required: float
    dscr: float
    dscr_verdict: str
    ranked_schemes: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# UDYAM Village Intelligence & Market Analysis Schemas (Phases 1-33)
# ---------------------------------------------------------------------------
class MarketAnalysisRequest(BaseModel):
    state: str = Field(..., description="State name (e.g., TELANGANA, MAHARASHTRA)")
    district: str = Field(..., description="District name (e.g., MEDAK, SATARA)")
    village: Optional[str] = Field("", description="Target village or locality name")
    target_lat: Optional[float] = Field(None, description="Target village latitude if known")
    target_lon: Optional[float] = Field(None, description="Target village longitude if known")
    radius_km: float = Field(10.0, gt=0, le=50.0, description="Analysis radius in km (default 10.0)")
    core_radius_km: float = Field(5.0, gt=0, le=25.0, description="Core market radius in km (default 5.0)")
    business_category: Optional[str] = Field("", description="Proposed business category (e.g. DAIRY, FOOD_RETAIL, TAILORING)")
    pincode: Optional[str] = Field(None, description="Optional pincode filter")
    max_records: Optional[int] = Field(1000, gt=0, le=10000, description="Max UDYAM records to process")


class MarketAnalysisResponse(BaseModel):
    target: dict[str, Any]
    geographic_quality: dict[str, Any]
    market_summary: dict[str, Any]
    business_categories: list[dict[str, Any]]
    nearby_businesses: list[dict[str, Any]]
    limitations: list[str]
    pipeline_metadata: dict[str, Any]
    diagnostic_report: str


# ---------------------------------------------------------------------------
# Document 2: Opportunity Engine & Multi-Category Comparison Schemas
# ---------------------------------------------------------------------------
class OpportunityAnalysisRequest(BaseModel):
    state: str = Field(..., description="State name (e.g., TELANGANA, MAHARASHTRA)")
    district: str = Field(..., description="District name (e.g., MEDAK, SATARA)")
    village: Optional[str] = Field("", description="Target village or locality name")
    target_lat: Optional[float] = Field(None, description="Target village latitude")
    target_lon: Optional[float] = Field(None, description="Target village longitude")
    business_intent: str = Field("dairy", description="Business intent or sector (e.g., dairy, kirana, tailoring, poultry, fabrication)")
    radius_km: float = Field(10.0, gt=0, le=50.0, description="Catchment radius in km")
    core_radius_km: float = Field(5.0, gt=0, le=25.0, description="Core village market radius in km")
    pincode: Optional[str] = Field(None, description="Optional pincode filter")
    max_records: Optional[int] = Field(1000, gt=0, le=10000, description="Max UDYAM records to analyze")
    base_population_2011: Optional[float] = Field(None, description="Optional 2011 Census base population override")
    snapshot_id: Optional[str] = Field(None, description="Optional pinned DataSnapshot ID for exact deterministic replay")


class OpportunityAnalysisResponse(BaseModel):
    target_location: dict[str, Any]
    business_intent: dict[str, Any]
    recommendation: str
    composite_score: float
    confidence: str
    supply_metrics: dict[str, Any]
    demand_features: dict[str, Any]
    opportunity_indicators: dict[str, Any]
    classified_competitors: list[dict[str, Any]]
    all_nearby_businesses: list[dict[str, Any]]
    evidence: dict[str, Any]
    sensitivity_analysis: list[dict[str, Any]]
    data_lineage: list[dict[str, Any]]
    generated_at: str
    version: str


class MultiCategoryCompareRequest(BaseModel):
    state: str = Field(..., description="State name")
    district: str = Field(..., description="District name")
    village: Optional[str] = Field("", description="Village name")
    target_lat: Optional[float] = Field(None)
    target_lon: Optional[float] = Field(None)
    categories: Optional[list[str]] = Field(None, description="List of business intents to compare (e.g. ['dairy', 'kirana', 'tailoring'])")
    radius_km: float = Field(10.0, gt=0, le=50.0)
    max_records: Optional[int] = Field(500, gt=0, le=5000)


class MultiCategoryCompareResponse(BaseModel):
    state: str
    district: str
    village: str
    comparisons: list[dict[str, Any]]
    count: int


# ---------------------------------------------------------------------------
# Document 5: Ecosystem Graph / Map Schemas
# ---------------------------------------------------------------------------
class EcosystemGraphRequest(BaseModel):
    state: str = Field(..., description="State name (e.g., TELANGANA, MAHARASHTRA)")
    district: str = Field(..., description="District name (e.g., MEDAK, SATARA)")
    village: Optional[str] = Field("", description="Target village or locality name")
    target_lat: Optional[float] = Field(None, description="Target latitude")
    target_lon: Optional[float] = Field(None, description="Target longitude")
    business_intent: str = Field("dairy", description="Business intent for competitor/supply-chain classification")
    radius_km: float = Field(10.0, gt=0, le=50.0, description="Scoring catchment radius in km")
    visualization_radius_km: Optional[float] = Field(None, gt=0, le=50.0, description="Optional visual catchment radius (does NOT alter scoring)")
    pincode: Optional[str] = Field(None, description="Optional pincode filter")
    max_records: Optional[int] = Field(1000, gt=0, le=10000, description="Max UDYAM records to process")
    snapshot_id: Optional[str] = Field(None, description="Optional snapshot ID for deterministic replay")


class EcosystemGraphResponse(BaseModel):
    schemaVersion: str
    catchment: dict[str, Any]
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    unmappedEntities: list[dict[str, Any]]
    metrics: dict[str, Any]
    temporal: dict[str, Any]
    layers: dict[str, Any]
    provenance: dict[str, Any]
    warnings: list[dict[str, Any]]
    intent: dict[str, Any]
    evidence: dict[str, Any]
    villageDensity: Optional[list[dict[str, Any]]] = Field(
        None,
        description="Village-level MSME registration density aggregation for heatmap rendering"
    )


