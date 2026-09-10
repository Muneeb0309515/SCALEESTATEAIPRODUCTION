from abc import ABC, abstractmethod
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class CanonicalProperty(BaseModel):
    """Normalized immutable property view with data origin retained per provider record."""
    provider_property_id: str
    address: str
    city: str
    state: str
    zip_code: str
    latitude: float | None = None
    longitude: float | None = None
    property_type: str
    list_price: float | None = None
    listing_url: str | None = None
    primary_photo: str | None = None
    beds: int | None = None
    baths: float | None = None
    living_area: int | None = None
    lot_size: int | None = None
    year_built: int | None = None
    estimated_market_value: float | None = None
    estimated_market_value_confidence: Literal["verified", "estimated", "inferred"] | None = None
    listing_status: str | None = None
    days_on_market: int | None = Field(default=None, ge=0)
    source: Literal["rapidapi", "batchdata", "realtyapi"]
    data_updated_at: datetime


class PropertySearchProvider(ABC):
    @abstractmethod
    async def search(self, city: str, state: str, filters: dict) -> list[CanonicalProperty]: ...


class PropertyDetailsProvider(ABC):
    @abstractmethod
    async def get_details(self, property_id: str) -> CanonicalProperty: ...


class OwnerDataProvider(ABC):
    @abstractmethod
    async def get_owner(self, property_id: str) -> dict: ...


class SalesHistoryProvider(ABC):
    @abstractmethod
    async def get_sales(self, city: str, state: str) -> list[dict]: ...
