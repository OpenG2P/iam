from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError


def validate_refresh_token_response(token_response: dict) -> dict:
    """Validate a refresh-token grant response from the OIDC provider."""
    if token_response.get("error"):
        description = (
            token_response.get("error_description")
            or token_response.get("error")
        )
        raise UnauthorizedError(
            message=f"Unauthorized. Refresh token response error: {description}",
        )

    access_token = token_response.get("access_token")
    if not access_token or not str(access_token).strip():
        raise UnauthorizedError(
            message="Unauthorized. Missing access_token in refresh token response.",
        )

    return token_response
