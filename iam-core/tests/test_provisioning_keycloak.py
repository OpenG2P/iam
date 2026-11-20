import httpx
import pytest

from iam_core.helpers.keycloak_admin import KeycloakAdmin
from iam_core.helpers.keycloak_admin_config import ProvisioningSettings


def _settings() -> ProvisioningSettings:
    return ProvisioningSettings(
        keycloak_admin_url="https://kc.example",
        keycloak_admin_client_id="iam-admin",
        keycloak_admin_client_secret="secret",
        action_email_client_id="agency-portal",
        action_email_redirect_uri="https://agency.example/home",
    )


@pytest.mark.asyncio
async def test_create_user_sends_password_actions_and_can_join_a_group():
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if request.url.path.endswith("/token"):
            return httpx.Response(200, json={"access_token": "t", "expires_in": 60})
        if request.method == "POST" and request.url.path.endswith("/users"):
            return httpx.Response(
                201, headers={"location": "https://kc.example/admin/realms/agent/users/user-1"}
            )
        if request.method == "PUT" and request.url.path.endswith("/groups/group-1"):
            return httpx.Response(204)
        if request.url.path.endswith("/execute-actions-email"):
            assert request.url.params["client_id"] == "agency-portal"
            assert b"UPDATE_PASSWORD" in request.content
            return httpx.Response(204)
        return httpx.Response(500, text=str(request.url))

    admin = KeycloakAdmin(_settings())
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        user_id = await admin.create_user(
            client,
            "agent",
            email="a@agency.example",
            first_name="Ada",
            last_name="Lovelace",
            agency_id="agency-1",
        )
        await admin.join_group(client, "agent", user_id, "group-1")
        await admin.send_password_email(client, "agent", user_id)

    assert user_id == "user-1"
    assert any(path.endswith("/users/user-1/execute-actions-email") for _, path in calls)


@pytest.mark.asyncio
async def test_client_and_group_are_separate_calls():
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(f"{request.method} {request.url.path}")
        if request.url.path.endswith("/token"):
            return httpx.Response(200, json={"access_token": "t", "expires_in": 60})
        if request.method == "POST" and request.url.path.endswith("/clients"):
            return httpx.Response(
                201, headers={"location": "https://kc.example/admin/realms/agent/clients/client-uuid"}
            )
        if request.method == "POST" and "/roles" in request.url.path:
            return httpx.Response(201)
        if request.method == "POST" and request.url.path.endswith("/groups"):
            return httpx.Response(
                201, headers={"location": "https://kc.example/admin/realms/agent/groups/group-uuid"}
            )
        return httpx.Response(500, text=str(request.url))

    admin = KeycloakAdmin(_settings())
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        client_uuid = await admin.create_client(client, "agent", "agency-1", "North")
        await admin.create_client_role(client, "agent", client_uuid, "AGC_region")
        group_id = await admin.create_group(client, "agent", "agency-1")

    assert client_uuid == "client-uuid"
    assert group_id == "group-uuid"
    assert seen[1].endswith("/clients")
    assert seen[-1].endswith("/groups")
