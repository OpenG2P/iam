from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match

from ..services import AuthService
from .helpers import AUTH_SESSION_COOKIE_NAME


class UserAuthMiddlewareBase(BaseHTTPMiddleware):
    """Shared route matching and token refresh helpers for IAM middleware."""

    def __init__(self, app):
        super().__init__(app)
        self._auth_service = AuthService.get_component() or AuthService()

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
