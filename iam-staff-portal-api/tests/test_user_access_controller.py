from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openg2p_fastapi_common.errors.http_exceptions import BadRequestError

from helpers import (
    make_app_row,
    make_auth,
    make_execute_result,
    make_mock_session,
    make_permission_row,
    make_request,
    make_role_row,
    make_session_factory,
)
from iam_staff_portal_api.controllers.user_access_controller import UserAccessController
from iam_staff_portal_api.schemas import (
    GetPermissionsForRolesRequest,
    RegisterApplicationPermission,
    RegisterApplicationRole,
    RegisterStaffPortalApplicationRequest,
)


@pytest.fixture
def controller():
    return UserAccessController()


@pytest.mark.asyncio
async def test_get_staff_portal_applications_marks_disabled_without_role(controller):
    apps = [
        make_app_row(application_mnemonic="registry-staff-portal"),
        make_app_row(id=2, application_mnemonic="other-app"),
    ]
    session, _ = make_mock_session(make_execute_result(all_rows=apps))
    request = make_request(auth=make_auth(client_roles={"registry-staff-portal": ["Data Editor"]}))

    with patch(
        "iam_staff_portal_api.controllers.user_access_controller.async_sessionmaker",
        return_value=make_session_factory(session),
    ):
        result = await controller.get_staff_portal_applications(request)

    assert len(result) == 2
    enabled = next(item for item in result if item["application_mnemonic"] == "registry-staff-portal")
    disabled = next(item for item in result if item["application_mnemonic"] == "other-app")
    assert enabled["disabled"] is False
    assert enabled["application_url"] == "https://registry.example.com"
    assert disabled["disabled"] is True
    assert disabled["application_url"] is None


@pytest.mark.asyncio
async def test_get_application_permissions_for_user_returns_empty_for_unknown_mnemonic(controller):
    request = make_request(auth=make_auth(client_roles={"other-app": ["Admin"]}))

    result = await controller.get_application_permissions_for_user(
        request,
        application_mnemonic="registry-staff-portal",
    )

    assert result == []


@pytest.mark.asyncio
async def test_get_application_permissions_for_user_skips_when_role_mappings_missing(controller):
    app = make_app_row()
    role = make_role_row()
    session, _ = make_mock_session(
        make_execute_result(first_row=app),
        make_execute_result(all_rows=[role]),
        make_execute_result(all_rows=[]),
    )
    request = make_request(auth=make_auth(client_roles={"registry-staff-portal": ["Data Editor"]}))

    with patch(
        "iam_staff_portal_api.controllers.user_access_controller.async_sessionmaker",
        return_value=make_session_factory(session),
    ):
        result = await controller.get_application_permissions_for_user(request)

    assert result == []


@pytest.mark.asyncio
async def test_get_application_permissions_for_user_returns_empty_without_roles(controller):
    request = make_request(auth=make_auth(client_roles={}))
    result = await controller.get_application_permissions_for_user(request)
    assert result == []


@pytest.mark.asyncio
async def test_get_application_permissions_for_user_skips_unknown_and_empty_results(controller):
    app = make_app_row()
    session, _ = make_mock_session(
        make_execute_result(first_row=app),
        make_execute_result(all_rows=[]),
        make_execute_result(first_row=None),
        make_execute_result(all_rows=[make_role_row()]),
        make_execute_result(all_rows=[]),
        make_execute_result(first_row=make_app_row(application_mnemonic="other")),
        make_execute_result(all_rows=[make_role_row()]),
        make_execute_result(all_rows=[10]),
        make_execute_result(all_rows=[]),
    )
    request = make_request(
        auth=make_auth(
            client_roles={
                "registry-staff-portal": ["Data Editor"],
                "missing-app": ["Admin"],
                "other": ["Data Editor"],
            }
        )
    )

    with patch(
        "iam_staff_portal_api.controllers.user_access_controller.async_sessionmaker",
        return_value=make_session_factory(session),
    ):
        result = await controller.get_application_permissions_for_user(request)

    assert result == []


