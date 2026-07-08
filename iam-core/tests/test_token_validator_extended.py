import types
from unittest.mock import AsyncMock

import pytest
from authlib.jose.errors import JoseError
from jose import jwt as jose_jwt
from openg2p_fastapi_common.errors.http_exceptions import ForbiddenError, UnauthorizedError

from iam_core.services.token_validator_service import TokenValidatorService
from iam_core.user_auth.config import ApiAuthSettings
from iam_core.user_auth.errors import ExpiredTokenError
from helpers import fake_jwt


def _validator_with_adapter(adapter, provider=None):
    validator = TokenValidatorService()

    async def mock_provider(_iss):
        return provider or types.SimpleNamespace(
            issuer="https://issuer",
            audiences_list=["portal"],
        )

    validator._get_login_provider_db_by_iss = mock_provider
    validator._adapters = types.SimpleNamespace(resolve_for_provider=lambda _lp: adapter)
    return validator


@pytest.mark.asyncio
async def test_token_validator_introspection_only_mode():
    token = jose_jwt.encode(
        {"iss": "https://issuer", "aud": "portal", "sub": "u-1"}, "secret", algorithm="HS256"
    )
    adapter = types.SimpleNamespace(
        introspect_token=AsyncMock(return_value={"active": True, "sub": "u-1"}),
        decode_access_token=AsyncMock(),
        decode_id_token=AsyncMock(),
        normalize_claims=lambda claims, **_: claims,
        validate_claims=lambda *_a, **_k: None,
    )
    validator = _validator_with_adapter(adapter)

    result = await validator.validate(
        jwt_token=token,
        jwt_id_token=None,
        api_auth_settings=ApiAuthSettings(enabled=True, validation_mode="introspection"),
    )
    assert result.sub == "u-1"
    adapter.decode_access_token.assert_not_called()


@pytest.mark.asyncio
async def test_token_validator_unknown_issuer_and_bad_jwt():
    validator = TokenValidatorService()
    validator._get_login_provider_db_by_iss = AsyncMock(return_value=None)
    token = fake_jwt({"iss": "https://unknown", "sub": "u"})

    with pytest.raises(UnauthorizedError, match="Unknown Issuer"):
        await validator.validate(token, None, ApiAuthSettings(enabled=True))

    with pytest.raises(UnauthorizedError, match="Jwt expired"):
        await validator.validate("not-a-jwt", None, ApiAuthSettings(enabled=True))


@pytest.mark.asyncio
async def test_token_validator_iss_aud_validation():
    token = jose_jwt.encode(
        {"iss": "https://wrong", "aud": "portal", "sub": "u"}, "secret", algorithm="HS256"
    )
    adapter = types.SimpleNamespace(
        introspect_token=AsyncMock(),
        decode_access_token=AsyncMock(return_value={"sub": "u"}),
        decode_id_token=AsyncMock(),
        normalize_claims=lambda claims, **_: claims,
        validate_claims=lambda *_a, **_k: None,
    )
    provider = types.SimpleNamespace(issuer="https://issuer", audiences_list=["portal"])
    validator = _validator_with_adapter(adapter, provider)

    with pytest.raises(UnauthorizedError, match="Unknown Issuer"):
        await validator.validate(token, None, ApiAuthSettings(enabled=True, validation_mode="jwt"))

    token = jose_jwt.encode(
        {"iss": "https://issuer", "aud": "wrong", "sub": "u"}, "secret", algorithm="HS256"
    )
    with pytest.raises(UnauthorizedError, match="Unknown Audience"):
        await validator.validate(token, None, ApiAuthSettings(enabled=True, validation_mode="jwt"))


