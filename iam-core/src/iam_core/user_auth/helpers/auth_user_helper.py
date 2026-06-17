from fastapi import Request
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError

from iam_core.schemas import AuthCredentials, AuthPrincipal, LoggedInUserResponse

from ..enums import RequestStateKey
from .claims_helper import claims_from_auth, extract_client_roles


def logged_in_user_from_claims(claims: dict) -> LoggedInUserResponse:
    """Map standard OIDC profile claims to the API user shape."""
    address = claims.get("address")
    if not isinstance(address, dict):
        address = {}

    return LoggedInUserResponse(
        sub=claims.get("sub"),
        email_verified=claims.get("email_verified"),
        address=address,
        name=claims.get("name"),
        preferred_username=claims.get("preferred_username"),
        given_name=claims.get("given_name"),
        family_name=claims.get("family_name"),
        email=claims.get("email"),
    )


def auth_principal_from_credentials(auth: AuthCredentials) -> AuthPrincipal:
    """Strip validated credentials down to the fields middleware and RBAC need."""
    claims = auth.model_dump()
    return AuthPrincipal(
        scheme=auth.scheme,
        name=auth.name,
        credentials=auth.credentials,
        sub=claims.get("sub"),
        aud=claims.get("aud"),
        client_roles=extract_client_roles(claims),
    )


async def build_logged_in_user(
    auth: AuthCredentials | AuthPrincipal,
    auth_service=None,
) -> LoggedInUserResponse:
    """Prefer live userinfo from the IdP; fall back to token claims on failure."""
    from iam_core.services import AuthService

    claims = claims_from_auth(auth)
    access_token = claims.get("credentials")
    if access_token:
        issuer = claims.get("iss")
        try:
            service = auth_service or AuthService.get_component() or AuthService()
            userinfo = await service.get_oauth_validation_data(
                auth=access_token,
                iss=issuer,
                combine=False,
            )
            if isinstance(userinfo, dict) and userinfo:
                return logged_in_user_from_claims(userinfo)
        except Exception:
            pass
    return logged_in_user_from_claims(claims)


def auth_from_request(request: Request) -> AuthPrincipal:
    """Return ``request.state.auth`` set by ValidateAndRefreshTokenMiddleware."""
    auth = getattr(request.state, RequestStateKey.AUTH, None)
    if not isinstance(auth, AuthPrincipal):
        raise UnauthorizedError()
    return auth


def logged_in_user_from_request(request: Request) -> LoggedInUserResponse:
    """Return ``request.state.user`` set by ValidateAndRefreshTokenMiddleware."""
    user = getattr(request.state, RequestStateKey.USER, None)
    if not isinstance(user, LoggedInUserResponse):
        raise UnauthorizedError()
    return user
