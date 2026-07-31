from __future__ import annotations

import logging

from openg2p_fastapi_common.controller import BaseController

from iam_core.user_auth.decorators import require_permissions

from ..config import Settings
from ..helpers.request_response_helper import RequestResponseHelper
from ..schemas import (
    CreateDataPolicyRequest,
    CreatePermissionRequest,
    CreateRolePermissionRequest,
    CreateRoleRequest,
    DataPoliciesResponse,
    DataPoliciesResponseBody,
    DataPolicyResponse,
    DataPolicyResponseBody,
    DeleteDataPolicyRequest,
    DeletePermissionRequest,
    DeleteRolePermissionRequest,
    DeleteRoleRequest,
    GetDataPoliciesRequest,
    GetPermissionsRequest,
    GetRolePermissionsRequest,
    GetRolesRequest,
    PermissionResponse,
    PermissionResponseBody,
    PermissionsResponse,
    PermissionsResponseBody,
    RolePermissionResponse,
    RolePermissionResponseBody,
    RolePermissionsResponse,
    RolePermissionsResponseBody,
    RoleResponse,
    RoleResponseBody,
    RolesResponse,
    RolesResponseBody,
)
from ..services.application_access_service import ApplicationAccessService

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


class ApplicationAccessController(BaseController):
    """Roles, permissions, mappings, and data policies under /applications."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router.tags += ["/applications"]
        self.router.prefix = "/applications"
        self.helper = RequestResponseHelper.get_component()
        self.application_access_service = ApplicationAccessService.get_component()

        self.router.add_api_route(
            "/get_roles",
            self.get_roles,
            responses={200: {"model": RolesResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/create_role",
            self.create_role,
            responses={200: {"model": RoleResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/delete_role",
            self.delete_role,
            responses={200: {"model": RoleResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_permissions",
            self.get_permissions,
            responses={200: {"model": PermissionsResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/create_permission",
            self.create_permission,
            responses={200: {"model": PermissionResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/delete_permission",
            self.delete_permission,
            responses={200: {"model": PermissionResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_role_permissions",
            self.get_role_permissions,
            responses={200: {"model": RolePermissionsResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/create_role_permission",
            self.create_role_permission,
            responses={200: {"model": RolePermissionResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/delete_role_permission",
            self.delete_role_permission,
            responses={200: {"model": RolePermissionResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_data_policies",
            self.get_data_policies,
            responses={200: {"model": DataPoliciesResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/create_data_policy",
            self.create_data_policy,
            responses={200: {"model": DataPolicyResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/delete_data_policy",
            self.delete_data_policy,
            responses={200: {"model": DataPolicyResponse}},
            methods=["POST"],
        )

    @require_permissions({"role:view"})
    async def get_roles(self, get_request: GetRolesRequest) -> RolesResponse:
        try:
            page, page_size = self.helper.pagination_from_request(
                get_request, default_page_size=_config.default_page_size
            )
            roles, total = await self.application_access_service.get_roles(
                get_request.request_body.request_payload, page, page_size
            )
            return self.helper.construct_payload_response(
                get_request,
                roles,
                RolesResponseBody,
                RolesResponse,
                total=total,
                page_size=page_size,
            )
        except Exception as error_exception:
            _logger.exception("get_roles failed")
            return self.helper.construct_error_response(error_exception, get_request)

    @require_permissions({"role:create"})
    async def create_role(self, create_request: CreateRoleRequest) -> RoleResponse:
        try:
            role = await self.application_access_service.create_role(
                create_request.request_body.request_payload
            )
            return self.helper.construct_payload_response(
                create_request,
                role,
                RoleResponseBody,
                RoleResponse,
            )
        except Exception as error_exception:
            _logger.exception("create_role failed")
            return self.helper.construct_error_response(error_exception, create_request)

    @require_permissions({"role:delete"})
    async def delete_role(self, delete_request: DeleteRoleRequest) -> RoleResponse:
        try:
            role = await self.application_access_service.delete_role(
                delete_request.request_body.request_payload
            )
            return self.helper.construct_payload_response(
                delete_request,
                role,
                RoleResponseBody,
                RoleResponse,
            )
        except Exception as error_exception:
            _logger.exception("delete_role failed")
            return self.helper.construct_error_response(error_exception, delete_request)

    @require_permissions({"permission:view"})
    async def get_permissions(self, get_request: GetPermissionsRequest) -> PermissionsResponse:
        try:
            page, page_size = self.helper.pagination_from_request(
                get_request, default_page_size=_config.default_page_size
            )
            permissions, total = await self.application_access_service.get_permissions(
                get_request.request_body.request_payload, page, page_size
            )
            return self.helper.construct_payload_response(
                get_request,
                permissions,
                PermissionsResponseBody,
                PermissionsResponse,
                total=total,
                page_size=page_size,
            )
        except Exception as error_exception:
            _logger.exception("get_permissions failed")
            return self.helper.construct_error_response(error_exception, get_request)

    @require_permissions({"permission:create"})
    async def create_permission(self, create_request: CreatePermissionRequest) -> PermissionResponse:
        try:
            permission = await self.application_access_service.create_permission(
                create_request.request_body.request_payload
            )
            return self.helper.construct_payload_response(
                create_request,
                permission,
                PermissionResponseBody,
                PermissionResponse,
            )
        except Exception as error_exception:
            _logger.exception("create_permission failed")
            return self.helper.construct_error_response(error_exception, create_request)

    @require_permissions({"permission:delete"})
    async def delete_permission(self, delete_request: DeletePermissionRequest) -> PermissionResponse:
        try:
            permission = await self.application_access_service.delete_permission(
                delete_request.request_body.request_payload
            )
            return self.helper.construct_payload_response(
                delete_request,
                permission,
                PermissionResponseBody,
                PermissionResponse,
            )
        except Exception as error_exception:
            _logger.exception("delete_permission failed")
            return self.helper.construct_error_response(error_exception, delete_request)

    @require_permissions({"rolePermission:view"})
    async def get_role_permissions(self, get_request: GetRolePermissionsRequest) -> RolePermissionsResponse:
        try:
            page, page_size = self.helper.pagination_from_request(
                get_request, default_page_size=_config.default_page_size
            )
            mappings, total = await self.application_access_service.get_role_permissions(
                get_request.request_body.request_payload, page, page_size
            )
            return self.helper.construct_payload_response(
                get_request,
                mappings,
                RolePermissionsResponseBody,
                RolePermissionsResponse,
                total=total,
                page_size=page_size,
            )
        except Exception as error_exception:
            _logger.exception("get_role_permissions failed")
            return self.helper.construct_error_response(error_exception, get_request)

    @require_permissions({"rolePermission:create"})
    async def create_role_permission(
        self, create_request: CreateRolePermissionRequest
    ) -> RolePermissionResponse:
        try:
            mapping = await self.application_access_service.create_role_permission(
                create_request.request_body.request_payload
            )
            return self.helper.construct_payload_response(
                create_request,
                mapping,
                RolePermissionResponseBody,
                RolePermissionResponse,
            )
        except Exception as error_exception:
            _logger.exception("create_role_permission failed")
            return self.helper.construct_error_response(error_exception, create_request)

    @require_permissions({"rolePermission:delete"})
    async def delete_role_permission(
        self, delete_request: DeleteRolePermissionRequest
    ) -> RolePermissionResponse:
        try:
            role_permission = await self.application_access_service.delete_role_permission(
                delete_request.request_body.request_payload
            )
            return self.helper.construct_payload_response(
                delete_request,
                role_permission,
                RolePermissionResponseBody,
                RolePermissionResponse,
            )
        except Exception as error_exception:
            _logger.exception("delete_role_permission failed")
            return self.helper.construct_error_response(error_exception, delete_request)

    @require_permissions({"dataPolicy:view"})
    async def get_data_policies(self, get_request: GetDataPoliciesRequest) -> DataPoliciesResponse:
        try:
            page, page_size = self.helper.pagination_from_request(
                get_request, default_page_size=_config.default_page_size
            )
            data_policies, total = await self.application_access_service.get_data_policies(
                get_request.request_body.request_payload, page, page_size
            )
            return self.helper.construct_payload_response(
                get_request,
                data_policies,
                DataPoliciesResponseBody,
                DataPoliciesResponse,
                total=total,
                page_size=page_size,
            )
        except Exception as error_exception:
            _logger.exception("get_data_policies failed")
            return self.helper.construct_error_response(error_exception, get_request)

    @require_permissions({"dataPolicy:create"})
    async def create_data_policy(self, create_request: CreateDataPolicyRequest) -> DataPolicyResponse:
        try:
            data_policy = await self.application_access_service.create_data_policy(
                create_request.request_body.request_payload
            )
            return self.helper.construct_payload_response(
                create_request,
                data_policy,
                DataPolicyResponseBody,
                DataPolicyResponse,
            )
        except Exception as error_exception:
            _logger.exception("create_data_policy failed")
            return self.helper.construct_error_response(error_exception, create_request)

    @require_permissions({"dataPolicy:delete"})
    async def delete_data_policy(self, delete_request: DeleteDataPolicyRequest) -> DataPolicyResponse:
        try:
            data_policy = await self.application_access_service.delete_data_policy(
                delete_request.request_body.request_payload
            )
            return self.helper.construct_payload_response(
                delete_request,
                data_policy,
                DataPolicyResponseBody,
                DataPolicyResponse,
            )
        except Exception as error_exception:
            _logger.exception("delete_data_policy failed")
            return self.helper.construct_error_response(error_exception, delete_request)