@pytest.mark.asyncio
async def test_token_validator_id_token_paths():
    access = jose_jwt.encode(
        {"iss": "https://issuer", "aud": "portal", "sub": "u"}, "secret", algorithm="HS256"
    )
    id_token = jose_jwt.encode(
        {"iss": "https://issuer", "aud": "portal", "sub": "u"}, "secret", algorithm="HS256"
    )

    adapter = types.SimpleNamespace(
        introspect_token=AsyncMock(),
        decode_access_token=AsyncMock(return_value={"sub": "u", "iss": "https://issuer"}),
        decode_id_token=AsyncMock(return_value={"sub": "u", "email": "a@b.c"}),
        normalize_claims=lambda claims, **_: claims,
        validate_claims=lambda *_a, **_k: None,
    )
    validator = _validator_with_adapter(adapter)
    result = await validator.validate(
        access,
        id_token,
        ApiAuthSettings(enabled=True, validation_mode="jwt"),
    )
    assert result.email == "a@b.c"

    from authlib.jose.errors import ExpiredTokenError as JoseExpiredTokenError

    adapter.decode_id_token = AsyncMock(side_effect=JoseExpiredTokenError())
    with pytest.raises(ExpiredTokenError, match="ID token expired"):
        await validator.validate(access, id_token, ApiAuthSettings(enabled=True, validation_mode="jwt"))

    adapter.decode_id_token = AsyncMock(side_effect=JoseError("bad"))
    with pytest.raises(UnauthorizedError, match="Invalid Jwt ID Token"):
        await validator.validate(access, id_token, ApiAuthSettings(enabled=True, validation_mode="jwt"))


@pytest.mark.asyncio
async def test_token_validator_claim_route_validation_branches():
    token = jose_jwt.encode(
        {"iss": "https://issuer", "aud": "portal", "sub": "u"}, "secret", algorithm="HS256"
    )
    adapter = types.SimpleNamespace(
        introspect_token=AsyncMock(),
        decode_access_token=AsyncMock(return_value={"sub": "u", "roles": ["staff"]}),
        decode_id_token=AsyncMock(),
        normalize_claims=lambda claims, **_: claims,
        validate_claims=lambda *_a, **_k: None,
    )
    validator = _validator_with_adapter(adapter)

    with pytest.raises(ForbiddenError, match="Claim\\(s\\) missing"):
        await validator.validate(
            token,
            None,
            ApiAuthSettings(
                enabled=True, validation_mode="jwt", claim_name="department", claim_values=["hr"]
            ),
        )

    with pytest.raises(ForbiddenError, match="don't match"):
        await validator.validate(
            token,
            None,
            ApiAuthSettings(enabled=True, validation_mode="jwt", claim_name="roles", claim_values=["agent"]),
        )

    with pytest.raises(ForbiddenError, match="don't match"):
        await validator.validate(
            token,
            None,
            ApiAuthSettings(
                enabled=True,
                validation_mode="jwt",
                claim_name="roles",
                claim_values=["staff", "agent"],
            ),
        )


@pytest.mark.asyncio
async def test_token_validator_adapter_validate_claims_failure():
    token = jose_jwt.encode(
        {"iss": "https://issuer", "aud": "portal", "sub": "u"}, "secret", algorithm="HS256"
    )
    adapter = types.SimpleNamespace(
        introspect_token=AsyncMock(),
        decode_access_token=AsyncMock(return_value={"sub": "u"}),
        decode_id_token=AsyncMock(),
        normalize_claims=lambda claims, **_: claims,
        validate_claims=lambda *_a, **_k: (_ for _ in ()).throw(ValueError("bad claims")),
    )
    validator = _validator_with_adapter(adapter)

    with pytest.raises(UnauthorizedError, match="bad claims"):
        await validator.validate(token, None, ApiAuthSettings(enabled=True, validation_mode="jwt"))


def test_token_validator_static_helpers():
    provider = types.SimpleNamespace(issuer="https://issuer", audiences_list=[])
    TokenValidatorService._validate_iss_aud({"iss": "https://issuer"}, provider)

    provider.audiences_list = ["portal"]
    TokenValidatorService._validate_iss_aud({"iss": "https://issuer", "aud": ["portal", "other"]}, provider)

    with pytest.raises(UnauthorizedError):
        TokenValidatorService._validate_iss_aud({"iss": "https://issuer", "aud": "wrong"}, provider)

    TokenValidatorService._validate_route_claims(
        {"roles": "admin"}, ApiAuthSettings(claim_name="roles", claim_values=["admin"])
    )
    with pytest.raises(ForbiddenError, match="doesn't match"):
        TokenValidatorService._validate_route_claims(
            {"roles": "viewer"},
            ApiAuthSettings(claim_name="roles", claim_values=["admin"]),
        )
    assert TokenValidatorService._combine_claims(None, {"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


@pytest.mark.asyncio
async def test_token_validator_get_login_provider_db_by_iss():
    from helpers import make_login_provider

    validator = TokenValidatorService()
    lp = make_login_provider()
    validator._providers = types.SimpleNamespace(get_by_iss=AsyncMock(return_value=lp))
    result = await validator._get_login_provider_db_by_iss(lp.issuer)
    assert result is lp
