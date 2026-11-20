"""Agency admin creates and lists the agents in the agency from their token group."""

from fastapi import Request
from jose import jwt
from openg2p_fastapi_common.context import get_async_session_maker
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import ForbiddenError

from iam_core.models.enum import ApplicationType
from iam_core.services.user_service import UserService
from iam_core.user_auth.decorators import requires_auth
from iam_core.user_auth.helpers.claims_helper import AGENCY_ID_STATE_KEY

from ..schemas import AgentUserListResponse, AgentUserResponse, CreateAgentBody, CreateAgentResponse


def _user_row(user) -> AgentUserResponse:
    return AgentUserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        agency_id=user.agency_id,
        is_agency_admin=user.is_agency_admin,
        enabled=user.enabled,
        sync_status=user.sync_status,
        keycloak_user_id=user.keycloak_user_id,
    )


class UsersController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router.prefix = "/users"
        self.router.tags += ["users"]
        self._service = UserService()
        self.router.add_api_route("", self.list_users, methods=["GET"])
        self.router.add_api_route("/create", self.create_user, methods=["POST"])

    def _agency_id(self, request: Request) -> str:
        agency_id = getattr(request.state, AGENCY_ID_STATE_KEY, None)
        if not agency_id:
            raise ForbiddenError(message="Agency group is missing from the token")
        return str(agency_id)

    async def _require_agency_admin(self, request: Request, session, agency_id: str):
        claims = jwt.get_unverified_claims(request.state.auth.credentials)
        admin = await self._service.agency_admin(session, agency_id)
        if admin is None or not admin.keycloak_user_id or admin.keycloak_user_id != claims.get("sub"):
            raise ForbiddenError(message="Only the agency admin can manage agents")
        return admin

    @requires_auth
    async def list_users(self, request: Request) -> AgentUserListResponse:
        agency_id = self._agency_id(request)
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            await self._require_agency_admin(request, session, agency_id)
            users = await self._service.list_for_agency(session, agency_id)
        return AgentUserListResponse(agency_id=agency_id, users=[_user_row(user) for user in users])

    @requires_auth
    async def create_user(self, request: Request, body: CreateAgentBody) -> CreateAgentResponse:
        agency_id = self._agency_id(request)
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            await self._require_agency_admin(request, session, agency_id)
            user = await self._service.create_user(
                session,
                realm=ApplicationType.AGENT.value,
                email=body.email,
                first_name=body.first_name,
                last_name=body.last_name,
                agency_id=agency_id,
                is_agency_admin=False,
            )
            await session.commit()
            user_id = user.id
        return CreateAgentResponse(id=user_id, agency_id=agency_id, sync_status="pending")