@pytest.mark.asyncio
async def test_get_application_permissions_for_user_returns_permissions_for_all_apps(controller):
    app = make_app_row()
    role = make_role_row()
    permission = make_permission_row()
    session, _ = make_mock_session(
        make_execute_result(first_row=app),
        make_execute_result(all_rows=[role]),
        make_execute_result(all_rows=[permission.id]),
        make_execute_result(all_rows=[permission]),
    )
    request = make_request(auth=make_auth(client_roles={"registry-staff-portal": ["Data Editor"]}))

    with patch(
        "iam_staff_portal_api.controllers.user_access_controller.async_sessionmaker",
        return_value=make_session_factory(session),
    ):
        result = await controller.get_application_permissions_for_user(request)

    assert len(result) == 1
    assert result[0]["permissions"] == ["register:view"]


@pytest.mark.asyncio
async def test_get_permission_mnemonics_for_role_returns_empty_without_mappings(controller):
    role = make_role_row()
    session, _ = make_mock_session(
        make_execute_result(first_row=role),
        make_execute_result(all_rows=[]),
    )
    with patch(
        "iam_staff_portal_api.controllers.user_access_controller.async_sessionmaker",
        return_value=make_session_factory(session),
    ):
        result = await controller.get_permission_mnemonics_for_role.__wrapped__(
            controller,
            "Data Editor",
        )
    assert result == []


@pytest.mark.asyncio
async def test_get_application_permissions_for_user_filters_by_mnemonic(controller):
    app = make_app_row()
    role = make_role_row()
    permission = make_permission_row()
    session, _ = make_mock_session(
        make_execute_result(first_row=app),
        make_execute_result(all_rows=[role]),
        make_execute_result(all_rows=[permission.id]),
        make_execute_result(all_rows=[permission]),
    )
    request = make_request(
        auth=make_auth(client_roles={"registry-staff-portal": ["Data Editor"], "other": ["Admin"]})
    )

    with patch(
        "iam_staff_portal_api.controllers.user_access_controller.async_sessionmaker",
        return_value=make_session_factory(session),
    ):
        result = await controller.get_application_permissions_for_user(
            request,
            application_mnemonic="registry-staff-portal",
        )

    assert len(result) == 1
    assert result[0]["application_mnemonic"] == "registry-staff-portal"
    assert result[0]["permissions"] == ["register:view"]


@pytest.mark.asyncio
async def test_get_permissions_for_roles_aggregates_unique_permissions(controller):
    with patch.object(
        controller,
        "get_permission_mnemonics_for_role",
        AsyncMock(side_effect=[["register:view"], ["register:view", "register:edit"]]),
    ):
        response = await controller.get_permissions_for_roles(
            GetPermissionsForRolesRequest(role_mnemonics=["Data Editor", "Admin"])
        )
    assert response.permissions == ["register:edit", "register:view"]


@pytest.mark.asyncio
async def test_get_permission_mnemonics_for_role_returns_empty_when_role_missing(controller):
    session, _ = make_mock_session(make_execute_result(first_row=None))
    with patch(
        "iam_staff_portal_api.controllers.user_access_controller.async_sessionmaker",
        return_value=make_session_factory(session),
    ):
        result = await controller.get_permission_mnemonics_for_role.__wrapped__(
            controller,
            "Missing Role",
        )
    assert result == []


@pytest.mark.asyncio
async def test_get_permission_mnemonics_for_role_resolves_active_permissions(controller):
    role = make_role_row()
    session, _ = make_mock_session(
        make_execute_result(first_row=role),
        make_execute_result(all_rows=[10, 11]),
        make_execute_result(all_rows=["register:view", "register:edit"]),
    )
    with patch(
        "iam_staff_portal_api.controllers.user_access_controller.async_sessionmaker",
        return_value=make_session_factory(session),
    ):
        result = await controller.get_permission_mnemonics_for_role.__wrapped__(
            controller,
            "Data Editor",
        )
    assert result == ["register:view", "register:edit"]


