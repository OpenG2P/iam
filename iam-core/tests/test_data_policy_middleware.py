from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from iam_core.user_auth.middleware.data_policy import (
    STATE_KEY_DATA_POLICY_MNEMONICS,
    DataPolicyMiddleware,
)
from iam_core.user_auth.helpers.data_policy_role_helper import (
    get_data_policy_mnemonics,
    is_dp_role,
    strip_dp_prefix,
)


def _make_request(path: str = "/records") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "headers": [],
    }
    return Request(scope)


def test_is_dp_role_is_case_insensitive():
    assert is_dp_role("DP_foo") is True
    assert is_dp_role("dp_bar") is True
    assert is_dp_role("Admin") is False


def test_strip_dp_prefix_removes_prefix():
    assert strip_dp_prefix("DP_registry") == "registry"
    assert strip_dp_prefix("admin") == "admin"


def test_get_data_policy_mnemonics_deduplicates_and_skips_non_dp_roles():
    mnemonics = get_data_policy_mnemonics(["DP_alpha", "admin", "dp_beta", "DP_alpha", "DP_"])
    assert mnemonics == ["alpha", "beta"]


def test_get_data_policy_mnemonics_returns_empty_for_missing_roles():
    assert get_data_policy_mnemonics(None) == []
    assert get_data_policy_mnemonics([]) == []


@pytest.mark.asyncio
async def test_data_policy_middleware_attaches_resolved_mnemonics():
    user = MagicMock()
    user.client_roles = {"registry-client": ["DP_view", "DP_edit", "DataEditor"]}
    request = _make_request()
    request.state.auth = user
    downstream = Response(content=b"ok", status_code=200)
    call_next = AsyncMock(return_value=downstream)

    middleware = DataPolicyMiddleware(MagicMock(), client_id="registry-client")
    response = await middleware.dispatch(request, call_next)

    assert response is downstream
    assert request.state.data_policy_mnemonics == ["view", "edit"]
    call_next.assert_awaited_once_with(request)


@pytest.mark.asyncio
async def test_data_policy_middleware_leaves_empty_when_client_or_roles_missing():
    request = _make_request()
    call_next = AsyncMock(return_value=Response(content=b"ok"))

    middleware = DataPolicyMiddleware(MagicMock(), client_id="")
    await middleware.dispatch(request, call_next)
    assert getattr(request.state, STATE_KEY_DATA_POLICY_MNEMONICS) == []

    user = MagicMock()
    user.client_roles = None
    request.state.auth = user
    middleware = DataPolicyMiddleware(MagicMock(), client_id="registry-client")
    await middleware.dispatch(request, call_next)
    assert getattr(request.state, STATE_KEY_DATA_POLICY_MNEMONICS) == []
