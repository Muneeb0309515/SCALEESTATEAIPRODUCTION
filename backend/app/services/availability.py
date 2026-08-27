"""Fail-closed integration guards used before any external data operation."""
from dataclasses import dataclass
import os
from ..core.config import get_settings


@dataclass(frozen=True)
class IntegrationUnavailable(Exception):
    code: str
    message: str


def require_project_database() -> None:
    if not get_settings().has_project_supabase_connection:
        raise IntegrationUnavailable("CONFIGURATION_REQUIRED", "Organization data requires a validated direct Supabase project connection.")


def require_property_provider() -> str:
    provider = os.getenv("PROPERTY_DATA_PROVIDER")
    if provider not in {"rapidapi", "batchdata"} or not os.getenv("PROPERTY_DATA_API_KEY"):
        raise IntegrationUnavailable("CONFIGURATION_REQUIRED", "Property search requires an approved configured provider; no records are fabricated.")
    return provider


def require_document_storage() -> None:
    require_project_database()
    if not get_settings().document_bucket:
        raise IntegrationUnavailable("CONFIGURATION_REQUIRED", "Versioned document storage requires a restricted S3 document bucket.")
