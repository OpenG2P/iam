from pydantic_settings import BaseSettings, SettingsConfigDict


class ProvisioningSettings(BaseSettings):
    """Service-account access used to administer both Keycloak realms.

    The same client id and secret must exist in the staff realm and the agent
    realm. Each client needs realm-management roles for the realm it lives in.
    """

    model_config = SettingsConfigDict(
        env_prefix="iam_provision_",
        extra="ignore",
    )

    keycloak_admin_url: str | None = None
    keycloak_admin_client_id: str | None = None
    keycloak_admin_client_secret: str | None = None
    staff_realm: str = "staff"
    agent_realm: str = "agent"
    beneficiary_realm: str = "beneficiary"
    # Public client the action-email link should return the person to.
    action_email_client_id: str | None = None
    action_email_redirect_uri: str | None = None
    action_email_lifespan_seconds: int = 60 * 60 * 12

    @property
    def is_configured(self) -> bool:
        return bool(
            self.keycloak_admin_url and self.keycloak_admin_client_id and self.keycloak_admin_client_secret
        )
