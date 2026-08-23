import asyncio
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

from iam_core.models import LoginProvider
from openg2p_fastapi_common.context import dbengine
from sqlalchemy import Date, DateTime, insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import Settings

_logger = logging.getLogger("iam-agent-data-loader")


class DataLoader:
    """Seeds the agent realm's row into the shared ``login_providers`` table.

    ``login_providers`` is a single table written by both portal APIs, so rows
    are seeded by ``issuer`` rather than only when the table is empty:
    whichever API migrates first must not stop the other from adding its own
    realm. Without this row the agent's access tokens cannot be validated —
    ``iam_core`` resolves the token issuer against this table — and every
    authenticated agent API call fails with 401.
    """

    model = LoginProvider

    def get_config(self) -> Settings:
        return Settings.get_config(strict=False)

    def get_mounted_data_dir(self) -> Path:
        return Path(self.get_config().data_dir)

    def load(self) -> None:
        """Sync entrypoint used by ``migrate_database``."""
        asyncio.run(self.run())

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

        session_factory = async_sessionmaker(dbengine.get(), expire_on_commit=False)

        _logger.info("Starting IAM agent data loader")
        async with session_factory() as session:
            await loader.seed_login_providers(session)
            await loader.sync_id_sequence(session)
            await session.commit()
        _logger.info("Completed IAM agent data loader")

    def load_dataset(self) -> list[dict[str, Any]]:
        dataset_path = self.get_mounted_data_dir() / f"{self.model.__tablename__}.json"
        if not dataset_path.exists():
            _logger.info("Skipping missing dataset: %s", dataset_path)
            return []

        try:
            payload = json.loads(dataset_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {dataset_path}: {exc.msg}") from exc

        if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
            raise ValueError(f"{dataset_path} must be a JSON array of objects")

        return self.coerce_rows(self.apply_client_secrets(payload))

    def apply_client_secrets(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Swap the ``clientSecret`` placeholder for the real Keycloak secret.

        The chart puts a key name (e.g. ``agent_portal_secret``) in the mounted
        JSON and supplies the value via IAM_AGENT_DATA_CLIENT_SECRETS__*, so the
        secret never has to be written into values.yaml.
        """
        client_secrets = self.get_config().data_client_secrets
        updated_rows: list[dict[str, Any]] = []

        for row in rows:
            updated_row = dict(row)
            client_secret_key = updated_row.get("client_secret")

            if client_secret_key in client_secrets:
                updated_row["client_secret"] = client_secrets[client_secret_key]

            updated_rows.append(updated_row)

        return updated_rows

    def coerce_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Drop non-column keys and parse date/datetime strings.

        The mounted JSON carries presentation-only keys (``user_type``) that are
        not columns; ``created_at``/``updated_at`` are left to the DB defaults.
        """
        columns = {column.name: column for column in self.model.__table__.columns}

        coerced_rows: list[dict[str, Any]] = []
        for row in rows:
            coerced: dict[str, Any] = {}

            for key, value in row.items():
                column = columns.get(key)
                if column is None or key in {"created_at", "updated_at"}:
                    continue

                if isinstance(value, str):
                    if isinstance(column.type, DateTime):
                        value = datetime.fromisoformat(value)
                    elif isinstance(column.type, Date):
                        value = date.fromisoformat(value)

                coerced[key] = value

            coerced_rows.append(coerced)

        return coerced_rows

    async def seed_login_providers(self, session: AsyncSession) -> None:
        rows = self.load_dataset()
        if not rows:
            return

        existing_issuers = set(
            (await session.execute(select(self.model.issuer))).scalars().all()
        )
        new_rows = [row for row in rows if row.get("issuer") not in existing_issuers]

        if not new_rows:
            return

        _logger.info("Seeding %s with %s new rows", self.model.__tablename__, len(new_rows))
        await session.execute(insert(self.model), new_rows)

    async def sync_id_sequence(self, session: AsyncSession) -> None:
        """Align the SERIAL sequence with MAX(id) after seeding explicit ids.

        PostgreSQL does not advance a sequence for rows inserted with an
        explicit id, so without this the next provider created through the API
        can reuse a seeded id and raise IntegrityError.
        """
        table = self.model.__tablename__
        await session.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "  # noqa: S608
                f"COALESCE((SELECT MAX(id) FROM {table}), 1), true)"
            )
        )
