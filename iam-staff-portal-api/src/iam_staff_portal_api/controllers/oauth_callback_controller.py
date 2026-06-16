from fastapi import Request
from fastapi.responses import RedirectResponse
from iam_core.services import AuthService
from iam_core.user_auth.helpers import set_auth_cookies
from openg2p_fastapi_common.controller import BaseController

from ..config import Settings

_config = Settings.get_config(strict=False)


class OAuthCallbackController(BaseController):
    """
    Controller for handling the OAuth callback endpoint, which completes the authentication transaction and sets the necessary cookies for authenticated sessions.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router.prefix += "/auth"
        self.router.tags += ["/auth"]
        self.auth_service = AuthService()

        self.router.add_api_route("/callback", self.oauth_callback, methods=["GET"])

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
