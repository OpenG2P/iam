# ruff: noqa: E402

import asyncio

from .config import Settings

_config = Settings.get_config()

from iam_core.models import LoginProvider
from iam_core.user_auth.app import Initializer as AuthInitializer
from iam_core.user_auth.middleware import CsrfMiddleware, ValidateAndRefreshTokenMiddleware

from .controllers.auth_controller import AuthController
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
)


class Initializer(AuthInitializer):
    def initialize(self, **kwargs):
        super().initialize()

        self.return_app().add_middleware(ValidateAndRefreshTokenMiddleware)
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

        AuthController().post_init()

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            await LoginProvider.create_migrate()

        asyncio.run(migrate())
        DataLoader().load()
