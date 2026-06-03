"""
GuardianHealth v2 - Celery Configuration

Background task processing with Redis as broker and result backend.
Tasks are routed to named queues based on their workload characteristics.
"""

from __future__ import annotations

from celery import Celery

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

_settings = get_settings()

# ---------------------------------------------------------------------------
# Celery app instance
# ---------------------------------------------------------------------------

celery_app = Celery(
    "guardian_health",
    broker=_settings.celery_broker_url,
    backend=_settings.celery_result_backend,
    include=[
        "app.tasks.audit_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.ml_tasks",
    ],
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Result backend
    result_expires=3600,  # 1 hour
    result_backend_always_retry=True,
    # Routing
    task_default_queue="default",
    task_routes={
        "app.tasks.audit_tasks.*": {"queue": "audit"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.tasks.ml_tasks.*": {"queue": "ml"},
    },
    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "app.tasks.audit_tasks.cleanup_expired_sessions",
            "schedule": 3600.0,  # every hour
        },
        "health-check-ping": {
            "task": "app.tasks.audit_tasks.health_check_ping",
            "schedule": 60.0,  # every minute
        },
    },
    # Redis broker settings
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        "visibility_timeout": 43200,  # 12 hours
    },
)

logger.info(
    "Celery configured: broker=%s queues=%s",
    _settings.celery_broker_url,
    list(celery_app.conf.task_routes.keys()),
)
