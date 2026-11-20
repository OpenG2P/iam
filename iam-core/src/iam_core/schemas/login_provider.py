from pydantic import BaseModel


class LoginProviderResponse(BaseModel):
    id: int
    name: str
    protocol: str = "oidc"
    displayName: str | dict
    displayIconUrl: str


class LoginProviderHttpResponse(BaseModel):
    loginProviders: list[LoginProviderResponse]


class StartAuthTransactionResponse(BaseModel):
    redirectUrl: str
    state: str


class LoginProviderByIssuerResponse(BaseModel):
    id: int | None = None
    application_type: str | None = None
    issuer: str
    jwks_uri: str | None = None
    server_metadata_url: str | None = None
    audiences: str | None = None
    adapter_name: str | None = None
    token_endpoint_auth_method: str | None = None
    client_id: str | None = None
    authorization_endpoint: str | None = None
    token_endpoint: str | None = None
    userinfo_endpoint: str | None = None
    extra_authorize_params: str | None = None
