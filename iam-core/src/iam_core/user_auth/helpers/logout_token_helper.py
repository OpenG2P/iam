from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError

from iam_core.models import LoginProvider

BACKCHANNEL_LOGOUT_EVENT = "http://schemas.openid.net/event/backchannel-logout"


def session_id_from_logout_token_claims(claims: dict, login_provider: LoginProvider) -> str:
    """Validate OIDC back-channel logout token claims and return the session id."""
    if claims.get("nonce") is not None:
        raise UnauthorizedError(
            message="Unauthorized. Invalid logout token: nonce claim must not be present.",
        )

    events = claims.get("events")
    if not isinstance(events, dict) or BACKCHANNEL_LOGOUT_EVENT not in events:
        raise UnauthorizedError(
            message="Unauthorized. Invalid logout token: missing backchannel-logout event.",
        )

    sid = claims.get("sid")
    if not sid:
        raise UnauthorizedError(
            message="Unauthorized. Invalid logout token: missing sid claim.",
        )

    client_id = login_provider.client_id
    aud = claims.get("aud")
    if isinstance(aud, list):
        if client_id not in aud:
            raise UnauthorizedError(message="Unauthorized. Invalid logout token audience.")
    elif aud != client_id:
        raise UnauthorizedError(message="Unauthorized. Invalid logout token audience.")

    return str(sid)
