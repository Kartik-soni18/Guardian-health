"""Shared FastAPI dependencies."""

from fastapi import Request, Depends
from app.services.auth_service import get_current_user_optional

# Re-export for convenience
get_current_user = get_current_user_optional


async def get_request_id(request: Request) -> str:
    """Extract or generate a request ID for tracing."""
    return request.headers.get("X-Request-ID", "")
