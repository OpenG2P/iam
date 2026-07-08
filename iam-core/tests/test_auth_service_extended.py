import json
import types
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError

from iam_core.models.login_provider import LoginProvider
from iam_core.services.auth_service import AuthService
from iam_core.services.auth_transaction_store import AuthTransactionStore
from iam_core.services.provider_repository import ProviderRepository, _ApiLoginProvider
from iam_core.services.redis_auth_transaction_store import RedisAuthTransactionStore
from iam_core.schemas import TokenEndpointAuthMethod
from helpers import FakeRedis, fake_jwt, make_login_provider, token_response


def _auth_service(**overrides) -> AuthService:
    from iam_core.services.redis_refresh_token_store import RedisRefreshTokenStore

    service = AuthService()
    store = RedisRefreshTokenStore()
    store._client = FakeRedis()
    service._refresh_token_store = store
    for key, value in overrides.items():
        setattr(service, key, value)
    return service


@pytest.mark.asyncio
async def test_get_login_providers_maps_repository_results():
    lp = make_login_provider(id=7, description="Staff SSO", icon_base64="data:icon")
    service = _auth_service(
        provider_repository=types.SimpleNamespace(get_all=AsyncMock(return_value=[lp])),
    )

    response = await service.get_login_providers()

    assert response.loginProviders[0].id == 7
    assert response.loginProviders[0].displayName == "Staff SSO"
    assert response.loginProviders[0].displayIconUrl == "data:icon"


@pytest.mark.asyncio
async def test_start_authentication_transaction_builds_redirect():
    lp = make_login_provider()
    store = AuthTransactionStore()
    adapter = types.SimpleNamespace(
        build_authorize_redirect=AsyncMock(return_value=("https://idp/auth", "state-1")),
    )
    service = _auth_service(
        provider_repository=types.SimpleNamespace(get_by_id=AsyncMock(return_value=lp)),
        _transaction_store=store,
        _adapters=types.SimpleNamespace(resolve_for_provider=lambda _lp: adapter),
    )

    with patch(
        "iam_core.services.auth_service.OidcClient.get_server_metadata",
        AsyncMock(return_value={"authorization_endpoint": "https://idp/auth"}),
    ):
        result = await service.start_authentication_transaction(provider_id=1, redirect_uri="")

    assert result.redirectUrl == "https://idp/auth"
    assert result.state == "state-1"


@pytest.mark.asyncio
async def test_start_authentication_transaction_rejects_unknown_provider():
    service = _auth_service(
        provider_repository=types.SimpleNamespace(get_by_id=AsyncMock(return_value=None)),
    )

    with pytest.raises(UnauthorizedError, match="Invalid Login Provider Id"):
        await service.start_authentication_transaction(provider_id=99)


@pytest.mark.asyncio
async def test_complete_authentication_transaction_from_store():
    lp = make_login_provider()
    store = AuthTransactionStore()
    tx = store.create(login_provider_id=1, redirect_uri="/home")
    token_resp = token_response()
    adapter = types.SimpleNamespace(
        exchange_code_for_token=AsyncMock(return_value=token_resp),
        validate_callback_id_token=AsyncMock(),
    )
    service = _auth_service(
        provider_repository=types.SimpleNamespace(get_by_id=AsyncMock(return_value=lp)),
        _transaction_store=store,
        _adapters=types.SimpleNamespace(resolve_for_provider=lambda _lp: adapter),
    )

    result = await service.complete_authentication_transaction(state_value=tx.state, code="code-1")

    assert result["redirect_uri"] == "/home"
    assert result["token_response"] == token_resp
    adapter.validate_callback_id_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_authentication_transaction_legacy_state():
    lp = make_login_provider()
    token_resp = token_response()
    adapter = types.SimpleNamespace(
        exchange_code_for_token=AsyncMock(return_value=token_resp),
        validate_callback_id_token=AsyncMock(),
    )
    service = _auth_service(
        provider_repository=types.SimpleNamespace(get_by_id=AsyncMock(return_value=lp)),
        _transaction_store=AuthTransactionStore(),
        _adapters=types.SimpleNamespace(resolve_for_provider=lambda _lp: adapter),
    )
    legacy_state = json.dumps({"p": 1, "r": "/legacy"})

    result = await service.complete_authentication_transaction(state_value=legacy_state, code="code-2")

    assert result["redirect_uri"] == "/legacy"
    adapter.exchange_code_for_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_authentication_transaction_errors():
    store = AuthTransactionStore()
    tx = store.create(login_provider_id=1, redirect_uri="/")
    service = _auth_service(
        provider_repository=types.SimpleNamespace(get_by_id=AsyncMock(return_value=None)),
        _transaction_store=store,
        _adapters=types.SimpleNamespace(resolve_for_provider=lambda _lp: None),
    )

    with pytest.raises(UnauthorizedError, match="Invalid Login Provider Id"):
        await service.complete_authentication_transaction(state_value=tx.state, code="c")

    service = _auth_service(_transaction_store=AuthTransactionStore())
    with pytest.raises(UnauthorizedError, match="Login Provider Id not received"):
        await service.complete_authentication_transaction(state_value="bad", code="c")


