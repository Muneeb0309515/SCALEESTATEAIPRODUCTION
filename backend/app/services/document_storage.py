"""S3 document storage through the managed server-side presign API.

Document metadata, access checks, versions, and audit entries remain in the
organization-scoped data store; file bytes never enter the database or project tree.
"""
from pathlib import PurePath
from uuid import uuid4
import httpx
from fastapi import HTTPException, UploadFile
from ..core.config import get_settings

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
}

def _safe_filename(filename: str | None) -> str:
    name = PurePath(filename or "document").name
    return "".join(character for character in name if character.isalnum() or character in {".", "-", "_"}) or "document"

async def put_document(organization_id: str, uploaded_file: UploadFile) -> tuple[str, str]:
    settings = get_settings()
    if not settings.built_in_forge_api_url or not settings.built_in_forge_api_key:
        raise HTTPException(status_code=503, detail={"code": "STORAGE_UNAVAILABLE", "message": "Managed server-side storage is not available."})
    if uploaded_file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail={"code": "UNSUPPORTED_DOCUMENT_TYPE", "message": "Only supported PDF, Word, and image document types can be uploaded."})
    key = f"organizations/{organization_id}/documents/{uuid4().hex}_{_safe_filename(uploaded_file.filename)}"
    headers = {"Authorization": f"Bearer {settings.built_in_forge_api_key}"}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            presign = await client.get(f"{settings.built_in_forge_api_url.rstrip('/')}/v1/storage/presign/put", params={"path": key}, headers=headers)
            presign.raise_for_status()
            s3_url = presign.json().get("url")
            if not s3_url:
                raise RuntimeError("Storage presign response did not include a URL")
            payload = await uploaded_file.read()
            upload = await client.put(s3_url, content=payload, headers={"Content-Type": uploaded_file.content_type})
            upload.raise_for_status()
    except (httpx.HTTPError, RuntimeError) as error:
        raise HTTPException(status_code=502, detail={"code": "DOCUMENT_UPLOAD_FAILED", "message": "The document could not be stored securely."}) from error
    return key, f"/manus-storage/{key}"

async def get_document_url(key: str) -> str:
    settings = get_settings()
    if not settings.built_in_forge_api_url or not settings.built_in_forge_api_key:
        raise HTTPException(status_code=503, detail={"code": "STORAGE_UNAVAILABLE", "message": "Managed server-side storage is not available."})
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{settings.built_in_forge_api_url.rstrip('/')}/v1/storage/presign/get", params={"path": key}, headers={"Authorization": f"Bearer {settings.built_in_forge_api_key}"})
            response.raise_for_status()
            url = response.json().get("url")
            if not url:
                raise RuntimeError("Storage presign response did not include a URL")
            return url
    except (httpx.HTTPError, RuntimeError) as error:
        raise HTTPException(status_code=502, detail={"code": "DOCUMENT_ACCESS_FAILED", "message": "The document access URL could not be created."}) from error
