# ruff: noqa: E402

import asyncio

from .config import Settings

_config = Settings.get_config()

from iam_core.controllers import AccessController, AuthController, IdentityProviderController
from iam_core.models.enum import ApplicationType
from iam_core.services.data_policy_service import DataPolicyService
from iam_core.models import LoginProvider
from iam_core.user_auth.app import Initializer as AuthInitializer
from iam_core.user_auth.helpers.data_policy_role_helper import AGC_ROLE_PREFIX
from iam_core.user_auth.middleware import CsrfMiddleware
from iam_core.user_auth.middleware.data_policy import DataPolicyMiddleware
from iam_core.user_auth.middleware.resolve_permissions import ResolvePermissionMiddleware

from .helpers.token import AgentTokenMiddleware
from .controllers.policies import PoliciesController
from .controllers.users import UsersController
from .data import DataLoader

# Endpoints that cannot present a double-submit token, mirroring the staff
# portal's list: the OIDC callback arrives from Keycloak, and logout/transaction
# start are reached before a CSRF cookie is in play. Every other state-changing
# route is protected by default, so a route added later is covered unless it is
# deliberately listed here.
IAM_AGENT_CSRF_EXCLUDED_PATHS = (
    "/ping",
    "/openapi.json",
    "/docs",
    "/redoc",
    "/docs/oauth2-redirect",
    "/auth/callback",
    "/auth/get_login_providers",
    "/auth/start_authentication_transaction",
    "/auth/logout",
    "/auth/backchannel-logout",
    "/identity-providers/get_provider_by_issuer",
    "/data-policies/evaluate_expression",
    "/user-access/get_permissions_for_roles",
)


class Initializer(AuthInitializer):
    def initialize(self, **kwargs):
        super().initialize()

        if _config.agent_api_url:
            self.return_app().add_middleware(
                ResolvePermissionMiddleware,
                permissions_api_url=_config.agent_api_url,
            )
            self.return_app().add_middleware(
                DataPolicyMiddleware,
                iam_api_url=_config.agent_api_url,
                role_prefix=AGC_ROLE_PREFIX,
            )
        self.return_app().add_middleware(
            AgentTokenMiddleware,
        )
        # Registered AFTER ValidateAndRefreshTokenMiddleware so it runs FIRST on
        # inbound requests -- same ordering as the staff portal. Without this the
        # chart's IAM_AGENT_CSRF_ENABLED was inert: it was read into config and
        # nothing consumed it, so the setting claimed a protection the service
        # did not apply.
        self.return_app().add_middleware(
            CsrfMiddleware,
            enabled=_config.csrf_enabled,
            excluded_paths=IAM_AGENT_CSRF_EXCLUDED_PATHS,
        )

        DataPolicyService()
        AuthController(ApplicationType.AGENT.value).post_init()
        IdentityProviderController(ApplicationType.AGENT.value).post_init()
        UsersController().post_init()
        PoliciesController().post_init()
        AccessController().post_init()

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            await LoginProvider.create_migrate()

        asyncio.run(migrate())
        DataLoader().load()
