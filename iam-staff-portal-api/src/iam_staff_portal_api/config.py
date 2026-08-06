from iam_core.user_auth.config import Settings as BaseSettings
from iam_core.user_auth.config import ApiAuthSettings

from pydantic import Field
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="iam_staff_",
        env_file=".env",
        extra="allow",
        env_nested_delimiter="__",
    )
    auth_api_get_staff_portal_applications: ApiAuthSettings = ApiAuthSettings(enabled=True)
    # Guards the self-registration write endpoint. Enabled by default so a valid
    # token from a trusted login provider is required. In production, tighten by
    # setting claim_name / claim_values (e.g. a mapped registrar role claim) via
    # IAM_STAFF_AUTH_API_REGISTER_STAFF_PORTAL_APPLICATION__* so only an
    # authorized service account can register applications.
    auth_api_register_staff_portal_application: ApiAuthSettings = ApiAuthSettings(enabled=True)
    data_application_urls: dict[str, str] = Field(
        default_factory=lambda: {
            "keycloak_application_url": "https://keycloak.openg2p.org",
            "registry_application_url": "https://registry.openg2p.org",
            "minio_application_url": "https://minio.openg2p.org",
            "superset_application_url": "https://superset.openg2p.org",
            "iam_staff_ui_application_url": "http://localhost:8035",
        }
    )
    data_client_secrets: dict[str, str] = Field(default_factory=dict)
    cache_expire_seconds: int = 7 * 24 * 60 * 60  # 7 days
    data_dir: str = "/opt/iam-staff-portal-data"
    # IAM staff-portal-api base URL for permission resolution (self-call).
    auth_provider_api_url: str | None = "http://localhost:8020"
    # Keycloak client_id / application mnemonic for iam-staff-ui permission checks.
    keycloak_client_id: str = "iam-staff-ui"
    # Keycloak admin API URL for role/client sync
    keycloak_admin_url: str | None = None
    keycloak_realm: str = "staff"
    # Default page size for list endpoints.
    default_page_size: int = 20
    # Registry API URL for data policy operations
    registry_api_url: str | None = None
    # Master data URL for data policy operations
    master_data_url: str | None = None
