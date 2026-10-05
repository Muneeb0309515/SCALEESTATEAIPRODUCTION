"""Organization-scoped production data access. Every query carries the organization id."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from supabase import create_client

from ..core.config import get_settings
from ..providers.base import CanonicalProperty
from ..services.availability import require_project_database


class PropertyPersistenceError(RuntimeError):
    """Safe, actionable persistence failure without leaking database internals."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class OrganizationRepository:
    def __init__(self, organization_id: str):
        require_project_database()
        settings = get_settings()
        self.organization_id = organization_id
        self.client = create_client(settings.supabase_project_url, settings.supabase_key)

    def list(self, table: str, order_column: str = "created_at") -> list[dict[str, Any]]:
        return self.client.table(table).select("*").eq("organization_id", self.organization_id).order(order_column, desc=True).execute().data

    def get(self, table: str, record_id: str) -> dict[str, Any] | None:
        response = self.client.table(table).select("*").eq("organization_id", self.organization_id).eq("id", record_id).limit(1).execute()
        return response.data[0] if response.data else None

    def require_record(self, table: str, record_id: str, entity_label: str) -> dict[str, Any]:
        record = self.get(table, record_id)
        if not record:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail={"code": f"{entity_label.upper()}_NOT_FOUND", "message": f"No {entity_label.lower()} was found in this organization."})
        return record

    def create(self, table: str, values: dict[str, Any]) -> dict[str, Any]:
        response = self.client.table(table).insert({**values, "organization_id": self.organization_id}).execute()
        return response.data[0]

    def upsert_property(self, property_record: CanonicalProperty) -> dict[str, Any]:
        """Persist one provider-backed canonical property without crossing organizations.

        Provider identity is scoped by organization and source. Existing known values are
        retained when a later provider response omits a field; missing values are recorded
        as UNKNOWN in property_fields rather than inferred or replacing known facts.
        """
        if not property_record.provider_property_id:
            raise ValueError("A provider property identifier is required for durable persistence")

        retrieved_at = (property_record.source_retrieved_at or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        provider_updated_at = property_record.data_updated_at.astimezone(timezone.utc).isoformat() if property_record.data_updated_at else None
        source_values = self._property_values(property_record)
        try:
            lookup = (
                self.client.table("properties")
                .select("*")
                .eq("organization_id", self.organization_id)
                .eq("source", property_record.source)
                .eq("provider_property_id", property_record.provider_property_id)
                .limit(1)
                .execute()
            )
            existing = lookup.data[0] if lookup.data else None
            provenance = self._provenance(property_record, retrieved_at)
            metadata = {
                "source_retrieved_at": retrieved_at,
                "data_updated_at": provider_updated_at,
                "last_seen_at": retrieved_at,
                "provenance": provenance,
            }

            if existing:
                updates = {key: value for key, value in source_values.items() if self._has_value(value)}
                updates.update(metadata)
                response = (
                    self.client.table("properties")
                    .update(updates)
                    .eq("organization_id", self.organization_id)
                    .eq("id", existing["id"])
                    .execute()
                )
                record = response.data[0] if response.data else {**existing, **updates}
            else:
                record = self.create("properties", {**source_values, **metadata})

            self._persist_property_fields(record["id"], property_record, retrieved_at)
            return record
        except PropertyPersistenceError:
            raise
        except Exception as error:
            detail = str(error).lower()
            if "unique" in detail or "duplicate" in detail:
                raise PropertyPersistenceError("PROPERTY_PERSISTENCE_CONFLICT", "The property already exists or conflicts with an existing property field.") from error
            raise PropertyPersistenceError("PROPERTY_PERSISTENCE_FAILED", "The property could not be persisted to the organization workspace.") from error

    def upsert_properties(self, property_records: list[CanonicalProperty]) -> list[dict[str, Any]]:
        return [self.upsert_property(property_record) for property_record in property_records]

    def _persist_property_fields(self, property_id: str, property_record: CanonicalProperty, retrieved_at: str) -> None:
        for field_name, value in self._property_values(property_record).items():
            field_values = {
                "organization_id": self.organization_id,
                "property_id": property_id,
                "field_name": field_name,
                "value": value,
                "classification": "SOURCE_DATA" if self._has_value(value) else "UNKNOWN",
                "source": property_record.source if self._has_value(value) else None,
                "confidence": "VERIFIED" if self._has_value(value) else "UNKNOWN",
                "updated_at": retrieved_at,
            }
            existing = (
                self.client.table("property_fields")
                .select("*")
                .eq("organization_id", self.organization_id)
                .eq("property_id", property_id)
                .eq("field_name", field_name)
                .limit(1)
                .execute()
            )
            if existing.data:
                self.client.table("property_fields").update(field_values).eq("organization_id", self.organization_id).eq("id", existing.data[0]["id"]).execute()
            else:
                self.client.table("property_fields").insert(field_values).execute()

    @staticmethod
    def _property_values(property_record: CanonicalProperty) -> dict[str, Any]:
        return {
            "source": property_record.source,
            "provider_property_id": property_record.provider_property_id,
            "provider_listing_id": property_record.provider_listing_id,
            "address": property_record.address,
            "city": property_record.city,
            "state": property_record.state,
            "zip": property_record.zip_code,
            "latitude": property_record.latitude,
            "longitude": property_record.longitude,
            "property_type": property_record.property_type,
            "list_price": property_record.list_price,
            "listing_url": property_record.listing_url,
            "primary_photo": property_record.primary_photo,
            "photos": property_record.photos,
            "beds": property_record.beds,
            "baths": property_record.baths,
            "living_area": property_record.living_area,
            "lot_size": property_record.lot_size,
            "year_built": property_record.year_built,
            "listing_status": property_record.listing_status,
            "days_on_market": property_record.days_on_market,
        }

    @staticmethod
    def _provenance(property_record: CanonicalProperty, retrieved_at: str) -> dict[str, dict[str, str]]:
        provenance: dict[str, dict[str, str]] = {}
        for field_name, value in OrganizationRepository._property_values(property_record).items():
            if field_name in {"source", "provider_property_id", "provider_listing_id"}:
                continue
            provenance[field_name] = {
                "classification": "SOURCE_DATA" if OrganizationRepository._has_value(value) else "UNKNOWN",
                "source": property_record.source if OrganizationRepository._has_value(value) else "UNKNOWN",
                "retrieved_at": retrieved_at,
            }
        return provenance

    @staticmethod
    def _has_value(value: Any) -> bool:
        return value is not None and value != "" and value != [] and value != "UNKNOWN"

    def append_activity(self, activity_type: str, description: str, user_id: str, deal_id: str | None = None, details: dict[str, Any] | None = None) -> None:
        self.client.table("activities").insert({"organization_id": self.organization_id, "deal_id": deal_id, "user_id": user_id, "activity_type": activity_type, "description": description, "details": details or {}}).execute()

    def append_audit(self, entity_type: str, entity_id: str | None, action: str, user_id: str, old_value: dict[str, Any] | None = None, new_value: dict[str, Any] | None = None) -> None:
        self.client.table("audit_logs").insert({"organization_id": self.organization_id, "entity_type": entity_type, "entity_id": entity_id, "action": action, "old_value": old_value, "new_value": new_value, "changed_by": user_id}).execute()
