from unittest.mock import AsyncMock

import pytest

from iam_core.controllers.issuer import IdentityProviderController
from iam_core.models.enum import ApplicationType


@pytest.fixture
def controller():
    return IdentityProviderController(ApplicationType.STAFF.value)


@pytest.mark.asyncio
async def test_get_provider_by_issuer_delegates_to_auth_service(controller):
    controller.auth_service.get_provider_by_issuer = AsyncMock(
        return_value={"issuer": "https://kc.example.com"}
    )
    result = await controller.get_provider_by_issuer("https://kc.example.com")
    controller.auth_service.get_provider_by_issuer.assert_awaited_once_with("https://kc.example.com", "staff")
    assert result["issuer"] == "https://kc.example.com"
