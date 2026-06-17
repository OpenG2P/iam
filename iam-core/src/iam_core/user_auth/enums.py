from enum import StrEnum


class EndpointMetadataKey(StrEnum):
    """Decorator metadata keys attached to route handlers."""

    REQUIRED_PERMISSIONS = "_required_permissions"
    REQUIRES_AUTH = "_requires_auth"
    REQUIRES_USER = "_requires_user"


class RequestStateKey(StrEnum):
    """``request.state`` keys populated by auth middleware."""

    AUTH = "auth"  # validated AuthPrincipal
    USER = "user"  # enriched profile when @requires_user
    PERMISSIONS = "permissions"  # resolved permission set for the request


class AuthCookieName(StrEnum):
    """Browser cookie names for auth state. Members are plain strings (``StrEnum``)."""

    ACCESS_TOKEN = "X-Access-Token"  # JWT access token; fallback when no Authorization header
    ID_TOKEN = "X-ID-Token"  # OIDC id token, paired with access token when present
    SESSION = "X-Session-Id"  # OIDC ``sid``; server-side key for silent token refresh
