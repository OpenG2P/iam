from typing import Any

from fastapi import Request
from starlette.routing import Match


def resolve_matched_route(route: Any, scope: dict) -> Any | None:
    """Resolve a matched route to the leaf APIRoute that owns the endpoint."""
    if getattr(route, "endpoint", None) is not None:
        return route

    match_route_fn = getattr(route, "_match", None)
    if callable(match_route_fn):
        match, _, inner_route, effective_context = match_route_fn(scope)
        if match != Match.FULL:
            return None
        if effective_context is not None:
            original_route = getattr(effective_context, "original_route", None)
            if original_route is not None:
                return original_route
        if inner_route is not None:
            return resolve_matched_route(inner_route, scope) or inner_route
        return None

    nested_routes = getattr(route, "routes", None)
    if nested_routes:
        return match_route_in_routes(list(nested_routes), scope)

    return None


def match_route_in_routes(routes: list[Any], scope: dict) -> Any | None:
    """Walk the router tree and return the first fully matched leaf route."""
    for route in routes:
        match, child_scope = route.matches(scope)
        if match == Match.NONE:
            continue

        merged_scope = {**scope, **child_scope} if child_scope else scope
        if match == Match.FULL:
            resolved = resolve_matched_route(route, merged_scope)
            if resolved is not None:
                return resolved

        nested_routes = getattr(route, "routes", None)
        if nested_routes:
            resolved = match_route_in_routes(list(nested_routes), merged_scope)
            if resolved is not None:
                return resolved

    return None


def match_route(request: Request) -> Any | None:
    """Resolve the current request to its APIRoute (supports nested mounts)."""
    router = getattr(request.app, "router", None)
    routes = list(getattr(router, "routes", []))
    return match_route_in_routes(routes, request.scope)
