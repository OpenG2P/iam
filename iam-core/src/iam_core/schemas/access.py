from pydantic import BaseModel, Field


class ClientRoles(BaseModel):
    client_id: str
    role_mnemonics: list[str] = Field(default_factory=list)


class RoleLookup(BaseModel):
    clients: list[ClientRoles] = Field(default_factory=list)


class PermissionsLookupResponse(BaseModel):
    permissions: list[str] = Field(default_factory=list)
