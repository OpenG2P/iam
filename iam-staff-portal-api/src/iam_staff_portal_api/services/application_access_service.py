from __future__ import annotations

import logging

from openg2p_fastapi_common.context import get_async_session_maker
from openg2p_fastapi_common.errors.http_exceptions import BadRequestError, NotFoundError
from openg2p_fastapi_common.service import BaseService
from sqlalchemy import delete, select

from ..helpers.query_helper import dt_iso, paginate
from ..helpers.keycloak_helper import KeycloakHelper
from ..models import (
    StaffApplicationPermission,
    StaffPortalApplication,
    StaffRole,
    StaffRolePermission,
)
from ..schemas import (
    ApplicationScopedPayload,
    PermissionCreatePayload,
    PermissionData,
    PermissionDeletePayload,
    RoleCreatePayload,
    RoleData,
    RoleDeletePayload,
    RolePermissionCreatePayload,
    RolePermissionData,
    RolePermissionDeletePayload,
    RolePermissionListPayload,
)


_logger = logging.getLogger("iam-application-access-service")


class ApplicationAccessService(BaseService):
    async def _get_application(self, session, application_id: int) -> StaffPortalApplication:
        app = await session.get(StaffPortalApplication, application_id)
        if app is None:
            raise NotFoundError(message="Application not found")
        return app

    def _role_data(self, role: StaffRole) -> RoleData:
        return RoleData(
            id=role.id,
            role_mnemonic=role.role_mnemonic,
            role_description=role.role_description,
            application_id=role.application_id,
            active=bool(role.active),
            created_at=dt_iso(role.created_at),
            updated_at=dt_iso(role.updated_at),
        )

    def _perm_data(self, perm: StaffApplicationPermission) -> PermissionData:
        return PermissionData(
            id=perm.id,
            permission_mnemonic=perm.permission_mnemonic,
            permission_description=perm.permission_description,
            application_id=perm.application_id,
            active=bool(perm.active),
            created_at=dt_iso(perm.created_at),
            updated_at=dt_iso(perm.updated_at),
        )

    async def get_roles(
        self, payload: ApplicationScopedPayload, page: int, page_size: int
    ) -> tuple[list[RoleData], int]:
        async_session = get_async_session_maker()
        async with async_session() as session:
            await self._get_application(session, payload.application_id)
            stmt = (
                select(StaffRole)
                .where(
                    StaffRole.application_id == payload.application_id, ~StaffRole.role_mnemonic.like("DP_%")
                )
                .order_by(StaffRole.id.desc())
            )
            rows, total = await paginate(session, stmt, page=page, page_size=page_size)
            return [self._role_data(r) for r in rows], total

    async def create_role(self, payload: RoleCreatePayload, auth_token: str = "") -> RoleData:
        mnemonic = payload.role_mnemonic.strip()
        if not mnemonic:
            raise BadRequestError(message="role_mnemonic is required")
        async_session = get_async_session_maker()
        async with async_session() as session:
            await self._get_application(session, payload.application_id)
            existing = (
                (
                    await session.execute(
                        select(StaffRole).where(
                            StaffRole.application_id == payload.application_id,
                            StaffRole.role_mnemonic == mnemonic,
                        )
                    )
                )
                .scalars()
                .first()
            )
            if existing is not None:
                raise BadRequestError(message=f"Role '{mnemonic}' already exists")
            role = StaffRole(
                application_id=payload.application_id,
                role_mnemonic=mnemonic,
                role_description=payload.role_description,
                active=True,
            )
            session.add(role)
            await session.flush()
            await session.refresh(role)

            # Sync to Keycloak before commit
            if auth_token:
                try:
                    kc_helper = KeycloakHelper(auth_token)
                    app = await self._get_application(session, payload.application_id)
                    role_name, already_existed = await kc_helper.create_role(
                        mnemonic,
                        app.application_mnemonic,
                        role_description=payload.role_description,
                    )
                    if already_existed:
                        await session.rollback()
                        raise BadRequestError(message=f"Role '{mnemonic}' already exists in Keycloak")
                except Exception as e:
                    await session.rollback()
                    raise BadRequestError(message=f"Failed to sync role to Keycloak: {e}")

            await session.commit()
            await session.refresh(role)
            return self._role_data(role)

    async def delete_role(self, payload: RoleDeletePayload, auth_token: str = "") -> RoleData:
        async_session = get_async_session_maker()
        async with async_session() as session:
            await self._get_application(session, payload.application_id)
            role = await session.get(StaffRole, payload.id)
            if role is None or role.application_id != payload.application_id:
                raise NotFoundError(message="Role not found")
            role_data = self._role_data(role)
            app = await self._get_application(session, payload.application_id)

            # Delete from Keycloak before database commit
            if auth_token:
                try:
                    kc_helper = KeycloakHelper(auth_token)
                    await kc_helper.delete_role(role_data.role_mnemonic, app.application_mnemonic)
                    # If role not found in Keycloak, still proceed with IAM delete (Keycloak is source of truth)
                except Exception as e:
                    raise BadRequestError(message=f"Failed to delete role from Keycloak: {e}")

            await session.execute(delete(StaffRolePermission).where(StaffRolePermission.role_id == role.id))
            await session.delete(role)
            await session.commit()
        return role_data

    async def get_permissions(
        self, payload: ApplicationScopedPayload, page: int, page_size: int
    ) -> tuple[list[PermissionData], int]:
        async_session = get_async_session_maker()
        async with async_session() as session:
            await self._get_application(session, payload.application_id)
            stmt = (
                select(StaffApplicationPermission)
                .where(StaffApplicationPermission.application_id == payload.application_id)
                .order_by(StaffApplicationPermission.id.desc())
            )
            rows, total = await paginate(session, stmt, page=page, page_size=page_size)
            return [self._perm_data(r) for r in rows], total

    async def create_permission(self, payload: PermissionCreatePayload) -> PermissionData:
        mnemonic = payload.permission_mnemonic.strip()
        if not mnemonic:
            raise BadRequestError(message="permission_mnemonic is required")
        async_session = get_async_session_maker()
        async with async_session() as session:
            await self._get_application(session, payload.application_id)
            existing = (
                (
                    await session.execute(
                        select(StaffApplicationPermission).where(
                            StaffApplicationPermission.application_id == payload.application_id,
                            StaffApplicationPermission.permission_mnemonic == mnemonic,
                        )
                    )
                )
                .scalars()
                .first()
            )
            if existing is not None:
                raise BadRequestError(message=f"Permission '{mnemonic}' already exists")
            perm = StaffApplicationPermission(
                application_id=payload.application_id,
                permission_mnemonic=mnemonic,
                permission_description=payload.permission_description or mnemonic,
                active=True,
            )
            session.add(perm)
            await session.commit()
            await session.refresh(perm)
            return self._perm_data(perm)

    async def delete_permission(self, payload: PermissionDeletePayload) -> PermissionData:
        async_session = get_async_session_maker()
        async with async_session() as session:
            await self._get_application(session, payload.application_id)
            perm = await session.get(StaffApplicationPermission, payload.id)
            if perm is None or perm.application_id != payload.application_id:
                raise NotFoundError(message="Permission not found")
            perm_data = self._perm_data(perm)
            await session.execute(
                delete(StaffRolePermission).where(StaffRolePermission.permission_id == perm.id)
            )
            await session.delete(perm)
            await session.commit()
        return perm_data

    async def get_role_permissions(
        self, payload: RolePermissionListPayload, page: int, page_size: int
    ) -> tuple[list[RolePermissionData], int]:
        async_session = get_async_session_maker()
        async with async_session() as session:
            await self._get_application(session, payload.application_id)
            roles = (
                (
                    await session.execute(
                        select(StaffRole).where(StaffRole.application_id == payload.application_id)
                    )
                )
                .scalars()
                .all()
            )
            role_ids = [r.id for r in roles]
            role_by_id = {r.id: r for r in roles}
            perms = (
                (
                    await session.execute(
                        select(StaffApplicationPermission).where(
                            StaffApplicationPermission.application_id == payload.application_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            perm_by_id = {p.id: p for p in perms}
            if not role_ids:
                return [], 0

            stmt = select(StaffRolePermission).where(StaffRolePermission.role_id.in_(role_ids))
            if payload.role_id is not None:
                stmt = stmt.where(StaffRolePermission.role_id == payload.role_id)
            if payload.permission_id is not None:
                stmt = stmt.where(StaffRolePermission.permission_id == payload.permission_id)
            stmt = stmt.order_by(StaffRolePermission.id.desc())
            rows, total = await paginate(session, stmt, page=page, page_size=page_size)
            items: list[RolePermissionData] = []
            for row in rows:
                role = role_by_id.get(row.role_id)
                perm = perm_by_id.get(row.permission_id)
                items.append(
                    RolePermissionData(
                        id=row.id,
                        role_id=row.role_id,
                        permission_id=row.permission_id,
                        role_mnemonic=role.role_mnemonic if role else None,
                        permission_mnemonic=perm.permission_mnemonic if perm else None,
                        active=bool(row.active),
                        created_at=dt_iso(row.created_at),
                        updated_at=dt_iso(row.updated_at),
                    )
                )
            return items, total

    async def create_role_permission(self, payload: RolePermissionCreatePayload) -> RolePermissionData:
        async_session = get_async_session_maker()
        async with async_session() as session:
            await self._get_application(session, payload.application_id)
            role = await session.get(StaffRole, payload.role_id)
            perm = await session.get(StaffApplicationPermission, payload.permission_id)
            if role is None or role.application_id != payload.application_id:
                raise BadRequestError(message="role_id does not belong to this application")
            if perm is None or perm.application_id != payload.application_id:
                raise BadRequestError(message="permission_id does not belong to this application")
            # Access mnemonics before session operations to avoid lazy loading issues
            role_mnemonic = role.role_mnemonic
            permission_mnemonic = perm.permission_mnemonic

            existing = (
                (
                    await session.execute(
                        select(StaffRolePermission).where(
                            StaffRolePermission.role_id == payload.role_id,
                            StaffRolePermission.permission_id == payload.permission_id,
                        )
                    )
                )
                .scalars()
                .first()
            )
            if existing is not None:
                raise BadRequestError(message="Mapping already exists")
            mapping = StaffRolePermission(
                role_id=payload.role_id,
                permission_id=payload.permission_id,
                active=True,
            )
            session.add(mapping)
            await session.commit()
            await session.refresh(mapping)
            return RolePermissionData(
                id=mapping.id,
                role_id=mapping.role_id,
                permission_id=mapping.permission_id,
                role_mnemonic=role_mnemonic,
                permission_mnemonic=permission_mnemonic,
                active=bool(mapping.active),
                created_at=dt_iso(mapping.created_at),
                updated_at=dt_iso(mapping.updated_at),
            )

    async def delete_role_permission(self, payload: RolePermissionDeletePayload) -> RolePermissionData:
        async_session = get_async_session_maker()
        async with async_session() as session:
            await self._get_application(session, payload.application_id)
            mapping = await session.get(StaffRolePermission, payload.id)
            if mapping is None:
                raise NotFoundError(message="Mapping not found")
            role = await session.get(StaffRole, mapping.role_id)
            if role is None or role.application_id != payload.application_id:
                raise NotFoundError(message="Mapping not found")
            perm = await session.get(StaffApplicationPermission, mapping.permission_id)
            role_mnemonic = role.role_mnemonic if role else None
            permission_mnemonic = perm.permission_mnemonic if perm else None
            mapping_data = RolePermissionData(
                id=mapping.id,
                role_id=mapping.role_id,
                permission_id=mapping.permission_id,
                role_mnemonic=role_mnemonic,
                permission_mnemonic=permission_mnemonic,
                active=bool(mapping.active),
                created_at=dt_iso(mapping.created_at),
                updated_at=dt_iso(mapping.updated_at),
            )
            await session.delete(mapping)
            await session.commit()
        return mapping_data
