from iam_core.user_auth.config import Settings as BaseSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="iam_agent_",
        env_file=".env",
        extra="allow",
        env_nested_delimiter="__",
    )
    # Directory the chart mounts login_providers.json into; read once at
    # migrate time by the data loader.
    data_dir: str = "/opt/iam-agent-portal-data"
    # Maps a placeholder name in the mounted login_providers.json (e.g.
    # ``agent_portal_secret``) to the real Keycloak client secret, supplied via
    # IAM_AGENT_DATA_CLIENT_SECRETS__* so it stays out of values.yaml.
    data_client_secrets: dict[str, str] = Field(default_factory=dict)
