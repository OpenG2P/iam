import base64
import types
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from jose import jwt as jose_jwt
from openg2p_fastapi_common.errors.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    UnauthorizedError,
)
from starlette.routing import Match

from iam_core.schemas import TokenEndpointAuthMethod
from iam_core.user_auth.decorators import (
    endpoint_requires_auth,
    endpoint_requires_token,
    endpoint_requires_user,
    get_required_permissions,
    require_permissions,
    requires_auth,
    requires_user,
)
from iam_core.user_auth.helpers.auth_user_helper import (
    auth_from_request,
    auth_principal_from_credentials,
    build_logged_in_user,
    logged_in_user_from_claims,
    logged_in_user_from_request,
)
from iam_core.user_auth.helpers.claims_helper import (
    claim_equals,
    claim_in,
    claims_from_auth,
    extract_client_roles,
    has_claim,
)
from iam_core.user_auth.helpers.client_assertion_helper import (
    generate_keymanager_client_assertion,
    generate_private_key_client_assertion,
)
from iam_core.user_auth.helpers.cookie_helper import (
    generate_csrf_token,
    issuer_from_token_response,
    set_csrf_cookie,
)
from iam_core.user_auth.helpers.jwks_helper import get_jwks
from iam_core.user_auth.helpers.jwt_helper import decode_jwt
from iam_core.user_auth.helpers.logout_token_helper import session_id_from_logout_token_claims
from iam_core.user_auth.helpers.pkce_helper import pkce_kwargs
from iam_core.user_auth.helpers.route_helper import match_route, match_route_in_routes, resolve_matched_route
from iam_core.user_auth.helpers.token_helper import (
    access_token_and_id_token_from_request,
    validate_request_token,
)
from iam_core.user_auth.middleware.resolve_permissions import ResolvePermissionMiddleware
from iam_core.schemas import AuthCredentials, AuthPrincipal, LoggedInUserResponse
from iam_core.user_auth.enums import AuthCookieName
from helpers import fake_jwt, make_login_provider, make_request, token_response


def _b64url_uint(value: int) -> str:
    length = (value.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(value.to_bytes(length, "big")).rstrip(b"=").decode()


def _rsa_jwks_and_token(*, nonce: str | None = None):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "kid-1",
                "use": "sig",
                "alg": "RS256",
                "n": _b64url_uint(public_numbers.n),
                "e": _b64url_uint(public_numbers.e),
            }
        ]
    }
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    claims = {"sub": "user-1", "iss": "https://issuer"}
    if nonce:
        claims["nonce"] = nonce
    token = jose_jwt.encode(claims, pem, algorithm="RS256", headers={"kid": "kid-1"})
    return jwks, token


def test_claims_helper_paths():
    assert claims_from_auth({"sub": "u"}) == {"sub": "u"}
    assert claims_from_auth(AuthCredentials(credentials="t", sub="u"))["sub"] == "u"
    assert claims_from_auth(object()) == {}
    assert extract_client_roles({"resource_access": {"c": {"roles": ["b", "a"]}}}) == {"c": ["a", "b"]}
    assert extract_client_roles({}) is None


@pytest.mark.asyncio
async def test_claim_dependency_factories():
    with pytest.raises(ForbiddenError, match="Missing claim"):
        await has_claim("roles")({"sub": "u"})
    assert (await has_claim("roles")({"roles": ["admin"]}))["roles"] == ["admin"]

    with pytest.raises(ForbiddenError, match="mismatch"):
        await claim_equals("roles", "admin")({"roles": "viewer"})
    assert (await claim_equals("roles", "admin")({"roles": "admin"}))["roles"] == "admin"

    with pytest.raises(ForbiddenError, match="not allowed"):
        await claim_in("roles", {"admin"})({"roles": 123})
    assert (await claim_in("roles", {"admin"})({"roles": ["admin"]}))["roles"] == ["admin"]


