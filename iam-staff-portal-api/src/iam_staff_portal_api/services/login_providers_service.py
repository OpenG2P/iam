from __future__ import annotations

from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.errors.http_exceptions import BadRequestError, NotFoundError
from openg2p_fastapi_common.service import BaseService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from iam_core.models import LoginProvider

from ..helpers.query_helper import dt_iso, paginate
from ..schemas import (
    LoginProviderCreatePayload,
    LoginProviderData,
    LoginProviderDeletePayload,
    LoginProviderIdPayload,
    LoginProviderUpdatePayload,
)


class LoginProvidersService(BaseService):
    def _encode_private_key(self, value: str | None) -> bytes | None:
        if value is None or value == "":
            return None
        return value.encode("utf-8")

    def _to_data(self, provider: LoginProvider) -> LoginProviderData:
        return LoginProviderData(
            id=provider.id,
            provider_name=provider.provider_name,
            description=provider.description,
            icon_base64=provider.icon_base64,
            client_id=provider.client_id,
            has_client_secret=bool(provider.client_secret),
            has_client_private_key=bool(provider.client_private_key),
            token_endpoint_auth_method=provider.token_endpoint_auth_method,
            issuer=provider.issuer,
            authorization_endpoint=provider.authorization_endpoint,
            token_endpoint=provider.token_endpoint,
            userinfo_endpoint=provider.userinfo_endpoint,
            server_metadata_url=provider.server_metadata_url,
            jwks_uri=provider.jwks_uri,
            adapter_name=provider.adapter_name,
            scope=provider.scope,
            enable_pkce=provider.enable_pkce,
            extra_authorize_params=provider.extra_authorize_params,
            jwt_assertion_aud=provider.jwt_assertion_aud,
            audiences=provider.audiences,
            oauth_callback_url=provider.oauth_callback_url,
            default_redirect_uri=provider.default_redirect_uri,
            keymanager_app_id=provider.keymanager_app_id,
            keymanager_ref_id=provider.keymanager_ref_id,
            active=bool(provider.active),
            created_at=dt_iso(provider.created_at),
            updated_at=dt_iso(provider.updated_at),
        )

    async def get_login_providers(self, page: int, page_size: int) -> tuple[list[LoginProviderData], int]:
        async_session = async_sessionmaker(dbengine.get())
        async with async_session() as session:
            stmt = select(LoginProvider).order_by(LoginProvider.id.desc())
            rows, total = await paginate(session, stmt, page=page, page_size=page_size)
            return [self._to_data(r) for r in rows], total

    async def get_login_provider(self, payload: LoginProviderIdPayload) -> LoginProviderData:
        async_session = async_sessionmaker(dbengine.get())
        async with async_session() as session:
            provider = await session.get(LoginProvider, payload.id)
            if provider is None:
                raise NotFoundError(message="Login provider not found")
            return self._to_data(provider)

    async def create_login_provider(self, payload: LoginProviderCreatePayload) -> LoginProviderData:
        if not payload.provider_name.strip():
            raise BadRequestError(message="provider_name is required")
        if not payload.client_id.strip():
            raise BadRequestError(message="client_id is required")
        if not payload.issuer.strip():
            raise BadRequestError(message="issuer is required")
        if not payload.oauth_callback_url.strip():
            raise BadRequestError(message="oauth_callback_url is required")

        async_session = async_sessionmaker(dbengine.get())
        async with async_session() as session:
            provider = LoginProvider(
                provider_name=payload.provider_name.strip(),
                description=payload.description,
                icon_base64=payload.icon_base64,
                client_id=payload.client_id.strip(),
                client_secret=payload.client_secret,
                client_private_key=self._encode_private_key(payload.client_private_key),
                token_endpoint_auth_method=payload.token_endpoint_auth_method,
                issuer=payload.issuer.strip(),
                authorization_endpoint=payload.authorization_endpoint,
                token_endpoint=payload.token_endpoint,
                userinfo_endpoint=payload.userinfo_endpoint,
                server_metadata_url=payload.server_metadata_url,
                jwks_uri=payload.jwks_uri,
                adapter_name=payload.adapter_name,
                scope=payload.scope,
                enable_pkce=payload.enable_pkce,
                extra_authorize_params=payload.extra_authorize_params,
                jwt_assertion_aud=payload.jwt_assertion_aud,
                audiences=payload.audiences,
                oauth_callback_url=payload.oauth_callback_url.strip(),
                default_redirect_uri=payload.default_redirect_uri,
                active=True,
            )
            session.add(provider)
            await session.commit()
            await session.refresh(provider)
            return self._to_data(provider)

    async def update_login_provider(self, payload: LoginProviderUpdatePayload) -> LoginProviderData:
        async_session = async_sessionmaker(dbengine.get())
        async with async_session() as session:
            provider = await session.get(LoginProvider, payload.id)
            if provider is None:
                raise NotFoundError(message="Login provider not found")

            for field in (
                "provider_name",
                "description",
                "icon_base64",
                "client_id",
                "token_endpoint_auth_method",
                "issuer",
                "authorization_endpoint",
                "token_endpoint",
                "userinfo_endpoint",
                "server_metadata_url",
                "jwks_uri",
                "adapter_name",
                "scope",
                "enable_pkce",
                "extra_authorize_params",
                "jwt_assertion_aud",
                "audiences",
                "oauth_callback_url",
                "default_redirect_uri",
            ):
                value = getattr(payload, field)
                if value is not None:
                    setattr(provider, field, value)

            if payload.client_secret:
                provider.client_secret = payload.client_secret
            if payload.client_private_key:
                provider.client_private_key = self._encode_private_key(payload.client_private_key)

            await session.commit()
            await session.refresh(provider)
            return self._to_data(provider)

    async def delete_login_provider(self, payload: LoginProviderDeletePayload) -> LoginProviderData:
        async_session = async_sessionmaker(dbengine.get())
        async with async_session() as session:
            provider = await session.get(LoginProvider, payload.id)
            if provider is None:
                raise NotFoundError(message="Login provider not found")
            provider_data = self._to_data(provider)
            await session.delete(provider)
            await session.commit()
        return provider_data
