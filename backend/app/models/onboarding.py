from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class OnboardingLocation(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    state_name: str = Field('', max_length=100)
    district_name: str = Field('', max_length=100)
    block_name: str = Field('', max_length=100)
    village_name: str = Field('', max_length=100)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    source: Literal['gps', 'manual'] = 'manual'
    confirmed: bool = False


class OnboardingDraft(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: Literal[1] = 1
    journey: Literal['existing', 'budget_only', 'idea_only'] | None = None
    language: Literal['en', 'hi', 'mr', 'ta', 'te', 'kn'] = 'en'
    location: OnboardingLocation | None = None
    answers: dict[str, str | float | bool | None] = Field(default_factory=dict, max_length=30)
    completed: bool = False


class GpsRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class OnboardingAnswer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    field: str = Field(max_length=40)
    value: str | float | bool | None
    hybrid_name: str | None = Field(None, max_length=160)
    hybrid_description: str | None = Field(None, max_length=600)

