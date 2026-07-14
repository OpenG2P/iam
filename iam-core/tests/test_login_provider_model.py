from unittest.mock import AsyncMock, patch

import pytest

from iam_core.models.login_provider import LoginProvider
from iam_core.schemas import TokenEndpointAuthMethod


def _login_provider(**kwargs) -> LoginProvider:
    defaults = {
        "id": 1,
        "provider_name": "keycloak",
        "client_id": "staff-portal",
        "token_endpoint_auth_method": TokenEndpointAuthMethod.client_secret_post,
        "issuer": "https://issuer",
        "oauth_callback_url": "https://app/callback",
    }
    defaults.update(kwargs)
    return LoginProvider(**defaults)


def test_login_provider_audiences_list():
    lp = _login_provider(audiences='["portal","api"]')
    assert lp.audiences_list == ["portal", "api"]
    lp.audiences = None
    assert lp.audiences_list == []


@pytest.mark.asyncio
async def test_login_provider_get_login_provider_from_iss():
    providers = [_login_provider(issuer="https://a"), _login_provider(issuer="https://b")]
    with patch.object(LoginProvider, "get_all", AsyncMock(return_value=providers)):
        found = await LoginProvider.get_login_provider_from_iss("https://b")
        assert found.issuer == "https://b"
        missing = await LoginProvider.get_login_provider_from_iss("https://missing")
        assert missing is None
