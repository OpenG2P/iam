from datetime import datetime, timedelta, timezone
import secrets

from fastapi import Response
from jose import jwt as jose_jwt
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError
from starlette.responses import Response as StarletteResponse

from iam_core.user_auth.config import Settings
from iam_core.user_auth.enums import AuthCookieName

_config = Settings.get_config(strict=False)


def oidc_session_id_from_token_response(token_response: dict) -> str:
    """Return OIDC ``sid`` from tokens; this value becomes the ``SESSION`` cookie."""
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
    """Return OIDC ``iss``; used to pick the right provider adapter on refresh/logout."""
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
    """Optional Set-Cookie expiry aligned with the provider's ``expires_in``."""
    if not _config.auth_cookie_set_expires:
        return None
    seconds = token_response.get("expires_in")
    if not seconds:
        return None
    return datetime.now(tz=timezone.utc) + timedelta(seconds=int(seconds))


def _cookie_delete_kwargs() -> dict:
    """Shared path/domain/flags so delete matches how cookies were originally set."""
    return {
        "path": _config.auth_cookie_path,
        "domain": _config.auth_cookie_domain,
        "httponly": _config.auth_cookie_httponly,
        "secure": _config.auth_cookie_secure,
    }


def _csrf_cookie_delete_kwargs() -> dict:
    """Delete kwargs for the CSRF cookie (not httponly)."""
    return {
        "path": _config.auth_cookie_path,
        "domain": _config.auth_cookie_domain,
        "httponly": False,
        "secure": _config.auth_cookie_secure,
    }


def generate_csrf_token() -> str:
    """Return a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(32)


def set_csrf_cookie(
    response: Response | StarletteResponse,
    *,
    token: str | None = None,
) -> str:
    """Write the double-submit CSRF cookie. Returns the token value."""
    csrf_token = token or generate_csrf_token()
    response.delete_cookie(AuthCookieName.CSRF_TOKEN, **_csrf_cookie_delete_kwargs())
    response.set_cookie(
        AuthCookieName.CSRF_TOKEN,
        csrf_token,
        max_age=_config.auth_refresh_token_ttl_seconds,
        path=_config.auth_cookie_path,
        domain=_config.auth_cookie_domain,
        httponly=False,
        secure=_config.auth_cookie_secure,
        samesite="lax",
    )
    return csrf_token


def set_auth_cookies(
    response: Response | StarletteResponse,
    token_response: dict,
    *,
    session_id: str | None = None,
) -> None:
    """Write auth cookies. Pass ``session_id`` on login only; refresh updates tokens alone."""
    delete_kwargs = _cookie_delete_kwargs()
    response.delete_cookie(AuthCookieName.ACCESS_TOKEN, **delete_kwargs)
    response.delete_cookie(AuthCookieName.ID_TOKEN, **delete_kwargs)
    if session_id:
        response.delete_cookie(AuthCookieName.SESSION, **delete_kwargs)

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
        AuthCookieName.ACCESS_TOKEN,
        token_response["access_token"],
        **cookie_kwargs,
    )
    if token_response.get("id_token"):
        response.set_cookie(
            AuthCookieName.ID_TOKEN,
            token_response["id_token"],
            **cookie_kwargs,
        )
    if session_id:
        # Session cookie outlives access tokens and ties the browser to stored refresh state.
        response.set_cookie(
            AuthCookieName.SESSION,
            session_id,
            max_age=_config.auth_refresh_token_ttl_seconds,
            path=_config.auth_cookie_path,
            domain=_config.auth_cookie_domain,
            httponly=True,
            secure=_config.auth_cookie_secure,
        )
    set_csrf_cookie(response)


def clear_auth_cookies(
    response: Response | StarletteResponse,
) -> None:
    """Remove every auth cookie (logout)."""
    delete_kwargs = _cookie_delete_kwargs()
    csrf_delete_kwargs = _csrf_cookie_delete_kwargs()
    for name in AuthCookieName:
        if name == AuthCookieName.CSRF_TOKEN:
            response.delete_cookie(name, **csrf_delete_kwargs)
        else:
            response.delete_cookie(name, **delete_kwargs)
