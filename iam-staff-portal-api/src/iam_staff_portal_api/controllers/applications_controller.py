from __future__ import annotations

import logging

from openg2p_fastapi_common.controller import BaseController

from iam_core.user_auth.decorators import require_permissions

from ..config import Settings
from ..helpers.request_response_helper import RequestResponseHelper
from ..schemas import (
    ApplicationData,
    ApplicationResponse,
    ApplicationResponseBody,
    ApplicationsResponse,
    ApplicationsResponseBody,
    CreateApplicationRequest,
    DeleteApplicationRequest,
    GetApplicationRequest,
    GetApplicationsRequest,
    OkResponse,
    UpdateApplicationRequest,
)
from ..services.applications_service import ApplicationsService

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


class ApplicationsController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router.tags += ["/applications"]
        self.router.prefix = "/applications"
        self.helper = RequestResponseHelper.get_component()
        self.applications_service = ApplicationsService.get_component()

        self.router.add_api_route(
            "/get_applications",
            self.get_applications,
            responses={200: {"model": ApplicationsResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/get_application",
            self.get_application,
            responses={200: {"model": ApplicationResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/create_application",
            self.create_application,
            responses={200: {"model": ApplicationResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/update_application",
            self.update_application,
            responses={200: {"model": ApplicationResponse}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/delete_application",
            self.delete_application,
            responses={200: {"model": OkResponse}},
            methods=["POST"],
        )

    @require_permissions({"application:view"})
    async def get_applications(self, get_request: GetApplicationsRequest) -> ApplicationsResponse:
        try:
            page, page_size = self.helper.pagination_from_request(
                get_request, default_page_size=_config.default_page_size
            )
            applications: list[ApplicationData]
            total: int
            applications, total = await self.applications_service.get_applications(
                page, page_size
            )
            return self.helper.construct_payload_response(
                get_request,
                applications,
                ApplicationsResponseBody,
                ApplicationsResponse,
                total=total,
                page_size=page_size,
            )
        except Exception as error_exception:
            _logger.exception("get_applications failed")
            return self.helper.construct_error_response(error_exception, get_request)

    @require_permissions({"application:view"})
    async def get_application(self, get_request: GetApplicationRequest) -> ApplicationResponse:
        try:
            application: ApplicationData = await self.applications_service.get_application(
                get_request.request_body.request_payload
            )
            return self.helper.construct_payload_response(
                get_request,
                application,
                ApplicationResponseBody,
                ApplicationResponse,
            )
        except Exception as error_exception:
            _logger.exception("get_application failed")
            return self.helper.construct_error_response(error_exception, get_request)

    @require_permissions({"application:create"})
    async def create_application(
        self, create_request: CreateApplicationRequest
    ) -> ApplicationResponse:
        try:
            application: ApplicationData = await self.applications_service.create_application(
                create_request.request_body.request_payload
            )
            return self.helper.construct_payload_response(
                create_request,
                application,
                ApplicationResponseBody,
                ApplicationResponse,
            )
        except Exception as error_exception:
            _logger.exception("create_application failed")
            return self.helper.construct_error_response(error_exception, create_request)

    @require_permissions({"application:edit"})
    async def update_application(
        self, update_request: UpdateApplicationRequest
    ) -> ApplicationResponse:
        try:
            application: ApplicationData = await self.applications_service.update_application(
                update_request.request_body.request_payload
            )
            return self.helper.construct_payload_response(
                update_request,
                application,
                ApplicationResponseBody,
                ApplicationResponse,
            )
        except Exception as error_exception:
            _logger.exception("update_application failed")
            return self.helper.construct_error_response(error_exception, update_request)

    @require_permissions({"application:delete"})
    async def delete_application(
        self, delete_request: DeleteApplicationRequest
    ) -> OkResponse:
        try:
            await self.applications_service.delete_application(
                delete_request.request_body.request_payload
            )
            return self.helper.construct_success_response(
                delete_request, {"ok": True}
            )
        except Exception as error_exception:
            _logger.exception("delete_application failed")
            return self.helper.construct_error_response(error_exception, delete_request)
