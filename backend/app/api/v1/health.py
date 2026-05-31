"""Health check API route."""

from fastapi import APIRouter

from app import db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    try:
        await db.db.command("ping")
        return {"status": "ok", "db": "mongodb connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}
