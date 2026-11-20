"""Save users. Keycloak provisioning is done by the Celery worker."""

from __future__ import annotations

import re

from openg2p_fastapi_common.errors.http_exceptions import BadRequestError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from iam_core.models.enum import ApplicationType, SyncStatus
from iam_core.models.user import User

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(email: str) -> str:
    cleaned = email.strip().lower()
    if not _EMAIL.match(cleaned):
        raise BadRequestError(message="A valid email is required")
    return cleaned


class UserService:
    async def create_user(
        self,
        session: AsyncSession,
        *,
        realm: str,
        email: str,
        first_name: str,
        last_name: str,
        agency_id: str | None = None,
        is_agency_admin: bool = False,
    ) -> User:
        if realm not in {item.value for item in ApplicationType}:
            raise BadRequestError(message="realm must be staff, agent, or beneficiary")
        if not first_name.strip() or not last_name.strip():
            raise BadRequestError(message="First name and last name are required")
        cleaned_email = _normalize_email(email)
        if realm == ApplicationType.AGENT.value and not agency_id:
            raise BadRequestError(message="An agent user requires an agency")
        if realm != ApplicationType.AGENT.value and agency_id:
            raise BadRequestError(message="Only an agent user belongs to an agency")

        existing = await session.scalar(
            select(User).where(
                User.realm == realm,
                func.lower(User.email) == cleaned_email,
            )
        )
        if existing is not None:
            raise BadRequestError(message="A user with this email already exists")

        user = User(
            realm=realm,
            email=cleaned_email,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            agency_id=agency_id,
            is_agency_admin=is_agency_admin,
            sync_status=SyncStatus.PENDING.value,
        )
        session.add(user)
        await session.flush()
        return user

    async def list_for_agency(self, session: AsyncSession, agency_id: str) -> list[User]:
        rows = await session.scalars(
            select(User)
            .where(
                User.realm == ApplicationType.AGENT.value,
                User.agency_id == agency_id,
            )
            .order_by(User.email.asc())
        )
        return list(rows)

    async def agency_admin(self, session: AsyncSession, agency_id: str) -> User | None:
        return await session.scalar(
            select(User).where(
                User.realm == ApplicationType.AGENT.value,
                User.agency_id == agency_id,
                User.is_agency_admin == True,  # noqa: E712
            )
        )
