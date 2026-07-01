from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from iam_core.user_auth.enums import AuthCookieName
from iam_core.user_auth.helpers.cookie_helper import set_auth_cookies, set_csrf_cookie
from iam_core.user_auth.middleware.csrf import CsrfMiddleware, _normalize_path, _path_is_excluded

_TEST_CSRF_EXCLUDED_PATHS = (
    "/ping",
    "/auth/start_authentication_transaction",
)


def _middleware(excluded_paths=_TEST_CSRF_EXCLUDED_PATHS) -> CsrfMiddleware:
    return CsrfMiddleware(
        app=MagicMock(),
        excluded_paths=excluded_paths,
    )


def _token_response() -> dict:
    return {
        "access_token": "access-token",
        "id_token": "id-token",
        "refresh_token": "refresh-token",
        "expires_in": 300,
    }


def _make_request(
    *,
    method: str = "POST",
    path: str = "/user-access/update",
    cookies: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> Request:
    raw_headers: list[tuple[bytes, bytes]] = []
    if headers:
        for key, value in headers.items():
            raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    if cookies:
        cookie_value = "; ".join(f"{name}={value}" for name, value in cookies.items())
        raw_headers.append((b"cookie", cookie_value.encode("latin-1")))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "headers": raw_headers,
    }
    return Request(scope)


def _set_cookie_names(response: Response) -> list[str]:
    return [value.split("=", 1)[0] for value in response.headers.getlist("set-cookie")]


def test_path_is_excluded_matches_exact_and_suffixed_paths():
    excluded = frozenset(_normalize_path(path) for path in ["/ping", "/auth/callback"])
    assert _path_is_excluded("/ping", excluded)
    assert _path_is_excluded("/api/v1/iam-staff/auth/callback", excluded)
    assert not _path_is_excluded("/user-access/update", excluded)


def test_set_auth_cookies_also_sets_csrf_cookie():
    response = Response()
    set_auth_cookies(response, _token_response(), session_id="session-1")

    assert AuthCookieName.CSRF_TOKEN in _set_cookie_names(response)


def test_set_csrf_cookie_is_not_httponly():
    response = Response()
    set_csrf_cookie(response, token="csrf-value")

    set_cookies = [value.decode() for name, value in response.raw_headers if name == b"set-cookie"]
    csrf_cookie = next(value for value in set_cookies if "csrf-value" in value)
    assert "httponly" not in csrf_cookie.lower()


@pytest.mark.asyncio
async def test_csrf_middleware_allows_matching_token():
    middleware = _middleware()
    request = _make_request(
        cookies={AuthCookieName.CSRF_TOKEN: "token-abc"},
        headers={"X-CSRF-Token": "token-abc"},
    )
    call_next = AsyncMock(return_value=Response(status_code=200))

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    call_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_csrf_middleware_rejects_missing_header():
    middleware = _middleware()
    request = _make_request(cookies={AuthCookieName.CSRF_TOKEN: "token-abc"})
    call_next = AsyncMock(return_value=Response(status_code=200))

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 403
    call_next.assert_not_called()


@pytest.mark.asyncio
async def test_csrf_middleware_rejects_mismatched_token():
    middleware = _middleware()
    request = _make_request(
        cookies={AuthCookieName.CSRF_TOKEN: "token-abc"},
        headers={"X-CSRF-Token": "token-xyz"},
    )
    call_next = AsyncMock(return_value=Response(status_code=200))

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 403
    call_next.assert_not_called()


@pytest.mark.asyncio
async def test_csrf_middleware_skips_safe_methods():
    middleware = _middleware()
    request = _make_request(method="GET")
    call_next = AsyncMock(return_value=Response(status_code=200))

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    call_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_csrf_middleware_skips_excluded_paths():
    middleware = _middleware()
    request = _make_request(method="POST", path="/auth/start_authentication_transaction")
    call_next = AsyncMock(return_value=Response(status_code=200))

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    call_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_csrf_middleware_skips_validation_when_disabled():
    middleware = CsrfMiddleware(
        app=MagicMock(),
        enabled=False,
        excluded_paths=_TEST_CSRF_EXCLUDED_PATHS,
    )
    request = _make_request(cookies={AuthCookieName.CSRF_TOKEN: "token-abc"})
    call_next = AsyncMock(return_value=Response(status_code=200))

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    call_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_csrf_middleware_uses_passed_excluded_paths():
    middleware = _middleware(excluded_paths=("/ping",))
    request = _make_request(method="POST", path="/auth/callback")
    call_next = AsyncMock(return_value=Response(status_code=200))

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 403
    call_next.assert_not_called()
