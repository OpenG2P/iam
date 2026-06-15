from collections.abc import Callable
from typing import Any

import httpx
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from openg2p_fastapi_common.errors.base_exception import BaseAppException
from openg2p_fastapi_common.errors.http_exceptions import ForbiddenError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match
from ..schemas import AuthPrincipal

from .config import Settings
from .dependencies import JwtBearerAuth, auth_principal
from .helpers import user_auth_error_response, get_required_permissions as default_get_required_permissions

_config = Settings.get_config(strict=False)


class AuthMiddleware(BaseHTTPMiddleware):
    """Reusable IAM authorization middleware.

    Subclasses may override ``get_required_permissions`` or pass a
    ``required_permissions_resolver`` callback.
    """

    def __init__(
        self,
        app,
        *,
        client_id: str | None = None,
        allow_by_default: bool = True,
        state_key: str = "auth",
        required_permissions_resolver: Callable[[Request, Any], set[str] | None] | None = None,
    ):
        super().__init__(app)
        self._auth_scheme = JwtBearerAuth()
        self._client_id = client_id
        self._allow_by_default = allow_by_default
        self._state_key = state_key
        self._required_permissions_resolver = required_permissions_resolver

    def get_required_permissions(self, request: Request, route: Any) -> set[str] | None:
        if self._required_permissions_resolver is not None:
            roles = self._required_permissions_resolver(request, route)
            if roles is None:
                return None
            return {str(role) for role in roles}
        return default_get_required_permissions(getattr(route, "endpoint", None))

    def get_client_id(self, request: Request) -> str | None:
        return self._client_id

    def _resolve_matched_route(self, route: Any, scope: dict) -> Any | None:
        """Resolve a matched route to the leaf APIRoute that owns the endpoint."""
        if getattr(route, "endpoint", None) is not None:
            return route

        match_route = getattr(route, "_match", None)
        if callable(match_route):
            match, _, inner_route, effective_context = match_route(scope)
            if match != Match.FULL:
                return None
            if effective_context is not None:
                original_route = getattr(effective_context, "original_route", None)
                if original_route is not None:
                    return original_route
            if inner_route is not None:
                return self._resolve_matched_route(inner_route, scope) or inner_route
            return None

        nested_routes = getattr(route, "routes", None)
        if nested_routes:
            return self._match_route_in_routes(list(nested_routes), scope)

        return None

    def _match_route_in_routes(self, routes: list[Any], scope: dict) -> Any | None:
        for route in routes:
            match, child_scope = route.matches(scope)
            if match == Match.NONE:
                continue

            merged_scope = {**scope, **child_scope} if child_scope else scope
            if match == Match.FULL:
                resolved = self._resolve_matched_route(route, merged_scope)
                if resolved is not None:
                    return resolved

            nested_routes = getattr(route, "routes", None)
            if nested_routes:
                resolved = self._match_route_in_routes(list(nested_routes), merged_scope)
                if resolved is not None:
                    return resolved

        return None

    def _match_route(self, request: Request) -> Any | None:
        router = getattr(request.app, "router", None)
        routes = list(getattr(router, "routes", []))
        return self._match_route_in_routes(routes, request.scope)

    async def _get_user_permissions(
        self,
        role_mnemonics: list[str],
    ) -> set[str]:
        auth_provider_api_url = (_config.auth_provider_api_url or "").strip()
        if not auth_provider_api_url:
            raise ForbiddenError(message="Forbidden. auth_provider_api_url is not configured.")

        if not role_mnemonics:
            return set()

        endpoint = auth_provider_api_url.rstrip("/") + "/user-access/get_permissions_for_roles"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json={"role_mnemonics": role_mnemonics},
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ForbiddenError(message="Forbidden. Unable to fetch user permissions.") from exc

        response_data = response.json() or {}
        return set(response_data.get("permissions") or [])

    async def dispatch(self, request: Request, call_next):
        try:
            matched_route = self._match_route(request)
            if matched_route is None:
                return await call_next(request)

            required_permissions = self.get_required_permissions(request, matched_route)
            if required_permissions is None and self._allow_by_default:
                return await call_next(request)

            request.scope["route"] = matched_route

            client_id = (self.get_client_id(request) or "").strip()
            if required_permissions and not client_id:
                raise ForbiddenError(message="Forbidden. keycloak_client_id is not configured.")

            auth_credentials: HTTPAuthorizationCredentials | None = await self._auth_scheme(request)
            principal: AuthPrincipal = await auth_principal(auth_credentials)

            user_roles = list((principal.client_roles or {}).get(client_id, []))
            user_permissions = await self._get_user_permissions(user_roles)

            if required_permissions and not required_permissions.issubset(user_permissions):
                raise ForbiddenError(message="Forbidden. Insufficient resource_access roles.")

            setattr(request.state, self._state_key, principal)
            return await call_next(request)
        except BaseAppException as exc:
            return user_auth_error_response(request, exc)
