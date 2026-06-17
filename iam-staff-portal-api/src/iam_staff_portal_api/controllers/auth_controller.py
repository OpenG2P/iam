from fastapi import Request, Response
from iam_core.schemas import LoggedInUserResponse, LoginProviderHttpResponse, StartAuthTransactionResponse
from iam_core.services import AuthService
from iam_core.user_auth.decorators import requires_auth, requires_user
from iam_core.user_auth.helpers import AuthCookieName, clear_auth_cookies
from openg2p_fastapi_common.controller import BaseController

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

    @requires_auth
    async def get_user_profile(self, request: Request):
        auth = request.state.auth
        return auth.model_dump(exclude={"credentials"})

    @requires_user
    async def get_logged_in_user(self, request: Request) -> LoggedInUserResponse:
        return request.state.user

    async def logout(self, request: Request, response: Response):
        session_id = request.cookies.get(AuthCookieName.SESSION)
        self.auth_service.delete_refresh_token(session_id)
        clear_auth_cookies(response)

    async def get_login_providers(self):
        return await self.auth_service.get_login_providers()

    async def start_authentication_transaction(self, id: int, redirect_uri: str = "/"):
        return await self.auth_service.start_authentication_transaction(
            provider_id=id,
            redirect_uri=redirect_uri,
        )
