from __future__ import annotations

from datetime import datetime
from math import ceil
from typing import Any, Optional

from openg2p_fastapi_common.errors.http_exceptions import BadRequestError
from openg2p_fastapi_common.schemas import (
    G2PPaginationResponse,
    G2PRequest,
    G2PResponse,
    G2PResponseBody,
    G2PResponseHeader,
    G2PResponseStatus,
)
from openg2p_fastapi_common.service import BaseService


class RequestResponseHelper(BaseService):
    def number_of_pages(self, total: int, page_size: int) -> int:
        if page_size <= 0:
            return 0
        return int(ceil(total / page_size)) if total else 0

    def pagination_from_request(self, request: G2PRequest, default_page_size: int = 20) -> tuple[int, int]:
        pagination = request.request_body.pagination_request if request.request_body else None
        if pagination is None:
            return 1, default_page_size
        return pagination.current_page, pagination.page_size

    def require_payload(self, request: G2PRequest) -> Any:
        payload = request.request_body.request_payload if request.request_body else None
        if payload is None:
            raise BadRequestError(message="request_payload is required")
        return payload

    def construct_payload_response(
        self,
        request: G2PRequest,
        response_payload: Any,
        response_body_type: type[G2PResponseBody],
        response_type: type[G2PResponse],
        *,
        total: int | None = None,
        page_size: int | None = None,
    ) -> G2PResponse:
        pagination_response: Optional[G2PPaginationResponse] = None
        if total is not None and page_size is not None:
            pagination_response = G2PPaginationResponse(
                number_of_items=total,
                number_of_pages=self.number_of_pages(total, page_size),
            )
        response_body = response_body_type(
            pagination_response=pagination_response,
            response_payload=response_payload,
        )
        return response_type(
            response_header=G2PResponseHeader(
                request_id=request.request_header.request_id,
                response_status=G2PResponseStatus.SUCCESS,
                response_error_code="",
                response_error_message="",
                response_timestamp=datetime.now(),
            ),
            response_body=response_body,
        )

    def construct_success_response(
        self,
        request: G2PRequest,
        response_payload: Any,
        *,
        total: int | None = None,
        page_size: int | None = None,
    ) -> G2PResponse:
        pagination_response: Optional[G2PPaginationResponse] = None
        if total is not None and page_size is not None:
            pagination_response = G2PPaginationResponse(
                number_of_items=total,
                number_of_pages=self.number_of_pages(total, page_size),
            )
        return G2PResponse(
            response_header=G2PResponseHeader(
                request_id=request.request_header.request_id,
                response_status=G2PResponseStatus.SUCCESS,
                response_error_code="",
                response_error_message="",
                response_timestamp=datetime.now(),
            ),
            response_body=G2PResponseBody(
                pagination_response=pagination_response,
                response_payload=response_payload,
            ),
        )

    def construct_error_response(self, error: Exception, request: G2PRequest | None = None) -> G2PResponse:
        message = getattr(error, "message", None) or str(error) or "Unexpected error"
        code = getattr(error, "code", None) or "G2P-IAM-400"
        request_id = ""
        if request is not None and getattr(request, "request_header", None) is not None:
            request_id = request.request_header.request_id
        return G2PResponse(
            response_header=G2PResponseHeader(
                request_id=request_id,
                response_status=G2PResponseStatus.ERROR,
                response_error_code=str(code),
                response_error_message=str(message),
                response_timestamp=datetime.now(),
            ),
            response_body=G2PResponseBody(pagination_response=None, response_payload=None),
        )
