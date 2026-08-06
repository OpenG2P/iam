from collections.abc import Callable, Iterable
from typing import Any

from .enums import EndpointMetadataKey


def _normalize_values(*values: str | Iterable[str]) -> frozenset[str]:
    if len(values) == 1 and not isinstance(values[0], str):
        raw_values = values[0]
    else:
        raw_values = values
    return frozenset(str(value).strip() for value in raw_values if value and str(value).strip())


def require_permissions(*allowed_permissions: str | Iterable[str]):
    """Attach required permissions to an endpoint for ResolvePermissionMiddleware."""
    normalized = _normalize_values(*allowed_permissions)

    def decorator(func: Callable[..., Any]):
        setattr(func, EndpointMetadataKey.REQUIRED_PERMISSIONS, frozenset(normalized))
        return func

    return decorator


def requires_auth(func: Callable[..., Any]):
    """Mark an endpoint as requiring a valid access token."""
    setattr(func, EndpointMetadataKey.REQUIRES_AUTH, True)
    return func


def requires_user(func: Callable[..., Any]):
    """Mark an endpoint as requiring auth plus enriched user profile on request.state.user."""
    setattr(func, EndpointMetadataKey.REQUIRES_AUTH, True)
    setattr(func, EndpointMetadataKey.REQUIRES_USER, True)
    return func


def data_policy(func: Callable[..., Any]):
    """Mark an endpoint as requiring data policy resolution."""
    setattr(func, EndpointMetadataKey.DATA_POLICY, True)
    return func


def _endpoint_candidates(endpoint: Any) -> list[Any]:
    if endpoint is None:
        return []
    candidates = [endpoint]
    endpoint_func = getattr(endpoint, "__func__", None)
    if endpoint_func is not None:
        candidates.append(endpoint_func)
    return candidates


def _read_bool_flag(endpoint: Any, key: EndpointMetadataKey) -> bool:
    for candidate in _endpoint_candidates(endpoint):
        if key in getattr(candidate, "__dict__", {}):
            return getattr(candidate, key) is True
    return False


def endpoint_requires_auth(endpoint: Any) -> bool:
    """True when the handler is marked with ``@requires_auth`` or ``@requires_user``."""
    return _read_bool_flag(endpoint, EndpointMetadataKey.REQUIRES_AUTH)


def endpoint_requires_user(endpoint: Any) -> bool:
    """True when the handler is marked with ``@requires_user``."""
    return _read_bool_flag(endpoint, EndpointMetadataKey.REQUIRES_USER)


def endpoint_requires_token(endpoint: Any) -> bool:
    """True when ValidateAndRefreshTokenMiddleware must run for this endpoint."""
    return (
        endpoint_requires_auth(endpoint)
        or endpoint_requires_user(endpoint)
        or get_required_permissions(endpoint) is not None
    )


def get_required_permissions(endpoint: Any) -> set[str] | None:
    """Return permissions from ``@require_permissions``, or None if unset."""
    for candidate in _endpoint_candidates(endpoint):
        if EndpointMetadataKey.REQUIRED_PERMISSIONS in getattr(candidate, "__dict__", {}):
            permissions = getattr(candidate, EndpointMetadataKey.REQUIRED_PERMISSIONS)
            return {str(permission) for permission in permissions}
    return None
