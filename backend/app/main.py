"""GuardianHealth v2 FastAPI Application — AWS-free, DynamoDB only."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.core.dependencies import get_rate_limiter
from app.routers import auth_router, chat_router, health_router, triage_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    # Startup: ensure DynamoDB tables exist (local dev)
    from app.dynamodb import create_tables, get_ddb_client
    try:
        await create_tables()
    except Exception:
        pass  # Tables may already exist or we're in production
    yield
    # Shutdown
    try:
        client = await get_ddb_client().__aenter__()
        await client.close()
    except Exception:
        pass


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="2.0.0",
        description="GuardianHealth v2 — AWS-free symptom checker API with DynamoDB",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Rate limiter
    limiter = get_rate_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(auth_router)
    app.include_router(triage_router)
    app.include_router(chat_router)
    app.include_router(health_router)

    return app


app = create_app()
