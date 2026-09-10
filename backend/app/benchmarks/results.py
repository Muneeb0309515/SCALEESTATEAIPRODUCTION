"""Structured results for repeatable property-to-outreach benchmark runs."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkStatus(str, Enum):
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class BenchmarkStep(str, Enum):
    SEARCH = "SEARCH"
    DETAIL = "DETAIL"
    INTELLIGENCE = "INTELLIGENCE"
    DISTRESS = "DISTRESS"
    MOTIVATION = "MOTIVATION"
    COMPS = "COMPS"
    ARV = "ARV"
    DEAL_ANALYSIS = "DEAL_ANALYSIS"
    QUALIFICATION = "QUALIFICATION"
    CRM = "CRM"
    OUTREACH = "OUTREACH"


class BenchmarkStepResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: BenchmarkStatus
    message: str | None = Field(default=None, max_length=2000)
    evidence: list[str] = Field(default_factory=list)
    source_url: str | None = None


class BenchmarkWorkflowResult(BaseModel):
    """One honest execution record for one real or explicitly unavailable property."""

    model_config = ConfigDict(extra="forbid")

    property_id: str = Field(min_length=1, max_length=200)
    county: str = Field(min_length=1, max_length=120)
    source: str = Field(min_length=1, max_length=120)
    source_timestamp: str | None = None
    distress_signals: list[str] = Field(default_factory=list)
    motivation: str | None = None
    arv: float | None = None
    mao: float | None = None
    opportunity: str | None = None
    confidence: str | None = None
    risk: str | None = None
    steps: dict[BenchmarkStep, BenchmarkStepResult]
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def failed_steps(self) -> list[BenchmarkStep]:
        return [step for step, result in self.steps.items() if result.status == BenchmarkStatus.FAIL]

    def incomplete_steps(self) -> list[BenchmarkStep]:
        return [step for step, result in self.steps.items() if result.status in {BenchmarkStatus.PARTIAL, BenchmarkStatus.UNKNOWN}]
