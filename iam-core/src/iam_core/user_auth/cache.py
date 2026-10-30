from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend


def init_cache() -> None:
    FastAPICache.init(InMemoryBackend(), prefix="iam-cache")
