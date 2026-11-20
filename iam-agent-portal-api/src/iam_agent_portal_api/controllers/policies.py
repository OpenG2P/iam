"""Read-only policy list for the agency group, plus assignment of those policies to an agent."""

from fastapi import Request
from openg2p_fastapi_common.context import get_async_session_maker
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import BadRequestError

from iam_core.helpers.keycloak_admin import KeycloakAdminError
from iam_core.helpers.keycloak_admin_config import ProvisioningSettings
from iam_core.models import User
from iam_core.models.enum import ApplicationType
from iam_core.schemas.data_policy import (
    GetAllPoliciesRequestPayload,
    GetAllPoliciesResponsePayload,
    GetPolicyRequestPayload,
    GetPolicyResponsePayload,
)
from iam_core.services.data_policy_service import DataPolicyService
from iam_core.services.user_role_assignment import assign_client_roles
from iam_core.user_auth.decorators import requires_auth
from iam_core.user_auth.helpers.data_policy_role_helper import AGC_ROLE_PREFIX

from ..schemas import AssignPoliciesBody, AssignPoliciesResponse
from .users import UsersController


class PoliciesController(BaseController):
    """Same policy reads as staff. Add and remove stay on the staff API."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router.prefix = "/data-policies"
        self.router.tags += ["data-policies"]
        self._users = UsersController()
        self._policies = DataPolicyService.get_component() or DataPolicyService()
        self._settings = ProvisioningSettings()
        self.router.add_api_route("/get_policy", self.get_policy, methods=["POST"])
        self.router.add_api_route("/get_all_policies", self.get_all_policies, methods=["POST"])
        self.router.add_api_route("/assign", self.assign_policies, methods=["POST"])

    @requires_auth
    async def get_policy(self, request: Request, body: GetPolicyRequestPayload) -> GetPolicyResponsePayload:
        agency_id = self._users._agency_id(request)
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            await self._users._require_agency_admin(request, session, agency_id)
            policy = await self._policies.get_policy(session, policy_id=body.policy_id)
            allowed = await self._policies.policies_for_agency(session, agency_id)
        if policy.policy_id not in {item.policy_id for item in allowed}:
            raise BadRequestError(message="Policy is not part of this agency")
        return GetPolicyResponsePayload(policy=policy)

    @requires_auth
    async def get_all_policies(
        self, request: Request, body: GetAllPoliciesRequestPayload
    ) -> GetAllPoliciesResponsePayload:
        agency_id = self._users._agency_id(request)
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            await self._users._require_agency_admin(request, session, agency_id)
            policies = await self._policies.policies_for_agency(session, agency_id)
        if body.policy_target is not None:
            policies = [policy for policy in policies if policy.policy_target == body.policy_target]
        if body.register_id is not None:
            policies = [policy for policy in policies if policy.register_id == body.register_id]
        return GetAllPoliciesResponsePayload(policies=policies)

    @requires_auth
    async def assign_policies(self, request: Request, body: AssignPoliciesBody) -> AssignPoliciesResponse:
        agency_id = self._users._agency_id(request)
        wanted = sorted({mnemonic.strip() for mnemonic in body.policy_mnemonics if mnemonic.strip()})
        if not wanted:
            raise BadRequestError(message="Choose at least one policy")
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            await self._users._require_agency_admin(request, session, agency_id)
            allowed = {
                policy.policy_mnemonic
                for policy in await self._policies.policies_for_agency(session, agency_id)
            }
            if any(mnemonic not in allowed for mnemonic in wanted):
                raise BadRequestError(message="Policy is not part of this agency")
            user = await session.get(User, body.user_id)
            if (
                user is None
                or user.realm != ApplicationType.AGENT.value
                or user.agency_id != agency_id
                or not user.keycloak_user_id
            ):
                raise BadRequestError(message="User is not an agent in this agency yet")
            keycloak_user_id = user.keycloak_user_id
        try:
            await assign_client_roles(
                realm=self._settings.agent_realm,
                client_id=agency_id,
                keycloak_user_id=keycloak_user_id,
                role_names=[f"{AGC_ROLE_PREFIX}{mnemonic}" for mnemonic in wanted],
            )
        except KeycloakAdminError as error:
            raise BadRequestError(message=str(error)) from error
        return AssignPoliciesResponse(user_id=body.user_id, policy_mnemonics=wanted)
