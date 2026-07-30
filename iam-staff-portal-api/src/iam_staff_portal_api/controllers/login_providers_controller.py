from __future__ import annotations

import logging

from openg2p_fastapi_common.controller import BaseController

from iam_core.user_auth.decorators import require_permissions

from ..config import Settings
from ..helpers.request_response_helper import RequestResponseHelper
from ..schemas import (
    CreateLoginProviderRequest,
    DeleteLoginProviderRequest,
    GetLoginProviderRequest,
    GetLoginProvidersRequest,
    LoginProviderData,
    LoginProviderResponse,
    LoginProviderResponseBody,
    LoginProvidersResponse,
    LoginProvidersResponseBody,
    OkResponse,
    UpdateLoginProviderRequest,
)
from ..services.login_providers_service import LoginProvidersService

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


class LoginProvidersController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router.tags += ["/login-providers"]
        self.router.prefix = "/login-providers"
        self.helper = RequestResponseHelper.get_component()
        self.login_providers_service = LoginProvidersService.get_component()

        self.router.add_api_route(
            "/get_login_providers",
            self.get_login_providers,
            responses={200: {"model": LoginProvidersResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_login_provider",
            self.get_login_provider,
            responses={200: {"model": LoginProviderResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/create_login_provider",
            self.create_login_provider,
            responses={200: {"model": LoginProviderResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/update_login_provider",
            self.update_login_provider,
            responses={200: {"model": LoginProviderResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/delete_login_provider",
            self.delete_login_provider,
            responses={200: {"model": OkResponse}},
            methods=["POST"],
        )

    @require_permissions({"loginProvider:view"})
    async def get_login_providers(
        self, get_request: GetLoginProvidersRequest
    ) -> LoginProvidersResponse:
        try:
            page, page_size = self.helper.pagination_from_request(
                get_request, default_page_size=_config.default_page_size
            )
            login_providers: list[LoginProviderData]
            total: int
            login_providers, total = await self.login_providers_service.get_login_providers(
                page, page_size
            )
            return self.helper.construct_payload_response(
                get_request,
                login_providers,
                LoginProvidersResponseBody,
                LoginProvidersResponse,
                total=total,
                page_size=page_size,
            )
        except Exception as error_exception:
            _logger.exception("get_login_providers failed")
            return self.helper.construct_error_response(error_exception, get_request)

    @require_permissions({"loginProvider:view"})
    async def get_login_provider(
        self, get_request: GetLoginProviderRequest
    ) -> LoginProviderResponse:
        try:
            login_provider: LoginProviderData = (
                await self.login_providers_service.get_login_provider(
                    get_request.request_body.request_payload
                )
            )
            return self.helper.construct_payload_response(
                get_request,
                login_provider,
                LoginProviderResponseBody,
                LoginProviderResponse,
            )
        except Exception as error_exception:
            _logger.exception("get_login_provider failed")
            return self.helper.construct_error_response(error_exception, get_request)

    @require_permissions({"loginProvider:create"})
    async def create_login_provider(
        self, create_request: CreateLoginProviderRequest
    ) -> LoginProviderResponse:
        try:
            login_provider: LoginProviderData = (
                await self.login_providers_service.create_login_provider(
                    create_request.request_body.request_payload
                )
            )
            return self.helper.construct_payload_response(
                create_request,
                login_provider,
                LoginProviderResponseBody,
                LoginProviderResponse,
            )
        except Exception as error_exception:
            _logger.exception("create_login_provider failed")
            return self.helper.construct_error_response(error_exception, create_request)

    @require_permissions({"loginProvider:edit"})
    async def update_login_provider(
        self, update_request: UpdateLoginProviderRequest
    ) -> LoginProviderResponse:
        try:
            login_provider: LoginProviderData = (
                await self.login_providers_service.update_login_provider(
                    update_request.request_body.request_payload
                )
            )
            return self.helper.construct_payload_response(
                update_request,
                login_provider,
                LoginProviderResponseBody,
                LoginProviderResponse,
            )
        except Exception as error_exception:
            _logger.exception("update_login_provider failed")
            return self.helper.construct_error_response(error_exception, update_request)

    @require_permissions({"loginProvider:delete"})
    async def delete_login_provider(
        self, delete_request: DeleteLoginProviderRequest
    ) -> OkResponse:
        try:
            await self.login_providers_service.delete_login_provider(
                delete_request.request_body.request_payload
            )
            return self.helper.construct_success_response(
                delete_request, {"ok": True}
            )
        except Exception as error_exception:
            _logger.exception("delete_login_provider failed")
            return self.helper.construct_error_response(error_exception, delete_request)
