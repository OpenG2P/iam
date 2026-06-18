import base64
import json
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from authlib.integrations.base_client.errors import OAuthError
from authlib.jose.errors import BadSignatureError, ExpiredTokenError as JoseExpiredTokenError
from jose import jwt as jose_jwt
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError
from starlette.requests import Request
from starlette.responses import Response

from iam_core.schemas import AuthCredentials, AuthPrincipal, RefreshTokenRecord
from iam_core.services.auth_service import AuthService
from iam_core.services.redis_refresh_token_store import RedisRefreshTokenStore
from iam_core.services.token_validator_service import TokenValidatorService
from iam_core.user_auth.config import ApiAuthSettings
from iam_core.user_auth.errors import ExpiredTokenError
from iam_core.user_auth.enums import AuthCookieName
from iam_core.user_auth.helpers.cookie_helper import (
    clear_auth_cookies,
    oidc_session_id_from_token_response,
    set_auth_cookies,
)
from iam_core.user_auth.helpers.token_helper import (
    REFRESH_FAILED_MESSAGE,
    SESSION_INVALIDATED_MESSAGE,
    validate_refresh_token_response,
)
from iam_core.user_auth.middleware import ResolvePermissionMiddleware, ValidateAndRefreshTokenMiddleware
from iam_core.user_auth.decorators import require_permissions, requires_auth


def _fake_jwt(claims: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.sig"


def _token_response(
    *,
    sid: str = "kc-session-123",
    iss: str = "https://keycloak.example.com/realms/staff",
    access_token: str | None = None,
    id_token: str | None = None,
    refresh_token: str = "refresh-1",
) -> dict:
    return {
        "access_token": access_token or _fake_jwt({"sid": sid, "sub": "user-1", "iss": iss}),
        "id_token": id_token or _fake_jwt({"sub": "user-1", "iss": iss}),
        "refresh_token": refresh_token,
        "expires_in": 300,
        "refresh_expires_in": 1800,
    }


def _make_request(
    *,
    cookies: dict[str, str] | None = None,
    authorization: str | None = None,
) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if authorization:
        headers.append((b"authorization", authorization.encode("latin-1")))
    if cookies:
        cookie_value = "; ".join(f"{name}={value}" for name, value in cookies.items())
        headers.append((b"cookie", cookie_value.encode("latin-1")))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "path": "/",
        "headers": headers,
    }
    return Request(scope)


def _set_cookie_names(response: Response) -> list[str]:
    return [value.split("=", 1)[0] for value in response.headers.getlist("set-cookie")]


def _fake_redis_client():
    class FakeRedis:
        def __init__(self):
            self._data: dict[str, str] = {}

        def setex(self, key, _ttl, value):
            self._data[key] = value

        def get(self, key):
            return self._data.get(key)

        def delete(self, key):
            self._data.pop(key, None)

    return FakeRedis()


def _make_refresh_token_store(*, ttl_seconds: int = 3600) -> RedisRefreshTokenStore:
    store = RedisRefreshTokenStore(ttl_seconds=ttl_seconds)
    store._client = _fake_redis_client()
    return store


def test_oidc_session_id_from_token_response_uses_access_token_sid():
    token_response = _token_response(sid="sid-from-access")

    assert oidc_session_id_from_token_response(token_response) == "sid-from-access"


def test_oidc_session_id_from_token_response_falls_back_to_id_token():
    token_response = {
        "access_token": _fake_jwt({"sub": "user-1"}),
        "id_token": _fake_jwt({"sid": "sid-from-id", "sub": "user-1"}),
        "refresh_token": "refresh-1",
    }

    assert oidc_session_id_from_token_response(token_response) == "sid-from-id"


def test_oidc_session_id_from_token_response_raises_when_sid_missing():
    token_response = {
        "access_token": _fake_jwt({"sub": "user-1"}),
        "id_token": _fake_jwt({"sub": "user-1"}),
        "refresh_token": "refresh-1",
    }

    with pytest.raises(UnauthorizedError, match="Missing sid claim"):
        oidc_session_id_from_token_response(token_response)


