from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar


T = TypeVar("T")


@dataclass
class _CacheItem(Generic[T]):
    value: T
    expires_at: float


class TTLCache(Generic[T]):
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl_seconds = max(0, int(ttl_seconds))
        self._item: Optional[_CacheItem[T]] = None

    def get(self) -> Optional[T]:
        # Renvoie la valeur si encore valide
        if self._item is None:
            return None
        if time.time() >= self._item.expires_at:
            self._item = None
            return None
        return self._item.value

    def set(self, value: T) -> None:
        # Stocke la valeur avec expiration
        self._item = _CacheItem(
            value=value,
            expires_at=time.time() + self._ttl_seconds,
        )

    def clear(self) -> None:
        self._item = None
