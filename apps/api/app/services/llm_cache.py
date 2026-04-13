"""
Simple TTL cache for LLM intelligence responses.
Keyed by SHA256 of input text. Avoids re-processing identical posts.
"""
import hashlib
import logging
import time
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class LLMResponseCache:
    def __init__(self, ttl_seconds: int = 86400, max_size: int = 10000):
        self._cache: dict[str, tuple[Any, float]] = {}  # key → (value, expiry)
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _make_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]

    def get(self, text: str) -> Any | None:
        key = self._make_key(text)
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            value, expiry = entry
            if time.monotonic() > expiry:
                del self._cache[key]
                self._misses += 1
                return None
            self._hits += 1
            return value

    def set(self, text: str, value: Any) -> None:
        key = self._make_key(text)
        with self._lock:
            # Evict oldest entries if at capacity
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
            self._cache[key] = (value, time.monotonic() + self._ttl)

    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / total, 3) if total > 0 else 0.0,
            }


# Module-level singleton
_cache: LLMResponseCache | None = None


def get_llm_cache() -> LLMResponseCache:
    global _cache
    if _cache is None:
        from app.core.config import get_settings
        settings = get_settings()
        _cache = LLMResponseCache(ttl_seconds=settings.intelligence_llm_cache_ttl_seconds)
    return _cache
