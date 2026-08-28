from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from pydantic import BaseModel, Field

from ..core.config import get_settings
from .base import CanonicalProperty


class RealtySearchCriteria(BaseModel):
    location: str = Field(min_length=1, max_length=200)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    min_beds: int | None = Field(default=None, ge=0)
    max_beds: int | None = Field(default=None, ge=0)
    min_baths: float | None = Field(default=None, ge=0)
    property_type: str | None = None
    status: str | None = None


class RealtySearchResult(BaseModel):
    results: list[CanonicalProperty]
    total: int
    page: int
    has_next_page: bool
    provider: str = "realtyapi"
    retrieved_at: datetime


class RealtyApiAdapter:
    """Read-only RealtyAPI.io Realtor adapter with canonical source metadata."""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = (settings.realtyapi_base_url or "https://realtor.realtyapi.io").rstrip("/")
        self.api_key = settings.realtyapi_api_key

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    def _headers(self) -> dict[str, str]:
        return {"x-realtyapi-key": self.api_key} if self.api_key else {}

    async def search(self, criteria: RealtySearchCriteria) -> RealtySearchResult:
        if not self.configured:
            raise RuntimeError("REALTYAPI_API_KEY and REALTYAPI_BASE_URL are required")
        params: dict[str, Any] = {"location": criteria.location, "page": criteria.page, "limit": criteria.limit}
        for field in ("min_price", "max_price", "min_beds", "max_beds", "min_baths", "property_type", "status"):
            value = getattr(criteria, field)
            if value is not None:
                params[field] = value
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.base_url}/search/bylocation", params=params, headers=self._headers())
            response.raise_for_status()
            payload = response.json()
        raw_results = payload.get("searchResults", [])
        normalized_records = [record for item in raw_results if (record := self._normalize(item)) is not None]
        records = normalized_records[: criteria.limit]
        has_more_records = len(normalized_records) > criteria.limit
        return RealtySearchResult(results=records, total=int(payload.get("total", len(normalized_records))), page=criteria.page, has_next_page=bool(payload.get("nextPage", False)) or has_more_records, retrieved_at=datetime.now(timezone.utc))

    async def details_by_address(self, address: str) -> CanonicalProperty:
        if not self.configured:
            raise RuntimeError("REALTYAPI_API_KEY and REALTYAPI_BASE_URL are required")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.base_url}/details/byaddress", params={"address": address}, headers=self._headers())
            response.raise_for_status()
            payload = response.json()
        record = self._normalize(payload.get("detail", {}))
        if record is None:
            raise ValueError("RealtyAPI response did not contain a normalizable property detail")
        return record

    @staticmethod
    def _normalize(item: dict[str, Any]) -> CanonicalProperty | None:
        address = item.get("address") or {}
        if not address.get("line") or not address.get("city") or not address.get("state_code") or not address.get("postal_code"):
            return None
        details = item.get("details") or {}
        baths_raw = details.get("baths")
        try:
            baths = float(baths_raw) if baths_raw is not None else None
        except (TypeError, ValueError):
            baths = None
        photos = item.get("photos") or []
        return CanonicalProperty(
            provider_property_id=str(item.get("property_id") or item.get("listing_id") or ""),
            address=f"{address['line']}, {address['city']}, {address['state_code']} {address['postal_code']}",
            city=str(address["city"]), state=str(address["state_code"]), zip_code=str(address["postal_code"]),
            latitude=address.get("latitude"), longitude=address.get("longitude"),
            property_type=str(item.get("property_type") or details.get("type") or "UNKNOWN"),
            list_price=item.get("list_price"), listing_url=item.get("href"), primary_photo=item.get("primary_photo"),
            beds=details.get("beds", item.get("beds")), baths=baths, living_area=details.get("sqft", item.get("sqft")),
            lot_size=details.get("lot_sqft", item.get("lot_sqft")), year_built=details.get("year_built"),
            estimated_market_value=None, estimated_market_value_confidence=None,
            listing_status=item.get("status"), days_on_market=item.get("days_on_market"),
            source="realtyapi", data_updated_at=datetime.now(timezone.utc),
        )
