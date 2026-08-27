"""Organization-scoped production data access. Every query carries the organization id."""
from typing import Any
from supabase import create_client
from ..core.config import get_settings
from ..services.availability import require_project_database


class OrganizationRepository:
    def __init__(self, organization_id: str):
        require_project_database()
        settings = get_settings()
        self.organization_id = organization_id
        self.client = create_client(settings.supabase_url, settings.supabase_key)

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

    def append_activity(self, activity_type: str, description: str, user_id: str, deal_id: str | None = None, details: dict[str, Any] | None = None) -> None:
        self.client.table("activities").insert({"organization_id": self.organization_id, "deal_id": deal_id, "user_id": user_id, "activity_type": activity_type, "description": description, "details": details or {}}).execute()

    def append_audit(self, entity_type: str, entity_id: str | None, action: str, user_id: str, old_value: dict[str, Any] | None = None, new_value: dict[str, Any] | None = None) -> None:
        self.client.table("audit_logs").insert({"organization_id": self.organization_id, "entity_type": entity_type, "entity_id": entity_id, "action": action, "old_value": old_value, "new_value": new_value, "changed_by": user_id}).execute()
