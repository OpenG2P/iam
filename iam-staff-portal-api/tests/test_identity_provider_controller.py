from unittest.mock import AsyncMock

import pytest

from iam_staff_portal_api.controllers.identity_provider_controller import IdentityProviderController


@pytest.fixture
def controller():
    return IdentityProviderController()


@pytest.mark.asyncio
async def test_get_provider_by_issuer_delegates_to_auth_service(controller):
    controller.auth_service.get_provider_by_issuer = AsyncMock(
        return_value={"issuer": "https://kc.example.com"}
    )
    result = await controller.get_provider_by_issuer("https://kc.example.com")
    controller.auth_service.get_provider_by_issuer.assert_awaited_once_with("https://kc.example.com")
    assert result["issuer"] == "https://kc.example.com"
