import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from starlette.requests import Request
from iam_staff_portal_api.controllers.oauth_callback_controller import OAuthCallbackController


@pytest.fixture
def controller():
    return OAuthCallbackController()


@pytest.mark.asyncio
async def test_oauth_callback_sets_cookies_and_redirects(controller):
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "path": "/auth/callback",
        "query_string": b"state=abc&code=def",
        "headers": [],
    }
    request = Request(scope)
    token_response = {
        "access_token": "access",
        "id_token": "id",
        "refresh_token": "refresh",
        "expires_in": 300,
        "refresh_expires_in": 1800,
    }
    refresh_token = types.SimpleNamespace(session_id="session-123")
    controller.auth_service.complete_authentication_transaction = AsyncMock(
        return_value={"token_response": token_response, "redirect_uri": "https://portal.example.com/"}
    )
    controller.auth_service.store_refresh_token = MagicMock(return_value=refresh_token)

    with patch("iam_staff_portal_api.controllers.oauth_callback_controller.set_auth_cookies") as set_cookies:
        response = await controller.oauth_callback(request)

    assert response.status_code == 307
    assert response.headers["location"] == "https://portal.example.com/"
    controller.auth_service.complete_authentication_transaction.assert_awaited_once_with(
        state_value="abc",
        code="def",
    )
    controller.auth_service.store_refresh_token.assert_called_once_with(token_response=token_response)
    set_cookies.assert_called_once()