@pytest.mark.asyncio
async def test_register_staff_portal_application_creates_new_application(controller):
    payload = RegisterStaffPortalApplicationRequest(
        application_mnemonic="registry-staff-portal",
        application_url="https://registry.example.com",
        api_url="https://staff-registry.example.com",
        permissions=[RegisterApplicationPermission(permission_mnemonic="register:view")],
        roles=[
            RegisterApplicationRole(
                role_mnemonic="Data Editor",
                permissions=["register:view"],
            )
        ],
    )
    session, _ = make_mock_session(
        make_execute_result(first_row=None),
        make_execute_result(all_rows=[]),
        make_execute_result(all_rows=[]),
    )
    session.refresh = AsyncMock(side_effect=lambda app: setattr(app, "id", 99))

    with (
        patch(
            "iam_staff_portal_api.controllers.user_access_controller.async_sessionmaker",
            return_value=make_session_factory(session),
        ),
        patch(
            "iam_staff_portal_api.controllers.user_access_controller.DataLoader.sync_staff_access_id_sequences",
            AsyncMock(),
        ),
    ):
        response = await controller.register_staff_portal_application(make_request(), payload)

    assert response.id == 99
    assert response.created is True
    assert response.permissions_count == 1
    assert response.roles_count == 1
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_staff_portal_application_updates_existing_application(controller):
    existing = make_app_row(is_self_registered=False)
    payload = RegisterStaffPortalApplicationRequest(
        application_mnemonic="registry-staff-portal",
        application_url="https://registry.example.com",
        application_description="Updated",
    )
    session, _ = make_mock_session(
        make_execute_result(first_row=existing),
        make_execute_result(all_rows=[]),
        make_execute_result(all_rows=[]),
    )
    session.refresh = AsyncMock()

    with (
        patch(
            "iam_staff_portal_api.controllers.user_access_controller.async_sessionmaker",
            return_value=make_session_factory(session),
        ),
        patch(
            "iam_staff_portal_api.controllers.user_access_controller.DataLoader.sync_staff_access_id_sequences",
            AsyncMock(),
        ),
    ):
        response = await controller.register_staff_portal_application(make_request(), payload)

    assert response.created is False
    assert existing.application_description == "Updated"
    assert existing.api_url is None
    assert existing.is_self_registered is True


@pytest.mark.asyncio
async def test_rebuild_role_permissions_rejects_unknown_permission(controller):
    role = make_role_row(id=20)
    perm = make_permission_row(id=10)
    roles_by_mnemonic = {"Data Editor": role}
    perms_by_mnemonic = {"register:view": perm}
    session = AsyncMock()

    with pytest.raises(BadRequestError, match="unknown permission"):
        await controller._rebuild_role_permissions(
            session,
            [RegisterApplicationRole(role_mnemonic="Data Editor", permissions=["missing:perm"])],
            roles_by_mnemonic,
            perms_by_mnemonic,
        )


@pytest.mark.asyncio
async def test_rebuild_role_permissions_replaces_mappings(controller):
    role = make_role_row(id=20)
    perm = make_permission_row(id=10)
    roles_by_mnemonic = {"Data Editor": role}
    perms_by_mnemonic = {"register:view": perm}
    session = MagicMock()
    session.execute = AsyncMock()

    await controller._rebuild_role_permissions(
        session,
        [RegisterApplicationRole(role_mnemonic="Data Editor", permissions=["register:view"])],
        roles_by_mnemonic,
        perms_by_mnemonic,
    )

    session.execute.assert_awaited_once()
    session.add.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_permissions_creates_and_updates_rows(controller):
    existing_perm = make_permission_row(permission_mnemonic="register:view")
    session, _ = make_mock_session(make_execute_result(all_rows=[existing_perm]))

    result = await controller._upsert_permissions(
        session,
        application_id=1,
        permissions=[
            RegisterApplicationPermission(
                permission_mnemonic="register:view",
                permission_description="Updated",
            ),
            RegisterApplicationPermission(permission_mnemonic="register:edit"),
        ],
    )

    assert existing_perm.permission_description == "Updated"
    assert "register:edit" in result
    assert session.add.call_count == 1


@pytest.mark.asyncio
async def test_upsert_roles_creates_and_updates_rows(controller):
    existing_role = make_role_row(role_mnemonic="Data Editor")
    session, _ = make_mock_session(make_execute_result(all_rows=[existing_role]))

    result = await controller._upsert_roles(
        session,
        application_id=1,
        roles=[
            RegisterApplicationRole(role_mnemonic="Data Editor", role_description="Updated"),
            RegisterApplicationRole(role_mnemonic="Admin"),
        ],
    )

    assert existing_role.role_description == "Updated"
    assert "Admin" in result
    assert session.add.call_count == 1