def test_set_auth_cookies_sets_access_id_and_session_on_login():
    response = Response()
    token_response = _token_response()

    set_auth_cookies(response, token_response, session_id="kc-session-123")

    cookie_names = _set_cookie_names(response)
    assert AuthCookieName.ACCESS_TOKEN in cookie_names
    assert AuthCookieName.ID_TOKEN in cookie_names
    assert AuthCookieName.SESSION in cookie_names


def test_set_auth_cookies_on_refresh_does_not_reset_session_cookie():
    response = Response()
    token_response = _token_response()

    set_auth_cookies(response, token_response)

    cookie_names = _set_cookie_names(response)
    assert AuthCookieName.ACCESS_TOKEN in cookie_names
    assert AuthCookieName.ID_TOKEN in cookie_names
    assert AuthCookieName.SESSION not in cookie_names


def test_clear_auth_cookies_removes_all_auth_cookies():
    response = Response()
    set_auth_cookies(response, _token_response(), session_id="kc-session-123")

    clear_auth_cookies(response)

    cleared = " ".join(value.decode() for _, value in response.raw_headers)
    assert AuthCookieName.ACCESS_TOKEN in cleared
    assert AuthCookieName.ID_TOKEN in cleared
    assert AuthCookieName.SESSION in cleared


def test_refresh_token_store_persists_only_refresh_token_data():
    store = _make_refresh_token_store(ttl_seconds=3600)
    token_response = _token_response(refresh_token="initial-refresh")

    stored_refresh_token = store.store(
        token_response=token_response,
        issuer="https://keycloak.example.com/realms/staff",
        session_id="kc-session-123",
    )

    assert stored_refresh_token.session_id == "kc-session-123"
    assert stored_refresh_token.refresh_token == "initial-refresh"
    assert stored_refresh_token.issuer == "https://keycloak.example.com/realms/staff"
    assert "access_token" not in RefreshTokenRecord.model_fields


def test_refresh_token_store_update_rotates_refresh_token_when_returned():
    store = _make_refresh_token_store(ttl_seconds=3600)
    stored_refresh_token = store.store(
        token_response=_token_response(refresh_token="old-refresh"),
        issuer="https://keycloak.example.com/realms/staff",
        session_id="kc-session-123",
    )

    updated = store.update_refresh_token(
        stored_refresh_token.session_id,
        {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "refresh_expires_in": 900,
        },
    )

    assert updated.refresh_token == "new-refresh"
    assert store.get(stored_refresh_token.session_id).refresh_token == "new-refresh"


def test_refresh_token_store_update_keeps_refresh_token_when_omitted():
    store = _make_refresh_token_store(ttl_seconds=3600)
    stored_refresh_token = store.store(
        token_response=_token_response(refresh_token="keep-me"),
        issuer="https://keycloak.example.com/realms/staff",
        session_id="kc-session-123",
    )

    updated = store.update_refresh_token(stored_refresh_token.session_id, {"access_token": "new-access"})

    assert updated.refresh_token == "keep-me"


def test_store_refresh_token_requires_refresh_token():
    service = AuthService()
    service._refresh_token_store = _make_refresh_token_store()

    with pytest.raises(UnauthorizedError, match="Missing refresh_token"):
        service.store_refresh_token(
            token_response={"access_token": _fake_jwt({"sid": "sid-1"})},
        )


def test_store_refresh_token_uses_sid_as_session_id():
    service = AuthService()
    service._refresh_token_store = _make_refresh_token_store()

    refresh_token = service.store_refresh_token(
        token_response=_token_response(sid="sid-42"),
    )

    assert refresh_token.session_id == "sid-42"
    assert service._refresh_token_store.get("sid-42").refresh_token == "refresh-1"


@pytest.mark.asyncio
async def test_refresh_access_token_returns_none_for_missing_session():
    service = AuthService()
    service._refresh_token_store = _make_refresh_token_store()

    result = await service.refresh_access_token("missing-session")

    assert result is None


@pytest.mark.asyncio
async def test_refresh_access_token_calls_idp_and_updates_store():
    service = AuthService()
    store = _make_refresh_token_store()
    service._refresh_token_store = store
    store.store(
        token_response=_token_response(sid="sid-99", refresh_token="rt-old"),
        issuer="https://keycloak.example.com/realms/staff",
        session_id="sid-99",
    )

    login_provider = types.SimpleNamespace(issuer="https://keycloak.example.com/realms/staff")
    refreshed = _token_response(sid="sid-99", refresh_token="rt-new", access_token="at-new")

    service.provider_repository = types.SimpleNamespace(
        get_by_iss=AsyncMock(return_value=login_provider),
    )
    service._adapters = types.SimpleNamespace(
        resolve_for_provider=lambda _lp: types.SimpleNamespace(
            refresh_access_token=AsyncMock(return_value=refreshed),
        ),
    )

    result = await service.refresh_access_token("sid-99")

    assert result["access_token"] == refreshed["access_token"]
    assert store.get("sid-99").refresh_token == "rt-new"


