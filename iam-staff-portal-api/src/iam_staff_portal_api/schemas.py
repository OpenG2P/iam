from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from iam_core.schemas import TokenEndpointAuthMethod
from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
    G2PResponse,
    G2PResponseBody,
)


class StaffPortalApplicationResponse(BaseModel):
    id: int
    application_mnemonic: str
    application_description: Optional[str] = None
    application_url: Optional[str] = None
    icon_base64: Optional[str] = None
    width: Optional[int] = None
    order: Optional[int] = None
    disabled: bool


class RegisterApplicationPermission(BaseModel):
    permission_mnemonic: str
    permission_description: Optional[str] = None
    active: bool = True


class RegisterApplicationRole(BaseModel):
    role_mnemonic: str
    role_description: Optional[str] = None
    active: bool = True
    # Permission mnemonics granted to this role. Must reference permissions
    # listed in the request's ``permissions`` array.
    permissions: List[str] = []


class RegisterStaffPortalApplicationRequest(BaseModel):
    """Payload an application (e.g. a registry) sends to register/update itself
    in the staff portal. Upserted by ``application_mnemonic``, which must equal
    the application's Keycloak client_id so role-gating resolves correctly.

    The optional ``permissions`` and ``roles`` carry the application's full
    access catalog; they are upserted under this application's id and the
    role->permission mappings are rebuilt to match the payload. Multiple
    instances of the same product each push their own (identical) catalog under
    their own mnemonic/client_id."""

    application_mnemonic: str
    application_url: str
    application_description: Optional[str] = None
    icon_base64: Optional[str] = None
    width: Optional[int] = None
    order: Optional[int] = None
    active: bool = True
    permissions: List[RegisterApplicationPermission] = []
    roles: List[RegisterApplicationRole] = []


class RegisterStaffPortalApplicationResponse(BaseModel):
    id: int
    application_mnemonic: str
    created: bool
    permissions_count: int = 0
    roles_count: int = 0


class ApplicationPermissionResponse(BaseModel):
    application_id: int
    application_mnemonic: str
    permissions: List[str]


class GetPermissionsForRolesRequest(BaseModel):
    role_mnemonics: List[str]


class PermissionsForRolesResponse(BaseModel):
    """Plain JSON for ResolvePermissionMiddleware (not G2P envelope)."""
    permissions: List[str]


# ---------------------------------------------------------------------------
# Staff portal domain payloads
# ---------------------------------------------------------------------------


class ApplicationData(BaseModel):
    id: int
    application_mnemonic: str
    application_description: Optional[str] = None
    application_url: Optional[str] = None
    icon_base64: Optional[str] = None
    width: Optional[int] = None
    order: Optional[int] = None
    is_self_registered: bool = False
    active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ApplicationCreatePayload(BaseModel):
    application_mnemonic: str
    application_description: Optional[str] = None
    application_url: Optional[str] = None
    icon_base64: Optional[str] = None
    order: Optional[int] = None
    width: Optional[int] = None


class ApplicationUpdatePayload(BaseModel):
    id: int
    application_description: Optional[str] = None
    application_url: Optional[str] = None
    icon_base64: Optional[str] = None
    order: Optional[int] = None
    width: Optional[int] = None


class ApplicationDeletePayload(BaseModel):
    id: int


class ApplicationIdPayload(BaseModel):
    id: int


class ApplicationScopedPayload(BaseModel):
    application_id: int


class RoleData(BaseModel):
    id: int
    role_mnemonic: str
    role_description: Optional[str] = None
    application_id: int
    active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RoleCreatePayload(BaseModel):
    application_id: int
    role_mnemonic: str
    role_description: Optional[str] = None


class RoleDeletePayload(BaseModel):
    application_id: int
    id: int


class PermissionData(BaseModel):
    id: int
    permission_mnemonic: str
    permission_description: Optional[str] = None
    application_id: int
    active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PermissionCreatePayload(BaseModel):
    application_id: int
    permission_mnemonic: str
    permission_description: Optional[str] = None


class PermissionDeletePayload(BaseModel):
    application_id: int
    id: int


class RolePermissionData(BaseModel):
    id: int
    role_id: int
    permission_id: int
    role_mnemonic: Optional[str] = None
    permission_mnemonic: Optional[str] = None
    active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RolePermissionListPayload(BaseModel):
    application_id: int
    role_id: Optional[int] = None
    permission_id: Optional[int] = None


class RolePermissionCreatePayload(BaseModel):
    application_id: int
    role_id: int
    permission_id: int


class RolePermissionDeletePayload(BaseModel):
    application_id: int
    id: int


class DataPolicyData(BaseModel):
    id: int
    data_policy_mnemonic: str
    role_description: Optional[str] = None
    application_id: int
    active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DataPolicyCreatePayload(BaseModel):
    application_id: int
    data_policy_mnemonic: str
    role_description: Optional[str] = None


class DataPolicyDeletePayload(BaseModel):
    application_id: int
    id: int


