from enum import StrEnum


class EndpointMetadataKey(StrEnum):
    """Decorator metadata keys attached to route handlers."""

    REQUIRED_PERMISSIONS = "_required_permissions"
    REQUIRES_AUTH = "_requires_auth"
    REQUIRES_USER = "_requires_user"
    DATA_POLICY = "_data_policy"


class RequestStateKey(StrEnum):
    """``request.state`` keys populated by auth middleware."""

    AUTH = "auth"  # validated AuthPrincipal
    USER = "user"  # enriched profile when @requires_user
    PERMISSIONS = "permissions"  # resolved permission set for the request


class AuthCookieName(StrEnum):
    """Browser cookie names for auth state. Members are plain strings (``StrEnum``).

    Use ``cookie_name()`` rather than a member directly: these are the BASE
    names, and a deployment may prefix them to keep portals apart.
    """

    ACCESS_TOKEN = "X-Access-Token"  # JWT access token; fallback when no Authorization header
    ID_TOKEN = "X-ID-Token"  # OIDC id token, paired with access token when present
    SESSION = "X-Session-Id"  # OIDC ``sid``; server-side key for silent token refresh
    CSRF_TOKEN = "X-CSRF-Token"  # Double-submit CSRF token; readable by JS (not httponly)


def cookie_name(name: AuthCookieName) -> str:
    """Return the cookie name for this deployment, with any prefix applied.

    Cookies are matched by DOMAIN, not by origin. Two portals sharing a parent
    auth_cookie_domain (e.g. `.example.org` for staff-iam.example.org and
    agent-iam.example.org) therefore both receive every cookie the other sets.
    With identical names the second login overwrites the first, and each
    portal's API is then handed the other's tokens -- the ID token especially,
    since it is read from a cookie while the access token comes from the
    Authorization header. The result is a token that cannot be verified against
    the receiving realm's JWKS.

    Set auth_cookie_prefix per portal to keep them independent. Default is
    empty, preserving the original names.
    """
    from iam_core.user_auth.config import Settings

    prefix = Settings.get_config(strict=False).auth_cookie_prefix or ""
    return f"{prefix}{name.value}" if prefix else name.value
