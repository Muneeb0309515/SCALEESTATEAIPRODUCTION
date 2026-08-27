from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, model_validator


class DataClassification(str, Enum):
    SOURCE_DATA = "SOURCE_DATA"
    NORMALIZED_DATA = "NORMALIZED_DATA"
    CALCULATED_DATA = "CALCULATED_DATA"
    AI_ESTIMATE = "AI_ESTIMATE"
    USER_INPUT = "USER_INPUT"
    UNKNOWN = "UNKNOWN"


class ResultState(str, Enum):
    CALCULATED = "CALCULATED"
    UNKNOWN = "UNKNOWN"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    INVALID_INPUT = "INVALID_INPUT"
    DATA_CONFLICT = "DATA_CONFLICT"
    CONFIGURATION_REQUIRED = "CONFIGURATION_REQUIRED"


class ProvenancedNumber(BaseModel):
    classification: DataClassification
    value: float | None = None
    source: str | None = None
    confidence: str | None = None

    @model_validator(mode="after")
    def enforce_unknown_without_value(self):
        if self.classification == DataClassification.UNKNOWN and self.value is not None:
            raise ValueError("UNKNOWN values cannot carry a numeric amount")
        return self


class AnalysisAssumptions(BaseModel):
    mao_percentage: ProvenancedNumber | None = None
    desired_profit: ProvenancedNumber | None = None
    transaction_costs: ProvenancedNumber | None = None
    holding_costs: ProvenancedNumber | None = None
    financing_costs: ProvenancedNumber | None = None
    other_costs: ProvenancedNumber | None = None
    total_invested_capital: ProvenancedNumber | None = None


class AnalysisInput(BaseModel):
    arv: ProvenancedNumber | None = None
    estimated_market_value: ProvenancedNumber | None = None
    outstanding_debt: ProvenancedNumber | None = None
    repair_cost: ProvenancedNumber | None = None
    purchase_contract_price: ProvenancedNumber | None = None
    expected_assignment_price: ProvenancedNumber | None = None
    asking_price: ProvenancedNumber | None = None
    expected_sale_price: ProvenancedNumber | None = None
    net_profit: ProvenancedNumber | None = None
    assumptions: AnalysisAssumptions = Field(default_factory=AnalysisAssumptions)


class MetricResult(BaseModel):
    state: ResultState
    value: float | None = None
    classification: DataClassification = DataClassification.CALCULATED_DATA
    formula: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = None


class AnalysisResult(BaseModel):
    arv: MetricResult
    equity: MetricResult
    mao: MetricResult
    wholesale_spread: MetricResult
    wholesale_margin: MetricResult
    flip_profit: MetricResult
    roi: MetricResult
    price_vs_comps: MetricResult
    price_vs_arv: MetricResult
    deal_score: MetricResult
    risk_score: MetricResult
    classification: MetricResult
    explanation: list[str]
