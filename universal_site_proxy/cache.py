"""Simple time-to-live cache implementation.

This module defines a very lightweight TTL cache used by the HTTP runtime to
store GET request results for a configurable period. It is deliberately
minimal and stores values in memory without eviction strategies beyond TTL
expiration.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Tuple


class TTLCache:
    """A dictionary-like cache with expiration times.

    Entries are stored with an expiration timestamp and automatically removed
    when accessed after their TTL has elapsed. This class is not thread-safe
    but is sufficient for the proxy's use cases.
    """

    def __init__(self) -> None:
        self.store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self.store.get(key)
        if not item:
            return None
        expires_at, value = item
        if time.time() >= expires_at:
            # Remove expired entry
            self.store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl_sec: int) -> None:
        expires_at = time.time() + ttl_sec
        self.store[key] = (expires_at, value)

    def clear(self) -> None:
        """Remove all cached entries."""
        self.store.clear()
