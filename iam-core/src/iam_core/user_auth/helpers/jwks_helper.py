import logging

import httpx
from fastapi_cache.coder import PickleCoder
from fastapi_cache.decorator import cache
from openg2p_fastapi_common.errors.http_exceptions import InternalServerError

from iam_core.user_auth.config import Settings

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


def _jwks_key_builder(func, namespace: str, *args, **kwargs) -> str:
    """Cache by issuer (same as the old ContextVar), falling back to jwks_uri."""
    call_args = kwargs.get("args") or ()
    call_kwargs = kwargs.get("kwargs") or {}
    metadata = call_args[0] if call_args else call_kwargs.get("metadata") or {}
    if len(call_args) > 1:
        issuer = call_args[1]
    else:
        issuer = call_kwargs.get("issuer")
    jwks_uri = metadata.get("jwks_uri") if isinstance(metadata, dict) else None
    return f"{namespace}:jwks:{issuer or jwks_uri or 'missing'}"


@cache(
    expire=_config.auth_jwks_cache_ttl_seconds,
    key_builder=_jwks_key_builder,
    coder=PickleCoder,
)
async def get_jwks(metadata: dict, issuer: str | None = None) -> dict:
    """Fetch JWKS for the given OIDC metadata. Cached process-wide by issuer."""
    jwks_url = metadata.get("jwks_uri")
    if not jwks_url and issuer:
        jwks_url = f"{issuer.rstrip('/')}/.well-known/jwks.json"
    if not jwks_url:
        raise InternalServerError(
            code="G2P-AUT-500",
            message="Missing jwks_uri for provider.",
        )

    async with httpx.AsyncClient(verify=_config.auth_verify_ssl, timeout=10) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        return response.json()
