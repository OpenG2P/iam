from urllib.parse import urlencode

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from iam_core.schemas import LoggedInUserResponse, LoginProviderHttpResponse, StartAuthTransactionResponse
from iam_core.services import AuthService, ProviderRepository
from iam_core.user_auth.decorators import requires_auth, requires_user
from iam_core.user_auth.helpers import AuthCookieName, clear_auth_cookies
from iam_core.user_auth.oidc_client import OidcClient
from jose import jwt as jose_jwt
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import InternalServerError, UnauthorizedError

from ..config import Settings

_config = Settings.get_config(strict=False)


class AuthController(BaseController):
    """
    Controller for authentication-related endpoints, such as retrieving user profile information and handling login/logout.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.provider_repository = ProviderRepository.get_component()
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
        self.router.add_api_route("/logout", self.logout, methods=["GET"])
        self.router.add_api_route("/backchannel-logout", self.backchannel_logout, methods=["POST"])
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

    @requires_auth
    async def logout(self, request: Request):
        session_id = request.cookies.get(AuthCookieName.SESSION)
        self.auth_service.delete_refresh_token(session_id)

        auth = request.state.auth
        try:
            issuer = jose_jwt.get_unverified_claims(auth.credentials).get("iss")
        except Exception:
            issuer = None
        if not issuer:
            raise UnauthorizedError("G2P-AUT-401", "Invalid issuer")

        provider_repository = self.provider_repository or ProviderRepository()
        login_provider = await provider_repository.get_by_iss(issuer)
        if not login_provider:
            raise UnauthorizedError("G2P-AUT-401", "Invalid issuer")

        redirect_uri = getattr(login_provider, "default_redirect_uri", None) or "/"

        oidc_client = OidcClient()
        metadata = await oidc_client.get_server_metadata(login_provider)

        logout_endpoint = metadata.get("end_session_endpoint")
        if not logout_endpoint:
            raise InternalServerError(
                "G2P-AUT-500",
                "Logout endpoint not available in provider metadata",
            )

        id_token = request.cookies.get(AuthCookieName.ID_TOKEN)

        params = {
            "post_logout_redirect_uri": redirect_uri,
        }
        if id_token:
            params["id_token_hint"] = id_token
        if getattr(login_provider, "client_id", None):
            params["client_id"] = login_provider.client_id

        response = RedirectResponse(url=f"{logout_endpoint}?{urlencode(params)}")
        clear_auth_cookies(response)
        return response

    async def backchannel_logout(self, request: Request):
        form = await request.form()
        logout_token = form.get("logout_token")
        if not logout_token:
            raise UnauthorizedError(message="Unauthorized. Missing logout_token.")

        await self.auth_service.handle_backchannel_logout(str(logout_token))
        return Response(status_code=200)

    async def get_login_providers(self):
        return await self.auth_service.get_login_providers()

    async def start_authentication_transaction(self, id: int, redirect_uri: str = "/"):
        return await self.auth_service.start_authentication_transaction(
            provider_id=id,
            redirect_uri=redirect_uri,
        )
