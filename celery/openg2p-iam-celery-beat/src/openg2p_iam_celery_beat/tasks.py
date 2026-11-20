"""Pick pending users and hand one chunk to the worker."""

import asyncio

from sqlalchemy import select

from iam_core.models.enum import SyncStatus
from iam_core.models.user import User
from openg2p_fastapi_common.context import get_async_session_maker

from .app import celery_app
from .config import Settings

_config = Settings.get_config()


async def _claim_pending() -> list[str]:
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        rows = (
            await session.scalars(
                select(User)
                .where(User.sync_status == SyncStatus.PENDING.value)
                .order_by(User.id.asc())
                .limit(_config.provision_users_batch_size)
            )
        ).all()
        for user in rows:
            user.sync_status = SyncStatus.SYNCING.value
        await session.commit()
        return [user.id for user in rows]


@celery_app.task(name="iam.provision_users_beat")
def provision_users_beat() -> None:
    user_ids = asyncio.run(_claim_pending())
    if not user_ids:
        return
    celery_app.send_task(
        "iam.provision_iam_users",
        args=[user_ids],
        queue=_config.worker_queue,
    )
