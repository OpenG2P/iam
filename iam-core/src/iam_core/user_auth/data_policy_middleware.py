"""Middleware that pulls DP_ prefixed data-policy roles off the current user and
attaches the resulting mnemonics to request.state for later use."""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .helpers.data_policy_role_helper import get_data_policy_mnemonics

logger = logging.getLogger(__name__)

STATE_KEY_DATA_POLICY_MNEMONICS = "data_policy_mnemonics"


class DataPolicyMiddleware(BaseHTTPMiddleware):
    """
    Executes after AuthMiddleware has run. Reads DP_ prefixed roles off the
    decoded access token and exposes the derived mnemonics via request.state
    so downstream routes/handlers can consume them.
    """

    def __init__(
        self,
        app,
        *,
        client_id: str | None = None,
        state_key: str = STATE_KEY_DATA_POLICY_MNEMONICS,
        auth_state_key: str = "auth",
    ):
        super().__init__(app)
        self.client_id = (client_id or "").strip()
        self.state_key = state_key
        self.auth_state_key = auth_state_key

    async def dispatch(self, request: Request, call_next):
        resolved_mnemonics: list[str] = []

        user = getattr(request.state, self.auth_state_key, None)
        if user and user.client_roles and self.client_id:
            roles_for_client = list(user.client_roles.get(self.client_id, []))
            resolved_mnemonics = get_data_policy_mnemonics(roles_for_client)

            if resolved_mnemonics:
                logger.debug(
                    "Resolved data policy mnemonics for path %s: %s",
                    request.url.path,
                    resolved_mnemonics,
                )

        setattr(request.state, self.state_key, resolved_mnemonics)
        return await call_next(request)
