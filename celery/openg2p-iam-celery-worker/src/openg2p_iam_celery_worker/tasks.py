from __future__ import annotations

import asyncio

import httpx
from openg2p_fastapi_common.context import get_async_session_maker
from openg2p_fastapi_common.errors.http_exceptions import BadRequestError

from iam_core.helpers.keycloak_admin import KeycloakAdmin, KeycloakAdminError
from iam_core.helpers.keycloak_admin_config import ProvisioningSettings
from iam_core.models.enum import ApplicationType, SyncStatus
from iam_core.models.user import User

from .app import celery_app


def keycloak_realm(realm: str, settings: ProvisioningSettings) -> str:
    if realm == ApplicationType.STAFF.value:
        return settings.staff_realm
    if realm == ApplicationType.AGENT.value:
        return settings.agent_realm
    if realm == ApplicationType.BENEFICIARY.value:
        return settings.beneficiary_realm
    raise BadRequestError(message="realm must be staff, agent, or beneficiary")


async def provision_user(session, admin: KeycloakAdmin, user_id: str) -> None:
    user = await session.get(User, user_id)
    if user is None:
        return
    if user.sync_status == SyncStatus.SYNCED.value and user.keycloak_user_id:
        return

    user.sync_error = None
    await session.flush()
    realm = keycloak_realm(user.realm, admin._settings)
    keycloak_id = user.keycloak_user_id
    try:
        async with httpx.AsyncClient(timeout=20) as http:
            group_id = None
            if user.agency_id:
                group_id = await admin.find_group_id(http, realm, user.agency_id)
                if not group_id:
                    user.sync_status = SyncStatus.FAILED.value
                    user.sync_error = "Agency group is missing"
                    await session.flush()
                    return
            keycloak_id = keycloak_id or await admin.find_user_id(http, realm, user.email)
            if not keycloak_id:
                keycloak_id = await admin.create_user(
                    http,
                    realm,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    agency_id=user.agency_id,
                )
            user.keycloak_user_id = keycloak_id
            if group_id:
                await admin.join_group(http, realm, keycloak_id, group_id)
            # Password email is off for now. The user is only created in Keycloak.
            # await admin.send_password_email(http, realm, keycloak_id)
    except KeycloakAdminError as exc:
        user.sync_status = SyncStatus.FAILED.value
        user.sync_error = str(exc)
        await session.flush()
        raise

    user.sync_status = SyncStatus.SYNCED.value
    user.sync_error = None
    await session.flush()


async def _provision_chunk(user_ids: list[str]) -> None:
    admin = KeycloakAdmin()
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        for user_id in user_ids:
            try:
                await provision_user(session, admin, user_id)
                await session.commit()
            except KeycloakAdminError:
                await session.commit()
            except Exception:
                await session.rollback()


@celery_app.task(name="iam.provision_iam_users", bind=True, max_retries=5)
def provision_iam_users(self, user_ids: list[str]) -> None:
    try:
        asyncio.run(_provision_chunk(user_ids))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30) from exc
