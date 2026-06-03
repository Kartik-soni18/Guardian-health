"""FastAPI dependency injection for GuardianHealth.

All dependencies are async where possible and use in-memory or DynamoDB
backends — NO Redis, NO Celery, NO MongoDB.
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.cache import get_cache_stats
from app.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, AuthorizationError, DatabaseError
from app.core.security import verify_token
from app.db.dynamodb import DynamoDBManager
from app.dynamodb import get_ddb_client, get_ddb_resource
from app.logging_config import get_logger
from app.models.enums import UserRole
from app.models.user import User, UserResponse, ddb_item_to_user, user_to_response

logger = get_logger("app.core.dependencies")

# ------------------------------------------------------------------------------
# Auth scheme
# ------------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)


# ------------------------------------------------------------------------------
# Current user extraction
# ------------------------------------------------------------------------------


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> UserResponse:
    """Dependency: extract and verify the current user from Authorization header.

    Args:
        credentials: Parsed Bearer token from the HTTP Authorization header.

    Returns:
        UserResponse for the authenticated user.

    Raises:
        AuthenticationError: If no token is provided, or it is invalid/expired.
    """
    if not credentials:
        raise AuthenticationError(
            "Authorization header missing or not a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_token(token, expected_type="access")
    username: Optional[str] = payload.get("sub")

    if not username:
        raise AuthenticationError(
            "Token missing 'sub' claim.",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    # Fetch user from DynamoDB to confirm existence and active status
    settings = get_settings()
    from app.dynamodb import ddb_get_item  # late import to avoid cycles

    item = await ddb_get_item(
        settings.table_users, key={"username": username}
    )
    if item is None:
        raise AuthenticationError(
            "User associated with this token no longer exists.",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    user = ddb_item_to_user(item)
    if not user.is_active:
        raise AuthenticationError(
            "User account is deactivated.",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    return user_to_response(user)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[UserResponse]:
    """Dependency: optionally extract the current user.

    Returns None if no token is present or if it is invalid.
    Useful for endpoints that work both authenticated and anonymously.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except AuthenticationError:
        return None


# Alias used by some routers
get_optional_user = get_current_user_optional


# ------------------------------------------------------------------------------
# Role-based guards
# ------------------------------------------------------------------------------


def require_role(required_role: UserRole):
    """Factory: create a dependency that enforces a minimum role level.

    Hierarchy (most to least privileged):
        ADMIN > CLINICIAN > RESEARCHER > PATIENT

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: UserResponse = Depends(require_role(UserRole.ADMIN))):
            ...
    """
    _role_rank = {
        UserRole.PATIENT: 0,
        UserRole.RESEARCHER: 1,
        UserRole.CLINICIAN: 2,
        UserRole.ADMIN: 3,
    }

    async def _checker(
        user: UserResponse = Depends(get_current_user),
    ) -> UserResponse:
        user_rank = _role_rank.get(user.role, -1)
        required_rank = _role_rank.get(required_role, 999)
        if user_rank < required_rank:
            raise AuthorizationError(
                f"This endpoint requires role '{required_role.value}' "
                f"or higher. Your role: '{user.role.value}'.",
            )
        return user

    return _checker


# Simple aliases
require_auth = get_current_user
require_admin = require_role(UserRole.ADMIN)
require_clinician = require_role(UserRole.CLINICIAN)


# ------------------------------------------------------------------------------
# Settings dependency
# ------------------------------------------------------------------------------


async def get_config() -> Settings:
    """Dependency: return the cached application settings."""
    return get_settings()


# ------------------------------------------------------------------------------
# DynamoDB manager dependency
# ------------------------------------------------------------------------------


def get_dynamodb_manager() -> DynamoDBManager:
    """Dependency: return a DynamoDBManager instance."""
    return DynamoDBManager()


# ------------------------------------------------------------------------------
# DynamoDB table dependencies
# ------------------------------------------------------------------------------


async def get_table_users():
    """Yield the users table resource (for use in API route handlers).

    Usage:
        @router.get("/users/me")
        async def me(table=Depends(get_table_users)):
            resp = await table.get_item(Key={"username": "alice"})
            ...
    """
    settings = get_settings()
    async with get_ddb_resource() as dynamo:
        table = await dynamo.Table(settings.table_users)
        yield table


async def get_table_chats():
    """Yield the chats table resource."""
    settings = get_settings()
    async with get_ddb_resource() as dynamo:
        table = await dynamo.Table(settings.table_chats)
        yield table


async def get_table_interactions():
    """Yield the interactions table resource."""
    settings = get_settings()
    async with get_ddb_resource() as dynamo:
        table = await dynamo.Table(settings.table_interactions)
        yield table


# ------------------------------------------------------------------------------
# Rate limiter
# ------------------------------------------------------------------------------

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Singleton limiter with in-memory storage
_limiter: Optional[Limiter] = None


def get_rate_limiter() -> Limiter:
    """Return the global slowapi Limiter instance backed by in-memory storage.

    The limiter key function extracts the client IP from requests.
    For authenticated endpoints, override per-route with key_func=lambda: user.id.
    """
    global _limiter
    if _limiter is None:
        _limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["100/minute"],
            storage_uri="memory://",  # in-memory, per-process
            strategy="fixed-window-elastic",
        )
    return _limiter


# Module-level limiter for direct import
limiter = get_rate_limiter()


# ------------------------------------------------------------------------------
# Cache stats (admin/monitoring)
# ------------------------------------------------------------------------------


async def get_cache_statistics() -> dict:
    """Dependency: return current in-memory cache statistics."""
    return get_cache_stats()
