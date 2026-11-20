from openg2p_fastapi_common.controller import BaseController

from iam_core.schemas.login_provider import LoginProviderByIssuerResponse
from iam_core.services import AuthService


class IdentityProviderController(BaseController):
    def __init__(self, application_type: str, **kwargs):
        super().__init__(**kwargs)
        self.application_type = application_type
        self.router.prefix += "/identity-providers"
        self.router.tags += ["/identity-providers"]
        self.auth_service = AuthService()
        self.router.add_api_route(
            "/get_provider_by_issuer",
            self.get_provider_by_issuer,
            methods=["GET"],
        )

    async def get_provider_by_issuer(self, issuer: str) -> LoginProviderByIssuerResponse:
        provider = await self.auth_service.get_provider_by_issuer(issuer, self.application_type)
        return LoginProviderByIssuerResponse(**provider)
