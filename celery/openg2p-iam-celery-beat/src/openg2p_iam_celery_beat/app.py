# ruff: noqa: E402

from celery import Celery
from openg2p_fastapi_common.app import Initializer as BaseInitializer

from .config import Settings

_config = Settings.get_config()


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()


celery_app = Celery(
    "iam_celery_beat",
    broker=_config.celery_broker_url,
    backend=_config.celery_backend_url,
    include=["openg2p_iam_celery_beat.tasks"],
)
celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "provision_users_beat": {
        "task": "iam.provision_users_beat",
        "schedule": _config.provision_users_beat_seconds,
    },
}
