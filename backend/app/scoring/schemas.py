from typing import Literal
from pydantic import BaseModel, Field, model_validator


class WeightedScoreInput(BaseModel):
    factors: dict[str, float] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_factor_ranges(self):
        invalid = [name for name, value in self.factors.items() if value < 0 or value > 1]
        if invalid:
            raise ValueError("Each factor score must be normalized between zero and one")
        return self


class WeightedScoreConfiguration(BaseModel):
    weights: dict[str, float] = Field(min_length=1)
    favorable_threshold: float = Field(ge=0, le=1)
    moderate_threshold: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_configuration(self):
        if round(sum(self.weights.values()), 8) != 1:
            raise ValueError("Configured factor weights must total 1.0")
        if self.moderate_threshold > self.favorable_threshold:
            raise ValueError("Moderate threshold cannot exceed favorable threshold")
        return self


class ClassificationConfiguration(BaseModel):
    strong_deal_score_minimum: float = Field(ge=0, le=1)
    moderate_deal_score_minimum: float = Field(ge=0, le=1)
    acceptable_risk_maximum: float = Field(ge=0, le=1)
    caution_risk_maximum: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_order(self):
        if self.moderate_deal_score_minimum > self.strong_deal_score_minimum or self.acceptable_risk_maximum > self.caution_risk_maximum:
            raise ValueError("Classification thresholds are not ordered")
        return self


class ClassificationResult(BaseModel):
    state: Literal["CALCULATED", "CONFIGURATION_REQUIRED"]
    label: Literal["STRONG_DEAL", "MODERATE_DEAL", "WEAK_DEAL", "HIGH_RISK", "UNKNOWN"]
    reason: str
