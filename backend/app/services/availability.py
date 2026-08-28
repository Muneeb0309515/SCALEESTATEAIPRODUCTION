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
        raise IntegrationUnavailable("CONFIGURATION_REQUIRED", "Organization data is disabled in the standalone preview; production persistence requires the approved data configuration.")


def require_property_provider() -> str:
    provider = os.getenv("PROPERTY_DATA_PROVIDER")
    if provider == "realtyapi" and os.getenv("REALTYAPI_API_KEY") and os.getenv("REALTYAPI_BASE_URL"):
        return provider
    if provider in {"rapidapi", "batchdata"} and os.getenv("PROPERTY_DATA_API_KEY"):
        return provider
    raise IntegrationUnavailable("CONFIGURATION_REQUIRED", "Property search requires an approved configured provider; no records are fabricated.")


def require_document_storage() -> None:
    require_project_database()
    settings = get_settings()
    if not settings.built_in_forge_api_url or not settings.built_in_forge_api_key:
        raise IntegrationUnavailable("CONFIGURATION_REQUIRED", "Versioned document storage requires managed server-side S3 access.")
