from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.responses import Response

from iam_core.schemas import AuthCredentials, LoggedInUserResponse
from iam_core.user_auth.decorators import requires_user
from iam_core.user_auth.enums import AuthCookieName
from iam_core.user_auth.middleware import ValidateAndRefreshTokenMiddleware
from helpers import make_request, token_response


@requires_user
def _requires_user_endpoint():
    return "profile"


def _auth_credentials(access_token: str = "valid-access") -> AuthCredentials:
    return AuthCredentials(credentials=access_token, sub="user-1", name="User")


@pytest.mark.asyncio
async def test_validate_and_refresh_middleware_requires_user_and_route_none():
    middleware = ValidateAndRefreshTokenMiddleware(app=MagicMock())
    request = make_request(
        cookies={
            AuthCookieName.ACCESS_TOKEN: "valid-access",
            AuthCookieName.SESSION: "kc-session-123",
        },
    )
    call_next = AsyncMock(return_value=Response(content=b"ok", status_code=200))

    with patch(
        "iam_core.user_auth.middleware.validate_and_refresh.match_route",
        return_value=None,
    ):
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 200

    route = MagicMock()
    route.endpoint = _requires_user_endpoint

    with (
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.match_route",
            return_value=route,
        ),
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.validate_request_token",
            AsyncMock(return_value=_auth_credentials()),
        ),
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.build_logged_in_user",
            AsyncMock(return_value=LoggedInUserResponse(sub="user-1", name="User")),
        ),
        patch(
            "iam_core.services.AuthService",
        ) as mock_auth_service_cls,
    ):
        mock_auth_service = MagicMock()
        mock_auth_service.has_active_refresh_session.return_value = True
        mock_auth_service_cls.get_component.return_value = mock_auth_service
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    assert request.state.user.name == "User"
    assert _requires_user_endpoint() == "profile"


@pytest.mark.asyncio
async def test_validate_and_refresh_applies_refreshed_tokens_with_id_token():
    middleware = ValidateAndRefreshTokenMiddleware(app=MagicMock())
    request = make_request(
        cookies={
            AuthCookieName.ACCESS_TOKEN: "expired",
            AuthCookieName.ID_TOKEN: "old-id",
            AuthCookieName.SESSION: "sid-1",
        },
    )
    request._cookies = dict(request.cookies)
    request._headers = request.headers

    refreshed = token_response(access_token="fresh", id_token="fresh-id")

    middleware._apply_refreshed_tokens_to_request(request, refreshed)
    assert request.headers.get("authorization") == "Bearer fresh"
    assert request.cookies[AuthCookieName.ACCESS_TOKEN] == "fresh"
    assert request.cookies[AuthCookieName.ID_TOKEN] == "fresh-id"


@pytest.mark.asyncio
async def test_validate_and_refresh_raises_without_access_token():
    middleware = ValidateAndRefreshTokenMiddleware(app=MagicMock())
    request = make_request(cookies={AuthCookieName.SESSION: "sid-1"})
    route = MagicMock(endpoint=_requires_user_endpoint)

    with (
        patch("iam_core.user_auth.middleware.validate_and_refresh.match_route", return_value=route),
        patch("iam_core.services.AuthService") as mock_auth_service_cls,
    ):
        mock_auth_service = MagicMock()
        mock_auth_service.has_active_refresh_session.return_value = True
        mock_auth_service_cls.get_component.return_value = mock_auth_service
        with pytest.raises(Exception):
            await middleware._authenticate_with_refresh(request)

    request = make_request()
    middleware._ensure_refresh_session_active(request)


@pytest.mark.asyncio
async def test_validate_and_refresh_refresh_access_token_path():
    middleware = ValidateAndRefreshTokenMiddleware(app=MagicMock())
    request = make_request(cookies={AuthCookieName.SESSION: "sid"})
    with patch("iam_core.services.AuthService") as mock_cls:
        mock_service = MagicMock()
        mock_service.refresh_access_token = AsyncMock(return_value={"access_token": "new"})
        mock_cls.get_component.return_value = mock_service
        result = await middleware._refresh_access_token(request)
        assert result["access_token"] == "new"
