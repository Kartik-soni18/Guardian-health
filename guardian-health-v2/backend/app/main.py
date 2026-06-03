"""GuardianHealth v2 FastAPI Application — AWS-free, DynamoDB only."""


from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.deps import limiter
from app.routers import auth_router, chat_router, health_router, triage_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    # Startup: ensure DynamoDB tables exist (local dev)
    from app.db.dynamodb import DynamoDBManager
    ddb = DynamoDBManager()
    try:
        await ddb.create_tables()
    except Exception:
        pass  # Tables may already exist or we're in production
    yield
    # Shutdown
    await ddb.close()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="GuardianHealth v2 — AWS-free symptom checker API with DynamoDB",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