class LoginProviderData(BaseModel):
    id: int
    provider_name: str
    description: Optional[str] = None
    icon_base64: Optional[str] = None
    client_id: str
    has_client_secret: bool = False
    has_client_private_key: bool = False
    token_endpoint_auth_method: TokenEndpointAuthMethod
    issuer: str
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    server_metadata_url: Optional[str] = None
    jwks_uri: Optional[str] = None
    adapter_name: Optional[str] = None
    scope: Optional[str] = None
    enable_pkce: Optional[bool] = None
    extra_authorize_params: Optional[str] = None
    jwt_assertion_aud: Optional[str] = None
    audiences: Optional[str] = None
    oauth_callback_url: str
    default_redirect_uri: Optional[str] = None
    keymanager_app_id: Optional[str] = None
    keymanager_ref_id: Optional[str] = None
    active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LoginProviderCreatePayload(BaseModel):
    provider_name: str
    description: Optional[str] = None
    icon_base64: Optional[str] = None
    client_id: str
    client_secret: Optional[str] = None
    client_private_key: Optional[str] = None
    token_endpoint_auth_method: TokenEndpointAuthMethod
    issuer: str
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    server_metadata_url: Optional[str] = None
    jwks_uri: Optional[str] = None
    adapter_name: Optional[str] = None
    scope: Optional[str] = None
    enable_pkce: Optional[bool] = None
    extra_authorize_params: Optional[str] = None
    jwt_assertion_aud: Optional[str] = None
    audiences: Optional[str] = None
    oauth_callback_url: str
    default_redirect_uri: Optional[str] = None


class LoginProviderUpdatePayload(BaseModel):
    id: int
    provider_name: Optional[str] = None
    description: Optional[str] = None
    icon_base64: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = Field(default=None)
    client_private_key: Optional[str] = Field(default=None)
    token_endpoint_auth_method: Optional[TokenEndpointAuthMethod] = None
    issuer: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    server_metadata_url: Optional[str] = None
    jwks_uri: Optional[str] = None
    adapter_name: Optional[str] = None
    scope: Optional[str] = None
    enable_pkce: Optional[bool] = None
    extra_authorize_params: Optional[str] = None
    jwt_assertion_aud: Optional[str] = None
    audiences: Optional[str] = None
    oauth_callback_url: Optional[str] = None
    default_redirect_uri: Optional[str] = None


class LoginProviderDeletePayload(BaseModel):
    id: int


class LoginProviderIdPayload(BaseModel):
    id: int


class OkPayload(BaseModel):
    ok: bool = True


class EmptyRequestPayload(BaseModel):
    pass


# ---------------------------------------------------------------------------
# Typed G2P request / response wrappers (registry-style)
# ---------------------------------------------------------------------------


class ApplicationsResponseBody(G2PResponseBody):
    response_payload: Optional[List[ApplicationData]] = None


class ApplicationsResponse(G2PResponse):
    response_body: Optional[ApplicationsResponseBody] = None


class ApplicationResponseBody(G2PResponseBody):
    response_payload: Optional[ApplicationData] = None


class ApplicationResponse(G2PResponse):
    response_body: Optional[ApplicationResponseBody] = None


class GetApplicationsRequestBody(G2PRequestBody):
    request_payload: Optional[EmptyRequestPayload] = None


class GetApplicationsRequest(G2PRequest):
    request_body: GetApplicationsRequestBody


class GetApplicationRequestBody(G2PRequestBody):
    request_payload: ApplicationIdPayload


class GetApplicationRequest(G2PRequest):
    request_body: GetApplicationRequestBody


class CreateApplicationRequestBody(G2PRequestBody):
    request_payload: ApplicationCreatePayload


class CreateApplicationRequest(G2PRequest):
    request_body: CreateApplicationRequestBody


class UpdateApplicationRequestBody(G2PRequestBody):
    request_payload: ApplicationUpdatePayload


class UpdateApplicationRequest(G2PRequest):
    request_body: UpdateApplicationRequestBody


class DeleteApplicationRequestBody(G2PRequestBody):
    request_payload: ApplicationDeletePayload


class DeleteApplicationRequest(G2PRequest):
    request_body: DeleteApplicationRequestBody


class RolesResponseBody(G2PResponseBody):
    response_payload: Optional[List[RoleData]] = None


class RolesResponse(G2PResponse):
    response_body: Optional[RolesResponseBody] = None


class RoleResponseBody(G2PResponseBody):
    response_payload: Optional[RoleData] = None


class RoleResponse(G2PResponse):
    response_body: Optional[RoleResponseBody] = None


class PermissionsResponseBody(G2PResponseBody):
    response_payload: Optional[List[PermissionData]] = None


class PermissionsResponse(G2PResponse):
    response_body: Optional[PermissionsResponseBody] = None


class PermissionResponseBody(G2PResponseBody):
    response_payload: Optional[PermissionData] = None


class PermissionResponse(G2PResponse):
    response_body: Optional[PermissionResponseBody] = None


class RolePermissionsResponseBody(G2PResponseBody):
    response_payload: Optional[List[RolePermissionData]] = None


