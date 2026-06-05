"""FastAPI dependency injection."""

from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.cache import get_rate_limit_storage_uri
from app.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import verify_token
from app.db.mongodb import MongoDBManager, ensure_mongodb
from app.logging_config import get_logger
from app.models.enums import UserRole
from app.models.user import UserResponse, user_doc_to_response

logger = get_logger("app.core.dependencies")

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_mongodb_manager() -> MongoDBManager:
    await ensure_mongodb()
    return MongoDBManager()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: MongoDBManager = Depends(get_mongodb_manager),
) -> UserResponse:
    if not credentials:
        raise AuthenticationError(
            "Authorization header missing or not a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials, expected_type="access")
    username: Optional[str] = payload.get("sub")
    if not username:
        raise AuthenticationError(
            "Token missing 'sub' claim.",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    item = await db.get_user_by_username(username)
    if item is None:
        raise AuthenticationError(
            "User associated with this token no longer exists.",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    response = user_doc_to_response(item)
    if not response.is_active:
        raise AuthenticationError(
            "User account is deactivated.",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    return response


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: MongoDBManager = Depends(get_mongodb_manager),
) -> Optional[UserResponse]:
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except AuthenticationError:
        return None


def require_role(required_role: UserRole):
    _role_rank = {
        UserRole.PATIENT: 0,
        UserRole.RESEARCHER: 1,
        UserRole.CLINICIAN: 2,
        UserRole.ADMIN: 3,
    }

    async def _checker(user: UserResponse = Depends(get_current_user)) -> UserResponse:
        user_rank = _role_rank.get(user.role, -1)
        required_rank = _role_rank.get(required_role, 999)
        if user_rank < required_rank:
            raise AuthorizationError(
                f"This endpoint requires role '{required_role.value}' or higher.",
            )
        return user

    return _checker


async def get_config() -> Settings:
    return get_settings()


_limiter: Optional[Limiter] = None


def get_rate_limiter() -> Limiter:
    global _limiter
    if _limiter is None:
        _limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["100/minute"],
            storage_uri=get_rate_limit_storage_uri(),
            strategy="fixed-window",
        )
    return _limiter


limiter = get_rate_limiter()
