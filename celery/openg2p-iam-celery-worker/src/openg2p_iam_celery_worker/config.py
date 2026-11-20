from iam_core.user_auth.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="iam_celery_", extra="ignore")

    openapi_title: str = "OpenG2P IAM Celery Worker"
    openapi_version: str = __version__

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_backend_url: str = "redis://localhost:6379/0"
    worker_queue: str = "iam_celery"
