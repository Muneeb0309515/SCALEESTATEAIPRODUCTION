"""Provider registry for approved property-data adapters."""
import os
from fastapi import HTTPException
from .base import PropertySearchProvider
from .realtyapi import RealtyApiAdapter


def get_property_provider() -> PropertySearchProvider:
    provider_name = os.getenv("PROPERTY_DATA_PROVIDER")
    if provider_name == "realtyapi" and os.getenv("REALTYAPI_API_KEY") and os.getenv("REALTYAPI_BASE_URL"):
        return RealtyApiAdapter()
    if provider_name in {"rapidapi", "batchdata"} and os.getenv("PROPERTY_DATA_API_KEY"):
        raise HTTPException(status_code=501, detail={"code": "ADAPTER_ENDPOINT_REQUIRED", "message": f"The {provider_name} adapter is not enabled until its approved endpoint contract is configured."})
    raise HTTPException(status_code=503, detail={"code": "CONFIGURATION_REQUIRED", "message": "Configure the approved property provider and server-only credential before property retrieval."})
