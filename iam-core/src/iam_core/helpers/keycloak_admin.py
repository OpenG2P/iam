"""Keycloak 24 Admin REST calls for agency clients, groups, and users."""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import quote

import httpx

from .keycloak_admin_config import ProvisioningSettings

_logger = logging.getLogger("iam-provision")


class KeycloakAdminError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class KeycloakAdmin:
    def __init__(self, settings: ProvisioningSettings | None = None) -> None:
        self._settings = settings or ProvisioningSettings()
        self._tokens: dict[str, tuple[str, float]] = {}

    def _base(self) -> str:
        if not self._settings.keycloak_admin_url:
            raise KeycloakAdminError("iam_provision_keycloak_admin_url is not set")
        return self._settings.keycloak_admin_url.rstrip("/")

    async def _token(self, client: httpx.AsyncClient, realm: str) -> str:
        cached = self._tokens.get(realm)
        if cached and cached[1] > time.time() + 15:
            return cached[0]
        if not self._settings.is_configured:
            raise KeycloakAdminError("Keycloak admin client is not configured")
        response = await client.post(
            f"{self._base()}/realms/{realm}/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self._settings.keycloak_admin_client_id,
                "client_secret": self._settings.keycloak_admin_client_secret,
            },
        )
        if response.status_code >= 400:
            raise KeycloakAdminError(
                f"Admin token failed for realm {realm}: {response.text}",
                response.status_code,
            )
        body = response.json()
        self._tokens[realm] = (body["access_token"], time.time() + int(body.get("expires_in", 60)))
        return body["access_token"]

    async def _request(
        self,
        client: httpx.AsyncClient,
        method: str,
        realm: str,
        path: str,
        *,
        json_body: Any = None,
        params: dict | None = None,
        expected: tuple[int, ...] = (200, 201, 204),
    ) -> httpx.Response:
        token = await self._token(client, realm)
        response = await client.request(
            method,
            f"{self._base()}/admin/realms/{realm}{path}",
            headers={"Authorization": f"Bearer {token}"},
            json=json_body,
            params=params,
        )
        if response.status_code not in expected:
            raise KeycloakAdminError(
                f"{method} {path} failed ({response.status_code}): {response.text}",
                response.status_code,
            )
        return response

    async def create_client(self, client: httpx.AsyncClient, realm: str, client_id: str, name: str) -> str:
        """Create a confidential role-container client. Returns its UUID."""
        response = await self._request(
            client,
            "POST",
            realm,
            "/clients",
            json_body={
                "clientId": client_id,
                "name": name,
                "protocol": "openid-connect",
                "publicClient": False,
                "serviceAccountsEnabled": False,
                "standardFlowEnabled": False,
                "directAccessGrantsEnabled": False,
                "enabled": True,
            },
            expected=(201, 409),
        )
        if response.status_code == 409:
            found = await self._request(
                client,
                "GET",
                realm,
                "/clients",
                params={"clientId": client_id},
            )
            rows = found.json()
            if not rows:
                raise KeycloakAdminError(f"Client {client_id} conflicted but was not found")
            return rows[0]["id"]
        location = response.headers.get("location", "")
        if not location:
            raise KeycloakAdminError("Keycloak did not return a client location")
        return location.rstrip("/").rsplit("/", 1)[-1]

    async def create_client_role(
        self, client: httpx.AsyncClient, realm: str, client_uuid: str, role_name: str
    ) -> None:
        await self._request(
            client,
            "POST",
            realm,
            f"/clients/{client_uuid}/roles",
            json_body={"name": role_name},
            expected=(201, 409),
        )

    async def create_group(self, client: httpx.AsyncClient, realm: str, name: str) -> str:
        response = await self._request(
            client,
            "POST",
            realm,
            "/groups",
            json_body={"name": name},
            expected=(201, 409),
        )
        if response.status_code == 409:
            found = await self._request(
                client,
                "GET",
                realm,
                "/groups",
                params={"search": name, "exact": "true"},
            )
            for row in found.json():
                if row.get("name") == name:
                    return row["id"]
            raise KeycloakAdminError(f"Group {name} conflicted but was not found")
        location = response.headers.get("location", "")
        if not location:
            raise KeycloakAdminError("Keycloak did not return a group location")
        return location.rstrip("/").rsplit("/", 1)[-1]

    async def map_client_roles_to_group(
        self,
        client: httpx.AsyncClient,
        realm: str,
        group_id: str,
        client_uuid: str,
        role_names: list[str],
    ) -> None:
        if not role_names:
            return
        roles = []
        for name in role_names:
            response = await self._request(
                client,
                "GET",
                realm,
                f"/clients/{client_uuid}/roles/{quote(name, safe='')}",
            )
            roles.append(response.json())
        await self._request(
            client,
            "POST",
            realm,
            f"/groups/{group_id}/role-mappings/clients/{client_uuid}",
            json_body=roles,
        )

    async def delete_client(self, client: httpx.AsyncClient, realm: str, client_uuid: str) -> None:
        await self._request(client, "DELETE", realm, f"/clients/{client_uuid}", expected=(204, 404))

    async def find_group_id(self, client: httpx.AsyncClient, realm: str, name: str) -> str | None:
        found = await self._request(
            client,
            "GET",
            realm,
            "/groups",
            params={"search": name, "exact": "true"},
        )
        for row in found.json():
            if row.get("name") == name:
                return row["id"]
        return None

    async def delete_group(self, client: httpx.AsyncClient, realm: str, group_id: str) -> None:
        await self._request(client, "DELETE", realm, f"/groups/{group_id}", expected=(204, 404))

    async def find_user_id(self, client: httpx.AsyncClient, realm: str, email: str) -> str | None:
        response = await self._request(
            client,
            "GET",
            realm,
            "/users",
            params={"email": email, "exact": "true"},
        )
        rows = response.json()
        for row in rows:
            if str(row.get("email", "")).lower() == email.lower():
                return row["id"]
        return None

    async def create_user(
        self,
        client: httpx.AsyncClient,
        realm: str,
        *,
        email: str,
        first_name: str,
        last_name: str,
        agency_id: str | None,
    ) -> str:
        attributes = {"agency_id": [agency_id]} if agency_id else {}
        response = await self._request(
            client,
            "POST",
            realm,
            "/users",
            json_body={
                "username": email,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True,
                "emailVerified": False,
                # "requiredActions": ["VERIFY_EMAIL", "UPDATE_PASSWORD"],
                "attributes": attributes,
            },
            expected=(201, 409),
        )
        if response.status_code == 409:
            existing = await self.find_user_id(client, realm, email)
            if not existing:
                raise KeycloakAdminError(f"User {email} conflicted but was not found")
            return existing
        location = response.headers.get("location", "")
        if not location:
            raise KeycloakAdminError("Keycloak did not return a user location")
        return location.rstrip("/").rsplit("/", 1)[-1]

    async def find_client_uuid(self, client: httpx.AsyncClient, realm: str, client_id: str) -> str | None:
        response = await self._request(
            client,
            "GET",
            realm,
            "/clients",
            params={"clientId": client_id},
        )
        for row in response.json():
            if row.get("clientId") == client_id:
                return row["id"]
        return None

    async def assign_client_roles_to_user(
        self,
        client: httpx.AsyncClient,
        realm: str,
        user_id: str,
        client_uuid: str,
        role_names: list[str],
    ) -> None:
        if not role_names:
            return
        roles = []
        for name in role_names:
            response = await self._request(
                client,
                "GET",
                realm,
                f"/clients/{client_uuid}/roles/{quote(name, safe='')}",
            )
            roles.append(response.json())
        await self._request(
            client,
            "POST",
            realm,
            f"/users/{user_id}/role-mappings/clients/{client_uuid}",
            json_body=roles,
        )

    async def join_group(self, client: httpx.AsyncClient, realm: str, user_id: str, group_id: str) -> None:
        await self._request(
            client,
            "PUT",
            realm,
            f"/users/{user_id}/groups/{group_id}",
        )

    async def send_password_email(self, client: httpx.AsyncClient, realm: str, user_id: str) -> None:
        """Ask Keycloak to email a link. The person sets the password. We never see it."""
        params: dict[str, str] = {
            "lifespan": str(self._settings.action_email_lifespan_seconds),
        }
        if self._settings.action_email_client_id:
            params["client_id"] = self._settings.action_email_client_id
        if self._settings.action_email_redirect_uri:
            params["redirect_uri"] = self._settings.action_email_redirect_uri
        await self._request(
            client,
            "PUT",
            realm,
            f"/users/{user_id}/execute-actions-email",
            json_body=["VERIFY_EMAIL", "UPDATE_PASSWORD"],
            params=params,
        )
