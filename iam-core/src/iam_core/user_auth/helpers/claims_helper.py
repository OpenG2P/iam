from typing import Any

from openg2p_fastapi_common.errors.http_exceptions import ForbiddenError


def claims_from_auth(auth: Any) -> dict:
    """Normalize AuthPrincipal, AuthCredentials, or a raw dict to a flat claims mapping."""
    if hasattr(auth, "model_dump"):
        return auth.model_dump()
    if isinstance(auth, dict):
        return auth
    return {}


def extract_client_roles(claims: dict) -> dict[str, list[str]] | None:
    """Pull Keycloak ``resource_access`` roles into ``{client_id: [roles]}``."""
    resource_access = claims.get("resource_access") or {}
    if not resource_access:
        return None
    result = {}
    for client, value in resource_access.items():
        roles = (value or {}).get("roles") or []
        if roles:
            result[client] = sorted(roles)
    return result or None


def has_claim(name: str):
    """Dependency factory: require a claim to be present."""

    async def check(auth: Any):
        claims = claims_from_auth(auth)
        if claims.get(name) is None:
            raise ForbiddenError(message=f"Forbidden. Missing claim: {name}.")
        return auth

    return check


def claim_equals(name: str, value: str):
    """Dependency factory: require an exact claim value."""

    async def check(auth: Any):
        claims = claims_from_auth(auth)
        if claims.get(name) != value:
            raise ForbiddenError(message=f"Forbidden. Claim {name} mismatch.")
        return auth

    return check


def claim_in(name: str, allowed: set[str]):
    """Dependency factory: require a claim value (or any list member) in ``allowed``."""

    async def check(auth: Any):
        claims = claims_from_auth(auth)
        claim_value = claims.get(name)
        if isinstance(claim_value, str):
            values = {claim_value}
        elif isinstance(claim_value, list):
            values = set(claim_value)
        else:
            values = set()
        if not values.intersection(allowed):
            raise ForbiddenError(message=f"Forbidden. Claim {name} not allowed.")
        return auth

    return check