@pytest.mark.asyncio
async def test_refresh_access_token_returns_none_when_idp_rejects_refresh():
    service = AuthService()
    store = _make_refresh_token_store()
    service._refresh_token_store = store
    store.store(
        token_response=_token_response(sid="sid-99", refresh_token="rt-old"),
        issuer="https://keycloak.example.com/realms/staff",
        session_id="sid-99",
    )

    login_provider = types.SimpleNamespace(issuer="https://keycloak.example.com/realms/staff")
    service.provider_repository = types.SimpleNamespace(
        get_by_iss=AsyncMock(return_value=login_provider),
    )
    service._adapters = types.SimpleNamespace(
        resolve_for_provider=lambda _lp: types.SimpleNamespace(
            refresh_access_token=AsyncMock(
                side_effect=OAuthError(error="invalid_grant", description="Session not active"),
            ),
        ),
    )

    result = await service.refresh_access_token("sid-99")

    assert result is None
    assert store.get("sid-99") is None


def test_validate_refresh_token_response_raises_for_oidc_error():
    with pytest.raises(UnauthorizedError, match="Session not active"):
        validate_refresh_token_response(
            {"error": "invalid_grant", "error_description": "Session not active"},
        )


def test_validate_refresh_token_response_raises_for_missing_access_token():
    with pytest.raises(UnauthorizedError, match="Missing access_token"):
        validate_refresh_token_response({"token_type": "Bearer"})


def test_validate_refresh_token_response_returns_valid_response():
    token_response = {"access_token": "at-new", "refresh_token": "rt-new"}
    assert validate_refresh_token_response(token_response) == token_response


@pytest.mark.asyncio
async def test_refresh_access_token_returns_none_when_token_response_has_oidc_error():
    service = AuthService()
    store = _make_refresh_token_store()
    service._refresh_token_store = store
    store.store(
        token_response=_token_response(sid="sid-99", refresh_token="rt-old"),
        issuer="https://keycloak.example.com/realms/staff",
        session_id="sid-99",
    )

    login_provider = types.SimpleNamespace(issuer="https://keycloak.example.com/realms/staff")
    service.provider_repository = types.SimpleNamespace(
        get_by_iss=AsyncMock(return_value=login_provider),
    )
    service._adapters = types.SimpleNamespace(
        resolve_for_provider=lambda _lp: types.SimpleNamespace(
            refresh_access_token=AsyncMock(
                return_value={"error": "invalid_grant", "error_description": "Session not active"},
            ),
        ),
    )

    result = await service.refresh_access_token("sid-99")

    assert result is None
    assert store.get("sid-99") is None


@pytest.mark.asyncio
async def test_refresh_access_token_returns_none_when_token_response_missing_access_token():
    service = AuthService()
    store = _make_refresh_token_store()
    service._refresh_token_store = store
    store.store(
        token_response=_token_response(sid="sid-99", refresh_token="rt-old"),
        issuer="https://keycloak.example.com/realms/staff",
        session_id="sid-99",
    )

    login_provider = types.SimpleNamespace(issuer="https://keycloak.example.com/realms/staff")
    service.provider_repository = types.SimpleNamespace(
        get_by_iss=AsyncMock(return_value=login_provider),
    )
    service._adapters = types.SimpleNamespace(
        resolve_for_provider=lambda _lp: types.SimpleNamespace(
            refresh_access_token=AsyncMock(return_value={"token_type": "Bearer"}),
        ),
    )

    result = await service.refresh_access_token("sid-99")

    assert result is None
    assert store.get("sid-99") is None


