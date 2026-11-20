"""Accept only an agent login provider, then store the single agency group."""

from fastapi import Request
from jose import jwt

from iam_core.models.enum import ApplicationType
from iam_core.user_auth.helpers.claims_helper import AGENCY_ID_STATE_KEY, agency_id_from_groups
from iam_core.user_auth.middleware.validate_and_refresh import ValidateAndRefreshTokenMiddleware


class AgentTokenMiddleware(ValidateAndRefreshTokenMiddleware):
    def __init__(self, app, **kwargs):
        super().__init__(app, application_type=ApplicationType.AGENT.value, **kwargs)

    async def _authenticate_with_refresh(self, request: Request):
        principal, refreshed_tokens = await super()._authenticate_with_refresh(request)
        claims = jwt.get_unverified_claims(principal.credentials)
        setattr(request.state, AGENCY_ID_STATE_KEY, agency_id_from_groups(claims.get("groups")))
        return principal, refreshed_tokens
