"""Health check service."""

from datetime import datetime, timezone
from typing import Any, Dict

from app.cache import ping_redis
from app.config import get_settings
from app.db.mongodb import ping_mongodb


class HealthService:
    async def get_status(self) -> Dict[str, Any]:
        mongo_ok = await ping_mongodb()
        redis_ok = await ping_redis()
        settings = get_settings()
        healthy = mongo_ok and (redis_ok or not settings.upstash_redis_rest_url)
        return {
            "status": "healthy" if healthy else "degraded",
            "version": settings.app_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mongodb": mongo_ok,
            "redis": redis_ok,
        }

    async def get_readiness(self) -> Dict[str, Any]:
        mongo_ok = await ping_mongodb()
        redis_ok = await ping_redis()
        settings = get_settings()
        checks = {
            "mongodb": mongo_ok,
            "redis": redis_ok if settings.upstash_redis_rest_url else True,
            "configuration": True,
        }
        return {
            "ready": all(checks.values()),
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_liveness(self) -> Dict[str, Any]:
        return {
            "alive": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
