from datetime import date
from pydantic import BaseModel, Field, model_validator


class ComparableCandidate(BaseModel):
    comparable_id: str
    sale_price: float = Field(gt=0)
    distance_miles: float = Field(ge=0)
    sale_date: date
    living_area_deviation: float = Field(ge=0)
    distance_score: float = Field(ge=0, le=1)
    recency_score: float = Field(ge=0, le=1)
    similarity_score: float = Field(ge=0, le=1)
    quality_score: float = Field(ge=0, le=1)
    selected_by_user: bool | None = None
    override_reason: str | None = None


class ComparableConfiguration(BaseModel):
    search_date: date
    max_distance_miles: float = Field(gt=0)
    max_sale_age_days: int = Field(gt=0)
    max_living_area_deviation: float = Field(ge=0)
    minimum_comparable_count: int = Field(default=3, ge=1)
    distance_weight: float = 0.35
    recency_weight: float = 0.25
    similarity_weight: float = 0.25
    quality_weight: float = 0.15
    outlier_mad_multiplier: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_weights(self):
        if round(self.distance_weight + self.recency_weight + self.similarity_weight + self.quality_weight, 8) != 1:
            raise ValueError("Comparable scoring weights must total 1.0")
        return self


class ComparableReview(BaseModel):
    comparable_id: str
    eligible: bool
    excluded_reason: str | None = None
    outlier: bool = False
    outlier_score: float | None = None
    comp_score: float | None = None
    effective_weight: float | None = None
    user_override_applied: bool = False
    audit_event_required: bool = False


class ComparableAnalysis(BaseModel):
    reviews: list[ComparableReview]
    weighted_arv: float | None
    arv_state: str
    arv_reason: str | None = None
    weighted_arv_formula: str = "ARV = Σ(Adjusted Comp Value × Normalized Weight)"
    included_comparable_count: int
    median_sale_price: float | None
    median_absolute_deviation: float | None
    configuration: ComparableConfiguration
