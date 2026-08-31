"""Production authentication and organization-membership boundary for operational routes."""
from dataclasses import dataclass
from functools import lru_cache
import logging
import os

import jwt
from fastapi import Header, HTTPException
from jwt import PyJWKClient
from supabase import create_client

from .config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthenticatedIdentity:
    user_id: str
    email: str | None


@lru_cache(maxsize=8)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=300)


def _verify_supabase_access_token(token: str, supabase_url: str) -> AuthenticatedIdentity:
    issuer = f"{supabase_url.rstrip('/')}/auth/v1"
    configured_jwks = (os.getenv("SUPABASE_JWKS_JSON") or "").strip()
    jwks_url = configured_jwks if configured_jwks.startswith("https://") else f"{issuer}/.well-known/jwks.json"
    signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256"],
        audience="authenticated",
        issuer=issuer,
        leeway=10,
    )
    user_id = claims.get("sub")
    if not user_id:
        raise jwt.InvalidTokenError("JWT subject is missing")
    return AuthenticatedIdentity(user_id=str(user_id), email=claims.get("email"))


def require_authenticated_identity(authorization: str | None = Header(default=None)) -> AuthenticatedIdentity:
    settings = get_settings()
    if not settings.has_project_supabase_connection:
        raise HTTPException(status_code=503, detail={"code": "CONFIGURATION_REQUIRED", "message": "Authentication is disabled in the standalone preview; production access requires the approved authentication configuration."})
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED", "message": "A valid bearer access token is required."})
    try:
        return _verify_supabase_access_token(authorization.removeprefix("Bearer ").strip(), settings.supabase_project_url)
    except Exception as error:
        token_issuer = None
        try:
            token_issuer = jwt.decode(authorization.removeprefix("Bearer ").strip(), options={"verify_signature": False}).get("iss")
        except Exception:
            pass
        expected_issuer = f"{settings.supabase_project_url.rstrip('/')}/auth/v1" if settings.supabase_project_url else None
        logger.warning("Supabase access-token verification failed: %s: %s; expected_issuer=%s token_issuer=%s", type(error).__name__, str(error)[:160], expected_issuer, token_issuer)
        raise HTTPException(status_code=401, detail={"code": "INVALID_SESSION", "message": "The session could not be verified."}) from error


def require_organization_member(
    identity: AuthenticatedIdentity,
    x_organization_id: str | None = Header(default=None),
) -> str:
    if not x_organization_id:
        raise HTTPException(status_code=400, detail={"code": "ORGANIZATION_REQUIRED", "message": "An organization identifier is required for operational data access."})
    settings = get_settings()
    try:
        result = create_client(settings.supabase_project_url, settings.supabase_key).table("organization_memberships").select("organization_id").eq("organization_id", x_organization_id).eq("user_id", identity.user_id).limit(1).execute()
    except Exception as error:
        raise HTTPException(status_code=503, detail={"code": "AUTHORIZATION_UNAVAILABLE", "message": "Organization membership could not be verified."}) from error
    if not result.data:
        raise HTTPException(status_code=403, detail={"code": "ORGANIZATION_ACCESS_DENIED", "message": "The authenticated user is not a member of this organization."})
    return x_organization_id