@pytest.mark.asyncio
async def test_refresh_access_token_deletes_when_provider_missing():
    store = AuthService()._refresh_token_store
    store._client = FakeRedis()
    store.store(
        session_id="sid-x",
        token_response=token_response(sid="sid-x"),
        issuer="https://missing",
    )
    service = _auth_service(
        _refresh_token_store=store,
        provider_repository=types.SimpleNamespace(get_by_iss=AsyncMock(return_value=None)),
    )

    result = await service.refresh_access_token("sid-x")

    assert result is None
    assert store.get("sid-x") is None


@pytest.mark.asyncio
async def test_refresh_access_token_handles_httpx_error():
    store = AuthService()._refresh_token_store
    store._client = FakeRedis()
    store.store(
        session_id="sid-x",
        token_response=token_response(sid="sid-x"),
        issuer="https://issuer",
    )
    lp = make_login_provider()
    service = _auth_service(
        _refresh_token_store=store,
        provider_repository=types.SimpleNamespace(get_by_iss=AsyncMock(return_value=lp)),
        _adapters=types.SimpleNamespace(
            resolve_for_provider=lambda _lp: types.SimpleNamespace(
                refresh_access_token=AsyncMock(side_effect=httpx.HTTPError("down")),
            ),
        ),
    )

    assert await service.refresh_access_token("sid-x") is None
    assert store.get("sid-x") is None


def test_delete_refresh_token_and_has_active_session_without_id():
    service = _auth_service()
    service.delete_refresh_token("sid-1")
    assert service.has_active_refresh_session(None) is True


@pytest.mark.asyncio
async def test_handle_backchannel_logout_error_paths():
    service = _auth_service()

    with pytest.raises(UnauthorizedError, match="Invalid logout token"):
        await service.handle_backchannel_logout("not-a-jwt")

    service.provider_repository = types.SimpleNamespace(get_by_iss=AsyncMock(return_value=None))
    logout_token = fake_jwt({"iss": "https://unknown"})
    with pytest.raises(UnauthorizedError, match="Unknown Issuer"):
        await service.handle_backchannel_logout(logout_token)


@pytest.mark.asyncio
async def test_get_oauth_validation_data_and_combine_tokens():
    lp = make_login_provider()
    adapter = types.SimpleNamespace(
        get_oauth_validation_data=AsyncMock(return_value={"sub": "u-1", "name": "User"}),
    )
    service = _auth_service(
        provider_repository=types.SimpleNamespace(get_by_iss=AsyncMock(return_value=lp)),
        _adapters=types.SimpleNamespace(resolve_for_provider=lambda _lp: adapter),
    )
    access = fake_jwt({"iss": lp.issuer, "sub": "u-1", "email": "a@b.c"})

    combined = await service.get_oauth_validation_data(access, combine=True)
    assert combined["name"] == "User"
    assert combined["email"] == "a@b.c"

    userinfo = await service.get_oauth_validation_data(access, combine=False)
    assert userinfo == {"sub": "u-1", "name": "User"}


