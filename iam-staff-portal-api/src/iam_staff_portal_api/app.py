# ruff: noqa: E402

import asyncio


from .config import Settings

_config = Settings.get_config()

print("DB datasource:", _config.db_datasource)

from iam_core.models import LoginProvider
from iam_core.user_auth.app import Initializer as AuthInitializer
from iam_core.user_auth.refresh_token_middleware import RefreshTokenMiddleware
from .cache import init_cache

from .controllers import (
    AuthController,
    IdentityProviderController,
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

STAFF_PORTAL_PROTECTED_ROUTE_NAMES = {
    "get_user_profile",
    "get_logged_in_user",
    "get_staff_portal_applications",
    "get_application_permissions_for_user",
}


class Initializer(AuthInitializer):
    def initialize(self, **kwargs):
        super().initialize()

        self.return_app().add_middleware(
            RefreshTokenMiddleware,
            protected_route_names=STAFF_PORTAL_PROTECTED_ROUTE_NAMES,
        )

        init_cache()

        AuthController().post_init()
        OAuthCallbackController().post_init()
        UserAccessController().post_init()
        IdentityProviderController().post_init()

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            await LoginProvider.create_migrate()
            await StaffPortalApplication.create_migrate()
            await StaffRole.create_migrate()
            await StaffApplicationPermission.create_migrate()
            await StaffRolePermission.create_migrate()

            await DataLoader.run()

        asyncio.run(migrate())
