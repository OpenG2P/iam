import secrets
from collections.abc import Iterable

from fastapi import Request
from openg2p_fastapi_common.errors.base_exception import BaseAppException
from openg2p_fastapi_common.errors.http_exceptions import ForbiddenError
from starlette.middleware.base import BaseHTTPMiddleware

from ..enums import AuthCookieName
from ..helpers.error_response_helper import user_auth_error_response

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_CSRF_HEADER_NAME = "X-CSRF-Token"
_CSRF_FORBIDDEN_MESSAGE = "Forbidden. CSRF token missing or invalid."


def _normalize_path(path: str) -> str:
    normalized = path.rstrip("/")
    return normalized or "/"


def _path_is_excluded(path: str, excluded_paths: frozenset[str]) -> bool:
    """Match exact path or suffix (supports API prefix mounts)."""
    normalized = _normalize_path(path)
    for excluded in excluded_paths:
        if normalized == excluded or normalized.endswith(excluded):
            return True
    return False


class CsrfMiddleware(BaseHTTPMiddleware):
    """Validate double-submit CSRF tokens on state-changing requests.

    Register after ValidateAndRefreshTokenMiddleware so it runs first on inbound
    requests. Safe methods and ``excluded_paths`` skip validation.
    Set ``enabled=False`` (or ``common_csrf_enabled=false``) to disable checks.
    """

    def __init__(
        self,
        app,
        *,
        enabled: bool = True,
        excluded_paths: Iterable[str] = (),
    ):
        super().__init__(app)
        self._enabled = enabled
        self._excluded_paths = frozenset(_normalize_path(path) for path in excluded_paths)

    def _should_skip(self, request: Request) -> bool:
        if request.method in _SAFE_METHODS:
            return True
        if _path_is_excluded(request.url.path, self._excluded_paths):
            return True
        return False

    def _validate_csrf(self, request: Request) -> None:
        cookie_token = request.cookies.get(AuthCookieName.CSRF_TOKEN)
        header_token = request.headers.get(_CSRF_HEADER_NAME)
        if not cookie_token or not header_token:
            raise ForbiddenError(message=_CSRF_FORBIDDEN_MESSAGE)
        if not secrets.compare_digest(cookie_token, header_token):
            raise ForbiddenError(message=_CSRF_FORBIDDEN_MESSAGE)

    async def dispatch(self, request: Request, call_next):
        if not self._enabled:
            return await call_next(request)

        try:
            if not self._should_skip(request):
                self._validate_csrf(request)
            return await call_next(request)
        except BaseAppException as exc:
            return user_auth_error_response(request, exc)
