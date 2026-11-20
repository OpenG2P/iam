"""Resolve active role mnemonics to permission mnemonics."""

from collections import defaultdict

from openg2p_fastapi_common.errors.http_exceptions import BadRequestError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from iam_core.models.application_permission import ApplicationPermission
from iam_core.models.application import Application
from iam_core.models.role import Role
from iam_core.models.role_permission import RolePermission


async def permissions_for_client_roles(
    session: AsyncSession,
    clients: list[tuple[str, list[str]]],
) -> list[str]:
    """Map every token client and its roles in one pass.

    A client that is not an application, such as ``realm-management`` or
    ``account``, is ignored. When the client is an application and a role from
    the token is not stored for it, that is an error. A role name matches only
    that application.
    """
    pairs = [
        (client_id, list(role_mnemonics))
        for client_id, role_mnemonics in clients
        if client_id and role_mnemonics
    ]
    if not pairs:
        return []

    applications = (
        (
            await session.execute(
                select(Application).where(
                    Application.application_mnemonic.in_([client_id for client_id, _ in pairs])
                )
            )
        )
        .scalars()
        .all()
    )
    by_mnemonic = {application.application_mnemonic: application for application in applications}
    known = [
        (by_mnemonic[client_id], role_mnemonics)
        for client_id, role_mnemonics in pairs
        if client_id in by_mnemonic
    ]
    if not known:
        return []

    roles = (
        (
            await session.execute(
                select(Role).where(
                    Role.application_id.in_([application.id for application, _ in known]),
                    Role.active == True,  # noqa: E712
                )
            )
        )
        .scalars()
        .all()
    )
    roles_by_application: dict[int, dict[str, Role]] = defaultdict(dict)
    for role in roles:
        roles_by_application[role.application_id][role.role_mnemonic] = role

    missing: list[str] = []
    role_ids: list[int] = []
    for application, role_mnemonics in known:
        stored = roles_by_application.get(application.id, {})
        for role_mnemonic in role_mnemonics:
            role = stored.get(role_mnemonic)
            if role is None:
                missing.append(f"{application.application_mnemonic}: {role_mnemonic}")
            else:
                role_ids.append(role.id)
    if missing:
        raise BadRequestError(
            message="Role is not defined for this application: " + ", ".join(sorted(missing))
        )
    if not role_ids:
        return []

    permission_ids = (
        (
            await session.execute(
                select(RolePermission.permission_id).where(
                    RolePermission.role_id.in_(role_ids),
                    RolePermission.active == True,  # noqa: E712
                )
            )
        )
        .scalars()
        .all()
    )
    if not permission_ids:
        return []

    mnemonics = (
        (
            await session.execute(
                select(ApplicationPermission.permission_mnemonic).where(
                    ApplicationPermission.id.in_(permission_ids),
                    ApplicationPermission.active == True,  # noqa: E712
                )
            )
        )
        .scalars()
        .all()
    )
    return sorted(set(mnemonics))