@pytest.mark.asyncio
async def test_get_provider_by_issuer_and_provider_dict():
    lp = make_login_provider(
        token_endpoint_auth_method=TokenEndpointAuthMethod.client_secret_basic,
    )
    service = _auth_service(
        provider_repository=types.SimpleNamespace(get_by_iss=AsyncMock(return_value=lp)),
    )

    payload = await service.get_provider_by_issuer(lp.issuer)
    assert payload["client_secret"] == "secret"
    assert payload["token_endpoint_auth_method"] == "client_secret_basic"

    public_payload = AuthService._provider_to_api_dict(lp, include_secrets=False)
    assert "client_secret" not in public_payload

    with pytest.raises(UnauthorizedError, match="Provider not found"):
        service.provider_repository.get_by_iss = AsyncMock(return_value=None)
        await service.get_provider_by_issuer("missing")


def test_combine_token_helpers():
    token_a = fake_jwt({"sub": "a", "roles": ["admin"]})
    token_b = fake_jwt({"email": "a@b.c"})
    merged = AuthService.combine_tokens(token_a, token_b)
    assert merged["sub"] == "a"
    assert merged["email"] == "a@b.c"

    assert AuthService.combine_token_dicts(None, {"x": 1}, {"y": 2, "x": 0}) == {"x": 1, "y": 2}
    assert AuthService.combine_tokens("bad-token", {"z": 1}) == {"z": 1}


def test_get_transaction_store_uses_redis_backend():
    with patch("iam_core.services.auth_service.Settings.get_config") as mock_cfg:
        mock_cfg.return_value = types.SimpleNamespace(auth_transaction_store_backend="redis")
        with patch.object(RedisAuthTransactionStore, "get_component", return_value=MagicMock()):
            service = AuthService()
            assert isinstance(service._transaction_store, MagicMock)


@pytest.mark.asyncio
async def test_provider_repository_cache_and_api_fallback():
    repo = ProviderRepository()
    lp = make_login_provider(id=3)

    with patch.object(LoginProvider, "get_by_id", AsyncMock(return_value=lp)) as mock_get:
        first = await repo.get_by_id(3)
        second = await repo.get_by_id(3)
        assert first is lp
        assert second is lp
        mock_get.assert_awaited_once()

    with patch.object(LoginProvider, "get_by_id", AsyncMock(side_effect=RuntimeError("db down"))):
        repo2 = ProviderRepository()
        assert await repo2.get_by_id(3) is None

    repo = ProviderRepository()
    api_provider = _ApiLoginProvider(
        issuer="https://api-issuer",
        id=9,
        client_id="c",
        token_endpoint_auth_method=TokenEndpointAuthMethod.client_secret_post,
        audiences='["portal"]',
    )

    async def fetch_and_cache(issuer):
        import time

        repo._by_iss_cache[issuer] = (api_provider, time.monotonic())
        return api_provider

    with (
        patch.object(LoginProvider, "get_login_provider_from_iss", AsyncMock(return_value=None)),
        patch.object(repo, "_fetch_provider_from_api", AsyncMock(side_effect=fetch_and_cache)) as mock_fetch,
    ):
        result = await repo.get_by_iss("https://api-issuer")
        assert result.issuer == "https://api-issuer"
        cached = await repo.get_by_iss("https://api-issuer")
        assert cached is result
        mock_fetch.assert_awaited_once()


