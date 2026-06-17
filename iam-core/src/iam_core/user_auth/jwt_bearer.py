from fastapi import Request
from fastapi.security import HTTPBearer
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError

from iam_core.schemas import AuthCredentials

from .config import Settings
from .helpers.token_helper import access_token_and_id_token_from_request, validate_request_token

_config = Settings.get_config(strict=False)


class JwtBearerAuth(HTTPBearer):
    """FastAPI dependency: validate Bearer/cookie tokens when auth is enabled."""

    async def __call__(self, request: Request) -> AuthCredentials | None:
        if not _config.model_dump().get("auth_enabled", None):
            return None

        access_token, id_token = access_token_and_id_token_from_request(request)
        if not access_token:
            raise UnauthorizedError()

        return await validate_request_token(
            request,
            jwt_token=access_token,
            jwt_id_token=id_token,
        )
