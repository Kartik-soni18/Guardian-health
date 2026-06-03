"""GuardianHealth v2 Auth Service — DynamoDB backend, no AWS dependencies."""


from datetime import timedelta
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.core.security import (
    create_token_pair,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.dynamodb import DynamoDBManager
from app.schemas.user import UserCreate, UserResponse


class AuthService:
    """Handles authentication logic with DynamoDB persistence."""

    def __init__(self, db: DynamoDBManager) -> None:
        self.db = db

    async def register(self, user_create: UserCreate) -> Dict[str, Any]:
        """Register a new user. Raises ValueError on duplicate username."""
        # Check uniqueness
        existing = await self.db.get_user_by_username(user_create.username)
        if existing is not None:
            raise ValueError("Username already exists")

        password_hash = get_password_hash(user_create.password)
        user_data = {
            "username": user_create.username,
            "email": str(user_create.email),
            "password_hash": password_hash,
            "full_name": user_create.full_name or "",
        }
        user = await self.db.create_user(user_data)
        return user

    async def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user. Returns user dict or None."""
        user = await self.db.get_user_by_username(username)
        if user is None:
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        if not user.get("is_active", True):
            return None
        return user

    async def login(self, username: str, password: str) -> Tuple[str, str]:
        """Authenticate and return token pair. Raises ValueError on failure."""
        user = await self.authenticate(username, password)
        if user is None:
            raise ValueError("Invalid credentials")
        access, refresh = create_token_pair(user["username"], extra_claims={"uid": user["id"]})
        return access, refresh

    async def refresh_access_token(self, refresh_token: str) -> str:
        """Validate refresh token and return new access token."""
        payload = decode_token(refresh_token)
        if payload is None:
            raise ValueError("Invalid or expired refresh token")
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        username = payload.get("sub")
        if not username:
            raise ValueError("Invalid token payload")
        user = await self.db.get_user_by_username(username)
        if user is None:
            raise ValueError("User not found")
        access = create_token_pair(user["username"], extra_claims={"uid": user["id"]})[0]
        return access

    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        return await self.db.get_user_by_username(username)
