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


def integration_readiness() -> dict[str, str]:
    """Return configuration status only; never include secret values or connection strings."""
    settings = get_settings()
    provider_configured = (
        os.getenv("PROPERTY_DATA_PROVIDER") == "realtyapi"
        and bool(settings.realtyapi_api_key)
        and bool(settings.realtyapi_base_url)
    )
    return {
        "realtyapi": "REALTYAPI_CONFIGURED" if provider_configured else "REALTYAPI_NOT_CONFIGURED",
        "supabase": "SUPABASE_CONFIGURED" if settings.has_project_supabase_connection else "SUPABASE_NOT_CONFIGURED",
    }


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
