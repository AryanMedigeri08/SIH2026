"""Optional business-synergy advice; never a financial/eligibility override."""
from typing import Annotated, Literal
import math
from pydantic import BaseModel, ConfigDict, Field, field_validator

ShortText = Annotated[str, Field(min_length=1, max_length=350)]


class HybridRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    consent: Literal[True]
    state_name: str = Field(min_length=1, max_length=100)
    district_name: str = Field(min_length=1, max_length=100)
    block_name: str = Field("", max_length=100)
    village_name: str = Field("", max_length=100)
    enterprise_name: str = Field(min_length=1, max_length=160)
    business_category: Literal["manufacturing", "service"]
    sector: str = Field(min_length=1, max_length=80)
    idea_description: str = Field("", max_length=1000)


class HybridAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    score: int = Field(ge=0, le=100, strict=True)
    summary: ShortText
    hybrid_name: str = Field(min_length=1, max_length=160)
    hybrid_description: str = Field(min_length=1, max_length=600)
    reasons: list[ShortText] = Field(min_length=1, max_length=3)
    practical_steps: list[ShortText] = Field(min_length=1, max_length=3)
    risks: list[ShortText] = Field(max_length=3)
    missing_information: list[ShortText] = Field(max_length=3)

    @field_validator("score", mode="before")
    @classmethod
    def exact_integer_score(cls, value):
        # JSON providers may serialize an integer as 85.0. Accept only that exact
        # numeric representation; never round fractions or coerce strings/bools.
        if isinstance(value, float) and math.isfinite(value) and value.is_integer():
            return int(value)
        return value
