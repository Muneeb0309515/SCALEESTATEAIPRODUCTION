"""Versioned benchmark contracts built on the existing canonical property shape.

The benchmark layer intentionally stores evidence and provenance separately from
provider normalization. It can represent Texas today and other states later
without changing the core property schema.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..providers.base import CanonicalProperty


class DataProvenance(str, Enum):
    SOURCE = "SOURCE"
    NORMALIZED = "NORMALIZED"
    CALCULATED = "CALCULATED"
    AI_ESTIMATE = "AI_ESTIMATE"
    USER_INPUT = "USER_INPUT"
    UNKNOWN = "UNKNOWN"


class BenchmarkSignal(BaseModel):
    """One evidence-backed signal; absence is represented by no signal, not false evidence."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    value: bool | None = None
    provenance: DataProvenance
    source: str | None = None
    source_url: str | None = None
    observed_at: datetime | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def require_evidence_for_positive_signal(self) -> "BenchmarkSignal":
        if self.value is True and self.provenance in {DataProvenance.UNKNOWN, DataProvenance.AI_ESTIMATE} and not self.source:
            raise ValueError("positive benchmark signals require source evidence or an explicit source")
        return self


class BenchmarkValue(BaseModel):
    """A scalar benchmark value with explicit origin."""

    value: Any = None
    provenance: DataProvenance = DataProvenance.UNKNOWN
    source: str | None = None
    source_url: str | None = None
    observed_at: datetime | None = None


class BenchmarkProperty(BaseModel):
    """A benchmark record that extends, rather than replaces, CanonicalProperty."""

    model_config = ConfigDict(extra="forbid")

    canonical: CanonicalProperty
    county: str = Field(min_length=1, max_length=120)
    field_provenance: dict[str, DataProvenance] = Field(default_factory=dict)
    values: dict[str, BenchmarkValue] = Field(default_factory=dict)
    signals: list[BenchmarkSignal] = Field(default_factory=list)
    investor_signal: BenchmarkValue = Field(default_factory=BenchmarkValue)
    cash_sale_signal: BenchmarkValue = Field(default_factory=BenchmarkValue)
    motivation_score: BenchmarkValue = Field(default_factory=BenchmarkValue)
    opportunity_score: BenchmarkValue = Field(default_factory=BenchmarkValue)
    confidence_score: BenchmarkValue = Field(default_factory=BenchmarkValue)
    risk_score: BenchmarkValue = Field(default_factory=BenchmarkValue)

    @field_validator("county")
    @classmethod
    def normalize_county(cls, value: str) -> str:
        return " ".join(value.split()).title()

    @model_validator(mode="after")
    def keep_property_provenance_explicit(self) -> "BenchmarkProperty":
        for field_name in ("list_price", "estimated_market_value", "beds", "baths", "living_area", "year_built"):
            if getattr(self.canonical, field_name, None) is not None and field_name not in self.field_provenance:
                raise ValueError(f"provenance is required for canonical field: {field_name}")
        return self


class TexasBenchmarkManifest(BaseModel):
    """Configuration/data manifest for the initial two-county benchmark."""

    model_config = ConfigDict(extra="forbid")

    state: str = Field(min_length=2, max_length=2)
    counties: list[str] = Field(min_length=2, max_length=2)
    properties: list[BenchmarkProperty] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("state")
    @classmethod
    def normalize_state(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def require_two_distinct_counties(self) -> "TexasBenchmarkManifest":
        normalized = {" ".join(county.split()).title() for county in self.counties}
        if len(normalized) != 2:
            raise ValueError("benchmark requires exactly two distinct counties")
        if any(property_record.canonical.state.upper() != self.state for property_record in self.properties):
            raise ValueError("every benchmark property must belong to the manifest state")
        if any(property_record.county not in normalized for property_record in self.properties):
            raise ValueError("every benchmark property must belong to one of the manifest counties")
        return self

    def properties_for_county(self, county: str) -> list[BenchmarkProperty]:
        normalized = " ".join(county.split()).title()
        return [property_record for property_record in self.properties if property_record.county == normalized]
