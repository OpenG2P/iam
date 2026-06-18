from fastapi import Request
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError

from iam_core.schemas import AuthCredentials

from ..config import ApiAuthSettings, Settings
from ..enums import AuthCookieName

_config = Settings.get_config(strict=False)

REFRESH_FAILED_MESSAGE = "Unauthorized. Access token expired and refresh failed."
SESSION_INVALIDATED_MESSAGE = "Unauthorized. Session has ended."


def access_token_and_id_token_from_request(request: Request) -> tuple[str | None, str | None]:
    """Return ``(access_token, id_token)`` from headers/cookies."""
    jwt_token = request.headers.get("Authorization") or request.cookies.get(AuthCookieName.ACCESS_TOKEN)
    access_token = jwt_token.removeprefix("Bearer ").strip() if jwt_token else None
    return access_token or None, request.cookies.get(AuthCookieName.ID_TOKEN)


def validate_refresh_token_response(token_response: dict) -> dict:
    """Validate a refresh-token grant response from the OIDC provider."""
    if token_response.get("error"):
        description = token_response.get("error_description") or token_response.get("error")
        raise UnauthorizedError(
            message=f"Unauthorized. Refresh token response error: {description}",
        )

    access_token = token_response.get("access_token")
    if not access_token or not str(access_token).strip():
        raise UnauthorizedError(
            message="Unauthorized. Missing access_token in refresh token response.",
        )

    return token_response


async def validate_request_token(
    request: Request,
    jwt_token: str,
    jwt_id_token: str | None = None,
) -> AuthCredentials:
    """Full signature/audience validation via TokenValidatorService."""
    from iam_core.services import TokenValidatorService

    api_call_name = str(request.scope["route"].name)
    api_auth_settings = ApiAuthSettings.model_validate(
        _config.model_dump().get("auth_api_" + api_call_name, {})
    )

    token_validator = TokenValidatorService.get_component() or TokenValidatorService()
    return await token_validator.validate(
        jwt_token=jwt_token,
        jwt_id_token=jwt_id_token,
        api_auth_settings=api_auth_settings,
    )
