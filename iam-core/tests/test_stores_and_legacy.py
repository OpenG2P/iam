import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch


from iam_core.services.auth_transaction_store import AuthTransactionStore
from iam_core.services.legacy_state_resolver import LegacyStateResolver
from iam_core.services.redis_auth_transaction_store import RedisAuthTransactionStore
from iam_core.services.redis_refresh_token_store import RedisRefreshTokenStore

from helpers import FakeRedis, token_response


def test_auth_transaction_store_create_and_get_and_pop():
    store = AuthTransactionStore(ttl_seconds=300)
    tx = store.create(login_provider_id=1, redirect_uri="/home", server_metadata={"issuer": "x"})

    assert tx.state in store._store
    popped = store.get_and_pop(tx.state)
    assert popped.login_provider_id == 1
    assert store.get_and_pop(tx.state) is None


def test_auth_transaction_store_get_and_pop_expired():
    store = AuthTransactionStore(ttl_seconds=300)
    tx = store.create(login_provider_id=1, redirect_uri="/")
    tx.expires_at = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    store._store[tx.state] = tx

    assert store.get_and_pop(tx.state) is None


def test_auth_transaction_store_get_and_pop_missing_state():
    store = AuthTransactionStore()
    assert store.get_and_pop(None) is None
    assert store.get_and_pop("missing") is None


def test_redis_auth_transaction_store_round_trip():
    store = RedisAuthTransactionStore(ttl_seconds=300)
    store._client = FakeRedis()
    tx = store.create(login_provider_id=2, redirect_uri="/dash")

    popped = store.get_and_pop(tx.state)
    assert popped.redirect_uri == "/dash"
    assert store.get_and_pop(tx.state) is None


def test_redis_auth_transaction_store_invalid_json_returns_none():
    store = RedisAuthTransactionStore()
    store._client = FakeRedis()
    store._client.setex("auth_tx:bad", 60, "not-json")

    assert store.get_and_pop("bad") is None


def test_redis_auth_transaction_store_expired_returns_none():
    store = RedisAuthTransactionStore()
    store._client = FakeRedis()
    tx = store.create(login_provider_id=1, redirect_uri="/")
    tx.expires_at = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    store._client.setex(
        f"auth_tx:{tx.state}",
        60,
        json.dumps(tx.model_dump(mode="json")),
    )

    assert store.get_and_pop(tx.state) is None


def test_redis_auth_transaction_store_lazy_client():
    store = RedisAuthTransactionStore(redis_url="redis://localhost:6379/0")
    with patch("redis.from_url", return_value=FakeRedis()) as mock_from_url:
        store.create(login_provider_id=1, redirect_uri="/")
        mock_from_url.assert_called_once()


def test_redis_refresh_token_store_lazy_client_and_edge_cases():
    store = RedisRefreshTokenStore(ttl_seconds=600)
    with patch("redis.from_url", return_value=FakeRedis()) as mock_from_url:
        store._get_client()
        mock_from_url.assert_called_once()

    store._client = FakeRedis()
    assert store.get(None) is None
    store.delete(None)

    store._client.setex("refresh_token:bad", 60, "not-json")
    assert store.get("bad") is None

    stored = store.store(
        session_id="sid-1",
        token_response=token_response(sid="sid-1"),
        issuer="https://issuer",
    )
    stored.expires_at = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    store._client.setex(
        "refresh_token:sid-1",
        60,
        json.dumps(stored.model_dump(mode="json")),
    )
    assert store.get("sid-1") is None

    assert store.update_refresh_token("missing", {"access_token": "x"}) is None


def test_redis_auth_transaction_store_get_and_pop_none_state():
    store = RedisAuthTransactionStore()
    store._client = FakeRedis()
    assert store.get_and_pop(None) is None


def test_legacy_state_resolver_paths():
    assert LegacyStateResolver.resolve(None) == (None, "/")
    assert LegacyStateResolver.resolve("not-json") == (None, "/")
    assert LegacyStateResolver.resolve('{"r": "/x"}') == (None, "/")
    assert LegacyStateResolver.resolve('{"p": 5, "r": "/ok"}') == (5, "/ok")
    assert LegacyStateResolver.resolve('{"p": 3}') == (3, "/")
