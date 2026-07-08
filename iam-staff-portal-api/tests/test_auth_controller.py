import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from iam_core.schemas import LoggedInUserResponse
from iam_core.user_auth.helpers import AuthCookieName
from openg2p_fastapi_common.errors.http_exceptions import InternalServerError, UnauthorizedError

from helpers import make_auth, make_request
from iam_core.schemas import AuthPrincipal
from iam_staff_portal_api.controllers.auth_controller import AuthController


@pytest.fixture
def controller():
    return AuthController()


@pytest.mark.asyncio
async def test_get_user_profile_excludes_credentials(controller):
    auth = make_auth()
    request = make_request(auth=auth)
    profile = await controller.get_user_profile(request)
    assert "credentials" not in profile
    assert profile["scheme"] == "bearer"


@pytest.mark.asyncio
async def test_get_logged_in_user_returns_request_state_user(controller):
    user = LoggedInUserResponse(id="user-1", name="Test User")
    request = make_request()
    request.state.user = user
    assert await controller.get_logged_in_user(request) == user


@pytest.mark.asyncio
async def test_logout_redirects_to_provider_end_session_endpoint(controller):
    auth = make_auth(iss="https://keycloak.example.com/realms/staff")
    request = make_request(
        auth=auth,
        cookies={
            AuthCookieName.SESSION: "session-1",
            AuthCookieName.ID_TOKEN: "id-token",
        },
    )
    provider = types.SimpleNamespace(
        issuer="https://keycloak.example.com/realms/staff",
        default_redirect_uri="https://portal.example.com/",
        client_id="staff-portal",
    )
    controller.provider_repository = MagicMock()
    controller.provider_repository.get_by_iss = AsyncMock(return_value=provider)
    controller.auth_service.delete_refresh_token = MagicMock()

    with patch(
        "iam_staff_portal_api.controllers.auth_controller.OidcClient.get_server_metadata",
        AsyncMock(return_value={"end_session_endpoint": "https://keycloak.example.com/logout"}),
    ):
        response = await controller.logout(request)

    assert response.status_code == 307
    assert response.headers["location"].startswith("https://keycloak.example.com/logout?")
    assert "post_logout_redirect_uri=" in response.headers["location"]
    controller.auth_service.delete_refresh_token.assert_called_once_with("session-1")


@pytest.mark.asyncio
async def test_logout_raises_when_provider_not_found(controller):
    auth = make_auth()
    request = make_request(auth=auth, cookies={AuthCookieName.SESSION: "session-1"})
    controller.auth_service.delete_refresh_token = MagicMock()
    controller.provider_repository = MagicMock()
    controller.provider_repository.get_by_iss = AsyncMock(return_value=None)

    with pytest.raises(UnauthorizedError, match="Invalid issuer"):
        await controller.logout(request)


@pytest.mark.asyncio
async def test_logout_raises_when_issuer_missing(controller):
    request = make_request(
        auth=AuthPrincipal(credentials="not-a-jwt", client_roles={}),
        cookies={AuthCookieName.SESSION: "session-1"},
    )
    controller.auth_service.delete_refresh_token = MagicMock()
    with pytest.raises(UnauthorizedError, match="Invalid issuer"):
        await controller.logout(request)


@pytest.mark.asyncio
async def test_logout_raises_when_end_session_endpoint_missing(controller):
    auth = make_auth()
    request = make_request(auth=auth, cookies={AuthCookieName.SESSION: "session-1"})
    provider = types.SimpleNamespace(
        issuer="https://keycloak.example.com/realms/staff",
        default_redirect_uri="/",
        client_id="staff-portal",
    )
    controller.provider_repository = MagicMock()
    controller.provider_repository.get_by_iss = AsyncMock(return_value=provider)
    controller.auth_service.delete_refresh_token = MagicMock()

    with patch(
        "iam_staff_portal_api.controllers.auth_controller.OidcClient.get_server_metadata",
        AsyncMock(return_value={}),
    ):
        with pytest.raises(InternalServerError, match="Logout endpoint not available"):
            await controller.logout(request)


@pytest.mark.asyncio
async def test_backchannel_logout_requires_logout_token(controller):
    request = MagicMock()
    request.form = AsyncMock(return_value={})
    with pytest.raises(UnauthorizedError, match="Missing logout_token"):
        await controller.backchannel_logout(request)


@pytest.mark.asyncio
async def test_backchannel_logout_delegates_to_auth_service(controller):
    request = MagicMock()
    request.form = AsyncMock(return_value={"logout_token": "token-value"})
    controller.auth_service.handle_backchannel_logout = AsyncMock()

    response = await controller.backchannel_logout(request)

    assert response.status_code == 200
    controller.auth_service.handle_backchannel_logout.assert_awaited_once_with("token-value")


@pytest.mark.asyncio
async def test_get_login_providers_delegates_to_auth_service(controller):
    controller.auth_service.get_login_providers = AsyncMock(return_value={"providers": []})
    result = await controller.get_login_providers()
    assert result == {"providers": []}


@pytest.mark.asyncio
async def test_start_authentication_transaction_delegates_to_auth_service(controller):
    controller.auth_service.start_authentication_transaction = AsyncMock(return_value={"state": "abc"})
    result = await controller.start_authentication_transaction(id=3, redirect_uri="/home")
    controller.auth_service.start_authentication_transaction.assert_awaited_once_with(
        provider_id=3,
        redirect_uri="/home",
    )
    assert result == {"state": "abc"}
