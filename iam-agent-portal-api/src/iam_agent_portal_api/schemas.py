from pydantic import BaseModel


class CreateAgentBody(BaseModel):
    first_name: str
    last_name: str
    email: str


class AssignPoliciesBody(BaseModel):
    user_id: str
    policy_mnemonics: list[str]


class AgentUserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    agency_id: str | None = None
    is_agency_admin: bool
    enabled: str
    sync_status: str
    keycloak_user_id: str | None = None


class AgentUserListResponse(BaseModel):
    agency_id: str
    users: list[AgentUserResponse]


class CreateAgentResponse(BaseModel):
    id: str
    agency_id: str
    sync_status: str


class AssignPoliciesResponse(BaseModel):
    user_id: str
    policy_mnemonics: list[str]
