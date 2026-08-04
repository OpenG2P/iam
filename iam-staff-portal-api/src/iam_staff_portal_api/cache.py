from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend


def init_cache():
    FastAPICache.init(InMemoryBackend(), prefix="iam-staff-cache")


def role_cache_key(func, namespace: str, *args, **kwargs):
    """
    Build a cache key scoped only by role mnemonic.
    """
    call_args = kwargs.get("args") or args
    call_kwargs = kwargs.get("kwargs") or {}

    role_mnemonic = call_kwargs.get("role_mnemonic")
    if role_mnemonic is None and len(call_args) > 1:
        role_mnemonic = call_args[1]

    return f"{namespace}:{role_mnemonic}"


def data_policy_expression_key(func, namespace: str, *args, **kwargs):
    """
    Build a cache key for data policy expression evaluation.
    Key is based on sorted policy mnemonics.
    """
    call_args = kwargs.get("args") or args
    call_kwargs = kwargs.get("kwargs") or {}

    # Get policy_mnemonics from kwargs
    policy_mnemonics = call_kwargs.get("policy_mnemonics")

    # If not in kwargs, try to get from args
    if not policy_mnemonics and len(call_args) > 1:
        policy_mnemonics = call_args[1]

    if policy_mnemonics:
        import hashlib
        import json

        key_parts = {
            "policy_mnemonics": (
                sorted(policy_mnemonics) if isinstance(policy_mnemonics, list) else [policy_mnemonics]
            ),
        }
        key_string = json.dumps(key_parts, sort_keys=True)
        hash_key = hashlib.md5(key_string.encode()).hexdigest()
        return f"{namespace}:{hash_key}"

    return f"{namespace}:unknown"
