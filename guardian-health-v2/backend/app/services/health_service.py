"""GuardianHealth v2 Health Check Service — NO external dependencies."""


from datetime import datetime, timezone
from typing import Any, Dict

from app.core.config import settings
from app.db.dynamodb import DynamoDBManager


_request_counts: Dict[str, int] = {}
_cache_hits = 0
_cache_misses = 0


class HealthService:
    """Health monitoring and metrics."""

    def __init__(self, db: DynamoDBManager) -> None:
        self.db = db

    async def get_status(self) -> Dict[str, Any]:
        """Overall health status."""
        dynamodb_ok = await self.db.ping()
        return {
            "status": "healthy" if dynamodb_ok else "degraded",
            "version": settings.APP_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dynamodb": dynamodb_ok,
        }

    async def get_readiness(self) -> Dict[str, Any]:
        """Readiness probe for orchestrators."""
        dynamodb_ok = await self.db.ping()
        checks = {
            "dynamodb": dynamodb_ok,
            "configuration": True,
        }
        return {
            "ready": all(checks.values()),
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_liveness(self) -> Dict[str, Any]:
        """Liveness probe — always returns OK if process is running."""
        return {
            "alive": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Return in-memory metrics."""
        global _cache_hits, _cache_misses, _request_counts
        return {
            "cache_stats": {
                "hits": _cache_hits,
                "misses": _cache_misses,
                "hit_rate": _cache_hits / max(_cache_hits + _cache_misses, 1),
            },
            "request_counts": dict(_request_counts),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def record_request(endpoint: str) -> None:
        """Increment request counter for an endpoint."""
        global _request_counts
        _request_counts[endpoint] = _request_counts.get(endpoint, 0) + 1

    @staticmethod
    def record_cache_hit() -> None:
        global _cache_hits
        _cache_hits += 1

    @staticmethod
    def record_cache_miss() -> None:
        global _cache_misses
        _cache_misses += 1

    @staticmethod
    def reset_metrics() -> None:
        """Reset all metrics (useful in tests)."""
        global _cache_hits, _cache_misses, _request_counts
        _cache_hits = 0
        _cache_misses = 0
        _request_counts = {}
