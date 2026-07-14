import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt as jose_jwt
from openg2p_fastapi_common.errors.http_exceptions import InternalServerError, UnauthorizedError

from iam_core.context import server_metadata_cache
from iam_core.schemas import TokenEndpointAuthMethod
from iam_core.user_auth.adapters.adapter_factory import AdapterFactory
from iam_core.user_auth.adapters.implementations.esignet_adapter import EsignetAdapter
from iam_core.user_auth.adapters.implementations.keycloak_adapter import KeycloakAdapter
from iam_core.user_auth.adapters.oidc_base import OIDCBase
from iam_core.user_auth.oidc_client import OidcClient
from helpers import make_login_provider


def _rsa_key_pem() -> bytes:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def test_adapter_factory_resolves_known_and_unknown_adapters():
    factory = AdapterFactory()
    factory._adapters = {
        "default_oidc": OIDCBase(),
        "keycloak": KeycloakAdapter(),
        "esignet": EsignetAdapter(),
        "mosip_esignet": EsignetAdapter(),
    }
    assert isinstance(factory.get("keycloak"), KeycloakAdapter)
    assert isinstance(factory.get("esignet"), EsignetAdapter)
    assert isinstance(factory.get("mosip_esignet"), EsignetAdapter)
    assert isinstance(factory.get(None), OIDCBase)
    assert isinstance(factory.get("unknown"), OIDCBase)
    assert isinstance(
        factory.resolve_for_provider(make_login_provider(adapter_name="KEYCLOAK")), KeycloakAdapter
    )


def test_oidc_base_delegates_and_helpers():
    mock_client = MagicMock()
    mock_client.build_authorize_redirect = AsyncMock(return_value=("url", "state"))
    mock_client.exchange_code_for_token = AsyncMock(return_value={"access_token": "a"})
    mock_client.refresh_access_token = AsyncMock(return_value={"access_token": "a"})
    mock_client.decode_jwt = AsyncMock(return_value={"sub": "u"})
    mock_client.get_oauth_validation_data = AsyncMock(return_value={"sub": "u"})
    mock_client.introspect_token = AsyncMock(return_value={"active": True})

    adapter = OIDCBase(oidc_client=mock_client)
    lp = make_login_provider()

    assert adapter.normalize_claims({"sub": "u"}, lp)["sub"] == "u"
    assert adapter.validate_claims({"sub": "u"}, lp) is None
    assert adapter.registrant_subject({"sub": "9"}, lp) == "9"
    assert adapter.registrant_subject({}, lp) is None
    assert adapter.get_authentication_method({"amr": ["otp"]}, lp) == "otp"
    assert adapter.get_authentication_method({"acr": "pwd-otp"}, lp) == "otp"
    assert adapter.get_authentication_method({"acr": "custom"}, lp) == "custom"
    assert adapter.get_authentication_method({"acr": "gold"}, lp) == "gold"
    assert adapter.get_authentication_method({}, lp) is None
    assert adapter.get_claim_verifications(
        {"email_verified": True, "phone_number_verified": False, "verified_attributes": ["email"]},
        lp,
    ) == {"email_verified": True, "phone_verified": False, "email": True}


@pytest.mark.asyncio
async def test_oidc_base_async_methods_delegate():
    mock_client = MagicMock()
    mock_client.build_authorize_redirect = AsyncMock(return_value=("url", "state"))
    mock_client.exchange_code_for_token = AsyncMock(return_value={"access_token": "a", "id_token": "id"})
    mock_client.refresh_access_token = AsyncMock(return_value={"access_token": "a"})
    mock_client.decode_jwt = AsyncMock(return_value={"sub": "u"})
    mock_client.get_oauth_validation_data = AsyncMock(return_value={"sub": "u"})
    mock_client.introspect_token = AsyncMock(return_value={"active": True})
    adapter = OIDCBase(oidc_client=mock_client)
    lp = make_login_provider()

    assert await adapter.build_authorize_redirect(lp, "s", "n", "cv") == ("url", "state")
    assert await adapter.exchange_code_for_token(lp, "code") == {"access_token": "a", "id_token": "id"}
    assert await adapter.refresh_access_token(lp, "rt") == {"access_token": "a"}
    await adapter.validate_callback_id_token(lp, {"id_token": "id"}, nonce="n")
    assert await adapter.get_oauth_validation_data(lp, "at") == {"sub": "u"}
    assert await adapter.decode_access_token(lp, "jwt") == {"sub": "u"}
    assert await adapter.decode_id_token(lp, "id", "jwt") == {"sub": "u"}
    assert await adapter.decode_logout_token(lp, "logout") == {"sub": "u"}
    assert await adapter.introspect_token(lp, "jwt") == {"active": True}
    assert await adapter.enrich_claims_from_userinfo({"sub": "u"}, login_provider=lp, access_token=None) == {
        "sub": "u"
    }


