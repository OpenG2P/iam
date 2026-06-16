from typing import Any

from fastapi import Request
from openg2p_fastapi_common.errors.base_exception import BaseAppException
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match

from ..services import AuthService
from .helpers import (
    AUTH_SESSION_COOKIE_NAME,
    apply_refreshed_tokens_to_request,
    access_token_from_request,
    is_access_token_expired,
    set_auth_cookies,
    user_auth_error_response,
)


class RefreshTokenMiddleware(BaseHTTPMiddleware):
    """Refresh expired access tokens for dependency-protected IAM endpoints.

    Uses a lightweight ``exp`` check only; full validation remains in dependencies.
    """

    def __init__(self, app, *, protected_route_names: set[str]):
        super().__init__(app)
        self._protected_route_names = protected_route_names
        self._auth_service = AuthService.get_component() or AuthService()

    def _resolve_matched_route(self, route: Any, scope: dict) -> Any | None:
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

    def _route_name(self, route: Any) -> str | None:
        name = getattr(route, "name", None)
        if name:
            return str(name)
        endpoint = getattr(route, "endpoint", None)
        if endpoint is not None:
            return getattr(endpoint, "__name__", None)
        return None

    async def _refresh_tokens(self, request: Request) -> dict | None:
        session_id = request.cookies.get(AUTH_SESSION_COOKIE_NAME)
        return await self._auth_service.refresh_access_token(session_id)

    async def dispatch(self, request: Request, call_next):
        refreshed_tokens: dict | None = None
        try:
            matched_route = self._match_route(request)
            if matched_route is None:
                return await call_next(request)

            route_name = self._route_name(matched_route)
            if route_name not in self._protected_route_names:
                return await call_next(request)

            request.scope["route"] = matched_route

            access_token = access_token_from_request(request)
            if access_token and is_access_token_expired(access_token):
                refreshed_tokens = await self._refresh_tokens(request)
                if not refreshed_tokens:
                    raise UnauthorizedError(
                        message="Unauthorized. Access token expired and refresh failed.",
                    ) from None
                apply_refreshed_tokens_to_request(request, refreshed_tokens)

            response = await call_next(request)
            if refreshed_tokens:
                set_auth_cookies(response, refreshed_tokens)
            return response
        except BaseAppException as exc:
            return user_auth_error_response(request, exc)
