"""Middleware that pulls DP_ prefixed data-policy roles off the current user and
attaches the resolved filter expressions to request.state for later use."""

import logging

import httpx
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from ..helpers.data_policy_role_helper import get_data_policy_mnemonics
from ..enums import EndpointMetadataKey

logger = logging.getLogger(__name__)

STATE_KEY_DATA_POLICY_MNEMONICS = "data_policy_mnemonics"
STATE_KEY_DATA_POLICIES = "data_policies"


class DataPolicyMiddleware(BaseHTTPMiddleware):
    """
    Executes after AuthMiddleware has run. Reads DP_ prefixed roles off the
    decoded access token, calls IAM to evaluate the filter expression, and
    exposes the result via request.state so downstream routes/handlers can consume it.
    """

    def __init__(
        self,
        app,
        *,
        iam_api_url: str,
        mnemonics_state_key: str = STATE_KEY_DATA_POLICY_MNEMONICS,
        policies_state_key: str = STATE_KEY_DATA_POLICIES,
        auth_state_key: str = "auth",
    ):
        super().__init__(app)
        self.iam_api_url = iam_api_url
        self.mnemonics_state_key = mnemonics_state_key
        self.policies_state_key = policies_state_key
        self.auth_state_key = auth_state_key

    async def dispatch(self, request: Request, call_next):
        resolved_mnemonics: list[str] = []
        resolved_policies: list[dict] = []

        # Check if the endpoint has the data_policy decorator
        should_resolve = False
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "endpoint"):
                endpoint = route.endpoint
                if hasattr(endpoint, EndpointMetadataKey.DATA_POLICY):
                    should_resolve = getattr(endpoint, EndpointMetadataKey.DATA_POLICY)

        if should_resolve:
            user = getattr(request.state, self.auth_state_key, None)
            if user and user.client_roles:
                # Get all DP_ prefixed roles from all clients
                all_roles = []
                for client_roles in user.client_roles.values():
                    all_roles.extend(client_roles)
                resolved_mnemonics = get_data_policy_mnemonics(all_roles)

                if resolved_mnemonics:
                    logger.debug(
                        "Resolved data policy mnemonics for path %s: %s",
                        request.url.path,
                        resolved_mnemonics,
                    )

                    # Call IAM to get all policies for mnemonics
                    try:
                        resolved_policies = await self._get_policies(
                            resolved_mnemonics,
                            request,
                        )
                        if resolved_policies:
                            logger.debug(
                                "Resolved %d data policies for path %s",
                                len(resolved_policies),
                                request.url.path,
                            )
                    except Exception as exc:
                        logger.error(
                            "Failed to get data policies: %s",
                            exc,
                        )

        setattr(request.state, self.mnemonics_state_key, resolved_mnemonics)
        setattr(request.state, self.policies_state_key, resolved_policies)
        return await call_next(request)

    async def _get_policies(
        self,
        mnemonics: list[str],
        request: Request,
    ) -> list[dict]:
        """Call IAM endpoint to get all policies for mnemonics."""
        url = f"{self.iam_api_url.rstrip('/')}/data-policies/evaluate_expression"
        payload = {
            "policy_mnemonics": mnemonics,
        }

        # Forward auth token from request
        headers = {}
        if hasattr(request.state, self.auth_state_key):
            auth = getattr(request.state, self.auth_state_key, None)
            if auth and hasattr(auth, "access_token"):
                headers["Authorization"] = f"Bearer {auth.access_token}"

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                logger.warning(
                    "IAM policy retrieval failed with status %s: %s",
                    resp.status_code,
                    resp.text,
                )
                return []

            result = resp.json()
            return result.get("policies", [])
