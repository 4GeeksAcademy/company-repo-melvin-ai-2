"""In-memory TTL cache for shared Brasaland catalog reads.

Do not store /auth/me, user rows, or profiles here. Those responses differ
per signed-in operator. A shared key would leak one session to another.
"""

from __future__ import annotations

import time
from typing import Any

PRODUCTS_PREFIX = "inventory:products:"
SUPPLIERS_PREFIX = "suppliers:list:"
# Backstop only. Writes delete the prefix immediately.
CATALOG_TTL_SECONDS = 60.0


class TtlCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if time.monotonic() >= expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        self._store[key] = (time.monotonic() + ttl_seconds, value)

    def delete_prefix(self, prefix: str) -> None:
        for key in [name for name in self._store if name.startswith(prefix)]:
            del self._store[key]

    def clear(self) -> None:
        self._store.clear()


catalog_cache = TtlCache()


def invalidate_product_catalog() -> None:
    catalog_cache.delete_prefix(PRODUCTS_PREFIX)


def invalidate_supplier_catalog() -> None:
    catalog_cache.delete_prefix(SUPPLIERS_PREFIX)
