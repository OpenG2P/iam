from datetime import date, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from iam_core.models import LoginProvider
from sqlalchemy import Column, Date, DateTime, Integer, MetaData, Table

from iam_staff_portal_api.data.data_loader import (
    STAFF_ACCESS_SEQUENCE_MODELS,
    DataLoader,
    DataLoaderBase,
)
from iam_staff_portal_api.models import StaffPortalApplication, StaffRole


class _Loader(DataLoaderBase):
    pass


def test_load_dataset_returns_empty_for_missing_file(tmp_path):
    loader = _Loader()
    rows = loader.load_dataset(StaffPortalApplication, tmp_path)
    assert rows == []


def test_load_dataset_rejects_invalid_json(tmp_path):
    path = tmp_path / "staff_portal_applications.json"
    path.write_text("{not-json", encoding="utf-8")
    loader = _Loader()
    with pytest.raises(ValueError, match="Invalid JSON"):
        loader.load_dataset(StaffPortalApplication, path.parent)


def test_load_dataset_rejects_non_array_payload(tmp_path):
    path = tmp_path / "staff_portal_applications.json"
    path.write_text('{"application_mnemonic":"x"}', encoding="utf-8")
    loader = _Loader()
    with pytest.raises(ValueError, match="must be a JSON array"):
        loader.load_dataset(StaffPortalApplication, path.parent)


def test_load_dataset_rejects_non_object_rows(tmp_path):
    path = tmp_path / "staff_portal_applications.json"
    path.write_text("[1, 2]", encoding="utf-8")
    loader = _Loader()
    with pytest.raises(ValueError, match="must contain only JSON objects"):
        loader.load_dataset(StaffPortalApplication, path.parent)


def test_apply_application_url_values_substitutes_config_keys():
    loader = _Loader()
    with patch.object(
        _Loader,
        "get_config",
        return_value=MagicMock(data_application_urls={"keycloak_application_url": "https://kc.example.com"}),
    ):
        rows = loader.apply_application_url_values(
            [{"application_mnemonic": "keycloak", "application_url": "keycloak_application_url"}]
        )
    assert rows[0]["application_url"] == "https://kc.example.com"


def test_apply_login_provider_values_substitutes_client_secret():
    loader = _Loader()
    with patch.object(
        _Loader,
        "get_config",
        return_value=MagicMock(data_client_secrets={"secret_key": "actual-secret"}),
    ):
        rows = loader.apply_login_provider_values([{"client_secret": "secret_key"}])
    assert rows[0]["client_secret"] == "actual-secret"


def test_coerce_rows_for_model_parses_dates_and_drops_timestamps():
    loader = _Loader()
    coerced = loader.coerce_rows_for_model(
        StaffPortalApplication,
        [
            {
                "application_mnemonic": "registry",
                "created_at": "2026-01-02 10:00:00",
                "updated_at": "2026-01-02 10:00:01",
            }
        ],
    )
    assert "created_at" not in coerced[0]
    assert "updated_at" not in coerced[0]


@pytest.mark.asyncio
async def test_seed_if_empty_skips_when_table_has_rows():
    loader = _Loader()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=3)
    session.execute = AsyncMock()

    await loader.seed_if_empty(session, StaffPortalApplication, [{"application_mnemonic": "x"}])
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_seed_if_empty_inserts_when_empty():
    loader = _Loader()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=0)
    session.execute = AsyncMock()

    await loader.seed_if_empty(
        session,
        StaffPortalApplication,
        [{"application_mnemonic": "registry", "active": True}],
    )
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_seed_applications_by_mnemonic_inserts_missing_rows():
    loader = _Loader()
    session = AsyncMock()
    existing = MagicMock()
    existing.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=existing)

    await loader.seed_applications_by_mnemonic(
        session,
        [{"application_mnemonic": "registry", "application_url": "https://registry.example.com"}],
    )
    assert session.execute.await_count == 2


@pytest.mark.asyncio
async def test_seed_applications_by_mnemonic_updates_seeded_existing_rows():
    loader = _Loader()
    existing_app = MagicMock()
    existing_app.application_mnemonic = "registry"
    existing_app.is_self_registered = False

    result = MagicMock()
    result.scalars.return_value.all.return_value = [existing_app]
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)

    await loader.seed_applications_by_mnemonic(
        session,
        [{"application_mnemonic": "registry", "application_url": "https://new.example.com"}],
    )
    assert existing_app.application_url == "https://new.example.com"


