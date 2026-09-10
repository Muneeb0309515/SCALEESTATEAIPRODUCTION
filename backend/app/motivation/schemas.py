from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class MotivationInput(BaseModel):
    estimated_equity: float | None = Field(default=None, ge=0)
    estimated_market_value: float | None = Field(default=None, gt=0)
    ownership_duration_years: float | None = Field(default=None, ge=0)
    tax_delinquent: bool | None = None
    foreclosure_related: bool | None = None
    vacant: bool | None = None
    expired_listing: bool | None = None
    withdrawn_listing: bool | None = None
    days_on_market: int | None = Field(default=None, ge=0)
    probate_related: bool | None = None
    entity_ownership: bool | None = None
    distressed_property: bool | None = None
    source: str = Field(min_length=1)
    source_confidence: Literal["verified", "estimated", "inferred"]
    detected_at: datetime


class MotivationSignal(BaseModel):
    signal_type: str
    evidence: str
    source: str
    confidence: str
    detected_at: datetime


class MotivationResult(BaseModel):
    signals: list[MotivationSignal]
    motivation_score_state: Literal["CONFIGURATION_REQUIRED"]
    confidence_state: Literal["CONFIGURATION_REQUIRED"]
    explanation: str
