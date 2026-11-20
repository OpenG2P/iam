"""Permission check shared by staff and agency. Roles stay with the client from the token."""

from collections.abc import Callable
from typing import Any
import hashlib

import httpx
from fastapi import Request
from fastapi_cache.coder import PickleCoder
from fastapi_cache.decorator import cache
from openg2p_fastapi_common.errors.base_exception import BaseAppException
from openg2p_fastapi_common.errors.http_exceptions import ForbiddenError, UnauthorizedError
from starlette.middleware.base import BaseHTTPMiddleware

from iam_core.schemas import AuthPrincipal
from iam_core.user_auth.config import Settings
from iam_core.user_auth.decorators import get_required_permissions
from iam_core.user_auth.enums import RequestStateKey
from iam_core.user_auth.helpers.error_response_helper import user_auth_error_response
from iam_core.user_auth.helpers.route_helper import match_route

_config = Settings.get_config(strict=False)


def _permissions_for_roles_key_builder(func, namespace: str, *args, **kwargs) -> str:
    """Cache key from the API URL and each client with its roles."""
    call_args = kwargs.get("args") or ()
    call_kwargs = kwargs.get("kwargs") or {}
    clients = call_args[0] if call_args else call_kwargs.get("clients")
    api_url = call_args[1] if len(call_args) > 1 else call_kwargs.get("permissions_api_url", "")
    parts = []
    for client_id, roles in clients or ():
        role_key = ",".join(roles) if isinstance(roles, (list, tuple)) else str(roles or "")
        parts.append(f"{client_id}:{role_key}")
    digest = hashlib.sha256(f"{api_url}|{'|'.join(parts)}".encode()).hexdigest()[:16]
    return f"{namespace}:permissions_for_roles:{digest}"


@cache(
    expire=_config.auth_permissions_cache_ttl_seconds,
    key_builder=_permissions_for_roles_key_builder,
    coder=PickleCoder,
)
async def _cached_fetch_permissions_for_roles(
    clients: tuple[tuple[str, tuple[str, ...]], ...],
    permissions_api_url: str,
) -> set[str]:
    endpoint = permissions_api_url.rstrip("/") + "/user-access/get_permissions_for_roles"
    body = {
        "clients": [{"client_id": client_id, "role_mnemonics": list(roles)} for client_id, roles in clients]
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=body)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        message = "Forbidden. Unable to fetch user permissions."
        try:
            payload = exc.response.json()
            message = payload.get("message") or payload.get("detail") or message
        except Exception:
            pass
        raise ForbiddenError(message=str(message)) from exc
    except httpx.HTTPError as exc:
        raise ForbiddenError(message="Forbidden. Unable to fetch user permissions.") from exc
    return set((response.json() or {}).get("permissions") or [])


class ResolvePermissionMiddleware(BaseHTTPMiddleware):
    """Enforce ``@require_permissions`` using each client and its roles on the token.

    ``permissions_api_url`` is the audience API that maps those roles to
    permissions. When it is omitted, the staff ``auth_provider_api_url`` setting
    is used.
    """

    def __init__(
        self,
        app,
        *,
        permissions_api_url: str | None = None,
        allow_by_default: bool = True,
        state_key: str | RequestStateKey = RequestStateKey.AUTH,
        permissions_state_key: str | RequestStateKey = RequestStateKey.PERMISSIONS,
        required_permissions_resolver: Callable[[Request, Any], set[str] | None] | None = None,
    ):
        super().__init__(app)
        self._permissions_api_url = permissions_api_url
        self._allow_by_default = allow_by_default
        self._state_key = str(state_key)
        self._permissions_state_key = str(permissions_state_key)
        self._required_permissions_resolver = required_permissions_resolver

    def _api_url(self) -> str:
        if self._permissions_api_url:
            return self._permissions_api_url
        config = Settings.get_config(strict=False)
        return (config.auth_provider_api_url or "").strip()

    @staticmethod
    def _clients_from_token(client_roles: dict | None) -> tuple[tuple[str, tuple[str, ...]], ...]:
        pairs = []
        for client_id, roles in sorted((client_roles or {}).items()):
            names = tuple(sorted(str(role) for role in (roles or []) if role))
            if client_id and names:
                pairs.append((str(client_id), names))
        return tuple(pairs)

    async def _fetch_permissions_for_roles(
        self, clients: tuple[tuple[str, tuple[str, ...]], ...]
    ) -> set[str]:
        if not clients:
            return set()
        api_url = self._api_url()
        if not api_url:
            raise ForbiddenError(message="Forbidden. auth_provider_api_url is not configured.")
        return await _cached_fetch_permissions_for_roles(clients, api_url)

    async def dispatch(self, request: Request, call_next):
        try:
            matched_route = match_route(request)
            if matched_route is None:
                return await call_next(request)

            if self._required_permissions_resolver is not None:
                permissions = self._required_permissions_resolver(request, matched_route)
                required_permissions = (
                    None if permissions is None else {str(permission) for permission in permissions}
                )
            else:
                required_permissions = get_required_permissions(getattr(matched_route, "endpoint", None))

            if required_permissions is None and self._allow_by_default:
                return await call_next(request)

            request.scope["route"] = matched_route

            principal = getattr(request.state, self._state_key, None)
            if not isinstance(principal, AuthPrincipal):
                raise UnauthorizedError()

            clients = self._clients_from_token(principal.client_roles)
            user_permissions = await self._fetch_permissions_for_roles(clients)

            if required_permissions and not required_permissions.issubset(user_permissions):
                raise ForbiddenError(message="Forbidden. Insufficient resource_access roles.")

            setattr(request.state, self._permissions_state_key, user_permissions)
            return await call_next(request)
        except BaseAppException as exc:
            return user_auth_error_response(request, exc)
