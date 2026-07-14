from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from iam_core.partner_auth.config import Settings as PartnerSettings
from iam_core.partner_auth.jwt_signature_validator import JWTSignatureValidator
from iam_core.partner_auth.jwt_validation_helper import JWTValidationHelper


def test_partner_auth_settings_defaults():
    settings = PartnerSettings.get_config(strict=False)
    assert settings.login_providers_table_enabled is True
    assert settings.login_providers_table_name == "login_providers"
    assert settings.keymanager_sign_app_id == ""


def test_get_partner_id_from_payload_uses_header_sender_id():
    helper = JWTValidationHelper()
    partner_id = helper.get_partner_id_from_payload({"header": {"sender_id": "my-registry"}})
    assert partner_id == "PARTNER_MY_REGISTRY"


def test_get_partner_id_from_payload_uses_request_header_mnemonic():
    helper = JWTValidationHelper()
    partner_id = helper.get_partner_id_from_payload({"request_header": {"sender_app_mnemonic": "farmer-reg"}})
    assert partner_id == "PARTNER_FARMER_REG"


def test_get_partner_id_from_payload_returns_unknown_when_missing():
    helper = JWTValidationHelper()
    assert helper.get_partner_id_from_payload({}) == "PARTNER_UNKNOWN"


@pytest.mark.asyncio
async def test_verify_jwt_delegates_to_crypto_helper():
    crypto = MagicMock()
    crypto.verify_jwt = AsyncMock(return_value=True)
    helper = JWTValidationHelper()
    helper.crypto_helper = crypto
    payload = {"header": {"sender_id": "registry-1"}}

    result = await helper.verify_jwt("signed-jwt", payload, extra="kwarg")

    assert result is True
    crypto.verify_jwt.assert_awaited_once()
    call_kwargs = crypto.verify_jwt.await_args.kwargs
    assert call_kwargs["payload"] == payload
    assert call_kwargs["km_ref_id"] == "PARTNER_REGISTRY_1"
    assert call_kwargs["extra"] == "kwarg"


@pytest.mark.asyncio
async def test_jwt_signature_validator_returns_false_without_signature_header():
    request = MagicMock()
    request.body = AsyncMock(return_value=b'{"amount": 1}')
    request.headers = MagicMock()
    request.headers.get.return_value = None

    result = await JWTSignatureValidator()(request)

    assert result is False


@pytest.mark.asyncio
async def test_jwt_signature_validator_delegates_to_validation_helper():
    request = MagicMock()
    request.body = AsyncMock(return_value=b'{"header":{"sender_id":"partner-a"}}')
    request.headers = MagicMock()
    request.headers.get.return_value = "jwt-signature"
    helper = MagicMock()
    helper.verify_jwt = AsyncMock(return_value=True)

    with patch.object(JWTValidationHelper, "get_component", return_value=helper):
        result = await JWTSignatureValidator()(request)

    assert result is True
    helper.verify_jwt.assert_awaited_once_with(
        "jwt-signature",
        {"header": {"sender_id": "partner-a"}},
    )
