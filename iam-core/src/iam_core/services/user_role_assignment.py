"""Assign existing client roles to a user. Staff and agency APIs choose the client and the role names."""

import httpx

from iam_core.helpers.keycloak_admin import KeycloakAdmin, KeycloakAdminError
from iam_core.helpers.keycloak_admin_config import ProvisioningSettings


async def assign_client_roles(
    *,
    realm: str,
    client_id: str,
    keycloak_user_id: str,
    role_names: list[str],
) -> None:
    settings = ProvisioningSettings()
    admin = KeycloakAdmin(settings)
    async with httpx.AsyncClient(timeout=30) as client:
        client_uuid = await admin.find_client_uuid(client, realm, client_id)
        if not client_uuid:
            raise KeycloakAdminError(f"Client {client_id} was not found")
        await admin.assign_client_roles_to_user(
            client,
            realm,
            keycloak_user_id,
            client_uuid,
            role_names,
        )
