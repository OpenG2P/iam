"""Data policy controller for IAM service."""

import logging

from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import async_sessionmaker

from openg2p_fastapi_common.context import dbengine
from ..config import Settings
from iam_core.schemas.data_policy import (
    AddPolicyRequest,
    AddPolicyResponsePayload,
    DataPolicyData,
    EvaluateExpressionRequestPayload,
    EvaluateExpressionResponsePayload,
    GetAllPoliciesRequest,
    GetAllPoliciesResponsePayload,
    GetPolicyRequest,
    GetPolicyResponsePayload,
    RemovePolicyRequest,
    RemovePolicyResponsePayload,
)
from iam_core.services.data_policy_service import DataPolicyService
from iam_core.user_auth.decorators import require_permissions
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import BadRequestError

from ..cache import data_policy_expression_key

_logger = logging.getLogger(__name__)
_config = Settings.get_config(strict=False)


class DataPolicyController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = DataPolicyService.get_component()
        self.router.tags += ["/data-policies"]
        self.router.prefix = "/data-policies"

        self.router.add_api_route(
            "/get_policy",
            self.get_policy,
            responses={200: {"model": GetPolicyResponsePayload}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_all_policies",
            self.get_all_policies,
            responses={200: {"model": GetAllPoliciesResponsePayload}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/add_policy",
            self.add_policy,
            responses={200: {"model": AddPolicyResponsePayload}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/remove_policy",
            self.remove_policy,
            responses={200: {"model": RemovePolicyResponsePayload}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/evaluate_expression",
            self.evaluate_expression,
            responses={200: {"model": EvaluateExpressionResponsePayload}},
            methods=["POST"],
        )

    @require_permissions({"dataPolicy:view"})
    async def get_policy(self, request: GetPolicyRequest) -> GetPolicyResponsePayload:
        try:
            payload = request.request_body.request_payload
            _logger.info("Getting data policy policy_id=%s", payload.policy_id)

            session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
            async with session_maker() as session:
                policy = await self._service.get_policy(
                    session,
                    policy_id=payload.policy_id,
                )
            return GetPolicyResponsePayload(policy=policy)
        except Exception as error_exception:
            _logger.error("Error in get_policy: %s", error_exception)
            raise BadRequestError(message=str(error_exception))

    @require_permissions({"dataPolicy:view"})
    async def get_all_policies(self, request: GetAllPoliciesRequest) -> GetAllPoliciesResponsePayload:
        try:
            _logger.info("Getting all data policies")

            session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
            async with session_maker() as session:
                policies, _ = await self._service.get_all_policies(session)
            return GetAllPoliciesResponsePayload(policies=policies)
        except Exception as error_exception:
            _logger.error("Error in get_all_policies: %s", error_exception)
            raise BadRequestError(message=str(error_exception))

    @require_permissions({"dataPolicy:create"})
    async def add_policy(self, request: AddPolicyRequest) -> AddPolicyResponsePayload:
        try:
            payload = request.request_body.request_payload
            _logger.info(
                "Adding data policy mnemonic=%s register_id=%s policy_target=%s",
                payload.policy_mnemonic,
                payload.register_id,
                payload.policy_target,
            )

            session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
            async with session_maker() as session:
                policy = await self._service.add_policy(
                    policy_mnemonic=payload.policy_mnemonic,
                    policy_description=payload.policy_description,
                    register_id=payload.register_id,
                    policy_filter_expression=payload.policy_filter_expression,
                    session=session,
                    policy_type=payload.policy_type,
                    policy_target=payload.policy_target,
                )
                await session.commit()
            return AddPolicyResponsePayload(policy=policy)
        except Exception as error_exception:
            _logger.error("Error in add_policy: %s", error_exception)
            raise BadRequestError(message=str(error_exception))

    @require_permissions({"dataPolicy:delete"})
    async def remove_policy(self, request: RemovePolicyRequest) -> RemovePolicyResponsePayload:
        try:
            payload = request.request_body.request_payload
            _logger.info("Removing data policy policy_id=%s", payload.policy_id)

            session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
            async with session_maker() as session:
                deleted_id, policy_mnemonic, should_delete_role = await self._service.remove_policy(
                    policy_id=payload.policy_id,
                    session=session,
                )
                await session.commit()
            return RemovePolicyResponsePayload(policy_id=deleted_id)
        except Exception as error_exception:
            _logger.error("Error in remove_policy: %s", error_exception)
            raise BadRequestError(message=str(error_exception))

    async def evaluate_expression(
        self, payload: EvaluateExpressionRequestPayload
    ) -> EvaluateExpressionResponsePayload:
        """
        Evaluate data policy expression for given policy mnemonics.
        This endpoint is called by registry middleware to get all policies matching mnemonics.
        Returns complete policy data; registry will handle filtering and expression merging.
        Results are cached based on policy mnemonics.
        No permission decorator - accessible by registry service-to-service.
        """
        _logger.info(
            "Evaluating expression for policy_mnemonics=%s",
            payload.policy_mnemonics,
        )

        # Call the cached internal method
        policies = await self._evaluate_expression_cached(
            policy_mnemonics=payload.policy_mnemonics,
        )

        return EvaluateExpressionResponsePayload(policies=policies)

    @cache(expire=_config.cache_expire_seconds, key_builder=data_policy_expression_key)
    async def _evaluate_expression_cached(
        self,
        policy_mnemonics: list[str],
    ) -> list[DataPolicyData]:
        """Internal cached method for expression evaluation."""
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            policies = await self._service.get_policies_by_mnemonics(
                policy_mnemonics=policy_mnemonics,
                session=session,
            )
            return policies
