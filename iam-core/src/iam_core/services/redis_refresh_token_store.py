import json
from datetime import datetime, timedelta, timezone

from openg2p_fastapi_common.service import BaseService

from iam_core.schemas import RefreshTokenRecord
from iam_core.user_auth.config import Settings

_config = Settings.get_config(strict=False)
REDIS_KEY_PREFIX = "refresh_token:"


class RedisRefreshTokenStore(BaseService):
    """Redis-backed refresh token store keyed by OIDC session id."""

    def __init__(self, ttl_seconds: int | None = None, redis_url: str | None = None):
        super().__init__()
        self._ttl = ttl_seconds or getattr(_config, "auth_refresh_token_ttl_seconds", 1800)
        self._redis_url = redis_url or getattr(_config, "auth_redis_url", "redis://localhost:6379/0")
        self._client = None

    def _get_client(self):
        if self._client is None:
            import redis

            self._client = redis.from_url(
                self._redis_url,
                decode_responses=True,
            )
        return self._client

    @staticmethod
    def _ttl_for_token_response(token_response: dict, default_ttl: int) -> int:
        refresh_expires_in = token_response.get("refresh_expires_in")
        if refresh_expires_in:
            return int(refresh_expires_in)
        return default_ttl

    def store(
        self,
        *,
        session_id: str,
        token_response: dict,
        issuer: str,
    ) -> RefreshTokenRecord:
        now = datetime.now(tz=timezone.utc)
        ttl = self._ttl_for_token_response(token_response, self._ttl)
        stored_refresh_token = RefreshTokenRecord(
            session_id=session_id,
            refresh_token=token_response["refresh_token"],
            issuer=issuer,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl),
        )
        key = f"{REDIS_KEY_PREFIX}{stored_refresh_token.session_id}"
        self._get_client().setex(
            key,
            ttl,
            json.dumps(stored_refresh_token.model_dump(mode="json")),
        )
        return stored_refresh_token

    def get(self, session_id: str | None) -> RefreshTokenRecord | None:
        if not session_id:
            return None
        key = f"{REDIS_KEY_PREFIX}{session_id}"
        raw = self._get_client().get(key)
        if raw is None:
            return None
        try:
            stored_refresh_token = RefreshTokenRecord.model_validate(json.loads(raw))
            if datetime.now(tz=timezone.utc) > stored_refresh_token.expires_at:
                self.delete(session_id)
                return None
            return stored_refresh_token
        except Exception:
            return None

    def update_refresh_token(
        self,
        session_id: str,
        token_response: dict,
    ) -> RefreshTokenRecord | None:
        stored_refresh_token = self.get(session_id)
        if stored_refresh_token is None:
            return None

        now = datetime.now(tz=timezone.utc)
        ttl = self._ttl_for_token_response(token_response, self._ttl)
        stored_refresh_token = stored_refresh_token.model_copy(
            update={
                "refresh_token": token_response.get("refresh_token", stored_refresh_token.refresh_token),
                "expires_at": now + timedelta(seconds=ttl),
            }
        )
        key = f"{REDIS_KEY_PREFIX}{session_id}"
        self._get_client().setex(
            key,
            ttl,
            json.dumps(stored_refresh_token.model_dump(mode="json")),
        )
        return stored_refresh_token

    def delete(self, session_id: str | None) -> None:
        if not session_id:
            return
        self._get_client().delete(f"{REDIS_KEY_PREFIX}{session_id}")
