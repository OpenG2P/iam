from datetime import datetime

from pydantic import BaseModel


class RefreshTokenRecord(BaseModel):
    session_id: str  # OIDC session id (``sid`` claim); Redis lookup key
    refresh_token: str
    issuer: str
    created_at: datetime
    expires_at: datetime  # refresh token expiry (SSO idle timeout)
