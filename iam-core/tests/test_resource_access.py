import pytest
from openg2p_fastapi_common.errors.http_exceptions import ForbiddenError
from unittest.mock import MagicMock

from iam_core.user_auth.helpers.resource_access_helper import (
    check_resource_access,
    enforce_resource_access,
)


def test_enforce_resource_access_with_client_id_passes():
    auth = {
        "client_roles": {
            "account": ["view-profile", "edit-profile"],
            "other": ["manage-users"],
        }
    }

    result = enforce_resource_access(
        auth=auth,
        allowed_roles={"view-profile"},
        client_id="account",
    )

    assert result is auth


def test_enforce_resource_access_with_client_id_forbidden():
    auth = {"client_roles": {"account": ["edit-profile"]}}

    with pytest.raises(ForbiddenError):
        enforce_resource_access(
            auth=auth,
            allowed_roles={"view-profile"},
            client_id="account",
        )


@pytest.mark.asyncio
async def test_check_resource_access_without_client_id_checks_all_clients():
    auth = {
        "client_roles": {
            "account": ["view-profile"],
            "admin-client": ["manage-users"],
        }
    }
    request = MagicMock()
    request.state.auth = auth

    result = check_resource_access(request, allowed_roles={"manage-users"}, client_id=None)
    assert result is auth


@pytest.mark.asyncio
async def test_check_resource_access_without_client_id_forbidden_when_no_match():
    auth = {
        "client_roles": {
            "account": ["view-profile"],
            "admin-client": ["view-audit"],
        }
    }
    request = MagicMock()
    request.state.auth = auth

    with pytest.raises(ForbiddenError):
        check_resource_access(request, allowed_roles={"manage-users"}, client_id=None)
