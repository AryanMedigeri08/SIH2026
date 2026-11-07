"""Inputs for optional pre-wizard planning. No financial formulas live here."""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlanningRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)

    path: Literal["budget_only", "idea_only"]
    own_cash: Optional[float] = Field(None, ge=0, le=100000000)
    business_id: Optional[str] = Field(None, max_length=80)
    idea_description: str = Field("", max_length=800)
    # A quote means plant/equipment only, not total outlay or promoter equity.
    machinery_quote: Optional[float] = Field(None, gt=0, le=55000000)
    custom_sector: Literal["dairy", "food_processing", "repair", "apparel", "fabrication", "general"] = "general"
    custom_category: Literal["manufacturing", "service"] = "manufacturing"
    state_name: str = Field(..., min_length=1, max_length=100)
    district_name: str = Field(..., min_length=1, max_length=100)
    block_name: str = Field(..., min_length=1, max_length=100)
    village_name: str = Field(..., min_length=1, max_length=100)
    promoter_name: str = Field(..., min_length=1, max_length=100)
    promoter_category: Literal["general", "sc", "st", "obc", "women", "artisan", "women_shg"] = "general"
    gender: Literal["Male", "Female", "Other", "Unspecified"] = "Unspecified"
    is_rural: bool = True
    premise_type: Literal["owned", "rented", "panchayat"] = "owned"
    monthly_rent: float = Field(0, ge=0, le=1000000)

    @model_validator(mode="after")
    def check_path(self):
        if self.path == "budget_only" and self.own_cash is None:
            raise ValueError("Enter available own money, including zero if none is available.")
        if self.path == "idea_only" and not self.business_id:
            raise ValueError("Choose the business type that matches your idea.")
        if self.business_id == "custom" and (not self.machinery_quote or len(self.idea_description) < 10):
            raise ValueError("For another business, describe the product/service and enter a machinery/setup quote.")
        return self


class AcceptPlan(BaseModel):
    proposal_id: str = Field(..., min_length=1, max_length=80)
    acknowledge_estimates: bool = False
    accept_risks: bool = False
