import time
from typing import Any


class TTLCache:
    """Minimal in-memory TTL cache. Good enough for a single-instance MVP;
    swap for Redis if the service is ever run with multiple replicas."""

    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        self._store[key] = (time.monotonic() + ttl_seconds, value)

    @staticmethod
    def build_key(*parts: str) -> str:
        return "|".join(p.lower().strip() for p in parts)
