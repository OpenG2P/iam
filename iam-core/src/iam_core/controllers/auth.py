"""Login routes shared by the staff and agency APIs. The application type selects the providers."""

from urllib.parse import urlencode

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from jose import jwt as jose_jwt
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import InternalServerError, UnauthorizedError

from iam_core.schemas import LoggedInUserResponse, LoginProviderHttpResponse, StartAuthTransactionResponse
from iam_core.services import AuthService, ProviderRepository
from iam_core.user_auth.decorators import requires_auth, requires_user
from iam_core.user_auth.helpers import AuthCookieName, clear_auth_cookies, cookie_name, set_auth_cookies
from iam_core.user_auth.oidc_client import OidcClient


class AuthController(BaseController):
    def __init__(self, application_type: str, **kwargs):
        super().__init__(**kwargs)
        self.application_type = application_type
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
        self.router.add_api_route(
            "/get_login_provider_redirect/{id}",
            self.get_login_provider_redirect,
            methods=["GET"],
        )
        self.router.add_api_route("/callback", self.oauth_callback, methods=["GET"])

    async def _provider_for_this_audience(self, provider_id: int):
        repository = self.provider_repository or ProviderRepository()
        provider = await repository.get_by_id(provider_id)
        if provider is None or getattr(provider, "application_type", None) != self.application_type:
            raise UnauthorizedError("G2P-AUT-401", "Invalid Login Provider Id")
        return provider

    @requires_auth
    async def get_user_profile(self, request: Request) -> dict:
        return request.state.auth.model_dump(exclude={"credentials"})

    @requires_user
    async def get_logged_in_user(self, request: Request) -> LoggedInUserResponse:
        return request.state.user

    @requires_auth
    async def logout(self, request: Request) -> RedirectResponse:
        session_id = request.cookies.get(cookie_name(AuthCookieName.SESSION))
        self.auth_service.delete_refresh_token(session_id)

        try:
            issuer = jose_jwt.get_unverified_claims(request.state.auth.credentials).get("iss")
        except Exception:
            issuer = None
        if not issuer:
            raise UnauthorizedError("G2P-AUT-401", "Invalid issuer")

        repository = self.provider_repository or ProviderRepository()
        login_provider = await repository.get_by_iss(issuer)
        if not login_provider or getattr(login_provider, "application_type", None) not in (
            None,
            self.application_type,
        ):
            raise UnauthorizedError("G2P-AUT-401", "Invalid issuer")

        redirect_uri = getattr(login_provider, "default_redirect_uri", None) or "/"
        metadata = await OidcClient().get_server_metadata(login_provider)
        logout_endpoint = metadata.get("end_session_endpoint")
        if not logout_endpoint:
            raise InternalServerError(
                "G2P-AUT-500",
                "Logout endpoint not available in provider metadata",
            )

        params = {"post_logout_redirect_uri": redirect_uri}
        id_token = request.cookies.get(cookie_name(AuthCookieName.ID_TOKEN))
        if id_token:
            params["id_token_hint"] = id_token
        if getattr(login_provider, "client_id", None):
            params["client_id"] = login_provider.client_id

        response = RedirectResponse(url=f"{logout_endpoint}?{urlencode(params)}")
        clear_auth_cookies(response)
        return response

    async def backchannel_logout(self, request: Request) -> Response:
        form = await request.form()
        logout_token = form.get("logout_token")
        if not logout_token:
            raise UnauthorizedError(message="Unauthorized. Missing logout_token.")
        await self.auth_service.handle_backchannel_logout(str(logout_token))
        return Response(status_code=200)

    async def get_login_providers(self) -> LoginProviderHttpResponse:
        return await self.auth_service.get_login_providers(self.application_type)

    async def start_authentication_transaction(
        self, id: int, redirect_uri: str = "/"
    ) -> StartAuthTransactionResponse:
        await self._provider_for_this_audience(id)
        return await self.auth_service.start_authentication_transaction(
            provider_id=id,
            redirect_uri=redirect_uri,
        )

    async def get_login_provider_redirect(self, id: int, redirect_uri: str = "/") -> RedirectResponse:
        await self._provider_for_this_audience(id)
        response = await self.auth_service.start_authentication_transaction(
            provider_id=id,
            redirect_uri=redirect_uri,
        )
        return RedirectResponse(response.redirectUrl)

    async def oauth_callback(self, request: Request) -> RedirectResponse:
        result = await self.auth_service.complete_authentication_transaction(
            state_value=request.query_params.get("state"),
            code=request.query_params.get("code"),
        )
        refresh_token = self.auth_service.store_refresh_token(token_response=result["token_response"])
        response = RedirectResponse(result["redirect_uri"])
        set_auth_cookies(response, result["token_response"], session_id=refresh_token.session_id)
        return response
