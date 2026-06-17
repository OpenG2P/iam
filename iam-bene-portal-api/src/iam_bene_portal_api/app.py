# ruff: noqa: E402

import asyncio

from .config import Settings

_config = Settings.get_config()

from iam_core.models import LoginProvider
from iam_core.user_auth.app import Initializer as AuthInitializer
from iam_core.user_auth.middleware import ValidateAndRefreshTokenMiddleware

from .controllers.auth_controller import AuthController


class Initializer(AuthInitializer):
    def initialize(self, **kwargs):
        super().initialize()

        self.return_app().add_middleware(ValidateAndRefreshTokenMiddleware)

        AuthController().post_init()

    def migrate_database(self, args):
        super().migrate_database(args)

        async def migrate():
            await LoginProvider.create_migrate()

        asyncio.run(migrate())
