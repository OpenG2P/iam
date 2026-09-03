import json
import logging
from abc import ABC
from datetime import date, datetime
from pathlib import Path
from typing import Any, Sequence, Type

from sqlalchemy import Date, DateTime, func, insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from iam_core.models import LoginProvider
from openg2p_fastapi_common.context import async_session_maker, dbengine, get_async_session_maker

from ..config import Settings
from ..models import (
    StaffApplicationPermission,
    StaffPortalApplication,
    StaffRole,
    StaffRolePermission,
)

_logger = logging.getLogger("iam-staff-data-loader")

# Tables touched by self-registration (farmer-registry, national-social-registry,
# and any other product that POSTs to /user-access/staff_portal_applications).
STAFF_ACCESS_SEQUENCE_MODELS = (
    StaffPortalApplication,
    StaffApplicationPermission,
    StaffRole,
    StaffRolePermission,
)

IAM_STAFF_UI_APPLICATION_MNEMONIC = "iam-staff-ui"
IAM_STAFF_UI_ADMIN_ROLE = "IAM_ADMIN"
IAM_STAFF_UI_PERMISSIONS = (
    "application:view",
    "application:create",
    "application:edit",
    "application:delete",
    "role:view",
    "role:create",
    "role:delete",
    "permission:view",
    "permission:create",
    "permission:delete",
    "rolePermission:view",
    "rolePermission:create",
    "rolePermission:delete",
    "dataPolicy:view",
    "dataPolicy:create",
    "dataPolicy:delete",
    "loginProvider:view",
    "loginProvider:create",
    "loginProvider:edit",
    "loginProvider:delete",
)