@pytest.mark.asyncio
async def test_token_validator_raises_expired_token_error_for_expired_access_token():
    validator = TokenValidatorService()
    token = jose_jwt.encode(
        {"iss": "https://issuer", "aud": "portal", "sub": "u-1"},
        "secret",
        algorithm="HS256",
    )

    async def mock_provider(_iss):
        return types.SimpleNamespace(
            issuer="https://issuer",
            audiences_list=["portal"],
        )

    async def mock_decode_expired(*_args, **_kwargs):
        raise JoseExpiredTokenError()

    mock_adapter = types.SimpleNamespace(
        introspect_token=AsyncMock(),
        decode_access_token=mock_decode_expired,
        decode_id_token=AsyncMock(),
        normalize_claims=lambda claims, **_: claims,
        validate_claims=lambda *_a, **_k: None,
    )

    validator._get_login_provider_db_by_iss = mock_provider
    validator._adapters = types.SimpleNamespace(
        resolve_for_provider=lambda _lp: mock_adapter,
    )

    with pytest.raises(ExpiredTokenError):
        await validator.validate(
            jwt_token=token,
            jwt_id_token=None,
            api_auth_settings=ApiAuthSettings(enabled=True, validation_mode="jwt"),
        )


@pytest.mark.asyncio
async def test_token_validator_raises_unauthorized_for_non_expiry_jose_error():
    validator = TokenValidatorService()
    token = jose_jwt.encode(
        {"iss": "https://issuer", "aud": "portal", "sub": "u-1"},
        "secret",
        algorithm="HS256",
    )

    async def mock_provider(_iss):
        return types.SimpleNamespace(
            issuer="https://issuer",
            audiences_list=["portal"],
        )

    async def mock_decode_invalid(*_args, **_kwargs):
        raise BadSignatureError(result=None)

    mock_adapter = types.SimpleNamespace(
        introspect_token=AsyncMock(),
        decode_access_token=mock_decode_invalid,
        decode_id_token=AsyncMock(),
        normalize_claims=lambda claims, **_: claims,
        validate_claims=lambda *_a, **_k: None,
    )

    validator._get_login_provider_db_by_iss = mock_provider
    validator._adapters = types.SimpleNamespace(
        resolve_for_provider=lambda _lp: mock_adapter,
    )

    with pytest.raises(UnauthorizedError, match="Invalid Jwt"):
        await validator.validate(
            jwt_token=token,
            jwt_id_token=None,
            api_auth_settings=ApiAuthSettings(enabled=True, validation_mode="jwt"),
        )


def _auth_credentials(access_token: str = "valid-access") -> AuthCredentials:
    return AuthCredentials(credentials=access_token, sub="user-1")


@requires_auth
def _requires_auth_endpoint():
    return None


def _public_endpoint():
    return None


@require_permissions({"admin"})
def _requires_permissions_endpoint():
    return None


@pytest.mark.asyncio
async def test_resolve_permission_middleware_enforces_permissions_from_state():
    middleware = ResolvePermissionMiddleware(app=MagicMock(), client_id="portal-client")
    request = _make_request()
    request.state.auth = AuthPrincipal(
        credentials="valid-access", sub="user-1", client_roles={"portal-client": ["admin"]}
    )

    route = MagicMock()
    route.endpoint = _requires_permissions_endpoint

    downstream = Response(content=b"ok", status_code=200)
    call_next = AsyncMock(return_value=downstream)

    with (
        patch(
            "iam_core.user_auth.middleware.resolve_permissions.match_route",
            return_value=route,
        ),
        patch.object(middleware, "_fetch_permissions_for_roles", AsyncMock(return_value={"admin"})),
    ):
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    assert request.state.permissions == {"admin"}