def test_auth_user_helper_paths():
    claims = {
        "sub": "u",
        "name": "User",
        "email": "a@b.c",
        "address": {"country": "IN"},
        "preferred_username": "user",
        "given_name": "U",
        "family_name": "Ser",
        "email_verified": True,
    }
    user = logged_in_user_from_claims(claims)
    assert user.name == "User"
    assert user.address == {"country": "IN"}

    user = logged_in_user_from_claims({"sub": "u", "address": "bad"})
    assert user.address == {}

    creds = AuthCredentials(credentials="token", sub="u", resource_access={"c": {"roles": ["admin"]}})
    principal = auth_principal_from_credentials(creds)
    assert principal.client_roles == {"c": ["admin"]}

    request = make_request()
    request.state.auth = principal
    assert auth_from_request(request).sub == "u"

    request.state.user = LoggedInUserResponse(sub="u")
    assert logged_in_user_from_request(request).sub == "u"

    request = make_request()
    with pytest.raises(UnauthorizedError):
        auth_from_request(request)
    with pytest.raises(UnauthorizedError):
        logged_in_user_from_request(request)


@pytest.mark.asyncio
async def test_build_logged_in_user_prefers_userinfo_and_falls_back():
    creds = AuthCredentials(credentials="token", sub="u", iss="https://issuer", name="Token Name")
    mock_service = types.SimpleNamespace(
        get_oauth_validation_data=AsyncMock(return_value={"sub": "u", "name": "Live Name"}),
    )
    user = await build_logged_in_user(creds, auth_service=mock_service)
    assert user.name == "Live Name"

    mock_service.get_oauth_validation_data = AsyncMock(side_effect=RuntimeError("down"))
    user = await build_logged_in_user(creds, auth_service=mock_service)
    assert user.name == "Token Name"

    user = await build_logged_in_user(AuthPrincipal(credentials="token", sub="u", name="Principal"))
    assert user.name == "Principal"


def test_cookie_and_pkce_helpers():
    from iam_core.user_auth.helpers.cookie_helper import oidc_session_id_from_token_response

    assert issuer_from_token_response(token_response()) == "https://keycloak.example.com/realms/staff"
    with pytest.raises(UnauthorizedError, match="Missing iss"):
        issuer_from_token_response({"access_token": fake_jwt({"sub": "u"})})

    token_response_data = {
        "id_token": fake_jwt({"sid": "sid-1", "iss": "https://issuer"}),
    }
    assert oidc_session_id_from_token_response(token_response_data) == "sid-1"

    token_response_data = {
        "access_token": "not-a-jwt",
        "id_token": fake_jwt({"sid": "sid-1", "iss": "https://issuer"}),
    }
    assert oidc_session_id_from_token_response(token_response_data) == "sid-1"
    assert issuer_from_token_response(token_response_data) == "https://issuer"

    with patch("iam_core.user_auth.helpers.cookie_helper._config") as cfg:
        cfg.auth_cookie_set_expires = True
        from iam_core.user_auth.helpers.cookie_helper import _cookie_expires

        assert _cookie_expires({"expires_in": 120}) is not None
        assert _cookie_expires({}) is None

    with pytest.raises(UnauthorizedError):
        issuer_from_token_response({"access_token": "not-jwt", "id_token": "also-bad"})

    response = MagicMock()
    token = set_csrf_cookie(response, token="csrf-1")
    assert token == "csrf-1"
    assert generate_csrf_token()

    lp = make_login_provider(enable_pkce=True)
    assert pkce_kwargs(lp, "verifier") == {"code_verifier": "verifier"}
    assert pkce_kwargs(lp, None) == {}


def test_logout_token_helper_validation_paths():
    lp = make_login_provider(client_id="staff-portal")
    valid = {
        "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
        "sid": "sid-1",
        "aud": "staff-portal",
    }
    assert session_id_from_logout_token_claims(valid, lp) == "sid-1"
    assert session_id_from_logout_token_claims({**valid, "aud": ["staff-portal"]}, lp) == "sid-1"

    with pytest.raises(UnauthorizedError, match="nonce"):
        session_id_from_logout_token_claims({**valid, "nonce": "n"}, lp)
    with pytest.raises(UnauthorizedError, match="backchannel-logout"):
        session_id_from_logout_token_claims({"sid": "s", "aud": "staff-portal"}, lp)
    with pytest.raises(UnauthorizedError, match="missing sid"):
        session_id_from_logout_token_claims({"events": valid["events"], "aud": "staff-portal"}, lp)
    with pytest.raises(UnauthorizedError, match="audience"):
        session_id_from_logout_token_claims({**valid, "aud": "other"}, lp)
    with pytest.raises(UnauthorizedError, match="audience"):
        session_id_from_logout_token_claims({**valid, "aud": ["other-client"]}, lp)