@pytest.mark.asyncio
async def test_provider_repository_fetch_from_api_paths():
    repo = ProviderRepository()
    with patch(
        "iam_core.services.provider_repository._config", types.SimpleNamespace(auth_provider_api_url=None)
    ):
        assert await repo._fetch_provider_from_api("https://x") is None

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "issuer": "https://remote",
        "client_id": "c",
        "token_endpoint_auth_method": "client_secret_post",
    }
    mock_response.raise_for_status = MagicMock()

    with (
        patch(
            "iam_core.services.provider_repository._config",
            types.SimpleNamespace(auth_provider_api_url="https://iam/api/v1"),
        ),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client
        provider = await repo._fetch_provider_from_api("https://remote")
        assert provider.issuer == "https://remote"

    with (
        patch(
            "iam_core.services.provider_repository._config",
            types.SimpleNamespace(auth_provider_api_url="https://iam/api/v1"),
        ),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("fail"))
        mock_client_cls.return_value = mock_client
        assert await repo._fetch_provider_from_api("https://remote") is None


def test_provider_repository_read_extra_authorize_params():
    lp = make_login_provider(extra_authorize_params='{"k":"v"}')
    assert ProviderRepository.read_extra_authorize_params(lp) == {"k": "v"}
    lp.extra_authorize_params = "bad-json"
    assert ProviderRepository.read_extra_authorize_params(lp) == {}


def test_api_login_provider_audiences_list():
    provider = _ApiLoginProvider(issuer="https://x", audiences='["a","b"]')
    assert provider.audiences_list == ["a", "b"]
    provider.audiences = None
    assert provider.audiences_list == []


@pytest.mark.asyncio
async def test_auth_service_legacy_invalid_provider_and_unknown_issuer():
    service = AuthService()
    service.provider_repository = types.SimpleNamespace(get_by_id=AsyncMock(return_value=None))
    service._transaction_store = types.SimpleNamespace(get_and_pop=lambda _s: None)
    service._adapters = types.SimpleNamespace(resolve_for_provider=lambda _lp: None)

    with pytest.raises(UnauthorizedError, match="Invalid Login Provider Id"):
        await service.complete_authentication_transaction(
            state_value='{"p": 1, "r": "/"}',
            code="code",
        )

    service.provider_repository.get_by_iss = AsyncMock(return_value=None)
    with pytest.raises(UnauthorizedError, match="Unknown Issuer"):
        await service.get_oauth_validation_data(fake_jwt({"iss": "https://missing", "sub": "u"}))


@pytest.mark.asyncio
async def test_provider_repository_db_and_cache_paths():
    repo = ProviderRepository()
    lp = make_login_provider()

    with patch.object(LoginProvider, "get_login_provider_from_iss", AsyncMock(return_value=lp)):
        found = await repo.get_by_iss(lp.issuer)
        assert found is lp

    repo._by_id_cache[99] = (lp, 0.0)
    with patch("iam_core.services.provider_repository.time.monotonic", return_value=100.0):
        with patch.object(LoginProvider, "get_by_id", AsyncMock(return_value=lp)) as mock_get:
            result = await repo.get_by_id(99)
            assert result is lp
            mock_get.assert_awaited_once()

    repo._by_iss_cache["https://cached"] = (lp, 95.0)
    with patch("iam_core.services.provider_repository.time.monotonic", return_value=100.0):
        with patch.object(
            LoginProvider,
            "get_login_provider_from_iss",
            AsyncMock(side_effect=RuntimeError("db")),
        ):
            cached = await repo.get_by_iss("https://cached")
            assert cached is lp

    repo._by_iss_cache["https://expired"] = (lp, 0.0)
    api_provider = types.SimpleNamespace(issuer="https://expired")
    with patch("iam_core.services.provider_repository.time.monotonic", return_value=100.0):
        with patch.object(
            LoginProvider,
            "get_login_provider_from_iss",
            AsyncMock(side_effect=RuntimeError("db")),
        ):
            with patch.object(
                repo, "_fetch_provider_from_api", AsyncMock(return_value=api_provider)
            ) as mock_fetch:
                result = await repo.get_by_iss("https://expired")
                assert result is api_provider
                mock_fetch.assert_awaited_once()

    assert (
        ProviderRepository.read_extra_authorize_params(make_login_provider(extra_authorize_params="")) == {}
    )


@pytest.mark.asyncio
async def test_provider_repository_get_all():
    repo = ProviderRepository()
    with patch.object(LoginProvider, "get_all", AsyncMock(return_value=[make_login_provider()])):
        providers = await repo.get_all()
        assert len(providers) == 1
