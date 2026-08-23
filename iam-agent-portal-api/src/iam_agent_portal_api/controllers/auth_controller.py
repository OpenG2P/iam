from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import RedirectResponse
from iam_core.schemas import LoggedInUserResponse, LoginProviderHttpResponse, StartAuthTransactionResponse
from iam_core.services import AuthService, ProviderRepository
from iam_core.user_auth.decorators import requires_auth, requires_user
from iam_core.user_auth.helpers import AuthCookieName, clear_auth_cookies, cookie_name, set_auth_cookies
from iam_core.user_auth.oidc_client import OidcClient
from jose import jwt as jose_jwt
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import InternalServerError, UnauthorizedError

from ..config import Settings

_config = Settings.get_config(strict=False)


class AuthController(BaseController):
    """Authentication endpoints for the agent portal.

    Deliberately the same surface as iam-staff-portal-api's AuthController: the
    agent portal UI is the staff portal UI pointed at a different realm and
    login provider, so its BFF calls the same routes with the same methods.
    Anything that differs here has to be special-cased there for no reason.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.provider_repository = ProviderRepository.get_component()
        self.router.prefix += "/auth"
        self.router.tags += ["auth"]
        self.auth_service = AuthService()

        self.router.add_api_route("/get_user_profile", self.get_user_profile, methods=["GET"])
        self.router.add_api_route(
            "/get_logged_in_user",
            self.get_logged_in_user,
            responses={200: {"model": LoggedInUserResponse}},
            methods=["GET"],
        )
        # GET, matching staff: this is a top-level browser navigation that ends
        # at the provider's end_session_endpoint, not an XHR.
        self.router.add_api_route("/logout", self.logout, methods=["GET"])
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

    @requires_user
    async def get_logged_in_user(self, request: Request) -> LoggedInUserResponse:
        return request.state.user

    @requires_auth
    async def logout(self, request: Request):
        session_id = request.cookies.get(cookie_name(AuthCookieName.SESSION))
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

        id_token = request.cookies.get(cookie_name(AuthCookieName.ID_TOKEN))

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
