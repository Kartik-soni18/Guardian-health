"""Upstash Redis cache — REST API, Lambda-friendly."""

import asyncio
import hashlib
import json
import logging
from typing import Any, Optional

from app.config import get_settings

logger = logging.getLogger("guardian.cache")

_redis_client: Any = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    settings = get_settings()
    if not settings.upstash_redis_rest_url or not settings.upstash_redis_rest_token:
        return None

    try:
        from upstash_redis import Redis

        _redis_client = Redis(
            url=settings.upstash_redis_rest_url,
            token=settings.upstash_redis_rest_token,
        )
        return _redis_client
    except Exception as exc:
        logger.warning("Upstash Redis unavailable: %s", exc)
        return None


async def ping_redis() -> bool:
    client = _get_redis()
    if client is None:
        return False
    try:
        result = await asyncio.to_thread(client.ping)
        return bool(result)
    except Exception:
        return False


def cache_key(prefix: str, *parts: str) -> str:
    raw = ":".join(parts)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"guardian:{prefix}:{digest}"


async def cache_get(key: str) -> Optional[Any]:
    client = _get_redis()
    if client is None:
        return None
    try:
        raw = await asyncio.to_thread(client.get, key)
        if raw is None:
            return None
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception as exc:
        logger.debug("cache_get miss key=%s err=%s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl_seconds: int | None = None) -> bool:
    client = _get_redis()
    if client is None:
        return False
    settings = get_settings()
    ttl = ttl_seconds or settings.cache_ttl_seconds
    try:
        payload = json.dumps(value, default=str)
        await asyncio.to_thread(client.set, key, payload, ex=ttl)
        return True
    except Exception as exc:
        logger.debug("cache_set failed key=%s err=%s", key, exc)
        return False


async def cache_delete(key: str) -> None:
    client = _get_redis()
    if client is None:
        return
    try:
        await asyncio.to_thread(client.delete, key)
    except Exception:
        pass


def get_rate_limit_storage_uri() -> str:
    settings = get_settings()
    if settings.upstash_redis_url:
        return settings.upstash_redis_url
    return "memory://"
