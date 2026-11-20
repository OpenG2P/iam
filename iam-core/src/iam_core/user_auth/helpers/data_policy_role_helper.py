"""Roles representing data policies are identified by a DP_ prefix in Keycloak."""

DP_ROLE_PREFIX = "DP_"
AGC_ROLE_PREFIX = "AGC_"


def is_dp_role(role: str, prefix: str = DP_ROLE_PREFIX) -> bool:
    """Check whether a role string carries the policy prefix (case-insensitive)."""
    return str(role).strip().upper().startswith(prefix.upper())


def strip_dp_prefix(role: str) -> str:
    """Remove the DP_ prefix from a role name, returning the mnemonic portion."""
    cleaned_role = str(role).strip()
    if cleaned_role.upper().startswith(DP_ROLE_PREFIX):
        return cleaned_role[len(DP_ROLE_PREFIX) :].strip()
    return cleaned_role


def get_data_policy_mnemonics(roles: list[str] | None, prefix: str = DP_ROLE_PREFIX) -> list[str]:
    """Return deduplicated policy role names that start with ``prefix``, in first-seen order."""
    if not roles:
        return []

    seen: set[str] = set()
    mnemonics: list[str] = []

    for role in roles:
        if not is_dp_role(role, prefix):
            continue
        cleaned_role = str(role).strip()
        if cleaned_role and cleaned_role not in seen:
            seen.add(cleaned_role)
            mnemonics.append(cleaned_role)

    return mnemonics
