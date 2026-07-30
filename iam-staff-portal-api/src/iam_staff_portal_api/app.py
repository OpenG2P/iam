# ruff: noqa: E402

import asyncio


from .config import Settings

_config = Settings.get_config()

print("DB datasource:", _config.db_datasource)

from iam_core.models import LoginProvider
from iam_core.user_auth.app import Initializer as AuthInitializer
from iam_core.user_auth.middleware import (
    CsrfMiddleware,
    ResolvePermissionMiddleware,
    ValidateAndRefreshTokenMiddleware,
)
from .cache import init_cache
from .helpers.request_response_helper import RequestResponseHelper
from .services.application_access_service import ApplicationAccessService
from .services.applications_service import ApplicationsService
from .services.login_providers_service import LoginProvidersService

from .controllers import (
    ApplicationAccessController,
    ApplicationsController,
    AuthController,
    IdentityProviderController,
    LoginProvidersController,
    OAuthCallbackController,
    UserAccessController,
)
from .models import (
    StaffApplicationPermission,
    StaffPortalApplication,
    StaffRole,
    StaffRolePermission,
)
from .data import DataLoader

# Pre-login browser flows, server-to-server callbacks, and logout (cookies cleared on response).
IAM_STAFF_CSRF_EXCLUDED_PATHS = (
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
    "/user-access/get_permissions_for_roles",
    "/user-access/staff_portal_applications",
)


class Initializer(AuthInitializer):
    def initialize(self, **kwargs):
        super().initialize()

        # Middleware order (last added = outermost on inbound):
        # CSRF -> ValidateAndRefresh -> ResolvePermission -> app
        self.return_app().add_middleware(
            ResolvePermissionMiddleware,
            client_id=_config.keycloak_client_id,
            allow_by_default=True,
        )
        self.return_app().add_middleware(ValidateAndRefreshTokenMiddleware)
        self.return_app().add_middleware(
            CsrfMiddleware,
            enabled=_config.csrf_enabled,
            excluded_paths=IAM_STAFF_CSRF_EXCLUDED_PATHS,
        )

        init_cache()

        RequestResponseHelper()
        ApplicationsService()
        ApplicationAccessService()
        LoginProvidersService()

        AuthController().post_init()
        OAuthCallbackController().post_init()
        UserAccessController().post_init()
        IdentityProviderController().post_init()
        ApplicationsController().post_init()
        ApplicationAccessController().post_init()
        LoginProvidersController().post_init()

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            await LoginProvider.create_migrate()
            await StaffPortalApplication.create_migrate()
            await StaffApplicationPermission.create_migrate()
            await StaffRole.create_migrate()
            await StaffRolePermission.create_migrate()

        asyncio.run(migrate())
        DataLoader().load()
