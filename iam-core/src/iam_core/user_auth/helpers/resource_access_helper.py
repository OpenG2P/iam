from fastapi import Request
from openg2p_fastapi_common.errors.http_exceptions import ForbiddenError

from ..enums import RequestStateKey
from .claims_helper import claims_from_auth


def enforce_resource_access(
    auth,
    allowed_roles: set[str],
    client_id: str | None = None,
):
    """Raise Forbidden when the principal lacks any of ``allowed_roles``."""
    claims = claims_from_auth(auth)
    client_roles = claims.get("client_roles") or {}

    if client_id:
        user_roles = set(client_roles.get(client_id, []))
    else:
        user_roles = set()
        for roles in client_roles.values():
            user_roles.update(roles)

    if not user_roles.intersection(allowed_roles):
        raise ForbiddenError(message="Forbidden. Insufficient resource_access roles.")
    return auth


def check_resource_access(
    request: Request,
    *,
    allowed_roles: set[str],
    client_id: str | None = None,
):
    """Like ``enforce_resource_access`` but reads ``request.state.auth``."""
    auth = getattr(request.state, RequestStateKey.AUTH, None)
    return enforce_resource_access(
        auth=auth,
        allowed_roles=allowed_roles,
        client_id=client_id,
    )
