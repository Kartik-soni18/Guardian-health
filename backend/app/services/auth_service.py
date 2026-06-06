"""Authentication service backed by MongoDB."""

import re
import secrets
from typing import Any, Dict, Optional, Tuple

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config import get_settings
from app.core.security import (
    create_token_pair,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.mongodb import MongoDBManager
from app.schemas.user import UserCreate

_GOOGLE_ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})


class AuthService:
    def __init__(self, db: MongoDBManager) -> None:
        self.db = db

    async def register(self, user_create: UserCreate) -> Dict[str, Any]:
        existing = await self.db.get_user_by_username(user_create.username)
        if existing is not None:
            raise ValueError("Username already exists")

        user_data = {
            "username": user_create.username,
            "hashed_password": get_password_hash(user_create.password),
            "auth_provider": "local",
        }
        return await self.db.create_user(user_data)

    async def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        user = await self.db.get_user_by_username(username)
        if user is None:
            return None
        hashed_password = user.get("hashed_password", user.get("password_hash", ""))
        if not hashed_password:
            return None
        if not verify_password(password, hashed_password):
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

    async def login_with_google(self, id_token: str) -> Tuple[str, str, Dict[str, Any]]:
        settings = get_settings()
        if not settings.client_id_google:
            raise ValueError("Google sign-in is not configured")

        try:
            payload = google_id_token.verify_oauth2_token(
                id_token,
                google_requests.Request(),
                settings.client_id_google,
            )
        except ValueError as exc:
            raise ValueError("Invalid Google token") from exc

        if payload.get("iss") not in _GOOGLE_ISSUERS:
            raise ValueError("Invalid Google token issuer")

        google_sub = payload.get("sub")
        email = payload.get("email")
        email_verified = payload.get("email_verified", False)

        if not google_sub:
            raise ValueError("Invalid Google token payload")
        if not email or not email_verified:
            raise ValueError("Google account email is not verified")

        user = await self.db.get_user_by_google_id(google_sub)
        if user is None:
            user = await self.db.get_user_by_email(email)

        if user is None:
            username = await self._derive_username_from_email(email)
            user = await self.db.create_oauth_user({
                "username": username,
                "google_id": google_sub,
                "email": email,
                "auth_provider": "google",
                "is_verified": True,
            })
        elif not user.get("google_id"):
            linked = await self.db.link_google_account(user["username"], google_sub, email)
            if linked is None:
                raise ValueError("Unable to link Google account")
            user = linked

        if not user.get("is_active", True):
            raise ValueError("Account disabled")

        access, refresh = create_token_pair(
            user["username"],
            extra_claims={"uid": user.get("id", user["username"])},
        )
        return access, refresh, user

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

    async def _derive_username_from_email(self, email: str) -> str:
        local_part = email.split("@", 1)[0].lower()
        cleaned = re.sub(r"[^a-z0-9_]", "_", local_part).strip("_")
        if len(cleaned) < 3:
            cleaned = f"user_{cleaned or secrets.token_hex(3)}"
        base = cleaned[:40]

        candidate = base
        suffix = 0
        while await self.db.get_user_by_username(candidate) is not None:
            suffix += 1
            candidate = f"{base}_{suffix}"[:50]

        return candidate