@pytest.mark.asyncio
async def test_jwks_helper_fetch_and_cache():
    FastAPICache.init(InMemoryBackend(), prefix="test-jwks")
    await FastAPICache.clear()
    metadata = {"jwks_uri": "https://issuer/jwks"}
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"keys": []}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__.return_value = mock_http
        mock_http.get = AsyncMock(return_value=response)
        mock_client_cls.return_value = mock_http
        first = await get_jwks(metadata, "https://issuer")
        second = await get_jwks(metadata, "https://issuer")
        assert first == {"keys": []}
        assert second == {"keys": []}
        mock_http.get.assert_awaited_once()

    with pytest.raises(Exception):
        await get_jwks({}, None)

    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"keys": [{"kty": "RSA"}]}
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__.return_value = mock_http
        mock_http.get = AsyncMock(return_value=response)
        mock_client_cls.return_value = mock_http
        jwks = await get_jwks({}, "https://issuer.example.com")
        assert jwks["keys"]


def test_jwt_helper_decode_paths():
    jwks, token = _rsa_jwks_and_token(nonce="n-once")
    claims = decode_jwt(token, jwks, verify_exp=False, nonce="n-once", access_token="at")
    assert claims["sub"] == "user-1"

    with pytest.raises(UnauthorizedError, match="Nonce mismatch"):
        decode_jwt(token, jwks, verify_exp=False, nonce="wrong", access_token="at")


