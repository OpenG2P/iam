from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from openg2p_fastapi_common.controller import BaseController
from iam_core.schemas import LoginProviderHttpResponse, StartAuthTransactionResponse
from iam_core.services import AuthService
from iam_core.user_auth.decorators import requires_auth
from iam_core.user_auth.helpers import AuthCookieName, clear_auth_cookies, set_auth_cookies

from ..config import Settings

_config = Settings.get_config(strict=False)


class AuthController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router.prefix += "/auth"
        self.router.tags += ["auth"]
        self.auth_service = AuthService()

        self.router.add_api_route("/get_user_profile", self.get_user_profile, methods=["GET"])
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
        self.router.add_api_route(
            "/get_login_provider_redirect/{id}",
            self.get_login_provider_redirect,
            methods=["GET"],
        )
        self.router.add_api_route("/callback", self.oauth_callback, methods=["GET"])

    @requires_auth
    async def get_user_profile(self, request: Request):
        auth = request.state.auth
        return auth.model_dump(exclude={"credentials"})

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

    async def get_login_provider_redirect(self, id: int, redirect_uri: str = "/"):
        response = await self.auth_service.start_authentication_transaction(
            provider_id=id,
            redirect_uri=redirect_uri,
        )
        return RedirectResponse(response.redirectUrl)

    async def oauth_callback(self, request: Request):
        result = await self.auth_service.complete_authentication_transaction(
            state_value=request.query_params.get("state"),
            code=request.query_params.get("code"),
        )
        token_response = result["token_response"]
        redirect_uri = result["redirect_uri"]
        refresh_token = self.auth_service.store_refresh_token(
            token_response=token_response,
        )

        response = RedirectResponse(redirect_uri)
        set_auth_cookies(
            response,
            token_response,
            session_id=refresh_token.session_id,
        )
        return response
