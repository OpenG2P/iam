import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from iam_agent_portal_api.data.data_loader import DataLoader


def _loader(tmp_path, client_secrets=None):
    loader = DataLoader()
    config = MagicMock()
    config.data_dir = str(tmp_path)
    config.data_client_secrets = client_secrets or {}
    loader.get_config = lambda: config
    return loader


def _session(existing_issuers=()):
    """AsyncSession double whose execute() awaits to a sync result object."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = list(existing_issuers)
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)
    return session


def _write(tmp_path, payload):
    path = tmp_path / "login_providers.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _row(**overrides):
    row = {
        "id": 10,
        "user_type": "agent",
        "provider_name": "Keycloak",
        "client_id": "agent-portal",
        "client_secret": "agent_portal_secret",
        "token_endpoint_auth_method": "client_secret_basic",
        "issuer": "https://keycloak.example.org/realms/agent",
        "oauth_callback_url": "https://agent-iam.example.org/auth/callback",
        "created_at": "2026-01-01 00:00:00",
        "updated_at": "2026-01-01 00:00:00",
        "active": True,
    }
    row.update(overrides)
    return row


def test_load_dataset_returns_empty_for_missing_file(tmp_path):
    assert _loader(tmp_path).load_dataset() == []


def test_load_dataset_rejects_invalid_json(tmp_path):
    _write(tmp_path, [])
    (tmp_path / "login_providers.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        _loader(tmp_path).load_dataset()


def test_load_dataset_rejects_non_array_payload(tmp_path):
    _write(tmp_path, {"issuer": "x"})
    with pytest.raises(ValueError, match="JSON array of objects"):
        _loader(tmp_path).load_dataset()


def test_load_dataset_rejects_non_object_rows(tmp_path):
    _write(tmp_path, ["not-an-object"])
    with pytest.raises(ValueError, match="JSON array of objects"):
        _loader(tmp_path).load_dataset()


def test_coerce_drops_non_column_keys_and_seed_timestamps(tmp_path):
    _write(tmp_path, [_row()])
    row = _loader(tmp_path).load_dataset()[0]

    # user_type is a presentation-only key in the mounted JSON, not a column;
    # passing it through would make the INSERT unusable outside the executemany
    # form that silently drops it.
    assert "user_type" not in row
    # created_at/updated_at are left to the DB defaults.
    assert "created_at" not in row and "updated_at" not in row
    assert row["issuer"] == "https://keycloak.example.org/realms/agent"


def test_client_secret_placeholder_is_substituted(tmp_path):
    _write(tmp_path, [_row()])
    loader = _loader(tmp_path, {"agent_portal_secret": "s3cr3t-from-keycloak"})
    assert loader.load_dataset()[0]["client_secret"] == "s3cr3t-from-keycloak"


def test_client_secret_left_alone_when_not_configured(tmp_path):
    _write(tmp_path, [_row()])
    assert _loader(tmp_path).load_dataset()[0]["client_secret"] == "agent_portal_secret"


@pytest.mark.asyncio
async def test_seed_inserts_when_issuer_absent(tmp_path):
    _write(tmp_path, [_row()])
    session = _session()

    await _loader(tmp_path).seed_login_providers(session)

    assert session.execute.await_count == 2  # select issuers, then insert


@pytest.mark.asyncio
async def test_seed_skips_when_issuer_already_present(tmp_path):
    """The staff API seeds the same table; its row must not block ours, and
    ours must not be duplicated when it is already there."""
    _write(tmp_path, [_row()])
    session = _session(["https://keycloak.example.org/realms/agent"])

    await _loader(tmp_path).seed_login_providers(session)

    assert session.execute.await_count == 1  # select only, no insert


@pytest.mark.asyncio
async def test_seed_inserts_alongside_another_realms_row(tmp_path):
    """A populated table (staff already seeded) must not stop the agent row."""
    _write(tmp_path, [_row()])
    session = _session(["https://keycloak.example.org/realms/staff"])

    await _loader(tmp_path).seed_login_providers(session)

    assert session.execute.await_count == 2


@pytest.mark.asyncio
async def test_seed_noop_without_a_dataset(tmp_path):
    session = AsyncMock()
    await _loader(tmp_path).seed_login_providers(session)
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_commits_after_seeding(tmp_path):
    _write(tmp_path, [_row()])
    session = _session()
    session_factory = MagicMock()
    session_factory.return_value.__aenter__.return_value = session
    session_factory.return_value.__aexit__.return_value = False

    engine = MagicMock()
    engine.dispose = AsyncMock()

    with (
        patch("iam_agent_portal_api.data.data_loader.dbengine") as dbengine,
        patch("iam_agent_portal_api.data.data_loader.async_sessionmaker", return_value=session_factory),
        patch.object(DataLoader, "get_config") as get_config,
    ):
        dbengine.get.return_value = engine
        get_config.return_value = MagicMock(data_dir=str(tmp_path), data_client_secrets={})
        await DataLoader.run()

    # The pool from migrate_database's own event loop is dropped, not closed.
    engine.dispose.assert_awaited_once_with(close=False)
    session.commit.assert_awaited_once()
