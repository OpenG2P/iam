"""
Sync IAM roles to Keycloak as client roles.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import Settings
from openg2p_fastapi_common.errors.http_exceptions import BadRequestError

_logger = logging.getLogger("iam-keycloak-role")


class KeycloakHelper:
    """Keycloak Admin REST client for role synchronization."""

    def __init__(self, auth_token: str) -> None:
        self._config = Settings.get_config(strict=False)
        self._auth_token = auth_token

    @property
    def is_configured(self) -> bool:
        return bool(self._config.keycloak_admin_url)

    def _admin_base_url(self) -> str:
        return f"{self._config.keycloak_admin_url.rstrip('/')}/admin"

    async def _admin_request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: dict | None = None,
    ) -> Any:
        url = f"{self._admin_base_url()}{path}"
        headers = {"Authorization": f"Bearer {self._auth_token}"}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.request(
                method,
                url,
                headers=headers,
                json=json_body,
                params=params,
            )
        if resp.status_code == 204:
            return None
        if resp.status_code == 409:
            return {"conflict": True, "body": resp.text}
        if resp.status_code == 404:
            return {"not_found": True, "body": resp.text}
        if resp.status_code >= 400:
            raise BadRequestError(message=resp.text)
        if not resp.content:
            return None
        return resp.json()

    async def _resolve_client_uuid(self, client_id: str) -> str:
        realm = self._config.keycloak_realm
        clients = await self._admin_request(
            "GET",
            f"/realms/{realm}/clients",
            params={"clientId": client_id},
        )
        if not clients:
            raise BadRequestError(message=f"Keycloak client not found: {client_id}")
        return clients[0]["id"]

    async def create_role(
        self,
        role_name: str,
        application_mnemonic: str,
        *,
        role_description: str | None = None,
    ) -> tuple[str, bool]:
        """
        Create client role on the application's Keycloak client if missing.
        Returns (role_name, already_existed).
        """
        if not self.is_configured:
            _logger.debug(
                "Keycloak role sync disabled or not configured; skipping %s",
                role_name,
            )
            return role_name, False

        client_id = application_mnemonic
        client_uuid = await self._resolve_client_uuid(client_id)
        realm = self._config.keycloak_realm

        body: dict[str, str] = {"name": role_name}
        if role_description:
            body["description"] = role_description

        result = await self._admin_request(
            "POST",
            f"/realms/{realm}/clients/{client_uuid}/roles",
            json_body=body,
        )
        if isinstance(result, dict) and result.get("conflict"):
            _logger.info(
                "Keycloak client role %s already exists on client %s",
                role_name,
                client_id,
            )
            return role_name, True
        else:
            _logger.info(
                "Created Keycloak client role %s on client %s",
                role_name,
                client_id,
            )
        return role_name, False

    async def delete_role(
        self,
        role_name: str,
        application_mnemonic: str,
    ) -> bool:
        """Remove client role from the application's Keycloak client.
        Returns True if deleted, False if not found."""
        if not self.is_configured:
            _logger.debug(
                "Keycloak role sync disabled or not configured; skipping delete %s",
                role_name,
            )
            return False

        client_id = application_mnemonic
        client_uuid = await self._resolve_client_uuid(client_id)
        realm = self._config.keycloak_realm

        result = await self._admin_request(
            "DELETE",
            f"/realms/{realm}/clients/{client_uuid}/roles/{role_name}",
        )
        if isinstance(result, dict) and result.get("not_found"):
            _logger.info(
                "Keycloak client role %s not found on client %s (already deleted)",
                role_name,
                client_id,
            )
            return False
        _logger.info(
            "Deleted Keycloak client role %s from client %s",
            role_name,
            client_id,
        )
        return True

    async def delete_client(self, client_id: str) -> bool:
        """Delete a Keycloak client by its client_id.
        Returns True if deleted, False if not found."""
        if not self.is_configured:
            _logger.debug(
                "Keycloak role sync disabled or not configured; skipping delete client %s",
                client_id,
            )
            return False

        realm = self._config.keycloak_realm
        clients = await self._admin_request(
            "GET",
            f"/realms/{realm}/clients",
            params={"clientId": client_id},
        )
        if not clients:
            _logger.info("Keycloak client not found: %s (already deleted)", client_id)
            return False

        client_uuid = clients[0]["id"]
        await self._admin_request(
            "DELETE",
            f"/realms/{realm}/clients/{client_uuid}",
        )
        _logger.info("Deleted Keycloak client: %s", client_id)
        return True

    async def create_client(
        self,
        client_id: str,
        *,
        description: str | None = None,
    ) -> tuple[str, bool]:
        """Create a Keycloak client by its client_id.
        Returns (client_id, already_existed)."""
        if not self.is_configured:
            _logger.debug(
                "Keycloak role sync disabled or not configured; skipping create client %s",
                client_id,
            )
            return client_id, False

        realm = self._config.keycloak_realm

        # Check if client already exists
        clients = await self._admin_request(
            "GET",
            f"/realms/{realm}/clients",
            params={"clientId": client_id},
        )
        if clients:
            _logger.info("Keycloak client already exists: %s", client_id)
            return client_id, True

        body: dict[str, Any] = {
            "clientId": client_id,
            "enabled": True,
            "clientAuthenticatorType": "client-secret",
            "secret": "",  # Will be set by Keycloak
            "protocol": "openid-connect",
            "publicClient": False,
        }
        if description:
            body["description"] = description

        await self._admin_request(
            "POST",
            f"/realms/{realm}/clients",
            json_body=body,
        )
        _logger.info("Created Keycloak client: %s", client_id)
        return client_id, False
