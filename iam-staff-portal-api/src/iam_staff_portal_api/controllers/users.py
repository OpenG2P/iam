"""Staff creates the single admin user for an agency. Other agents are created later by that admin."""

from __future__ import annotations

from openg2p_fastapi_common.context import get_async_session_maker
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import BadRequestError

from iam_core.helpers.keycloak_admin import KeycloakAdminError
from iam_core.models import User
from iam_core.models.enum import ApplicationType
from iam_core.services.data_policy_service import DataPolicyService
from iam_core.services.user_service import UserService
from iam_core.services.user_role_assignment import assign_client_roles
from iam_core.user_auth.decorators import require_permissions
from iam_core.user_auth.helpers.data_policy_role_helper import DP_ROLE_PREFIX
from ..config import Settings
from ..schemas import (
    AssignPoliciesBody,
    AssignPoliciesResponse,
    CreateAgencyAdminBody,
    CreateAgencyAdminResponse,
)


class UsersController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router.prefix = "/users"
        self.router.tags += ["users"]
        self._service = UserService()
        self._policies = DataPolicyService.get_component() or DataPolicyService()
        self._settings = Settings.get_config(strict=False)
        self.router.add_api_route("/create_agency_admin", self.create_agency_admin, methods=["POST"])
        self.router.add_api_route("/assign_policies", self.assign_policies, methods=["POST"])

    @require_permissions({"user:create"})
    async def create_agency_admin(self, body: CreateAgencyAdminBody) -> CreateAgencyAdminResponse:
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            existing = await self._service.agency_admin(session, body.agency_id)
            if existing is not None:
                raise BadRequestError(message="This agency already has an admin")
            user = await self._service.create_user(
                session,
                realm=ApplicationType.AGENT.value,
                email=body.email,
                first_name=body.first_name,
                last_name=body.last_name,
                agency_id=body.agency_id,
                is_agency_admin=True,
            )
            await session.commit()
            user_id = user.id
        return CreateAgencyAdminResponse(
            id=user_id,
            agency_id=body.agency_id,
            is_agency_admin=True,
            sync_status="pending",
        )

    @require_permissions({"user:create"})
    async def assign_policies(self, body: AssignPoliciesBody) -> AssignPoliciesResponse:
        """Give an existing staff user the DP_ roles for policies that already exist."""
        wanted = sorted({mnemonic.strip() for mnemonic in body.policy_mnemonics if mnemonic.strip()})
        if not wanted:
            raise BadRequestError(message="Choose at least one policy")
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            known = await self._policies.get_policies_by_mnemonics(wanted, session)
            known_mnemonics = {policy.policy_mnemonic for policy in known}
            if any(mnemonic not in known_mnemonics for mnemonic in wanted):
                raise BadRequestError(message="Policy does not exist")
            user = await session.get(User, body.user_id)
            if user is None or user.realm != ApplicationType.STAFF.value or not user.keycloak_user_id:
                raise BadRequestError(message="User is not a staff user yet")
            keycloak_user_id = user.keycloak_user_id
        try:
            await assign_client_roles(
                realm=self._settings.keycloak_realm,
                client_id=self._settings.keycloak_client_id,
                keycloak_user_id=keycloak_user_id,
                role_names=[f"{DP_ROLE_PREFIX}{mnemonic}" for mnemonic in wanted],
            )
        except KeycloakAdminError as error:
            raise BadRequestError(message=str(error)) from error
        return AssignPoliciesResponse(user_id=body.user_id, policy_mnemonics=wanted)