@pytest.mark.asyncio
async def test_seed_applications_by_mnemonic_skips_self_registered_rows():
    loader = _Loader()
    existing_app = MagicMock()
    existing_app.application_mnemonic = "registry"
    existing_app.is_self_registered = True
    existing_app.application_url = "https://original.example.com"

    result = MagicMock()
    result.scalars.return_value.all.return_value = [existing_app]
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)

    await loader.seed_applications_by_mnemonic(
        session,
        [{"application_mnemonic": "registry", "application_url": "https://new.example.com"}],
    )
    assert existing_app.application_url == "https://original.example.com"


@pytest.mark.asyncio
async def test_sync_postgres_id_sequences_skips_non_postgresql():
    loader = _Loader()
    session = AsyncMock()
    bind = MagicMock()
    bind.dialect.name = "sqlite"
    session.get_bind = MagicMock(return_value=bind)

    await loader.sync_postgres_id_sequences(session)
    session.scalar.assert_not_called()


@pytest.mark.asyncio
async def test_sync_postgres_id_sequences_updates_sequence_on_postgresql():
    loader = _Loader()
    session = AsyncMock()
    bind = MagicMock()
    bind.dialect.name = "postgresql"
    session.get_bind = MagicMock(return_value=bind)
    session.scalar = AsyncMock(side_effect=["staff_portal_applications_id_seq", 42])
    session.execute = AsyncMock()

    await loader.sync_postgres_id_sequences(session, [StaffPortalApplication])
    assert session.scalar.await_count == 2
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_seed_models_from_dir_skips_missing_directory(tmp_path):
    loader = _Loader()
    session = AsyncMock()
    missing = tmp_path / "missing"
    await loader.seed_models_from_dir(session, missing)
    session.execute.assert_not_called()


def test_load_dataset_from_bundled_seed_file():
    loader = _Loader()
    data_dir = Path(__file__).resolve().parents[1] / "src/iam_staff_portal_api/data"
    rows = loader.load_dataset(StaffPortalApplication, data_dir)
    assert rows
    assert rows[0]["application_mnemonic"] == "iam-staff-ui"


def test_apply_config_values_routes_by_model():
    loader = _Loader()
    with patch.object(loader, "apply_application_url_values", return_value=["app"]) as app_patch:
        assert loader.apply_config_values(StaffPortalApplication, []) == ["app"]
        app_patch.assert_called_once()

    with patch.object(loader, "apply_login_provider_values", return_value=["provider"]) as provider_patch:
        assert loader.apply_config_values(LoginProvider, []) == ["provider"]
        provider_patch.assert_called_once()

    assert loader.apply_config_values(StaffRole, [{"x": 1}]) == [{"x": 1}]


@pytest.mark.asyncio
async def test_data_loader_run_commits_after_loading():
    session = AsyncMock()
    session_factory = MagicMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)
    session_factory.return_value = cm
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()

    with (
        patch.object(DataLoader, "load_data", AsyncMock()),
        patch.object(DataLoader, "load_fallback_data", AsyncMock()),
        patch.object(DataLoader, "sync_postgres_id_sequences", AsyncMock()),
        patch.object(DataLoader, "create_session_factory", return_value=session_factory),
        patch("iam_staff_portal_api.data.data_loader.dbengine.get", return_value=mock_engine),
    ):
        await DataLoader.run()

    session.commit.assert_awaited_once()


def test_get_mounted_and_fallback_data_dirs():
    loader = _Loader()
    with patch.object(_Loader, "get_config", return_value=MagicMock(data_dir="/opt/iam-staff-portal-data")):
        assert loader.get_mounted_data_dir() == Path("/opt/iam-staff-portal-data")
    assert loader.get_fallback_data_dir().name == "data"


