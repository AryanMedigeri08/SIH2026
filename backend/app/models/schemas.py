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
    annual_turnover_estimate: float = Field(..., gt=0, description="Estimated annual gross sales/turnover in INR (₹)")
    tenure_years: float = Field(5.0, gt=0, le=15, description="Requested bank loan repayment tenure in years")
    moratorium_months: int = Field(6, ge=0, le=36, description="Moratorium grace period in months")
    expected_monthly_units: Optional[float] = Field(None, description="Expected monthly production / service units")
    infrastructure_score: Optional[float] = Field(None, ge=0, le=10, description="Optional site infrastructure score (0-10)")
    cpi_inflation_pct: Optional[float] = Field(None, description="Optional state CPI inflation override (%)")
    weather_risk_score: Optional[float] = Field(None, ge=0, le=1, description="Optional weather disruption score (0-1)")
    monthly_net_operating_income_override: Optional[float] = Field(None, description="Optional monthly net profit override (₹)")
    language: str = Field("en", description="Target language: en | hi | mr | ta | te | kn")


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



# ---------------------------------------------------------------------------
# Project Persistence Schemas
# ---------------------------------------------------------------------------
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
    language: str = "en"


class ProjectUpdate(BaseModel):
    business_name: Optional[str] = None
    investment_amount: Optional[float] = None
    annual_turnover_estimate: Optional[float] = None
    tenure_years: Optional[float] = None
    moratorium_months: Optional[int] = None
    language: Optional[str] = None


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
    language: str
    status: str = "draft"  # draft | analyzed
    analysis_result: Optional[dict[str, Any]] = None
    created_at: str
    updated_at: str


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