class RolePermissionsResponse(G2PResponse):
    response_body: Optional[RolePermissionsResponseBody] = None


class RolePermissionResponseBody(G2PResponseBody):
    response_payload: Optional[RolePermissionData] = None


class RolePermissionResponse(G2PResponse):
    response_body: Optional[RolePermissionResponseBody] = None


class DataPoliciesResponseBody(G2PResponseBody):
    response_payload: Optional[List[DataPolicyData]] = None


class DataPoliciesResponse(G2PResponse):
    response_body: Optional[DataPoliciesResponseBody] = None


class DataPolicyResponseBody(G2PResponseBody):
    response_payload: Optional[DataPolicyData] = None


class DataPolicyResponse(G2PResponse):
    response_body: Optional[DataPolicyResponseBody] = None


class LoginProvidersResponseBody(G2PResponseBody):
    response_payload: Optional[List[LoginProviderData]] = None


class LoginProvidersResponse(G2PResponse):
    response_body: Optional[LoginProvidersResponseBody] = None


class LoginProviderResponseBody(G2PResponseBody):
    response_payload: Optional[LoginProviderData] = None


class LoginProviderResponse(G2PResponse):
    response_body: Optional[LoginProviderResponseBody] = None


class OkResponseBody(G2PResponseBody):
    response_payload: Optional[OkPayload] = None


class OkResponse(G2PResponse):
    response_body: Optional[OkResponseBody] = None


class GetRolesRequestBody(G2PRequestBody):
    request_payload: ApplicationScopedPayload


class GetRolesRequest(G2PRequest):
    request_body: GetRolesRequestBody


class CreateRoleRequestBody(G2PRequestBody):
    request_payload: RoleCreatePayload


class CreateRoleRequest(G2PRequest):
    request_body: CreateRoleRequestBody


class DeleteRoleRequestBody(G2PRequestBody):
    request_payload: RoleDeletePayload


class DeleteRoleRequest(G2PRequest):
    request_body: DeleteRoleRequestBody


class GetPermissionsRequestBody(G2PRequestBody):
    request_payload: ApplicationScopedPayload


class GetPermissionsRequest(G2PRequest):
    request_body: GetPermissionsRequestBody


class CreatePermissionRequestBody(G2PRequestBody):
    request_payload: PermissionCreatePayload


class CreatePermissionRequest(G2PRequest):
    request_body: CreatePermissionRequestBody


class DeletePermissionRequestBody(G2PRequestBody):
    request_payload: PermissionDeletePayload


class DeletePermissionRequest(G2PRequest):
    request_body: DeletePermissionRequestBody


class GetRolePermissionsRequestBody(G2PRequestBody):
    request_payload: RolePermissionListPayload


class GetRolePermissionsRequest(G2PRequest):
    request_body: GetRolePermissionsRequestBody


class CreateRolePermissionRequestBody(G2PRequestBody):
    request_payload: RolePermissionCreatePayload


class CreateRolePermissionRequest(G2PRequest):
    request_body: CreateRolePermissionRequestBody


class DeleteRolePermissionRequestBody(G2PRequestBody):
    request_payload: RolePermissionDeletePayload


class DeleteRolePermissionRequest(G2PRequest):
    request_body: DeleteRolePermissionRequestBody


class GetDataPoliciesRequestBody(G2PRequestBody):
    request_payload: ApplicationScopedPayload


class GetDataPoliciesRequest(G2PRequest):
    request_body: GetDataPoliciesRequestBody


class CreateDataPolicyRequestBody(G2PRequestBody):
    request_payload: DataPolicyCreatePayload


class CreateDataPolicyRequest(G2PRequest):
    request_body: CreateDataPolicyRequestBody


class DeleteDataPolicyRequestBody(G2PRequestBody):
    request_payload: DataPolicyDeletePayload


class DeleteDataPolicyRequest(G2PRequest):
    request_body: DeleteDataPolicyRequestBody


class GetLoginProvidersRequestBody(G2PRequestBody):
    request_payload: Optional[EmptyRequestPayload] = None


class GetLoginProvidersRequest(G2PRequest):
    request_body: GetLoginProvidersRequestBody


class GetLoginProviderRequestBody(G2PRequestBody):
    request_payload: LoginProviderIdPayload


class GetLoginProviderRequest(G2PRequest):
    request_body: GetLoginProviderRequestBody


class CreateLoginProviderRequestBody(G2PRequestBody):
    request_payload: LoginProviderCreatePayload


class CreateLoginProviderRequest(G2PRequest):
    request_body: CreateLoginProviderRequestBody


class UpdateLoginProviderRequestBody(G2PRequestBody):
    request_payload: LoginProviderUpdatePayload


class UpdateLoginProviderRequest(G2PRequest):
    request_body: UpdateLoginProviderRequestBody


class DeleteLoginProviderRequestBody(G2PRequestBody):
    request_payload: LoginProviderDeletePayload


class DeleteLoginProviderRequest(G2PRequest):
    request_body: DeleteLoginProviderRequestBody
