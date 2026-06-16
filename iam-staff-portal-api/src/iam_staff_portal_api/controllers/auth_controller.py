from typing import Annotated

from fastapi import Depends, Request, Response
from openg2p_fastapi_common.controller import BaseController
from iam_core.schemas import (
    AuthPrincipal,
    LoginProviderHttpResponse,
    LoggedInUserResponse,
    StartAuthTransactionResponse,
)
from iam_core.services import AuthService
from iam_core.user_auth.dependencies import (
    auth_principal,
    logged_in_user,
    require_auth,
)
from iam_core.user_auth.helpers import AUTH_SESSION_COOKIE_NAME, clear_auth_cookies

from ..config import Settings

_config = Settings.get_config(strict=False)


class AuthController(BaseController):
    """
    Controller for authentication-related endpoints, such as retrieving user profile information and handling login/logout.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router.prefix += "/auth"
        self.router.tags += ["/auth"]
        self.auth_service = AuthService()

        self.router.add_api_route("/get_user_profile", self.get_user_profile, methods=["GET"])
        self.router.add_api_route(
            "/get_logged_in_user",
            self.get_logged_in_user,
            responses={200: {"model": LoggedInUserResponse}},
            methods=["GET"],
        )
        self.router.add_api_route("/logout", self.logout, methods=["POST"])
        self.router.add_api_route(
            "/get_login_providers",
            self.get_login_providers,
            responses={200: {"model": LoginProviderHttpResponse}},
            methods=["GET"],
        )
        self.router.add_api_route(
            "/start_authentication_transaction",
            self.start_authentication_transaction,
            responses={200: {"model": StartAuthTransactionResponse}},
            methods=["POST"],
        )

    async def get_user_profile(
        self,
        auth: Annotated[
            AuthPrincipal,
            Depends(require_auth(auth_principal)),
        ],
    ):
        return auth.model_dump(exclude={"credentials"})

    async def get_logged_in_user(
        self,
        user: Annotated[
            LoggedInUserResponse,
            Depends(logged_in_user),
        ],
    ) -> LoggedInUserResponse:
        return user

    async def logout(self, request: Request, response: Response):
        session_id = request.cookies.get(AUTH_SESSION_COOKIE_NAME)
        self.auth_service.delete_refresh_token(session_id)
        clear_auth_cookies(response)

    async def get_login_providers(self):
        return await self.auth_service.get_login_providers()

    async def start_authentication_transaction(self, id: int, redirect_uri: str = "/"):
        return await self.auth_service.start_authentication_transaction(
            provider_id=id,
            redirect_uri=redirect_uri,
        )
