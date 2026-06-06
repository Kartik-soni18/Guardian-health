"""GuardianHealth FastAPI — MongoDB auth + LangGraph triage."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings, validate_startup
from app.core.dependencies import get_rate_limiter
from app.core.exceptions import GuardianException
from app.db.mongodb import close_mongodb, connect_mongodb, ensure_mongodb
from app.routers import auth_router, chat_router, health_router, triage_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_startup()
    await ensure_mongodb()
    yield
    await close_mongodb()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="GuardianHealth — MongoDB auth + LangGraph LLM triage",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    limiter = get_rate_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(GuardianException)
    async def guardian_exception_handler(request, exc: GuardianException):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
            headers=exc.headers,
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(triage_router)
    app.include_router(health_router)

    return app


app = create_app()
