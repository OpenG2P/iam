"""Roles representing data policies are identified by a DP_ prefix in Keycloak."""

DP_ROLE_PREFIX = "DP_"


def is_dp_role(role: str) -> bool:
    """Check whether a role string carries the DP_ prefix (case-insensitive)."""
    return str(role).strip().upper().startswith(DP_ROLE_PREFIX)


def strip_dp_prefix(role: str) -> str:
    """Remove the DP_ prefix from a role name, returning the mnemonic portion."""
    cleaned_role = str(role).strip()
    if cleaned_role.upper().startswith(DP_ROLE_PREFIX):
        return cleaned_role[len(DP_ROLE_PREFIX) :].strip()
    return cleaned_role


def get_data_policy_mnemonics(roles: list[str] | None) -> list[str]:
    """Given a list of client roles, return the deduplicated set of data-policy
    mnemonics (i.e. DP_ roles with the prefix removed), preserving first-seen order."""
    if not roles:
        return []

    seen: set[str] = set()
    mnemonics: list[str] = []

    for role in roles:
        if not is_dp_role(role):
            continue
        mnemonic = strip_dp_prefix(role)
        if mnemonic and mnemonic not in seen:
            seen.add(mnemonic)
            mnemonics.append(mnemonic)

    return mnemonics
