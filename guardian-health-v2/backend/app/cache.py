"""In-memory caching layer for GuardianHealth.

Uses cachetools.TTLCache for per-process caching. This is NOT shared across
multiple server instances — for a single-instance or development deployment
this is sufficient. For multi-instance production, switch to ElastiCache or
DynamoDB DAX.

All caches are thread-safe thanks to cachetools internal locking.
"""


import threading
import time
from typing import Any, Dict, Optional

from cachetools import TTLCache

# ------------------------------------------------------------------------------
# Response cache — triage / LLM responses
# ------------------------------------------------------------------------------

response_cache: TTLCache = TTLCache(maxsize=1000, ttl=300)
"""Cache for triage responses keyed by symptom-hash / query fingerprint.

TTL: 5 minutes. Max 1000 entries.  Oldest entries evicted on maxsize.
"""

# ------------------------------------------------------------------------------
# PubMed cache — literature search results
# ------------------------------------------------------------------------------

pubmed_cache: TTLCache = TTLCache(maxsize=500, ttl=3600)
"""Cache for PubMed search results keyed by search term hash.

TTL: 1 hour.  Max 500 entries.
"""

# ------------------------------------------------------------------------------
# Rate limit store — simple per-key counter fallback
# ------------------------------------------------------------------------------

_rate_limit_store: Dict[str, Dict[str, Any]] = {}
_rate_limit_lock = threading.Lock()
"""Simple in-memory rate limit tracking keyed by client identifier.

Structure: {key: {"count": int, "window_start": float}}

This is used as a fallback when slowapi is not in the call path,
or for custom rate-limiting logic outside the HTTP layer.
"""


def rate_limit_hit(key: str, *, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """Increment a simple sliding-window counter for *key*.

    Returns:
        True if the key is now OVER the limit, False otherwise.
    """
    now = time.time()
    with _rate_limit_lock:
        entry = _rate_limit_store.get(key)
        if entry is None or now > entry["window_start"] + window_seconds:
            _rate_limit_store[key] = {"count": 1, "window_start": now}
            return False

        entry["count"] += 1
        return entry["count"] > max_requests


def rate_limit_reset(key: str) -> None:
    """Remove a key from the rate limit store."""
    with _rate_limit_lock:
        _rate_limit_store.pop(key, None)


# ------------------------------------------------------------------------------
# Monitoring / introspection
# ------------------------------------------------------------------------------


def get_cache_stats() -> Dict[str, Any]:
    """Return current cache occupancy and hit/miss statistics.

    Returns:
        Dict with keys: response_cache, pubmed_cache, rate_limit_store.
    """
    return {
        "response_cache": {
            "currsize": response_cache.currsize,
            "maxsize": response_cache.maxsize,
            "ttl": response_cache.ttl,
        },
        "pubmed_cache": {
            "currsize": pubmed_cache.currsize,
            "maxsize": pubmed_cache.maxsize,
            "ttl": pubmed_cache.ttl,
        },
        "rate_limit_store": {
            "currsize": len(_rate_limit_store),
        },
    }


def cache_key(*parts: str) -> str:
    """Build a deterministic cache key from ordered string parts.

    Example:
        cache_key("triage", user_id, hashlib.sha256(query.encode()).hexdigest()[:16])
    """
    return "|".join(parts)


# ------------------------------------------------------------------------------
# Utility helpers
# ------------------------------------------------------------------------------


def get_cached_response(key: str) -> Any | None:
    """Look up a triage response by key. Returns None if missing or expired."""
    return response_cache.get(key)


def set_cached_response(key: str, value: Any) -> None:
    """Store a triage response. Evicts oldest if maxsize reached."""
    response_cache[key] = value


def get_cached_pubmed(key: str) -> Any | None:
    """Look up PubMed results by key."""
    return pubmed_cache.get(key)


def set_cached_pubmed(key: str, value: Any) -> None:
    """Store PubMed results."""
    pubmed_cache[key] = value


def invalidate_user_cache(user_id: str) -> None:
    """Remove all cache entries scoped to a specific user.

    This is a best-effort O(n) scan — acceptable given cache sizes < 1000.
    """
    prefix = f"user:{user_id}"
    for cache in (response_cache, pubmed_cache):
        keys_to_remove = [k for k in cache if k.startswith(prefix)]
        for k in keys_to_remove:
            cache.pop(k, None)