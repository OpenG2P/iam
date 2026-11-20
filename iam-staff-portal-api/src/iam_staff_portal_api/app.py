# ruff: noqa: E402

import asyncio


from .config import Settings

_config = Settings.get_config()

print("DB datasource:", _config.db_datasource)

from iam_core.models import DataPolicy, LoginProvider, User
from iam_core.models.enum import ApplicationType
from iam_core.user_auth.app import Initializer as AuthInitializer
from iam_core.user_auth.helpers.data_policy_role_helper import DP_ROLE_PREFIX
from iam_core.user_auth.middleware import CsrfMiddleware, ValidateAndRefreshTokenMiddleware
from iam_core.user_auth.middleware.data_policy import DataPolicyMiddleware
from iam_core.user_auth.middleware.resolve_permissions import ResolvePermissionMiddleware
from .cache import init_cache
from .helpers.request_response_helper import RequestResponseHelper
from .services.application_access_service import ApplicationAccessService
from .services.applications_service import ApplicationsService
from .services.login_providers_service import LoginProvidersService
from iam_core.controllers import AccessController, AuthController, IdentityProviderController
from iam_core.services.data_policy_service import DataPolicyService

from .controllers import (
    ApplicationAccessController,
    ApplicationsController,
    DataPolicyController,
    LoginProvidersController,
    UsersController,
    UserAccessController,
)
from iam_core.models import (
    ApplicationPermission,
    Application,
    Role,
    RolePermission,
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
    "/identity-providers/get_provider_by_issuer",
    "/user-access/get_permissions_for_roles",
    "/user-access/staff_portal_applications",
    "/data-policies/evaluate_expression",
)


class Initializer(AuthInitializer):
    def initialize(self, **kwargs):
        super().initialize()

        # Middleware order (last added = outermost on inbound):
        # CSRF -> ValidateAndRefresh -> DataPolicy -> ResolvePermission -> app
        self.return_app().add_middleware(
            ResolvePermissionMiddleware,
            permissions_api_url=_config.auth_provider_api_url,
            allow_by_default=True,
        )
        if _config.auth_provider_api_url:
            self.return_app().add_middleware(
                DataPolicyMiddleware,
                iam_api_url=_config.auth_provider_api_url,
                role_prefix=DP_ROLE_PREFIX,
            )
        self.return_app().add_middleware(
            ValidateAndRefreshTokenMiddleware,
            application_type=ApplicationType.STAFF.value,
        )
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
        DataPolicyService()

        AuthController(ApplicationType.STAFF.value).post_init()
        UserAccessController().post_init()
        IdentityProviderController(ApplicationType.STAFF.value).post_init()
        ApplicationsController().post_init()
        ApplicationAccessController().post_init()
        LoginProvidersController().post_init()
        DataPolicyController().post_init()
        AccessController().post_init()
        UsersController().post_init()

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            await LoginProvider.create_migrate()
            await DataPolicy.create_migrate()
            await Application.create_migrate()
            await ApplicationPermission.create_migrate()
            await Role.create_migrate()
            await RolePermission.create_migrate()
            await User.create_migrate()

        asyncio.run(migrate())
        DataLoader().load()