def test_keycloak_adapter_validate_claims_raises_for_missing_sub():
    adapter = KeycloakAdapter()
    with pytest.raises(ValueError, match="Missing required 'sub'"):
        adapter.validate_claims({}, login_provider=make_login_provider())


@pytest.mark.asyncio
async def test_esignet_adapter_enrich_and_authorize_paths():
    adapter = EsignetAdapter()
    lp = make_login_provider(adapter_name="esignet")
    adapter.get_oauth_validation_data = AsyncMock(return_value={"individual_id": "IND-1"})
    enriched = await adapter.enrich_claims_from_userinfo(
        {"sub": "u"},
        login_provider=lp,
        access_token="token",
    )
    assert enriched["individual_id"] == "IND-1"

    adapter.get_oauth_validation_data = AsyncMock(side_effect=RuntimeError("fail"))
    await adapter.enrich_claims_from_userinfo(
        {"sub": "u"},
        login_provider=lp,
        access_token="token",
    ) == {"sub": "u"}

    assert await adapter.enrich_claims_from_userinfo({"sub": "u"}, login_provider=lp, access_token=None) == {
        "sub": "u"
    }
    adapter.get_oauth_validation_data = AsyncMock(return_value={})
    assert await adapter.enrich_claims_from_userinfo({"sub": "u"}, login_provider=lp, access_token="t") == {
        "sub": "u"
    }

    adapter.oidc_client.build_authorize_redirect = AsyncMock(return_value=("url", "state"))
    lp.extra_authorize_params = json.dumps({"claims": {"userinfo": {"email": None}}})
    url, state = await adapter.build_authorize_redirect(lp, "s", "n", "cv")
    assert url == "url"
    assert state == "state"

    lp.extra_authorize_params = "bad-json"
    await adapter.build_authorize_redirect(lp, "s", "n", "cv")


@pytest.mark.asyncio
async def test_oidc_base_validate_callback_skips_without_id_token():
    client = MagicMock()
    adapter = OIDCBase(oidc_client=client)
    await adapter.validate_callback_id_token(make_login_provider(), {"access_token": "a"}, nonce="n")
    client.decode_jwt.assert_not_called()


def test_esignet_adapter_validate_and_registrant_subject():
    adapter = EsignetAdapter()
    lp = make_login_provider(adapter_name="esignet")
    with pytest.raises(ValueError, match="Missing required subject"):
        adapter.validate_claims({}, lp)
    assert adapter.registrant_subject({"individual_id": 7}, lp) == "7"


def test_oidc_client_extra_params_and_metadata_url():
    lp = make_login_provider(extra_authorize_params='{"issuer":"https://extra"}')
    assert OidcClient._extra_params(lp) == {"issuer": "https://extra"}
    lp.extra_authorize_params = "bad"
    assert OidcClient._extra_params(lp) == {}
    lp.extra_authorize_params = None

    lp.server_metadata_url = "https://meta"
    assert OidcClient._metadata_url(lp) == "https://meta"
    lp.server_metadata_url = None
    lp.extra_authorize_params = json.dumps({"server_metadata_url": "https://extra-meta"})
    assert OidcClient._metadata_url(lp) == "https://extra-meta"
    lp.extra_authorize_params = None
    assert OidcClient._metadata_url(lp) == "https://keycloak.example.com/.well-known/openid-configuration"


