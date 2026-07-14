from unittest.mock import patch

from iam_core.user_auth.app import Initializer


def test_initializer_registers_auth_components():
    init = Initializer.__new__(Initializer)

    with (
        patch("openg2p_fastapi_common.app.Initializer.initialize"),
        patch("iam_core.user_auth.app.OIDCBase") as oidc_base,
        patch("iam_core.user_auth.app.KeycloakAdapter") as keycloak_adapter,
        patch("iam_core.user_auth.app.EsignetAdapter") as esignet_adapter,
        patch("iam_core.user_auth.app.AdapterFactory") as adapter_factory,
        patch("iam_core.user_auth.app.ProviderRepository") as provider_repository,
        patch("iam_core.user_auth.app.AuthTransactionStore") as auth_transaction_store,
        patch("iam_core.user_auth.app.RedisAuthTransactionStore") as redis_auth_transaction_store,
        patch("iam_core.user_auth.app.RedisRefreshTokenStore") as redis_refresh_token_store,
        patch("iam_core.user_auth.app.TokenValidatorService") as token_validator_service,
        patch("iam_core.user_auth.app.JWTValidationHelper") as jwt_validation_helper,
    ):
        Initializer.initialize(init)

    oidc_base.assert_called_once()
    keycloak_adapter.assert_called_once()
    esignet_adapter.assert_called_once()
    adapter_factory.assert_called_once()
    provider_repository.assert_called_once()
    auth_transaction_store.assert_called_once()
    redis_auth_transaction_store.assert_called_once()
    redis_refresh_token_store.assert_called_once()
    token_validator_service.assert_called_once()
    jwt_validation_helper.assert_called_once()
