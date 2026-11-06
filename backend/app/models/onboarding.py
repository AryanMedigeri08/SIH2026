"""Validated conversational inputs. Derived geography, classifications and money are server-owned."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class CostItems(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    equipment: float | None = Field(None, ge=0, le=1e10)
    premises_setup: float | None = Field(None, ge=0, le=1e10)
    inventory: float | None = Field(None, ge=0, le=1e10)
    working_capital: float | None = Field(None, ge=0, le=1e10)
    other: float | None = Field(None, ge=0, le=1e10)


class Facts(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)
    name: str | None = Field(None, min_length=1, max_length=120)
    gender: Literal["Male", "Female", "Other", "Unspecified"] | None = None
    promoter_category: Literal["general", "sc", "st", "obc", "minority", "ph", "artisan", "women", "women_shg"] | None = None
    phone: str | None = Field(None, pattern=r'^\+91[6-9]\d{9}$')
    email: str | None = Field(None, max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    email_status: Literal['provided','skipped'] | None = None
    idea_status: Literal["known", "explore"] | None = None
    idea: str | None = Field(None, min_length=3, max_length=1000)
    activity: Literal["manufacture", "process", "retail", "distribute", "service", "other"] | None = None
    products: str | None = Field(None, min_length=2, max_length=500)
    operations: str | None = Field(None, min_length=2, max_length=500)
    scale: str | None = Field(None, min_length=2, max_length=300)
    budget: float | None = Field(None, ge=0, le=1e10)
    budget_kind: Literal["personal", "total", "borrowing", "other", "unknown_budget"] | None = None
    funding_source: str | None = Field(None, max_length=300)
    personal_contribution: float | None = Field(None, ge=0, le=1e10)
    monthly_sales: float | None = Field(None, ge=0, le=1e10)
    monthly_expenses: float | None = Field(None, ge=0, le=1e10)
    monthly_fixed_costs: float | None = Field(None, ge=0, le=1e10)
    variable_cost_pct: float | None = Field(None, ge=0, le=100)
    operating_basis: Literal['user_estimate', 'sector_model'] | None = None
    skills: str | None = Field(None, min_length=2, max_length=500)
    constraints: str | None = Field(None, min_length=2, max_length=500)
    premises: Literal["owned", "rented", "shared", "purchase", "mobile"] | None = None
    space: str | None = Field(None, min_length=2, max_length=300)
    premises_suitable: bool | None = None
    rent_amount: float | None = Field(None, ge=0, le=1e8)
    rent_period: Literal["monthly", "annual"] | None = None
    project_cost: float | None = Field(None, gt=0, le=1e10)
    cost_items: CostItems | None = None
    cost_basis: str | None = Field(None, min_length=3, max_length=500)
    odop_preference: Literal["explore", "keep", "reject"] | None = None
    enterprise_name: str | None = Field(None, min_length=2, max_length=160)
    financing_choice: Literal["increase", "normal", "sca", "self"] | None = None


class Turn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(..., ge=0)
    request_id: str = Field(..., min_length=8, max_length=100)
    text: str = Field("", max_length=3000)
    updates: Facts | None = None
    action: Literal["answer", "repeat", "explain", "pause", "resume", "confirm_change", "discard_change",
                    "confirm_location", "change_location", "confirm_business", "alternatives", "suggest_names", "confirm_estimate", "confirm_rent", "accept_regional_risk", "explore_alternatives", "align_odop", "use_operating_estimate", "accept_financial_risk", "compare_recommendations", "recommendation_details"] = "answer"
    correction: bool = False
    source: Literal["text", "voice", "control"] = "text"
    language: Literal["en", "hi", "mr", "ta", "te", "kn"] = "en"
    recommendation_id: str | None = Field(None, max_length=100)


class LocationSelection(BaseModel):
    revision: int = Field(..., ge=0)
    state_code: int
    district_code: int
    block_code: int
    village_code: int
    # Legacy clients may send this; the server no longer uses user-selected area status.
    verified_is_rural: bool | None = None
    language: Literal["en", "hi", "mr", "ta", "te", "kn"] = "en"


class GPSRequest(BaseModel):
    revision: int = Field(..., ge=0)
    latitude: float = Field(..., ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(..., ge=-180, le=180, allow_inf_nan=False)
    accuracy: float = Field(..., ge=0, allow_inf_nan=False)
    language: Literal["en", "hi", "mr", "ta", "te", "kn"] = "en"


def new_session(profile: dict[str, Any]) -> dict:
    fields = {}
    for key in ("name", "gender", "promoter_category", "phone", "email"):
        value = profile.get(key)
        if key == 'email' and value and (value == f"{profile.get('firebase_uid')}@udyam.gov.in" or value.endswith('@evaluator.invalid')):
            continue
        if value and (key != "gender" or value != "Unspecified" or profile.get("promoter_category")):
            fields[key] = {"value": value, "source": "profile", "confirmed": True, "valid": True,
                           "required": True, "dependencies": [], "changed": False}
    return {"version": 1, "revision": 0, "fields": fields, "history": [], "pending_changes": {},
            "location": None, "physical_location": None, "location_confirmed": False,
            "classification": None, "business_confirmed": False, "regional": None,
            "odop": None, "recommendations": [], "rejected": [], "estimate": None,
            "assessment": None, "paused": False, "next": None, "processed_requests": []}
