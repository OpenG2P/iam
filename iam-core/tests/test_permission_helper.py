from iam_core.user_auth.dependencies import enforce_resource_access
from iam_core.user_auth.helpers.permission_helper import (
    get_required_permissions,
    require_permissions,
)


class _StubStaffPortalController:
    """Mirrors staff-portal controller permission metadata without external deps."""

    @require_permissions({"intakeFormDefinition:view"})
    def get_intake_form(self):
        return None

    @require_permissions({"registryConfiguration:view", "changeRequest:view"})
    def get_number_of_requests_pending(self):
        return None


def test_require_permissions_accepts_varargs():
    @require_permissions("one", "two")
    def endpoint():
        return None

    assert get_required_permissions(endpoint) == {"one", "two"}


def test_require_permissions_accepts_set_and_normalizes_values():
    @require_permissions({" one ", "", "two"})
    def endpoint():
        return None

    assert get_required_permissions(endpoint) == {"one", "two"}


def test_enforce_resource_access_uses_or_semantics_for_multiple_permissions():
    auth = {"client_roles": {"staff-portal": ["changeRequest:view"]}}

    result = enforce_resource_access(
        auth=auth,
        allowed_roles={"registryConfiguration:view", "changeRequest:view"},
        client_id="staff-portal",
    )

    assert result is auth


def test_staff_portal_single_permission_metadata_is_set():
    controller = _StubStaffPortalController()
    assert get_required_permissions(controller.get_intake_form) == {
        "intakeFormDefinition:view",
    }


def test_staff_portal_multi_permission_metadata_is_set():
    controller = _StubStaffPortalController()
    assert get_required_permissions(controller.get_number_of_requests_pending) == {
        "registryConfiguration:view",
        "changeRequest:view",
    }