def test_oidc_client_guess_issuer_from_endpoints():
    lp = make_login_provider(
        token_endpoint="https://idp.example.com/realms/r/protocol/openid-connect/token",
        authorization_endpoint=None,
        userinfo_endpoint=None,
    )
    assert OidcClient._guess_issuer(lp) == "https://idp.example.com"
    lp.token_endpoint = None
    assert OidcClient._guess_issuer(lp) is None


@pytest.mark.asyncio
async def test_oidc_client_get_server_metadata_fetches_and_caches():
    server_metadata_cache.set(None)
    lp = make_login_provider(server_metadata_url="https://idp/.well-known/openid-configuration")
    client = OidcClient()
    metadata_response = MagicMock()
    metadata_response.raise_for_status = MagicMock()
    metadata_response.json.return_value = {"issuer": "https://idp"}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__.return_value = mock_http
        mock_http.get = AsyncMock(return_value=metadata_response)
        mock_client_cls.return_value = mock_http
        first = await client.get_server_metadata(lp)
        second = await client.get_server_metadata(lp)
        assert first["authorization_endpoint"] == lp.authorization_endpoint
        assert second["issuer"] == "https://idp"
        mock_http.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_oidc_client_build_authorize_redirect_with_pkce():
    lp = make_login_provider(enable_pkce=True)
    client = OidcClient()
    mock_oauth = MagicMock()
    mock_oauth.create_authorization_url = MagicMock(return_value=("https://auth", "state"))

    with patch.object(
        OidcClient, "get_server_metadata", AsyncMock(return_value={"authorization_endpoint": "https://auth"})
    ):
        with patch("iam_core.user_auth.oidc_client.AsyncOAuth2Client", return_value=mock_oauth):
            url, state = await client.build_authorize_redirect(lp, "state", "nonce", "verifier")
            assert url == "https://auth"
            assert state == "state"


@pytest.mark.asyncio
async def test_oidc_client_build_authorize_redirect_missing_endpoint():
    client = OidcClient()
    with patch.object(OidcClient, "get_server_metadata", AsyncMock(return_value={})):
        with pytest.raises(InternalServerError, match="authorization_endpoint missing"):
            await client.build_authorize_redirect(make_login_provider(), "s", "n", "cv")


@pytest.mark.asyncio
async def test_oidc_client_exchange_code_for_token_auth_methods():
    client = OidcClient()
    metadata = {"token_endpoint": "https://idp/token"}
    token_payload = {"access_token": "at", "refresh_token": "rt", "id_token": "id"}

    async def run_exchange(lp):
        mock_oauth_instance = MagicMock()
        mock_oauth_instance.fetch_token = AsyncMock(return_value=token_payload)
        with patch("iam_core.user_auth.oidc_client.AsyncOAuth2Client", return_value=mock_oauth_instance):
            return await client.exchange_code_for_token(
                lp, "code", code_verifier="cv", server_metadata=metadata
            )

    lp = make_login_provider(token_endpoint_auth_method=TokenEndpointAuthMethod.client_secret_basic)
    assert (await run_exchange(lp))["access_token"] == "at"

    lp = make_login_provider(token_endpoint_auth_method=TokenEndpointAuthMethod.private_key_jwt_keymanager)
    with patch(
        "iam_core.user_auth.oidc_client.generate_keymanager_client_assertion",
        AsyncMock(return_value=("type", "assertion")),
    ):
        assert (await run_exchange(lp))["access_token"] == "at"

    pem = _rsa_key_pem()
    lp = make_login_provider(
        token_endpoint_auth_method=TokenEndpointAuthMethod.private_key_jwt,
        client_private_key=pem,
        jwt_assertion_aud="https://idp/token",
    )
    assert (await run_exchange(lp))["access_token"] == "at"