def test_coerce_rows_for_model_parses_datetime_and_date_columns():
    metadata = MetaData()
    coerce_model = type(
        "CoerceModel",
        (),
        {
            "__tablename__": "coerce_test",
            "__table__": Table(
                "coerce_test",
                metadata,
                Column("id", Integer, primary_key=True),
                Column("event_at", DateTime),
                Column("birth_date", Date),
            ),
        },
    )
    loader = _Loader()
    coerced = loader.coerce_rows_for_model(
        coerce_model,
        [
            {
                "event_at": "2026-01-02T10:00:00",
                "birth_date": "2026-01-02",
            }
        ],
    )
    assert coerced[0]["event_at"] == datetime.fromisoformat("2026-01-02T10:00:00")
    assert coerced[0]["birth_date"] == date.fromisoformat("2026-01-02")


@pytest.mark.asyncio
async def test_seed_applications_by_mnemonic_returns_when_rows_empty():
    loader = _Loader()
    session = AsyncMock()
    session.execute = AsyncMock()

    await loader.seed_applications_by_mnemonic(session, [])

    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_seed_if_empty_returns_when_rows_empty():
    loader = _Loader()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=0)
    session.execute = AsyncMock()

    await loader.seed_if_empty(session, StaffPortalApplication, [])

    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_seed_models_from_dir_loads_each_model(tmp_path):
    loader = _Loader()
    for model in loader.data_models:
        (tmp_path / f"{model.__tablename__}.json").write_text("[]", encoding="utf-8")

    session = AsyncMock()
    # Mock session.execute to return a result with scalars().first() returning None
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result
    with (
        patch.object(loader, "seed_applications_by_mnemonic", AsyncMock()) as seed_apps,
        patch.object(loader, "seed_if_empty", AsyncMock()) as seed_empty,
    ):
        await loader.seed_models_from_dir(session, tmp_path)

    seed_apps.assert_awaited_once()
    assert seed_empty.await_count == len(loader.data_models) - 1


@pytest.mark.asyncio
async def test_sync_postgres_id_sequences_skips_tables_without_id():
    loader = _Loader()
    session = AsyncMock()
    bind = MagicMock()
    bind.dialect.name = "postgresql"
    session.get_bind = MagicMock(return_value=bind)

    model = MagicMock()
    model.__tablename__ = "no_id_table"
    model.__table__ = MagicMock()
    model.__table__.c = {"name": MagicMock()}

    await loader.sync_postgres_id_sequences(session, [model])

    session.scalar.assert_not_called()


@pytest.mark.asyncio
async def test_sync_postgres_id_sequences_skips_when_sequence_missing():
    loader = _Loader()
    session = AsyncMock()
    bind = MagicMock()
    bind.dialect.name = "postgresql"
    session.get_bind = MagicMock(return_value=bind)
    session.scalar = AsyncMock(return_value=None)
    session.execute = AsyncMock()

    await loader.sync_postgres_id_sequences(session, [StaffPortalApplication])

    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_sync_staff_access_id_sequences_delegates_to_postgres_sync():
    loader = _Loader()
    session = AsyncMock()
    with patch.object(loader, "sync_postgres_id_sequences", AsyncMock()) as sync_sequences:
        await loader.sync_staff_access_id_sequences(session)

    sync_sequences.assert_awaited_once_with(session, STAFF_ACCESS_SEQUENCE_MODELS)


def test_create_session_factory_uses_dbengine():
    loader = DataLoader()
    mock_engine = MagicMock()
    with patch("iam_staff_portal_api.data.data_loader.dbengine.get", return_value=mock_engine):
        factory = loader.create_session_factory()
    assert factory is not None


@pytest.mark.asyncio
async def test_load_data_and_fallback_data_delegate_to_seed_models_from_dir():
    loader = DataLoader()
    session = AsyncMock()
    with (
        patch.object(loader, "seed_models_from_dir", AsyncMock()) as seed_models,
        patch.object(loader, "get_mounted_data_dir", return_value=Path("/mounted")),
        patch.object(loader, "get_fallback_data_dir", return_value=Path("/fallback")),
    ):
        await loader.load_data(session)
        await loader.load_fallback_data(session)

    assert seed_models.await_args_list[0].args == (session, Path("/mounted"))
    assert seed_models.await_args_list[1].args == (session, Path("/fallback"))


def test_data_loader_load_invokes_asyncio_run():
    with (
        patch.object(DataLoader, "run", new_callable=AsyncMock),
        patch("asyncio.run") as asyncio_run,
    ):
        DataLoader().load()
    asyncio_run.assert_called_once()
