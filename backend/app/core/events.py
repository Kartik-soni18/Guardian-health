"""Application lifecycle events (startup / shutdown)."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown hooks."""
    # ── Startup ──────────────────────────────────────────────────────────────
    configure_logging()
    import logging

    logger = logging.getLogger("guardianhealth")
    logger.info("GuardianHealth starting up", extra={"env": settings.guardian_env})

    # Verify critical configuration
    if not settings.together_api_key and not settings.is_development:
        logger.error("TOGETHER_API_KEY is missing in production mode!")

    if not settings.mongodb_uri:
        logger.error("MONGODB_URI is missing!")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("GuardianHealth shutting down")
