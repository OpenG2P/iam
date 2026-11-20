"""Service-to-service policy and permission lookups used by staff and agency APIs."""

from openg2p_fastapi_common.context import get_async_session_maker
from openg2p_fastapi_common.controller import BaseController

from iam_core.schemas.access import PermissionsLookupResponse, RoleLookup
from iam_core.schemas.data_policy import (
    EvaluateExpressionRequestPayload,
    EvaluateExpressionResponsePayload,
)
from iam_core.services.data_policy_service import DataPolicyService
from iam_core.services.role_permission_service import permissions_for_client_roles


class AccessController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router.tags += ["access"]
        self._policies = DataPolicyService.get_component() or DataPolicyService()
        self.router.add_api_route(
            "/data-policies/evaluate_expression",
            self.evaluate_expression,
            methods=["POST"],
        )
        self.router.add_api_route(
            "/user-access/get_permissions_for_roles",
            self.permissions_for_roles,
            methods=["POST"],
        )

    async def evaluate_expression(
        self, body: EvaluateExpressionRequestPayload
    ) -> EvaluateExpressionResponsePayload:
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            policies = await self._policies.policies_for_client_roles(
                session,
                [(client.client_id, client.policy_mnemonics) for client in body.clients],
            )
        return EvaluateExpressionResponsePayload(policies=policies)

    async def permissions_for_roles(self, body: RoleLookup) -> PermissionsLookupResponse:
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            permissions = await permissions_for_client_roles(
                session,
                [(client.client_id, client.role_mnemonics) for client in body.clients],
            )
        return PermissionsLookupResponse(permissions=permissions)
