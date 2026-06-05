"""Health probes."""

from fastapi import APIRouter, Depends, Request

from app.config import get_settings
from app.core.dependencies import limiter
from app.schemas.health import HealthStatus, ReadinessStatus
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthStatus)
@limiter.limit(get_settings().rate_limit_health)
async def health(request: Request, health_svc: HealthService = Depends(HealthService)) -> HealthStatus:
    return HealthStatus.model_validate(await health_svc.get_status())


@router.get("/ready", response_model=ReadinessStatus)
@limiter.limit(get_settings().rate_limit_health)
async def ready(request: Request, health_svc: HealthService = Depends(HealthService)) -> ReadinessStatus:
    return ReadinessStatus.model_validate(await health_svc.get_readiness())


@router.get("/live")
@limiter.limit(get_settings().rate_limit_health)
async def live(request: Request, health_svc: HealthService = Depends(HealthService)) -> dict:
    return health_svc.get_liveness()
