from typing import List, Optional
from pydantic import BaseModel


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


class PermissionsResponse(BaseModel):
    permissions: List[str]