def test_jwt_helper_validates_exp():
    from authlib.jose import JsonWebKey, jwt as authlib_jwt
    from datetime import datetime, timedelta, timezone

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    jwk = JsonWebKey.import_key(public_pem, {"kty": "RSA", "alg": "RS256", "kid": "kid"})
    jwks = {"keys": [dict(jwk.as_dict())]}
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    claims = {
        "sub": "u",
        "exp": int((datetime.now(tz=timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    token = authlib_jwt.encode({"alg": "RS256", "kid": "kid"}, claims, pem)
    decoded = decode_jwt(token, jwks, verify_exp=True)
    assert decoded["sub"] == "u"


@pytest.mark.asyncio
async def test_client_assertion_helpers():
    lp = make_login_provider(
        token_endpoint_auth_method=TokenEndpointAuthMethod.private_key_jwt_keymanager,
        jwt_assertion_aud="https://idp/token",
    )
    helper = AsyncMock(create_jwt_token=AsyncMock(return_value="signed"))
    assertion = await generate_keymanager_client_assertion(lp, keymanager_helper=helper)
    assert assertion[1] == "signed"

    with pytest.raises(Exception):
        await generate_keymanager_client_assertion(
            make_login_provider(token_endpoint_auth_method=TokenEndpointAuthMethod.client_secret_post),
            keymanager_helper=helper,
        )
    with pytest.raises(Exception):
        await generate_keymanager_client_assertion(lp, keymanager_helper=None)

    pem = rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    lp = make_login_provider(
        token_endpoint_auth_method=TokenEndpointAuthMethod.private_key_jwt,
        client_private_key=pem,
        jwt_assertion_aud="https://idp/token",
    )
    assertion = generate_private_key_client_assertion(lp, private_key_jwt_kid="kid-1")
    assert assertion[0].endswith("jwt-bearer")
    assert assertion[1]

    with pytest.raises(Exception):
        generate_private_key_client_assertion(
            make_login_provider(token_endpoint_auth_method=TokenEndpointAuthMethod.client_secret_post),
        )
    with pytest.raises(Exception):
        generate_private_key_client_assertion(
            make_login_provider(
                token_endpoint_auth_method=TokenEndpointAuthMethod.private_key_jwt,
                client_private_key=None,
            ),
        )

    lp = make_login_provider(token_endpoint_auth_method=None, token_endpoint=None, jwt_assertion_aud=None)
    with pytest.raises(InternalServerError, match="token_endpoint"):
        from iam_core.user_auth.helpers.client_assertion_helper import _jwt_payload

        _jwt_payload(lp)


def test_access_token_and_id_token_from_request():
    request = make_request(
        authorization="Bearer header-token",
        cookies={AuthCookieName.ID_TOKEN: "id-token"},
    )
    access, id_token = access_token_and_id_token_from_request(request)
    assert access == "header-token"
    assert id_token == "id-token"


class _LeafRoute:
    def __init__(self, endpoint=None):
        self.endpoint = endpoint

    def matches(self, scope):
        return Match.FULL, {}


class _NestedRoute:
    def __init__(self, routes):
        self.routes = routes
        self.endpoint = None

    def matches(self, scope):
        return Match.FULL, {"path_params": {}}


class _MatchRoute:
    def __init__(self, inner_route, original_route=None):
        self.endpoint = None
        self._inner = inner_route
        self._original = original_route

    def _match(self, scope):
        return Match.FULL, {}, self._inner, types.SimpleNamespace(original_route=self._original)


class _NonFullMatchRoute:
    endpoint = None

    def _match(self, scope):
        return Match.PARTIAL, {}, None, None


class _InnerMatchRoute:
    endpoint = None

    def _match(self, scope):
        child = _LeafRoute(endpoint=lambda: None)
        return Match.FULL, {}, child, None


class _EmptyInnerMatchRoute:
    endpoint = None

    def _match(self, scope):
        return Match.FULL, {}, None, types.SimpleNamespace(original_route=None)


class _PartialParent:
    endpoint = None
    routes = []

    def matches(self, scope):
        return Match.PARTIAL, {"root_path": "/api"}


class _ContextRoute:
    endpoint = None

    def _match(self, scope):
        return Match.FULL, {}, None, types.SimpleNamespace(original_route=_LeafRoute(endpoint=lambda: None))


class _NoneMatchRoute:
    def matches(self, scope):
        return Match.NONE, {}


def test_route_helper_resolution():
    scope = {"type": "http", "path": "/x", "method": "GET"}
    leaf = _LeafRoute(endpoint=lambda: None)
    assert resolve_matched_route(leaf, scope) is leaf

    nested = _NestedRoute([leaf])
    assert match_route_in_routes([nested], scope) is leaf

    wrapper = _MatchRoute(leaf, original_route=leaf)
    assert resolve_matched_route(wrapper, scope) is leaf

    request = MagicMock()
    request.scope = make_request(path="/x").scope
    request.app = types.SimpleNamespace(router=types.SimpleNamespace(routes=[leaf]))
    assert match_route(request) is leaf

    parent = _PartialParent()
    parent.routes = [_LeafRoute(endpoint=lambda: None)]
    assert match_route_in_routes([parent], scope) is parent.routes[0]
    assert resolve_matched_route(types.SimpleNamespace(endpoint=None), scope) is None
    assert resolve_matched_route(_ContextRoute(), scope).endpoint is not None
    assert resolve_matched_route(_NonFullMatchRoute(), scope) is None
    assert resolve_matched_route(_InnerMatchRoute(), scope).endpoint is not None
    assert resolve_matched_route(_EmptyInnerMatchRoute(), scope) is None
    assert match_route_in_routes([_NoneMatchRoute()], scope) is None


@requires_user
def _requires_user_endpoint():
    return "user"


@requires_auth
def _requires_auth_only():
    return "auth"


@require_permissions({"perm"})
def _requires_perm_endpoint():
    return "perm"


def test_decorator_metadata_helpers():
    assert endpoint_requires_auth(_requires_auth_only) is True
    assert endpoint_requires_user(_requires_user_endpoint) is True
    assert endpoint_requires_token(_requires_perm_endpoint) is True
    assert get_required_permissions(_requires_perm_endpoint) == {"perm"}
    assert _requires_user_endpoint() == "user"
    assert _requires_auth_only() == "auth"
    assert _requires_perm_endpoint() == "perm"


@pytest.mark.asyncio
async def test_resolve_permission_middleware_extra_paths():
    middleware = ResolvePermissionMiddleware(app=MagicMock(), client_id="portal", allow_by_default=False)
    request = make_request()
    call_next = AsyncMock(return_value=MagicMock())

    with patch("iam_core.user_auth.middleware.resolve_permissions.match_route", return_value=None):
        await middleware.dispatch(request, call_next)
        call_next.assert_awaited_once()

    route = MagicMock(endpoint=None)
    with patch("iam_core.user_auth.middleware.resolve_permissions.match_route", return_value=route):
        await middleware.dispatch(request, call_next)

    middleware = ResolvePermissionMiddleware(app=MagicMock(), client_id="", allow_by_default=True)
    request = make_request()
    request.state.auth = AuthPrincipal(credentials="t", sub="u", client_roles={"": ["admin"]})
    route = MagicMock(endpoint=_requires_perm_endpoint)
    with (
        patch("iam_core.user_auth.middleware.resolve_permissions.match_route", return_value=route),
        patch.object(middleware, "_fetch_permissions_for_roles", AsyncMock(return_value={"admin"})),
    ):
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403

    def resolver(_request, _route):
        return {"custom"}

    middleware = ResolvePermissionMiddleware(
        app=MagicMock(),
        client_id="portal",
        required_permissions_resolver=resolver,
    )
    request = make_request()
    request.state.auth = AuthPrincipal(
        credentials="t",
        sub="u",
        client_roles={"portal": ["admin"]},
    )
    route = MagicMock(endpoint=lambda: None)
    with patch.object(middleware, "_fetch_permissions_for_roles", AsyncMock(return_value={"custom"})):
        with patch("iam_core.user_auth.middleware.resolve_permissions.match_route", return_value=route):
            await middleware.dispatch(request, call_next)
            assert request.state.permissions == {"custom"}


@pytest.mark.asyncio
async def test_resolve_permission_fetch_permissions_paths():
    from fastapi_cache import FastAPICache
    from fastapi_cache.backends.inmemory import InMemoryBackend

    FastAPICache.init(InMemoryBackend(), prefix="test-iam-permissions")
    middleware = ResolvePermissionMiddleware(app=MagicMock(), client_id="portal")

    assert await middleware._fetch_permissions_for_roles([]) == set()

    with patch(
        "iam_core.user_auth.middleware.resolve_permissions.Settings.get_config",
        return_value=types.SimpleNamespace(auth_provider_api_url=None),
    ):
        await FastAPICache.clear()
        with pytest.raises(ForbiddenError, match="auth_provider_api_url"):
            await middleware._fetch_permissions_for_roles(["admin"])

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"permissions": ["p1", "p2"]}
    with (
        patch(
            "iam_core.user_auth.middleware.resolve_permissions.Settings.get_config",
            return_value=types.SimpleNamespace(auth_provider_api_url="https://iam/api"),
        ),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        await FastAPICache.clear()
        mock_http = AsyncMock()
        mock_http.__aenter__.return_value = mock_http
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_http
        perms = await middleware._fetch_permissions_for_roles(["admin"])
        assert perms == {"p1", "p2"}

    with (
        patch(
            "iam_core.user_auth.middleware.resolve_permissions.Settings.get_config",
            return_value=types.SimpleNamespace(auth_provider_api_url="https://iam/api"),
        ),
        patch("httpx.AsyncClient") as mock_client_cls,
    ):
        await FastAPICache.clear()
        mock_http = AsyncMock()
        mock_http.__aenter__.return_value = mock_http
        mock_http.post = AsyncMock(side_effect=httpx.HTTPError("down"))
        mock_client_cls.return_value = mock_http
        with pytest.raises(ForbiddenError, match="Unable to fetch"):
            await middleware._fetch_permissions_for_roles(["admin-fail"])


@pytest.mark.asyncio
async def test_validate_request_token_delegates_to_validator():
    request = make_request()
    request.scope["route"] = types.SimpleNamespace(name="get_user_profile")
    creds = types.SimpleNamespace()
    with patch(
        "iam_core.services.token_validator_service.TokenValidatorService.validate",
        AsyncMock(return_value=creds),
    ):
        with patch(
            "iam_core.services.token_validator_service.TokenValidatorService.get_component", return_value=None
        ):
            result = await validate_request_token(request, "jwt-token", "id-token")
            assert result is creds


@pytest.mark.asyncio
async def test_resolve_permissions_allow_by_default_paths():
    middleware = ResolvePermissionMiddleware(app=MagicMock(), allow_by_default=True)
    request = make_request()
    route = MagicMock(endpoint=lambda: None)
    call_next = AsyncMock(return_value=MagicMock())
    with patch("iam_core.user_auth.middleware.resolve_permissions.match_route", return_value=route):
        await middleware.dispatch(request, call_next)
        call_next.assert_awaited_once()

    middleware = ResolvePermissionMiddleware(app=MagicMock(), allow_by_default=False, client_id="portal")
    request = make_request()
    call_next = AsyncMock(return_value=MagicMock())
    with patch("iam_core.user_auth.middleware.resolve_permissions.match_route", return_value=route):
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 401
        call_next.assert_not_called()
