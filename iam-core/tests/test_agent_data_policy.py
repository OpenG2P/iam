from iam_core.user_auth.helpers.data_policy_role_helper import AGC_ROLE_PREFIX
from iam_core.user_auth.middleware.data_policy import DataPolicyMiddleware
from iam_core.user_auth.helpers.data_policy_role_helper import get_data_policy_mnemonics


def test_agency_prefix_keeps_agc_roles_grouped_by_client():
    middleware = DataPolicyMiddleware(None, iam_api_url="http://agency.example", role_prefix=AGC_ROLE_PREFIX)
    clients, roles = middleware._clients_for_request(
        {"agency-1": ["AGC_region", "portal-admin"], "account": ["manage-account"]},
    )
    assert clients == [{"client_id": "agency-1", "policy_mnemonics": ["AGC_region"]}]
    assert roles == ["AGC_region"]


def test_staff_prefix_is_unchanged():
    assert get_data_policy_mnemonics(["DP_alpha", "AGC_region", "admin"]) == ["DP_alpha"]
