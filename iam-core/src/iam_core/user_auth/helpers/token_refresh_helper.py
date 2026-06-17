from datetime import datetime, timezone

from fastapi import Request
from jose import jwt as jose_jwt

from .cookie_helper import AUTH_ACCESS_TOKEN_COOKIE_NAME, AUTH_ID_TOKEN_COOKIE_NAME


def access_token_from_request(request: Request) -> str | None:
    jwt_token = request.headers.get("Authorization") or request.cookies.get(AUTH_ACCESS_TOKEN_COOKIE_NAME)
    if not jwt_token:
        return None
    return jwt_token.removeprefix("Bearer ").strip() or None


def is_access_token_expired(access_token: str) -> bool:
    try:
        claims = jose_jwt.get_unverified_claims(access_token)
    except Exception:
        return False
    exp = claims.get("exp")
    if exp is None:
        return False
    return datetime.now(tz=timezone.utc).timestamp() >= float(exp)


def apply_refreshed_tokens_to_request(request: Request, token_response: dict) -> None:
    access_token = token_response["access_token"]
    cookies = dict(request.cookies)
    cookies[AUTH_ACCESS_TOKEN_COOKIE_NAME] = access_token
    id_token = token_response.get("id_token")
    if id_token:
        cookies[AUTH_ID_TOKEN_COOKIE_NAME] = id_token

    cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
    headers = [(k, v) for k, v in request.scope["headers"] if k.lower() not in (b"cookie", b"authorization")]
    headers.append((b"authorization", f"Bearer {access_token}".encode("latin-1")))
    headers.append((b"cookie", cookie_header.encode("latin-1")))
    request.scope["headers"] = headers
    if hasattr(request, "_cookies"):
        delattr(request, "_cookies")
    if hasattr(request, "_headers"):
        delattr(request, "_headers")
