"""Data policy controller for IAM service."""

import logging

from fastapi import Request
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import async_sessionmaker

from openg2p_fastapi_common.context import dbengine
from ..config import Settings
from iam_core.schemas.data_policy import (
    AddPolicyRequest,
    AddPolicyResponse,
    AddPolicyResponseBody,
    AddPolicyResponsePayload,
    DataPolicyData,
    EvaluateExpressionRequestPayload,
    EvaluateExpressionResponsePayload,
    GetAllPoliciesRequest,
    GetAllPoliciesResponse,
    GetAllPoliciesResponseBody,
    GetAllPoliciesResponsePayload,
    GetPolicyRequest,
    GetPolicyResponse,
    GetPolicyResponseBody,
    GetPolicyResponsePayload,
    RemovePolicyRequest,
    RemovePolicyResponse,
    RemovePolicyResponseBody,
    RemovePolicyResponsePayload,
)
from iam_core.services.data_policy_service import DataPolicyService
from iam_core.user_auth.decorators import require_permissions
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import BadRequestError

from ..cache import data_policy_expression_key
from ..helpers.auth_token import bearer_from_request
from ..helpers.keycloak_helper import KeycloakHelper
from ..helpers.request_response_helper import RequestResponseHelper

_logger = logging.getLogger(__name__)
_config = Settings.get_config(strict=False)


