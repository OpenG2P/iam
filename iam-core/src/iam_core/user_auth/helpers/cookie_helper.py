from datetime import datetime, timedelta, timezone

from fastapi import Response
from jose import jwt as jose_jwt
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError
from starlette.responses import Response as StarletteResponse

from iam_core.user_auth.config import Settings

_config = Settings.get_config(strict=False)

AUTH_ACCESS_TOKEN_COOKIE_NAME = "X-Access-Token"
AUTH_ID_TOKEN_COOKIE_NAME = "X-ID-Token"
AUTH_SESSION_COOKIE_NAME = "X-Session-Id"


def oidc_session_id_from_token_response(token_response: dict) -> str:
    """Return Keycloak/OIDC ``sid`` from access or id token claims."""
    for token in (token_response.get("access_token"), token_response.get("id_token")):
        if not token:
            continue
        try:
            sid = jose_jwt.get_unverified_claims(token).get("sid")
        except Exception:
            continue
        if sid:
            return str(sid)
    raise UnauthorizedError("G2P-AUT-401", "Missing sid claim in token response.")


def issuer_from_token_response(token_response: dict) -> str:
    """Return OIDC ``iss`` from access or id token claims."""
    for token in (token_response.get("access_token"), token_response.get("id_token")):
        if not token:
            continue
        try:
            issuer = jose_jwt.get_unverified_claims(token).get("iss")
        except Exception:
            continue
        if issuer:
            return str(issuer)
    raise UnauthorizedError("G2P-AUT-401", "Missing iss claim in token response.")


def _cookie_expires(token_response: dict) -> datetime | None:
    if not _config.auth_cookie_set_expires:
        return None
    seconds = token_response.get("expires_in")
    if not seconds:
        return None
    return datetime.now(tz=timezone.utc) + timedelta(seconds=int(seconds))


def _cookie_delete_kwargs() -> dict:
    return {
        "path": _config.auth_cookie_path,
        "domain": _config.auth_cookie_domain,
        "httponly": _config.auth_cookie_httponly,
        "secure": _config.auth_cookie_secure,
    }


def set_auth_cookies(
    response: Response | StarletteResponse,
    token_response: dict,
    *,
    session_id: str | None = None,
) -> None:
    delete_kwargs = _cookie_delete_kwargs()
    response.delete_cookie(AUTH_ACCESS_TOKEN_COOKIE_NAME, **delete_kwargs)
    response.delete_cookie(AUTH_ID_TOKEN_COOKIE_NAME, **delete_kwargs)
    if session_id:
        response.delete_cookie(AUTH_SESSION_COOKIE_NAME, **delete_kwargs)

    expires_in = _cookie_expires(token_response)
    cookie_kwargs = {
        "max_age": _config.auth_cookie_max_age,
        "expires": expires_in,
        "path": _config.auth_cookie_path,
        "domain": _config.auth_cookie_domain,
        "httponly": _config.auth_cookie_httponly,
        "secure": _config.auth_cookie_secure,
    }
    response.set_cookie(
        AUTH_ACCESS_TOKEN_COOKIE_NAME,
        token_response["access_token"],
        **cookie_kwargs,
    )
    if token_response.get("id_token"):
        response.set_cookie(
            AUTH_ID_TOKEN_COOKIE_NAME,
            token_response["id_token"],
            **cookie_kwargs,
        )
    if session_id:
        response.set_cookie(
            AUTH_SESSION_COOKIE_NAME,
            session_id,
            max_age=_config.auth_refresh_token_ttl_seconds,
            path=_config.auth_cookie_path,
            domain=_config.auth_cookie_domain,
            httponly=True,
            secure=_config.auth_cookie_secure,
        )


def clear_auth_cookies(
    response: Response | StarletteResponse,
) -> None:
    delete_kwargs = _cookie_delete_kwargs()
    response.delete_cookie(AUTH_ACCESS_TOKEN_COOKIE_NAME, **delete_kwargs)
    response.delete_cookie(AUTH_ID_TOKEN_COOKIE_NAME, **delete_kwargs)
    response.delete_cookie(AUTH_SESSION_COOKIE_NAME, **delete_kwargs)
