"""GuardianHealth v2 Health Router — Status, readiness, liveness, metrics."""

from fastapi import APIRouter, Depends, Request

from app.config import get_settings
from app.core.dependencies import get_dynamodb_manager, limiter
from app.schemas.health import HealthMetrics, HealthStatus, ReadinessStatus
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["health"])


def _health_service(db=Depends(get_dynamodb_manager)) -> HealthService:
    return HealthService(db)


# ---------------------------------------------------------------------------
# GET /health — Overall status
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=HealthStatus,
    summary="Health status",
    response_description="Application health with DynamoDB connectivity",
)
@limiter.limit(get_settings().rate_limit_health)
async def health(
    request: Request,
    health_svc: HealthService = Depends(_health_service),
) -> HealthStatus:
    """Return overall health status including DynamoDB connectivity."""
    data = await health_svc.get_status()
    return HealthStatus.model_validate(data)


# ---------------------------------------------------------------------------
# GET /health/ready — Readiness probe
# ---------------------------------------------------------------------------
@router.get(
    "/ready",
    response_model=ReadinessStatus,
    summary="Readiness probe",
    response_description="Ready status for orchestrators (k8s, etc.)",
)
@limiter.limit(get_settings().rate_limit_health)
async def ready(
    request: Request,
    health_svc: HealthService = Depends(_health_service),
) -> ReadinessStatus:
    """Kubernetes-style readiness probe."""
    data = await health_svc.get_readiness()
    return ReadinessStatus.model_validate(data)


# ---------------------------------------------------------------------------
# GET /health/live — Liveness probe
# ---------------------------------------------------------------------------
@router.get(
    "/live",
    summary="Liveness probe",
    response_description="Always returns 200 if process is alive",
)
@limiter.limit(get_settings().rate_limit_health)
async def live(
    request: Request,
    health_svc: HealthService = Depends(_health_service),
) -> dict:
    """Kubernetes-style liveness probe."""
    return health_svc.get_liveness()


# ---------------------------------------------------------------------------
# GET /health/metrics — In-memory metrics
# ---------------------------------------------------------------------------
@router.get(
    "/metrics",
    response_model=HealthMetrics,
    summary="Application metrics",
    response_description="Cache stats and request counts",
)
@limiter.limit(get_settings().rate_limit_health)
async def metrics(
    request: Request,
    health_svc: HealthService = Depends(_health_service),
) -> HealthMetrics:
    """Return in-memory metrics for monitoring."""
    data = health_svc.get_metrics()
    return HealthMetrics.model_validate(data)