class DataLoaderBase(ABC):
    data_models = (
        LoginProvider,
        StaffPortalApplication,
        StaffRole,
        StaffApplicationPermission,
        StaffRolePermission,
    )

    def get_mounted_data_dir(self) -> Path:
        return Path(Settings.get_config(strict=False).data_dir)

    def get_fallback_data_dir(self) -> Path:
        return Path(__file__).resolve().parent

    def get_config(self) -> Settings:
        return Settings.get_config(strict=False)

    def get_dataset_path(self, model, data_dir: Path) -> Path:
        return data_dir / f"{model.__tablename__}.json"

    def load_dataset(
        self,
        model,
        data_dir: Path,
    ) -> list[dict[str, Any]]:
        dataset_path = self.get_dataset_path(model, data_dir)
        if not dataset_path.exists():
            return []

        raw_value = dataset_path.read_text(encoding="utf-8")

        try:
            payload = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {dataset_path}: {exc.msg}") from exc

        if not isinstance(payload, list):
            raise ValueError(f"{dataset_path} must be a JSON array of objects")

        if any(not isinstance(row, dict) for row in payload):
            raise ValueError(f"{dataset_path} must contain only JSON objects")

        return self.apply_config_values(model, payload)

    def apply_config_values(
        self,
        model,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if model is StaffPortalApplication:
            return self.apply_application_url_values(rows)

        if model is LoginProvider:
            return self.apply_login_provider_values(rows)

        return rows

    def apply_application_url_values(
        self,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        application_urls = self.get_config().data_application_urls
        updated_rows: list[dict[str, Any]] = []

        for row in rows:
            updated_row = dict(row)
            application_url_key = updated_row.get("application_url")

            if application_url_key in application_urls:
                updated_row["application_url"] = application_urls[application_url_key]

            updated_rows.append(updated_row)

        return updated_rows

    def apply_login_provider_values(
        self,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        client_secrets = self.get_config().data_client_secrets
        updated_rows: list[dict[str, Any]] = []

        for row in rows:
            updated_row = dict(row)
            client_secret_key = updated_row.get("client_secret")

            if client_secret_key in client_secrets:
                updated_row["client_secret"] = client_secrets[client_secret_key]

            updated_rows.append(updated_row)

        return updated_rows

    async def seed_models_from_dir(
        self,
        session: AsyncSession,
        data_dir: Path,
    ) -> None:
        if not data_dir.exists() or not data_dir.is_dir():
            _logger.info("Skipping missing data directory: %s", data_dir)
            return

        _logger.info("Loading data from %s", data_dir)

        for model in self.data_models:
            rows = self.load_dataset(model, data_dir)
            if model is StaffPortalApplication:
                await self.seed_applications_by_mnemonic(session, rows)
            else:
                await self.seed_if_empty(session, model, rows)

        await self.seed_iam_staff_ui_catalog(session)

    async def seed_applications_by_mnemonic(
        self,
        session: AsyncSession,
        rows: list[dict[str, Any]],
    ) -> None:
        """Idempotently seed staff_portal_applications keyed by mnemonic.

        Unlike the whole-table ``seed_if_empty`` check, this inserts any seeded
        singletons that are missing and refreshes the URL/metadata of existing
        seeded rows (so changing IAM_STAFF_DATA_APPLICATION_URLS__* and
        re-running migrate takes effect). Rows flagged ``is_self_registered``
        (e.g. registries that registered themselves via the API) are never
        touched, so seeding can run repeatedly without clobbering them.
        """
        if not rows:
            return

        existing_rows = (await session.execute(select(StaffPortalApplication))).scalars().all()
        existing_by_mnemonic = {row.application_mnemonic: row for row in existing_rows}

        new_rows: list[dict[str, Any]] = []
        for row in self.coerce_rows_for_model(StaffPortalApplication, rows):
            mnemonic = row.get("application_mnemonic")
            existing = existing_by_mnemonic.get(mnemonic)

            if existing is None:
                new_rows.append(row)
                continue

            if existing.is_self_registered:
                # Owned by the application itself; never overwrite from seed.
                continue

            for key, value in row.items():
                if key in {"id", "application_mnemonic"}:
                    continue
                setattr(existing, key, value)

        if new_rows:
            _logger.info("Seeding %s with %s new rows", StaffPortalApplication.__tablename__, len(new_rows))
            await session.execute(insert(StaffPortalApplication), new_rows)

    async def seed_iam_staff_ui_catalog(self, session: AsyncSession) -> None:
        """Idempotently seed IAM_ADMIN role + low-level permissions for iam-staff-ui.

        Resolves ``application_id`` by mnemonic so seed works regardless of the
        numeric id assigned to the ``iam-staff-ui`` application row.
        """
        result = await session.execute(
            select(StaffPortalApplication).where(
                StaffPortalApplication.application_mnemonic == IAM_STAFF_UI_APPLICATION_MNEMONIC
            )
        )
        app = result.scalars().first()
        if app is None:
            _logger.warning(
                "Skipping iam-staff-ui catalog seed; application '%s' not found",
                IAM_STAFF_UI_APPLICATION_MNEMONIC,
            )
            return

        result = await session.execute(
            select(StaffApplicationPermission).where(StaffApplicationPermission.application_id == app.id)
        )
        existing_perms = result.scalars().all()
        perms_by_mnemonic = {p.permission_mnemonic: p for p in existing_perms}

        for mnemonic in IAM_STAFF_UI_PERMISSIONS:
            row = perms_by_mnemonic.get(mnemonic)
            if row is None:
                row = StaffApplicationPermission(
                    application_id=app.id,
                    permission_mnemonic=mnemonic,
                    permission_description=mnemonic,
                    active=True,
                )
                session.add(row)
                perms_by_mnemonic[mnemonic] = row
            else:
                row.permission_description = row.permission_description or mnemonic
                row.active = True

        await session.flush()

        existing_roles = (
            (await session.execute(select(StaffRole).where(StaffRole.application_id == app.id)))
            .scalars()
            .all()
        )
        roles_by_mnemonic = {r.role_mnemonic: r for r in existing_roles}

        admin_role = roles_by_mnemonic.get(IAM_STAFF_UI_ADMIN_ROLE)
        if admin_role is None:
            admin_role = StaffRole(
                application_id=app.id,
                role_mnemonic=IAM_STAFF_UI_ADMIN_ROLE,
                role_description="IAM staff UI administrator",
                active=True,
            )
            session.add(admin_role)
            roles_by_mnemonic[IAM_STAFF_UI_ADMIN_ROLE] = admin_role
        else:
            admin_role.role_description = admin_role.role_description or "IAM staff UI administrator"
            admin_role.active = True

        await session.flush()

        existing_mappings = (
            (
                await session.execute(
                    select(StaffRolePermission).where(StaffRolePermission.role_id == admin_role.id)
                )
            )
            .scalars()
            .all()
        )
        mapped_permission_ids = {m.permission_id for m in existing_mappings}

        for mnemonic in IAM_STAFF_UI_PERMISSIONS:
            perm = perms_by_mnemonic[mnemonic]
            await session.flush()
            if perm.id is None:
                continue
            if perm.id in mapped_permission_ids:
                continue
            session.add(
                StaffRolePermission(
                    role_id=admin_role.id,
                    permission_id=perm.id,
                    active=True,
                )
            )
            mapped_permission_ids.add(perm.id)

        _logger.info(
            "Ensured iam-staff-ui catalog: role=%s permissions=%s",
            IAM_STAFF_UI_ADMIN_ROLE,
            len(IAM_STAFF_UI_PERMISSIONS),
        )

    async def seed_if_empty(
        self,
        session: AsyncSession,
        model,
        rows: list[dict[str, Any]],
    ) -> None:
        row_count = await session.scalar(select(func.count()).select_from(model))
        if row_count and row_count > 0:
            return

        if not rows:
            return

        _logger.info("Seeding %s with %s rows", model.__tablename__, len(rows))
        await session.execute(insert(model), self.coerce_rows_for_model(model, rows))

    def coerce_rows_for_model(
        self,
        model,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        datetime_columns: set[str] = set()
        date_columns: set[str] = set()

        for column in model.__table__.columns:
            if isinstance(column.type, DateTime):
                datetime_columns.add(column.name)
            elif isinstance(column.type, Date):
                date_columns.add(column.name)

        coerced_rows: list[dict[str, Any]] = []
        for row in rows:
            coerced = dict(row)

            for column_name in datetime_columns:
                if column_name in {"created_at", "updated_at"}:
                    coerced.pop(column_name, None)
                    continue

                value = coerced.get(column_name)
                if isinstance(value, str):
                    coerced[column_name] = datetime.fromisoformat(value)

            for column_name in date_columns:
                value = coerced.get(column_name)
                if isinstance(value, str):
                    coerced[column_name] = date.fromisoformat(value)

            coerced_rows.append(coerced)

        return coerced_rows

    async def sync_postgres_id_sequences(
        self,
        session: AsyncSession,
        models: Sequence[Type] | None = None,
    ) -> None:
        """Align SERIAL sequences with MAX(id) after bulk seed inserts.

        PostgreSQL sequences are not advanced when rows are inserted with
        explicit ids (or restored from dumps). Without this, the next ORM
        insert can reuse an existing primary key and raise IntegrityError.
        """
        bind = session.get_bind()
        if bind.dialect.name != "postgresql":
            return

        for model in models or self.data_models:
            table_name = model.__tablename__
            if "id" not in model.__table__.c:
                continue

            sequence = await session.scalar(
                text("SELECT pg_get_serial_sequence(:table_name, 'id')"),
                {"table_name": table_name},
            )
            if not sequence:
                continue

            next_id = await session.scalar(
                text(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table_name}"),
            )
            await session.execute(
                text("SELECT setval(CAST(:sequence AS regclass), :next_id, false)"),
                {"sequence": sequence, "next_id": next_id},
            )
            _logger.debug("Synced id sequence for %s (next id %s)", table_name, next_id)

    async def sync_staff_access_id_sequences(self, session: AsyncSession) -> None:
        """Sync id sequences for staff portal app / role / permission tables."""
        await self.sync_postgres_id_sequences(session, STAFF_ACCESS_SEQUENCE_MODELS)

    def create_session_factory(self) -> async_sessionmaker[AsyncSession]:
        # Dispose (in run()) can leave the process-wide factory bound to a dead
        # pool; drop it so the next checkout opens connections on this event loop.
        async_session_maker.set(None)
        return get_async_session_maker()


class DataLoader(DataLoaderBase):
    @classmethod
    async def run(cls) -> None:
        loader = cls()

        # ``migrate_database`` runs create_migrate() in its own asyncio.run()
        # before this one, so the shared engine's pool can hold asyncpg
        # connections bound to that earlier (now-closed) event loop. Reusing one
        # here raises "got Future attached to a different loop" on the first
        # query. Drop the old pool so this loop opens its own fresh connections.
        # close=False ABANDONS the orphaned connections rather than trying to
        # close them on their dead loop (which would just log a spurious
        # "Event loop is closed" error); they are garbage-collected instead.
        await dbengine.get().dispose(close=False)

        session_factory = loader.create_session_factory()

        _logger.info("Starting IAM staff data loader")
        async with session_factory() as session:
            await loader.load_data(session)
            await loader.load_fallback_data(session)
            await loader.sync_postgres_id_sequences(session)
            await session.commit()
        _logger.info("Completed IAM staff data loader")

    def load(self) -> None:
        """Sync entrypoint used by ``migrate_database``."""
        import asyncio

        asyncio.run(self.run())

    async def load_data(self, session: AsyncSession) -> None:
        await self.seed_models_from_dir(session, self.get_mounted_data_dir())

    async def load_fallback_data(self, session: AsyncSession) -> None:
        await self.seed_models_from_dir(session, self.get_fallback_data_dir())
