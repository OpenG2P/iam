import base64
import json
import types

from iam_core.schemas import TokenEndpointAuthMethod
from starlette.requests import Request


def fake_jwt(claims: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.sig"


def token_response(
    *,
    sid: str = "kc-session-123",
    iss: str = "https://keycloak.example.com/realms/staff",
    access_token: str | None = None,
    id_token: str | None = None,
    refresh_token: str = "refresh-1",
) -> dict:
    return {
        "access_token": access_token or fake_jwt({"sid": sid, "sub": "user-1", "iss": iss}),
        "id_token": id_token or fake_jwt({"sub": "user-1", "iss": iss}),
        "refresh_token": refresh_token,
        "expires_in": 300,
        "refresh_expires_in": 1800,
    }


def make_request(
    *,
    cookies: dict[str, str] | None = None,
    authorization: str | None = None,
    path: str = "/",
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
        "path": path,
        "headers": headers,
    }
    return Request(scope)


class FakeRedis:
    def __init__(self):
        self._data: dict[str, str] = {}

    def setex(self, key, _ttl, value):
        self._data[key] = value

    def get(self, key):
        return self._data.get(key)

    def delete(self, key):
        self._data.pop(key, None)


def make_login_provider(**overrides) -> types.SimpleNamespace:
    defaults = {
        "id": 1,
        "provider_name": "keycloak",
        "description": "Keycloak",
        "icon_base64": "icon",
        "client_id": "staff-portal",
        "client_secret": "secret",
        "token_endpoint_auth_method": TokenEndpointAuthMethod.client_secret_post,
        "issuer": "https://keycloak.example.com/realms/staff",
        "audiences": '["staff-portal"]',
        "audiences_list": ["staff-portal"],
        "adapter_name": "keycloak",
        "oauth_callback_url": "https://app.example.com/callback",
        "authorization_endpoint": "https://keycloak.example.com/realms/staff/protocol/openid-connect/auth",
        "token_endpoint": "https://keycloak.example.com/realms/staff/protocol/openid-connect/token",
        "userinfo_endpoint": "https://keycloak.example.com/realms/staff/protocol/openid-connect/userinfo",
        "jwks_uri": "https://keycloak.example.com/realms/staff/protocol/openid-connect/certs",
        "server_metadata_url": None,
        "scope": "openid profile email",
        "enable_pkce": False,
        "extra_authorize_params": None,
        "default_redirect_uri": "/home",
        "keymanager_app_id": "app",
        "keymanager_ref_id": "ref",
        "jwt_assertion_aud": None,
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)
