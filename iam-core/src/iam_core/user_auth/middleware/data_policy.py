"""Data-policy middleware shared by staff and agency. Only the role prefix differs."""

import logging

import httpx
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from iam_core.user_auth.enums import EndpointMetadataKey
from openg2p_fastapi_common.errors.http_exceptions import BadRequestError

from iam_core.user_auth.helpers.data_policy_role_helper import (
    AGC_ROLE_PREFIX,
    DP_ROLE_PREFIX,
)

logger = logging.getLogger(__name__)

STATE_KEY_DATA_POLICY_MNEMONICS = "data_policy_mnemonics"
STATE_KEY_DATA_POLICIES = "data_policies"

__all__ = [
    "AGC_ROLE_PREFIX",
    "DP_ROLE_PREFIX",
    "STATE_KEY_DATA_POLICIES",
    "STATE_KEY_DATA_POLICY_MNEMONICS",
    "DataPolicyMiddleware",
]


class DataPolicyMiddleware(BaseHTTPMiddleware):
    """Read policy roles off every client on the token. The prefix selects them.

    Staff passes ``DP_``. An agency passes ``AGC_``.
    """

    def __init__(
        self,
        app,
        *,
        iam_api_url: str,
        role_prefix: str = DP_ROLE_PREFIX,
        mnemonics_state_key: str = STATE_KEY_DATA_POLICY_MNEMONICS,
        policies_state_key: str = STATE_KEY_DATA_POLICIES,
        auth_state_key: str = "auth",
    ):
        super().__init__(app)
        self.iam_api_url = iam_api_url
        self.role_prefix = role_prefix
        self.mnemonics_state_key = mnemonics_state_key
        self.policies_state_key = policies_state_key
        self.auth_state_key = auth_state_key

    def _clients_for_request(self, client_roles: dict) -> tuple[list[dict], list[str]]:
        """Keep roles with this prefix, grouped by the client they came from."""
        prefix = self.role_prefix.upper()
        clients: list[dict] = []
        role_names: list[str] = []
        seen: set[str] = set()
        for client_id, roles in sorted((client_roles or {}).items()):
            mnemonics: list[str] = []
            for role in roles or []:
                text = str(role).strip()
                if not text.upper().startswith(prefix):
                    continue
                mnemonics.append(text)
                if text not in seen:
                    seen.add(text)
                    role_names.append(text)
            if client_id and mnemonics:
                clients.append({"client_id": str(client_id), "policy_mnemonics": mnemonics})
        return clients, role_names

    async def dispatch(self, request: Request, call_next):
        resolved_mnemonics: list[str] = []
        resolved_policies: list[dict] = []

        if self._endpoint_wants_policy(request):
            user = getattr(request.state, self.auth_state_key, None)
            client_roles = getattr(user, "client_roles", None) if user else None
            if client_roles:
                clients, resolved_mnemonics = self._clients_for_request(client_roles)
                if clients:
                    resolved_policies = await self._get_policies(clients, request)

        setattr(request.state, self.mnemonics_state_key, resolved_mnemonics)
        setattr(request.state, self.policies_state_key, resolved_policies)
        return await call_next(request)

    def _endpoint_wants_policy(self, request: Request) -> bool:
        route = request.scope.get("route") if hasattr(request, "scope") else None
        endpoint = getattr(route, "endpoint", None)
        return bool(endpoint and getattr(endpoint, EndpointMetadataKey.DATA_POLICY, False))

    async def _get_policies(self, clients: list[dict], request: Request) -> list[dict]:
        url = f"{self.iam_api_url.rstrip('/')}/data-policies/evaluate_expression"
        headers = {}
        auth = getattr(request.state, self.auth_state_key, None)
        access_token = getattr(auth, "access_token", None) or getattr(auth, "credentials", None)
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json={"clients": clients}, headers=headers)
        except Exception:
            logger.exception("Policy lookup failed")
            return []
        if response.status_code == 400:
            message = "Policy lookup failed"
            try:
                message = response.json().get("message") or message
            except Exception:
                pass
            raise BadRequestError(message=str(message))
        if response.status_code >= 400:
            logger.warning("Policy lookup failed with status %s: %s", response.status_code, response.text)
            return []
        return response.json().get("policies", [])
