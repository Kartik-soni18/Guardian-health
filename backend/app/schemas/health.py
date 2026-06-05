"""Health check schemas."""

from typing import Any, Dict

from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str
    version: str
    timestamp: str
    mongodb: bool
    redis: bool = False


class ReadinessStatus(BaseModel):
    ready: bool
    checks: Dict[str, Any]
    timestamp: str