@pytest.mark.asyncio
async def test_resolve_permission_middleware_raises_unauthorized_without_auth_state():
    middleware = ResolvePermissionMiddleware(app=MagicMock(), client_id="portal-client")
    request = _make_request()

    route = MagicMock()
    route.endpoint = _requires_permissions_endpoint
    call_next = AsyncMock()

    with patch(
        "iam_core.user_auth.middleware.resolve_permissions.match_route",
        return_value=route,
    ):
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_resolve_permission_middleware_raises_forbidden_when_permissions_missing():
    middleware = ResolvePermissionMiddleware(app=MagicMock(), client_id="portal-client")
    request = _make_request()
    request.state.auth = AuthPrincipal(
        credentials="valid-access", sub="user-1", client_roles={"portal-client": ["viewer"]}
    )

    route = MagicMock()
    route.endpoint = _requires_permissions_endpoint
    call_next = AsyncMock()

    with (
        patch(
            "iam_core.user_auth.middleware.resolve_permissions.match_route",
            return_value=route,
        ),
        patch.object(middleware, "_fetch_permissions_for_roles", AsyncMock(return_value={"viewer"})),
    ):
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_validate_and_refresh_runs_for_require_permissions_endpoints():
    middleware = ValidateAndRefreshTokenMiddleware(app=MagicMock())
    request = _make_request(
        cookies={
            AuthCookieName.ACCESS_TOKEN: "valid-access",
            AuthCookieName.SESSION: "kc-session-123",
        },
    )

    route = MagicMock()
    route.endpoint = _requires_permissions_endpoint

    downstream = Response(content=b"ok", status_code=200)
    call_next = AsyncMock(return_value=downstream)

    with (
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.match_route",
            return_value=route,
        ),
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.validate_request_token",
            AsyncMock(return_value=_auth_credentials()),
        ) as mock_validate,
    ):
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    mock_validate.assert_awaited_once()
    assert request.state.auth.credentials == "valid-access"


@pytest.mark.asyncio
async def test_validate_and_refresh_middleware_refreshes_expired_token_and_updates_cookies():
    middleware = ValidateAndRefreshTokenMiddleware(app=MagicMock())
    request = _make_request(
        cookies={
            AuthCookieName.ACCESS_TOKEN: "expired-access",
            AuthCookieName.SESSION: "kc-session-123",
        },
    )

    route = MagicMock()
    route.name = "get_user_profile"
    route.endpoint = _requires_auth_endpoint
    refreshed_tokens = _token_response(sid="kc-session-123", access_token="fresh-access")

    downstream = Response(content=b"ok", status_code=200)
    call_next = AsyncMock(return_value=downstream)

    with (
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.match_route",
            return_value=route,
        ),
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.validate_request_token",
            AsyncMock(
                side_effect=[
                    ExpiredTokenError(),
                    _auth_credentials("fresh-access"),
                ],
            ),
        ),
        patch.object(middleware, "_refresh_access_token", AsyncMock(return_value=refreshed_tokens)),
    ):
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    cookie_names = _set_cookie_names(response)
    assert AuthCookieName.ACCESS_TOKEN in cookie_names
    assert AuthCookieName.ID_TOKEN in cookie_names
    assert AuthCookieName.SESSION not in cookie_names
    assert request.headers.get("authorization") == "Bearer fresh-access"


@pytest.mark.asyncio
async def test_validate_and_refresh_middleware_skips_refresh_when_token_is_valid():
    middleware = ValidateAndRefreshTokenMiddleware(app=MagicMock())
    request = _make_request(
        cookies={
            AuthCookieName.ACCESS_TOKEN: "valid-access",
            AuthCookieName.SESSION: "kc-session-123",
        },
    )

    route = MagicMock()
    route.name = "get_user_profile"
    route.endpoint = _requires_auth_endpoint

    downstream = Response(content=b"ok", status_code=200)
    call_next = AsyncMock(return_value=downstream)

    with (
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.match_route",
            return_value=route,
        ),
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.validate_request_token",
            AsyncMock(return_value=_auth_credentials()),
        ) as mock_validate,
        patch.object(middleware, "_refresh_access_token", AsyncMock()) as mock_refresh,
    ):
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    mock_validate.assert_awaited_once()
    mock_refresh.assert_not_called()
    assert request.state.auth.credentials == "valid-access"


@pytest.mark.asyncio
async def test_validate_and_refresh_middleware_skips_unprotected_routes():
    middleware = ValidateAndRefreshTokenMiddleware(app=MagicMock())
    request = _make_request()
    route = MagicMock()
    route.name = "get_login_providers"
    route.endpoint = _public_endpoint

    downstream = Response(content=b"ok", status_code=200)
    call_next = AsyncMock(return_value=downstream)

    with (
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.match_route",
            return_value=route,
        ),
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.validate_request_token",
            AsyncMock(),
        ) as mock_validate,
    ):
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    mock_validate.assert_not_called()


