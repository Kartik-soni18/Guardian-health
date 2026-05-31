"""Aggregate all API routers under /v1 prefix."""

from fastapi import APIRouter

from app.api.v1 import auth, chats, triage, health

api_router = APIRouter(prefix="/v1")
api_router.include_router(auth.router)
api_router.include_router(chats.router)
api_router.include_router(triage.router)
api_router.include_router(health.router)
