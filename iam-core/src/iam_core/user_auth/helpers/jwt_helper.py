import logging

from authlib.jose import JsonWebKey, JsonWebToken, jwt
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError

from iam_core.user_auth.config import Settings

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


def decode_jwt(
    token: str,
    jwks: dict,
    verify_exp: bool = True,
    nonce: str | None = None,
    access_token: str | None = None,
) -> dict:
    """Decode and validate a JWT using the given JWKS. Returns claims dict."""
    key_set = JsonWebKey.import_key_set(jwks)
    claims = jwt.decode(token, key_set, claims_params={"nonce": nonce})
    if verify_exp:
        claims.validate()
    claim_dict = dict(claims)
    if nonce and claim_dict.get("nonce") != nonce:
        raise UnauthorizedError("G2P-AUT-401", "Nonce mismatch")
    if access_token and claim_dict.get("at_hash") is None:
        _logger.debug("ID token missing at_hash while access_token is present.")
    return claim_dict


# Asymmetric algorithms only. A signed response is checked against the keys the
# provider publishes, so "none" and the HMAC family (where the "key" would have
# to be shared, or guessed) have no place here.
_SIGNED_RESPONSE_ALGORITHMS = [
    "RS256", "RS384", "RS512",
    "PS256", "PS384", "PS512",
    "ES256", "ES384", "ES512",
    "EdDSA",
]
_signed_response_jwt = JsonWebToken(_SIGNED_RESPONSE_ALGORITHMS)


def verify_signed_jwt(token: str, jwks: dict) -> dict:
    """Verify a signed provider response (e.g. a JWT userinfo) and return its claims.

    Unlike decode_jwt this expects no nonce: a userinfo response carries none.
    Any failure -- bad signature, unknown key, disallowed algorithm, expired --
    raises, because the caller would otherwise act on claims nobody vouched for.
    """
    try:
        claims = _signed_response_jwt.decode(token, JsonWebKey.import_key_set(jwks))
        claims.validate()
    except Exception as e:
        raise UnauthorizedError("G2P-AUT-401", "Signed response failed verification.") from e
    return dict(claims)
