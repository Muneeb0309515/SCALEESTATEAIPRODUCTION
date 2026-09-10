from fastapi import Depends, Header
from pydantic import BaseModel
from ..core.auth import AuthenticatedIdentity, require_authenticated_identity, require_organization_member


class OrganizationScope(BaseModel):
    organization_id: str
    user_id: str


def require_organization_scope(
    identity: AuthenticatedIdentity = Depends(require_authenticated_identity),
    x_organization_id: str | None = Header(default=None),
) -> OrganizationScope:
    organization_id = require_organization_member(identity, x_organization_id)
    return OrganizationScope(organization_id=organization_id, user_id=identity.user_id)
