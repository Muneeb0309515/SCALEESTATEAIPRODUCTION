"""Supabase Auth and organization-membership boundary for operational routes."""
from dataclasses import dataclass
from fastapi import Header, HTTPException
from supabase import create_client
from .config import get_settings


@dataclass(frozen=True)
class AuthenticatedIdentity:
    user_id: str
    email: str | None


def require_authenticated_identity(authorization: str | None = Header(default=None)) -> AuthenticatedIdentity:
    settings = get_settings()
    if not settings.has_project_supabase_connection:
        raise HTTPException(status_code=503, detail={"code": "CONFIGURATION_REQUIRED", "message": "Authentication requires a validated direct Supabase project connection."})
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED", "message": "A valid bearer access token is required."})
    try:
        user = create_client(settings.supabase_url, settings.supabase_key).auth.get_user(authorization.removeprefix("Bearer ")).user
    except Exception as error:
        raise HTTPException(status_code=401, detail={"code": "INVALID_SESSION", "message": "The session could not be verified."}) from error
    if not user:
        raise HTTPException(status_code=401, detail={"code": "INVALID_SESSION", "message": "The session could not be verified."})
    return AuthenticatedIdentity(user_id=str(user.id), email=user.email)


def require_organization_member(
    identity: AuthenticatedIdentity,
    x_organization_id: str | None = Header(default=None),
) -> str:
    if not x_organization_id:
        raise HTTPException(status_code=400, detail={"code": "ORGANIZATION_REQUIRED", "message": "An organization identifier is required for operational data access."})
    settings = get_settings()
    try:
        result = create_client(settings.supabase_url, settings.supabase_key).table("organization_memberships").select("organization_id").eq("organization_id", x_organization_id).eq("user_id", identity.user_id).limit(1).execute()
    except Exception as error:
        raise HTTPException(status_code=503, detail={"code": "AUTHORIZATION_UNAVAILABLE", "message": "Organization membership could not be verified."}) from error
    if not result.data:
        raise HTTPException(status_code=403, detail={"code": "ORGANIZATION_ACCESS_DENIED", "message": "The authenticated user is not a member of this organization."})
    return x_organization_id
