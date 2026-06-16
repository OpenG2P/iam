from fastapi import Request
from openg2p_fastapi_common.errors.base_exception import BaseAppException
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError

from .helpers import (
    apply_refreshed_tokens_to_request,
    access_token_from_request,
    is_access_token_expired,
    set_auth_cookies,
    user_auth_error_response,
)
from .middleware_base import UserAuthMiddlewareBase


class RefreshTokenMiddleware(UserAuthMiddlewareBase):
    """Refresh expired access tokens for dependency-protected IAM endpoints.

    Uses a lightweight ``exp`` check only; full validation remains in dependencies.
    """

    def __init__(self, app, *, protected_route_names: set[str]):
        super().__init__(app)
        self._protected_route_names = protected_route_names

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
