"""Authentication service backed by MongoDB."""

from typing import Any, Dict, Optional, Tuple

from app.core.security import (
    create_token_pair,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.mongodb import MongoDBManager
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: MongoDBManager) -> None:
        self.db = db

    async def register(self, user_create: UserCreate) -> Dict[str, Any]:
        existing = await self.db.get_user_by_username(user_create.username)
        if existing is not None:
            raise ValueError("Username already exists")

        user_data = {
            "username": user_create.username,
            "email": str(user_create.email),
            "password_hash": get_password_hash(user_create.password),
            "full_name": user_create.full_name or "",
        }
        return await self.db.create_user(user_data)

    async def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        user = await self.db.get_user_by_username(username)
        if user is None:
            return None
        if not verify_password(password, user.get("hashed_password", user.get("password_hash", ""))):
            return None
        if not user.get("is_active", True):
            return None
        return user

    async def login(self, username: str, password: str) -> Tuple[str, str]:
        user = await self.authenticate(username, password)
        if user is None:
            raise ValueError("Invalid credentials")
        return create_token_pair(
            user["username"],
            extra_claims={"uid": user.get("id", user["username"])},
        )

    async def refresh_access_token(self, refresh_token: str) -> str:
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
        access, _ = create_token_pair(
            user["username"],
            extra_claims={"uid": user.get("id", user["username"])},
        )
        return access

    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        return await self.db.get_user_by_username(username)