@pytest.mark.asyncio
async def test_oidc_client_exchange_code_missing_token_endpoint():
    client = OidcClient()
    with pytest.raises(UnauthorizedError, match="Missing token endpoint"):
        await client.exchange_code_for_token(make_login_provider(), "code", server_metadata={})


@pytest.mark.asyncio
async def test_oidc_client_refresh_access_token():
    client = OidcClient()
    metadata = {"token_endpoint": "https://idp/token"}
    lp = make_login_provider(enable_pkce=True)
    mock_oauth_instance = MagicMock()
    mock_oauth_instance.refresh_token = AsyncMock(
        return_value={"access_token": "new", "refresh_token": "rt"},
    )
    with patch("iam_core.user_auth.oidc_client.AsyncOAuth2Client", return_value=mock_oauth_instance):
        result = await client.refresh_access_token(lp, "rt", server_metadata=metadata)
        assert result["access_token"] == "new"


@pytest.mark.asyncio
async def test_oidc_client_decode_jwt_and_userinfo_and_introspection():
    client = OidcClient()
    metadata = {
        "userinfo_endpoint": "https://idp/userinfo",
        "introspection_endpoint": "https://idp/introspect",
        "jwks_uri": "https://idp/jwks",
        "issuer": "https://idp",
    }
    lp = make_login_provider()

    with patch("iam_core.user_auth.oidc_client.jwks_get", AsyncMock(return_value={"keys": []})):
        with patch("iam_core.user_auth.oidc_client.jwt_decode", MagicMock(return_value={"sub": "u"})):
            claims = await client.decode_jwt(lp, "jwt", server_metadata=metadata)
            assert claims["sub"] == "u"

    userinfo_response = MagicMock()
    userinfo_response.raise_for_status = MagicMock()
    userinfo_response.headers = {"content-type": "application/json"}
    userinfo_response.json.return_value = {"sub": "u", "name": "N"}
    jwt_response = MagicMock()
    jwt_response.raise_for_status = MagicMock()
    jwt_response.headers = {"content-type": "application/jwt"}
    jwt_response.text = jose_jwt.encode({"sub": "jwt-user"}, "secret", algorithm="HS256")
    empty_response = MagicMock()
    empty_response.raise_for_status = MagicMock()
    empty_response.headers = {"content-type": "text/plain"}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__.return_value = mock_http
        mock_http.get = AsyncMock(side_effect=[userinfo_response, jwt_response, empty_response])
        mock_client_cls.return_value = mock_http

        json_user = await client.get_oauth_validation_data(lp, "token", server_metadata=metadata)
        assert json_user["name"] == "N"
        jwt_user = await client.get_oauth_validation_data(lp, "token", server_metadata=metadata)
        assert jwt_user["sub"] == "jwt-user"
        assert await client.get_oauth_validation_data(lp, "token", server_metadata=metadata) == {}

    with pytest.raises(InternalServerError, match="userinfo endpoint missing"):
        await client.get_oauth_validation_data(lp, "token", server_metadata={})

    intro_response = MagicMock()
    intro_response.raise_for_status = MagicMock()
    intro_response.json.return_value = {"active": True, "sub": "u"}
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__.return_value = mock_http
        mock_http.post = AsyncMock(return_value=intro_response)
        mock_client_cls.return_value = mock_http
        payload = await client.introspect_token(lp, "token", server_metadata=metadata)
        assert payload["active"] is True

    lp_basic = make_login_provider(token_endpoint_auth_method=TokenEndpointAuthMethod.client_secret_basic)
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__.return_value = mock_http
        mock_http.post = AsyncMock(return_value=intro_response)
        mock_client_cls.return_value = mock_http
        await client.introspect_token(lp_basic, "token", server_metadata=metadata)

    inactive = MagicMock()
    inactive.raise_for_status = MagicMock()
    inactive.json.return_value = {"active": False}
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__.return_value = mock_http
        mock_http.post = AsyncMock(return_value=inactive)
        mock_client_cls.return_value = mock_http
        with pytest.raises(UnauthorizedError, match="Inactive token"):
            await client.introspect_token(lp, "token", server_metadata=metadata)

    with pytest.raises(InternalServerError, match="introspection endpoint missing"):
        await client.introspect_token(lp, "token", server_metadata={}, endpoint=None)


