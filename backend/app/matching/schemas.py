from pydantic import BaseModel, Field, model_validator


class DealCandidate(BaseModel):
    market: str
    zip_code: str
    property_type: str
    purchase_price: float | None = Field(default=None, ge=0)
    arv: float | None = Field(default=None, ge=0)
    wholesale_spread: float | None = None
    requires_financing: bool
    buyer_activity_score: float | None = Field(default=None, ge=0, le=1)


class BuyerCriteria(BaseModel):
    buyer_id: str
    markets: set[str] = set()
    zip_codes: set[str] = set()
    property_types: set[str] = set()
    price_min: float | None = Field(default=None, ge=0)
    price_max: float | None = Field(default=None, ge=0)
    arv_min: float | None = Field(default=None, ge=0)
    arv_max: float | None = Field(default=None, ge=0)
    minimum_spread: float | None = None
    cash_only: bool = False
    financing_available: bool = False

    @model_validator(mode="after")
    def validate_ranges(self):
        if self.price_min is not None and self.price_max is not None and self.price_min > self.price_max:
            raise ValueError("price minimum cannot exceed price maximum")
        if self.arv_min is not None and self.arv_max is not None and self.arv_min > self.arv_max:
            raise ValueError("ARV minimum cannot exceed ARV maximum")
        return self


class MatchConfiguration(BaseModel):
    """Weights retain design-doc.md factors; the engine normalizes their documented sum."""
    market_weight: float = 0.20
    zip_weight: float = 0.20
    property_type_weight: float = 0.15
    price_weight: float = 0.15
    arv_weight: float = 0.10
    spread_weight: float = 0.05
    financing_weight: float = 0.05
    activity_weight: float = 0.05
    high_confidence_threshold: float
    medium_confidence_threshold: float

    @model_validator(mode="after")
    def validate_scoring_configuration(self):
        if sum([self.market_weight, self.zip_weight, self.property_type_weight, self.price_weight, self.arv_weight, self.spread_weight, self.financing_weight, self.activity_weight]) <= 0:
            raise ValueError("buyer-match weights must have a positive total")
        if not 0 <= self.medium_confidence_threshold <= self.high_confidence_threshold <= 1:
            raise ValueError("confidence thresholds must be ordered between zero and one")
        return self


class BuyerMatch(BaseModel):
    buyer_id: str
    match_score: float
    confidence: str
    factor_scores: dict[str, float]
    match_reasons: list[str]
    failed_criteria: list[str]
    configuration: MatchConfiguration