class DataPolicyController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = DataPolicyService.get_component()
        self.router.tags += ["/data-policies"]
        self.router.prefix = "/data-policies"
        self.helper = RequestResponseHelper.get_component()

        self.router.add_api_route(
            "/get_policy",
            self.get_policy,
            responses={200: {"model": GetPolicyResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_all_policies",
            self.get_all_policies,
            responses={200: {"model": GetAllPoliciesResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/add_policy",
            self.add_policy,
            responses={200: {"model": AddPolicyResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/remove_policy",
            self.remove_policy,
            responses={200: {"model": RemovePolicyResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/evaluate_expression",
            self.evaluate_expression,
            responses={200: {"model": EvaluateExpressionResponsePayload}},
            methods=["POST"],
        )

    @require_permissions({"dataPolicy:view"})
    async def get_policy(self, request: GetPolicyRequest) -> GetPolicyResponse:
        try:
            payload = request.request_body.request_payload
            _logger.info("Getting data policy policy_id=%s", payload.policy_id)

            session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
            async with session_maker() as session:
                policy = await self._service.get_policy(
                    session,
                    policy_id=payload.policy_id,
                )
            return self.helper.construct_payload_response(
                request,
                GetPolicyResponsePayload(policy=policy),
                GetPolicyResponseBody,
                GetPolicyResponse,
            )
        except Exception as error_exception:
            _logger.error("Error in get_policy: %s", error_exception)
            raise BadRequestError(message=str(error_exception))

    @require_permissions({"dataPolicy:view"})
    async def get_all_policies(self, request: GetAllPoliciesRequest) -> GetAllPoliciesResponse:
        try:
            payload = request.request_body.request_payload
            _logger.info(
                "Getting all data policies with application_id=%s, policy_target=%s, register_id=%s",
                payload.application_id,
                payload.policy_target,
                payload.register_id,
            )

            session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
            async with session_maker() as session:
                policies, total = await self._service.get_all_policies(
                    session,
                    application_id=payload.application_id,
                    policy_target=payload.policy_target.value if payload.policy_target else None,
                    register_id=payload.register_id,
                )
            return self.helper.construct_payload_response(
                request,
                GetAllPoliciesResponsePayload(policies=policies),
                GetAllPoliciesResponseBody,
                GetAllPoliciesResponse,
                total=total,
                page_size=(
                    request.request_body.pagination_request.page_size
                    if request.request_body and request.request_body.pagination_request
                    else None
                ),
            )
        except Exception as error_exception:
            _logger.error("Error in get_all_policies: %s", error_exception)
            raise BadRequestError(message=str(error_exception))

    @require_permissions({"dataPolicy:create"})
    async def add_policy(self, request: AddPolicyRequest, http_request: Request) -> AddPolicyResponse:
        try:
            payload = request.request_body.request_payload
            _logger.info(
                "Adding data policy mnemonic=%s register_id=%s policy_target=%s application_id=%s",
                payload.policy_mnemonic,
                payload.register_id,
                payload.policy_target,
                payload.application_id,
            )

            # Add DP_ prefix if not already present for IAM application policies
            mnemonic = payload.policy_mnemonic
            if payload.application_id is not None and not mnemonic.startswith("DP_"):
                mnemonic = f"DP_{mnemonic}"

            session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
            async with session_maker() as session:
                policy = await self._service.add_policy(
                    policy_mnemonic=mnemonic,
                    policy_description=payload.policy_description,
                    register_id=payload.register_id,
                    policy_filter_expression=payload.policy_filter_expression,
                    session=session,
                    policy_type=payload.policy_type,
                    policy_target=payload.policy_target,
                    application_id=payload.application_id,
                )

                # Sync to Keycloak for IAM application policies
                if payload.application_id is not None:
                    auth_token = bearer_from_request(http_request) or ""
                    if auth_token:
                        try:
                            from ..models import StaffPortalApplication

                            app = await session.get(StaffPortalApplication, payload.application_id)
                            if app:
                                kc_helper = KeycloakHelper(auth_token)
                                role_name, already_existed = await kc_helper.create_role(
                                    mnemonic,
                                    app.application_mnemonic,
                                    role_description=payload.policy_description,
                                )
                                # If role already exists in Keycloak, that's fine - just save in DB
                                if already_existed:
                                    _logger.info(
                                        f"Data policy role '{mnemonic}' already exists in Keycloak, proceeding with DB save"
                                    )
                        except Exception as e:
                            await session.rollback()
                            _logger.error("Failed to sync data policy to Keycloak: %s", e)
                            raise BadRequestError(message=f"Failed to sync data policy to Keycloak: {e}")

                await session.commit()
            return self.helper.construct_payload_response(
                request,
                AddPolicyResponsePayload(policy=policy),
                AddPolicyResponseBody,
                AddPolicyResponse,
            )
        except Exception as error_exception:
            _logger.error("Error in add_policy: %s", error_exception)
            raise BadRequestError(message=str(error_exception))

    @require_permissions({"dataPolicy:delete"})
    async def remove_policy(
        self, request: RemovePolicyRequest, http_request: Request
    ) -> RemovePolicyResponse:
        try:
            payload = request.request_body.request_payload
            _logger.info("Removing data policy policy_id=%s", payload.policy_id)

            session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
            async with session_maker() as session:
                # Get policy first to check if it's an IAM application policy
                from iam_core.models import DataPolicy

                policy = await session.get(DataPolicy, payload.policy_id)
                if not policy:
                    raise BadRequestError(message=f"Data policy not found: {payload.policy_id}")

                # Sync to Keycloak for IAM application policies
                if policy.application_id is not None:
                    auth_token = bearer_from_request(http_request) or ""
                    if auth_token:
                        try:
                            from ..models import StaffPortalApplication

                            app = await session.get(StaffPortalApplication, policy.application_id)
                            if app:
                                kc_helper = KeycloakHelper(auth_token)
                                await kc_helper.delete_role(policy.policy_mnemonic, app.application_mnemonic)
                                _logger.info(
                                    f"Deleted Keycloak role '{policy.policy_mnemonic}' from client '{app.application_mnemonic}'"
                                )
                        except Exception as e:
                            _logger.warning("Failed to delete data policy from Keycloak: %s", e)
                            # Continue with DB deletion even if Keycloak sync fails

                deleted_id, policy_mnemonic, should_delete_role = await self._service.remove_policy(
                    policy_id=payload.policy_id,
                    session=session,
                )
                await session.commit()
            return self.helper.construct_payload_response(
                request,
                RemovePolicyResponsePayload(policy_id=deleted_id),
                RemovePolicyResponseBody,
                RemovePolicyResponse,
            )
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
