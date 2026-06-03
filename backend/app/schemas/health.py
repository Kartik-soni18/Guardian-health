"""Health check schema definitions."""

from typing import Any, Dict

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Overall application health status."""

    status: str = "healthy"
    version: str = "2.0.0"
    timestamp: str = ""
    dynamodb: bool = True


class ReadinessStatus(BaseModel):
    """Kubernetes-style readiness probe response."""

    ready: bool = True
    checks: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = ""


class HealthMetrics(BaseModel):
    """In-memory application metrics."""

    cache_stats: Dict[str, Any] = Field(default_factory=dict)
    request_counts: Dict[str, int] = Field(default_factory=dict)
    timestamp: str = ""
