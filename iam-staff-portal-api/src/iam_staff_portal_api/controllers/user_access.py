from typing import List, Optional

from fastapi import Request
from fastapi_cache.decorator import cache
from openg2p_fastapi_common.context import get_async_session_maker
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import BadRequestError
from sqlalchemy import delete, select
from iam_core.user_auth.decorators import requires_auth

from ..cache import role_cache_key
from ..config import Settings
from ..data import DataLoader
from iam_core.models import (
    ApplicationPermission,
    Application,
    Role,
    RolePermission,
)
from ..schemas import (
    ApplicationPermissionResponse,
    RegisterPortalApplicationRequest,
    RegisterPortalApplicationResponse,
    PortalApplicationResponse,
)


_config = Settings.get_config(strict=False)


class UserAccessController(BaseController):
    """
    Controller for managing user access to staff portal applications and their associated permissions.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router.prefix += "/user-access"
        self.router.tags += ["/user-access"]

        self.router.add_api_route(
            "/get_staff_portal_applications",
            self.get_staff_portal_applications,
            response_model=List[PortalApplicationResponse],
            methods=["GET"],
        )
        self.router.add_api_route(
            "/get_application_permissions_for_user",
            self.get_application_permissions_for_user,
            response_model=List[ApplicationPermissionResponse],
            methods=["GET"],
        )
        self.router.add_api_route(
            "/staff_portal_applications",
            self.register_staff_portal_application,
            response_model=RegisterPortalApplicationResponse,
            methods=["POST"],
        )

    @requires_auth
    async def get_staff_portal_applications(
        self,
        request: Request,
    ) -> List[PortalApplicationResponse]:
        auth = request.state.auth
        client_roles = auth.client_roles or {}
        allowed_mnemonics = list(client_roles.keys())

        async_session = get_async_session_maker()
        async with async_session() as session:
            stmt = (
                select(Application)
                .where(Application.active.is_(True))
                .order_by(
                    Application.order.asc().nullslast(),
                    Application.id.asc(),
                )
            )
            apps = (await session.execute(stmt)).scalars().all()

        return [
            {
                "id": app.id,
                "application_mnemonic": app.application_mnemonic,
                "application_description": app.application_description,
                "icon_base64": app.icon_base64,
                "width": app.width,
                "order": app.order,
                "disabled": app.application_mnemonic not in allowed_mnemonics,
                "application_url": (
                    app.application_url if app.application_mnemonic in allowed_mnemonics else None
                ),
                "api_url": (app.api_url if app.application_mnemonic in allowed_mnemonics else None),
            }
            for app in apps
        ]

    @requires_auth
    async def register_staff_portal_application(
        self,
        request: Request,
        payload: RegisterPortalApplicationRequest,
    ) -> RegisterPortalApplicationResponse:
        """Register or update a staff portal application and its access catalog.

        Intended for applications such as registries to self-register at install
        time — their tile (URL, icon, ordering) plus their roles and permissions —
        instead of any of it being hardcoded into IAM ahead of time. Everything is
        upserted by mnemonic and scoped to this application's id, so it is
        idempotent across re-installs/upgrades.

        ``application_mnemonic`` must equal the application's Keycloak client_id so
        role-gating in ``get_staff_portal_applications`` /
        ``get_application_permissions_for_user`` resolves correctly. Multiple
        instances of the same product coexist by each using a distinct
        mnemonic/client_id and pushing their own (identical) catalog under it.
        """
        async_session = get_async_session_maker()
        async with async_session() as session:
            # Seed dumps / manual SQL can leave SERIAL sequences behind MAX(id).
            # Sync before any inserts so self-registration (farmer-registry,
            # national-social-registry, etc.) does not collide on primary keys.
            await DataLoader().sync_staff_access_id_sequences(session)

            app, created = await self._upsert_application(session, payload)
            await session.flush()  # ensure app.id is available

            perms_by_mnemonic = await self._upsert_permissions(session, app.id, payload.permissions)
            await session.flush()  # ensure permission ids exist before role queries autoflush
            roles_by_mnemonic = await self._upsert_roles(session, app.id, payload.roles)
            await session.flush()  # ensure role ids are available

            await self._rebuild_role_permissions(session, payload.roles, roles_by_mnemonic, perms_by_mnemonic)

            await session.commit()
            await session.refresh(app)

        return RegisterPortalApplicationResponse(
            id=app.id,
            application_mnemonic=app.application_mnemonic,
            created=created,
            permissions_count=len(payload.permissions),
            roles_count=len(payload.roles),
        )

    async def _upsert_application(self, session, request):
        existing = (
            (
                await session.execute(
                    select(Application).where(
                        Application.application_mnemonic == request.application_mnemonic
                    )
                )
            )
            .scalars()
            .first()
        )

        if existing is not None:
            existing.application_url = request.application_url
            existing.api_url = request.api_url
            existing.application_description = request.application_description
            existing.icon_base64 = request.icon_base64
            existing.width = request.width
            existing.order = request.order
            existing.active = request.active
            existing.is_self_registered = True
            return existing, False

        app = Application(
            application_mnemonic=request.application_mnemonic,
            application_url=request.application_url,
            api_url=request.api_url,
            application_description=request.application_description,
            icon_base64=request.icon_base64,
            width=request.width,
            order=request.order,
            active=request.active,
            is_self_registered=True,
        )
        session.add(app)
        return app, True

    async def _upsert_permissions(self, session, application_id, permissions):
        existing = (
            (
                await session.execute(
                    select(ApplicationPermission).where(
                        ApplicationPermission.application_id == application_id
                    )
                )
            )
            .scalars()
            .all()
        )
        by_mnemonic = {p.permission_mnemonic: p for p in existing}

        for perm in permissions:
            row = by_mnemonic.get(perm.permission_mnemonic)
            if row is None:
                row = ApplicationPermission(
                    application_id=application_id,
                    permission_mnemonic=perm.permission_mnemonic,
                    permission_description=perm.permission_description,
                    active=perm.active,
                )
                session.add(row)
                by_mnemonic[perm.permission_mnemonic] = row
            else:
                row.permission_description = perm.permission_description
                row.active = perm.active

        return by_mnemonic

    async def _upsert_roles(self, session, application_id, roles):
        existing = (
            (await session.execute(select(Role).where(Role.application_id == application_id))).scalars().all()
        )
        by_mnemonic = {r.role_mnemonic: r for r in existing}

        for role in roles:
            row = by_mnemonic.get(role.role_mnemonic)
            if row is None:
                row = Role(
                    application_id=application_id,
                    role_mnemonic=role.role_mnemonic,
                    role_description=role.role_description,
                    active=role.active,
                )
                session.add(row)
                by_mnemonic[role.role_mnemonic] = row
            else:
                row.role_description = role.role_description
                row.active = role.active

        return by_mnemonic

    async def _rebuild_role_permissions(self, session, roles, roles_by_mnemonic, perms_by_mnemonic):
        """Replace role->permission mappings for the roles in the payload so the
        result exactly matches what was sent (mappings dropped from the payload
        are removed). Only touches roles present in this request."""
        payload_role_ids = [roles_by_mnemonic[r.role_mnemonic].id for r in roles]
        if not payload_role_ids:
            return

        await session.execute(delete(RolePermission).where(RolePermission.role_id.in_(payload_role_ids)))

        for role in roles:
            role_row = roles_by_mnemonic[role.role_mnemonic]
            for permission_mnemonic in role.permissions:
                perm_row = perms_by_mnemonic.get(permission_mnemonic)
                if perm_row is None:
                    raise BadRequestError(
                        message=(
                            f"Role '{role.role_mnemonic}' references unknown permission "
                            f"'{permission_mnemonic}'. It must be listed in 'permissions'."
                        )
                    )
                session.add(
                    RolePermission(
                        role_id=role_row.id,
                        permission_id=perm_row.id,
                        active=True,
                    )
                )

    @requires_auth
    async def get_application_permissions_for_user(
        self,
        request: Request,
        application_mnemonic: Optional[str] = None,
    ) -> List[ApplicationPermissionResponse]:
        auth = request.state.auth
        client_roles = auth.client_roles or {}
        if not client_roles:
            return []

        if application_mnemonic:
            roles = client_roles.get(application_mnemonic)
            if not roles:
                return []
            client_roles_items = [(application_mnemonic, roles)]
        else:
            client_roles_items = client_roles.items()

        result = []
        async_session = get_async_session_maker()
        async with async_session() as session:
            for client_id, roles in client_roles_items:
                stmt = select(Application).where(
                    Application.application_mnemonic == client_id,
                    Application.active == True,  # noqa: E712
                )
                app_row = (await session.execute(stmt)).scalars().first()
                if not app_row:
                    continue

                role_stmt = select(Role).where(
                    Role.application_id == app_row.id,
                    Role.role_mnemonic.in_(roles),
                    Role.active == True,  # noqa: E712
                )
                role_rows = (await session.execute(role_stmt)).scalars().all()
                role_ids = [r.id for r in role_rows]

                if not role_ids:
                    continue

                mapping_stmt = select(RolePermission.permission_id).where(
                    RolePermission.role_id.in_(role_ids),
                    RolePermission.active == True,  # noqa: E712
                )
                permission_ids = (await session.execute(mapping_stmt)).scalars().all()

                if not permission_ids:
                    continue

                permission_stmt = select(ApplicationPermission).where(
                    ApplicationPermission.id.in_(permission_ids),
                    ApplicationPermission.active == True,  # noqa: E712
                )
                permission_rows = (await session.execute(permission_stmt)).scalars().all()

                permissions = sorted({p.permission_mnemonic for p in permission_rows})

                if permissions:
                    result.append(
                        {
                            "application_id": app_row.id,
                            "application_mnemonic": app_row.application_mnemonic,
                            "permissions": permissions,
                        }
                    )

        return result

    @cache(expire=_config.cache_expire_seconds, key_builder=role_cache_key)
    async def get_permission_mnemonics_for_role(
        self,
        role_mnemonic: str,
    ) -> List[str]:
        async_session = get_async_session_maker()
        async with async_session() as session:
            role_stmt = select(Role).where(
                Role.role_mnemonic == role_mnemonic,
                Role.active == True,  # noqa: E712
            )
            role = (await session.execute(role_stmt)).scalars().first()

            if not role:
                return []

            mapping_stmt = select(RolePermission.permission_id).where(
                RolePermission.role_id == role.id,
                RolePermission.active == True,  # noqa: E712
            )
            permission_ids = (await session.execute(mapping_stmt)).scalars().all()

            if not permission_ids:
                return []

            permission_stmt = select(ApplicationPermission.permission_mnemonic).where(
                ApplicationPermission.id.in_(permission_ids),
                ApplicationPermission.active == True,  # noqa: E712
            )
            return (await session.execute(permission_stmt)).scalars().all()
