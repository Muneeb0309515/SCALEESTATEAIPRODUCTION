"""Public canonical response contract for persisted properties."""
from __future__ import annotations

from typing import Any


def canonical_property_response(record: dict[str, Any]) -> dict[str, Any]:
    """Map a persisted row to the provider-independent public property shape."""
    return {
        "organization_property_id": record.get("id"),
        "provider_property_id": record.get("provider_property_id"),
        "provider_listing_id": record.get("provider_listing_id"),
        "address": record.get("address") or "UNKNOWN",
        "city": record.get("city") or "UNKNOWN",
        "state": record.get("state") or "UNKNOWN",
        "zip_code": record.get("zip") or "UNKNOWN",
        "latitude": record.get("latitude"),
        "longitude": record.get("longitude"),
        "property_type": record.get("property_type") or "UNKNOWN",
        "list_price": record.get("list_price"),
        "listing_url": record.get("listing_url"),
        "primary_photo": record.get("primary_photo"),
        "photos": record.get("photos") or [],
        "beds": record.get("beds"),
        "baths": record.get("baths"),
        "living_area": record.get("living_area"),
        "lot_size": record.get("lot_size"),
        "year_built": record.get("year_built"),
        "estimated_market_value": record.get("estimated_market_value", record.get("estimated_value")),
        "listing_status": record.get("listing_status"),
        "days_on_market": record.get("days_on_market"),
        "source": record.get("source") or "UNKNOWN",
        "data_updated_at": record.get("data_updated_at"),
        "source_retrieved_at": record.get("source_retrieved_at"),
        "last_seen_at": record.get("last_seen_at"),
        "provenance": record.get("provenance") or {},
    }
