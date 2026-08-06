from iam_staff_portal_api.schemas import (
    ApplicationPermissionResponse,
    GetPermissionsForRolesRequest,
    PermissionsForRolesResponse,
    RegisterApplicationPermission,
    RegisterApplicationRole,
    RegisterStaffPortalApplicationRequest,
    RegisterStaffPortalApplicationResponse,
    StaffPortalApplicationResponse,
)


def test_staff_portal_application_response_defaults():
    response = StaffPortalApplicationResponse(
        id=1,
        application_mnemonic="registry",
        disabled=False,
    )
    assert response.application_description is None
    assert response.application_url is None
    assert response.disabled is False


def test_register_request_accepts_catalog():
    request = RegisterStaffPortalApplicationRequest(
        application_mnemonic="registry-staff-portal",
        application_url="https://registry.example.com",
        permissions=[
            RegisterApplicationPermission(permission_mnemonic="register:view"),
        ],
        roles=[
            RegisterApplicationRole(
                role_mnemonic="Data Editor",
                permissions=["register:view"],
            )
        ],
    )
    assert request.active is True
    assert len(request.permissions) == 1
    assert request.roles[0].permissions == ["register:view"]


def test_register_response_and_permission_models():
    response = RegisterStaffPortalApplicationResponse(
        id=7,
        application_mnemonic="registry-staff-portal",
        created=True,
        permissions_count=2,
        roles_count=1,
    )
    assert response.permissions_count == 2

    perm_response = ApplicationPermissionResponse(
        application_id=1,
        application_mnemonic="registry-staff-portal",
        permissions=["register:view", "register:edit"],
    )
    assert len(perm_response.permissions) == 2

    roles_request = GetPermissionsForRolesRequest(role_mnemonics=["Data Editor", "Admin"])
    permissions_response = PermissionsForRolesResponse(permissions=["register:view"])
    assert roles_request.role_mnemonics == ["Data Editor", "Admin"]
    assert permissions_response.permissions == ["register:view"]
