import base64
import json
import types
from collections import deque
from unittest.mock import AsyncMock, MagicMock

from iam_core.schemas import AuthPrincipal
from starlette.requests import Request


def fake_jwt(claims: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{payload}.sig"


def make_request(
    *,
    cookies: dict[str, str] | None = None,
    authorization: str | None = None,
    path: str = "/",
    auth: AuthPrincipal | None = None,
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
    request = Request(scope)
    if auth is not None:
        request.state.auth = auth
    return request


def make_auth(
    *,
    client_roles: dict[str, list[str]] | None = None,
    iss: str = "https://keycloak.example.com/realms/staff",
) -> AuthPrincipal:
    return AuthPrincipal(
        credentials=fake_jwt({"iss": iss, "sub": "user-1"}),
        client_roles=client_roles or {},
    )


def make_app_row(**overrides) -> types.SimpleNamespace:
    defaults = {
        "id": 1,
        "application_mnemonic": "registry-staff-portal",
        "application_description": "Registry",
        "application_url": "https://registry.example.com",
        "api_url": None,
        "icon_base64": "icon",
        "width": 80,
        "order": 1,
        "active": True,
        "is_self_registered": False,
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def make_permission_row(**overrides) -> types.SimpleNamespace:
    defaults = {
        "id": 10,
        "application_id": 1,
        "permission_mnemonic": "register:view",
        "permission_description": "View register",
        "active": True,
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def make_role_row(**overrides) -> types.SimpleNamespace:
    defaults = {
        "id": 20,
        "application_id": 1,
        "role_mnemonic": "Data Editor",
        "role_description": "Editor",
        "active": True,
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def make_execute_result(*, all_rows=None, first_row=None, scalar_rows=None):
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = all_rows if all_rows is not None else []
    scalars.first.return_value = first_row
    result.scalars.return_value = scalars
    if scalar_rows is not None:
        result.scalar.side_effect = scalar_rows
    return result


def make_mock_session(*execute_results):
    session = AsyncMock()
    queue = deque(execute_results)

    async def _execute(*_args, **_kwargs):
        if not queue:
            return make_execute_result()
        return queue.popleft()

    session.execute = AsyncMock(side_effect=_execute)
    session.scalar = AsyncMock(side_effect=lambda *_a, **_k: None)
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.get_bind = MagicMock()
    return session, queue


def make_session_factory(session):
    factory = MagicMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)
    factory.return_value = cm
    return factory
