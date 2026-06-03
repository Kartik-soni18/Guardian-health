"""
GuardianHealth v2 - Async Redis Client

Provides a connection-pooled async Redis client with health checking.
Uses redis.asyncio for full async compatibility with FastAPI.
"""

from __future__ import annotations

from redis.asyncio import Redis, ConnectionPool

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_redis_pool: ConnectionPool | None = None
_redis_client: Redis | None = None


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------


def _get_pool() -> ConnectionPool:
    """Return the singleton Redis connection pool, creating it if needed."""
    global _redis_pool  # noqa: PLW0603

    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=50,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30,
            decode_responses=True,
        )
        logger.info("Redis connection pool created: %s", settings.redis_url)

    return _redis_pool


def get_redis() -> Redis:
    """
    Return a Redis client backed by the shared connection pool.

    The caller should use the client as an async context manager or
    await individual commands.  The pool handles connection reuse.
    """
    pool = _get_pool()
    return Redis(connection_pool=pool)


async def close_redis() -> None:
    """
    Close the Redis connection pool.

    Should be called during application shutdown to release connections.
    """
    global _redis_pool, _redis_client  # noqa: PLW0603

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None

    if _redis_pool is not None:
        await _redis_pool.disconnect(inuse_connections=True)
        _redis_pool = None
        logger.info("Redis connection pool closed")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


async def health_check() -> dict[str, str | bool]:
    """
    Perform a Redis health check via PING.

    Returns:
        A dict with keys: status (str), ping_ok (bool).
    """
    try:
        redis = get_redis()
        pong = await redis.ping()
        return {"status": "connected", "ping_ok": pong is True}
    except Exception as exc:
        logger.error("Redis health check failed: %s", exc)
        return {"status": "disconnected", "ping_ok": False, "error": str(exc)}