@pytest.mark.asyncio
async def test_oidc_client_remaining_branches():
    lp = make_login_provider(
        extra_authorize_params=json.dumps({"issuer": "https://extra/"}),
        server_metadata_url=None,
        token_endpoint=None,
        authorization_endpoint=None,
        userinfo_endpoint=None,
    )
    assert OidcClient._guess_issuer(lp) == "https://extra"
    assert OidcClient._metadata_url(lp) == "https://extra/.well-known/openid-configuration"

    client = OidcClient()
    metadata = {"token_endpoint": "https://idp/token"}
    lp = make_login_provider(enable_pkce=True)
    lp.token_endpoint_auth_method = TokenEndpointAuthMethod.client_secret_post

    mock_oauth = MagicMock()
    mock_oauth.fetch_token = AsyncMock(return_value={"access_token": "a", "refresh_token": "r"})
    mock_oauth.refresh_token = AsyncMock(return_value={"access_token": "a", "refresh_token": "r"})
    with patch("iam_core.user_auth.oidc_client.AsyncOAuth2Client", return_value=mock_oauth):
        await client.exchange_code_for_token(lp, "code", code_verifier="cv", server_metadata=metadata)
        await client.refresh_access_token(lp, "rt", server_metadata=metadata)

    with patch.object(
        OidcClient, "get_server_metadata", AsyncMock(return_value={"authorization_endpoint": "https://a"})
    ):
        mock_oauth = MagicMock()
        mock_oauth.create_authorization_url = MagicMock(side_effect=RuntimeError("boom"))
        with patch("iam_core.user_auth.oidc_client.AsyncOAuth2Client", return_value=mock_oauth):
            with pytest.raises(RuntimeError):
                await client.build_authorize_redirect(lp, "s", "n", "cv")

    assert (
        OidcClient._metadata_url(
            make_login_provider(
                server_metadata_url=None,
                extra_authorize_params=None,
                token_endpoint=None,
                authorization_endpoint=None,
                userinfo_endpoint=None,
            )
        )
        is None
    )

    pem = _rsa_key_pem()
    lp_km = make_login_provider(
        token_endpoint_auth_method=TokenEndpointAuthMethod.private_key_jwt_keymanager,
        jwt_assertion_aud="https://idp/token",
    )
    lp_pk = make_login_provider(
        token_endpoint_auth_method=TokenEndpointAuthMethod.private_key_jwt,
        client_private_key=pem,
        jwt_assertion_aud="https://idp/token",
    )
    mock_oauth = MagicMock()
    mock_oauth.refresh_token = AsyncMock(return_value={"access_token": "a", "refresh_token": "r"})
    with (
        patch(
            "iam_core.user_auth.oidc_client.generate_keymanager_client_assertion",
            AsyncMock(return_value=("type", "assertion")),
        ),
        patch("iam_core.user_auth.oidc_client.AsyncOAuth2Client", return_value=mock_oauth),
    ):
        await client.refresh_access_token(
            lp_km, "rt", server_metadata=metadata, keymanager_helper=MagicMock()
        )
    with patch("iam_core.user_auth.oidc_client.AsyncOAuth2Client", return_value=mock_oauth):
        await client.refresh_access_token(lp_pk, "rt", server_metadata=metadata)

    with pytest.raises(UnauthorizedError, match="Missing token endpoint"):
        await client.refresh_access_token(lp_pk, "rt", server_metadata={})

    lp_basic = make_login_provider(token_endpoint_auth_method=TokenEndpointAuthMethod.client_secret_basic)
    mock_oauth.refresh_token = AsyncMock(return_value={"access_token": "a", "refresh_token": "r"})
    with patch("iam_core.user_auth.oidc_client.AsyncOAuth2Client", return_value=mock_oauth):
        await client.refresh_access_token(lp_basic, "rt", server_metadata=metadata)