@pytest.mark.asyncio
async def test_validate_and_refresh_middleware_raises_unauthorized_when_refresh_fails():
    middleware = ValidateAndRefreshTokenMiddleware(app=MagicMock())
    request = _make_request(
        cookies={
            AuthCookieName.ACCESS_TOKEN: "expired-access",
            AuthCookieName.SESSION: "kc-session-123",
        },
    )
    route = MagicMock()
    route.name = "get_user_profile"
    route.endpoint = _requires_auth_endpoint
    call_next = AsyncMock()

    with (
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.match_route",
            return_value=route,
        ),
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.validate_request_token",
            AsyncMock(side_effect=ExpiredTokenError()),
        ),
        patch.object(middleware, "_refresh_access_token", AsyncMock(return_value=None)),
    ):
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 401
    cookie_names = _set_cookie_names(response)
    assert AuthCookieName.ACCESS_TOKEN in cookie_names
    assert AuthCookieName.ID_TOKEN in cookie_names
    assert AuthCookieName.SESSION in cookie_names
    body = json.loads(response.body)
    assert body["response_header"]["response_error_message"] == REFRESH_FAILED_MESSAGE


def test_has_active_refresh_session_returns_false_when_missing():
    store = _make_refresh_token_store()
    service = AuthService()
    service._refresh_token_store = store

    assert service.has_active_refresh_session("missing-session") is False


def test_has_active_refresh_session_returns_true_when_present():
    store = _make_refresh_token_store()
    service = AuthService()
    service._refresh_token_store = store
    service.store_refresh_token(token_response=_token_response(sid="sid-99"))

    assert service.has_active_refresh_session("sid-99") is True


@pytest.mark.asyncio
async def test_handle_backchannel_logout_deletes_refresh_token_by_sid():
    store = _make_refresh_token_store()
    service = AuthService()
    service._refresh_token_store = store
    service.store_refresh_token(token_response=_token_response(sid="sid-bc-logout"))

    login_provider = MagicMock()
    login_provider.client_id = "staff-portal"
    login_provider.audiences_list = ["staff-portal"]

    adapter = MagicMock()
    adapter.decode_logout_token = AsyncMock(
        return_value={
            "iss": "https://keycloak.example.com/realms/staff",
            "aud": "staff-portal",
            "sid": "sid-bc-logout",
            "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
        }
    )

    service.provider_repository = types.SimpleNamespace(
        get_by_iss=AsyncMock(return_value=login_provider),
    )
    service._adapters = types.SimpleNamespace(
        resolve_for_provider=lambda _provider: adapter,
    )

    logout_token = _fake_jwt(
        {
            "iss": "https://keycloak.example.com/realms/staff",
            "aud": "staff-portal",
            "sid": "sid-bc-logout",
            "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
        }
    )

    await service.handle_backchannel_logout(logout_token)

    assert store.get("sid-bc-logout") is None


@pytest.mark.asyncio
async def test_validate_and_refresh_middleware_rejects_when_refresh_token_missing_from_redis():
    middleware = ValidateAndRefreshTokenMiddleware(app=MagicMock())
    request = _make_request(
        cookies={
            AuthCookieName.ACCESS_TOKEN: "valid-access",
            AuthCookieName.SESSION: "kc-session-123",
        },
    )
    route = MagicMock()
    route.name = "get_user_profile"
    route.endpoint = _requires_auth_endpoint
    call_next = AsyncMock()

    with (
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.match_route",
            return_value=route,
        ),
        patch(
            "iam_core.user_auth.middleware.validate_and_refresh.validate_request_token",
            AsyncMock(),
        ) as mock_validate,
        patch(
            "iam_core.services.AuthService",
        ) as mock_auth_service_cls,
    ):
        mock_auth_service = MagicMock()
        mock_auth_service.has_active_refresh_session.return_value = False
        mock_auth_service_cls.get_component.return_value = mock_auth_service
        response = await middleware.dispatch(request, call_next)

    assert response.status_code == 401
    mock_validate.assert_not_called()
    call_next.assert_not_called()
    cookie_names = _set_cookie_names(response)
    assert AuthCookieName.ACCESS_TOKEN in cookie_names
    assert AuthCookieName.ID_TOKEN in cookie_names
    assert AuthCookieName.SESSION in cookie_names
    body = json.loads(response.body)
    assert body["response_header"]["response_error_message"] == SESSION_INVALIDATED_MESSAGE
