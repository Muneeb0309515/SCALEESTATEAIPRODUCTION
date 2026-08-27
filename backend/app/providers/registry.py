"""Provider registry retains vendor independence and does not guess vendor endpoint contracts."""
import os
from fastapi import HTTPException
from .base import PropertySearchProvider


def get_property_provider() -> PropertySearchProvider:
    provider_name = os.getenv("PROPERTY_DATA_PROVIDER")
    if provider_name not in {"rapidapi", "batchdata"} or not os.getenv("PROPERTY_DATA_API_KEY"):
        raise HTTPException(status_code=503, detail={"code": "CONFIGURATION_REQUIRED", "message": "Configure an approved provider adapter and server-only credential before property retrieval."})
    raise HTTPException(status_code=501, detail={"code": "ADAPTER_ENDPOINT_REQUIRED", "message": f"The {provider_name} adapter is intentionally unavailable until its user-approved endpoint contract is configured; no provider response is fabricated."})
