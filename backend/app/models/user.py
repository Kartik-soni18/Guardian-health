"""Pydantic models for User domain — MongoDB-native."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from app.core.exceptions import ValidationError as GuardianValidationError
from app.core.validators import validate_password, validate_username
from app.models.enums import UserRole


class User(BaseModel):
    """Complete user record as stored in MongoDB."""

    username: str
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    role: UserRole = UserRole.PATIENT
    created_at: str = Field(default_factory=lambda: _utc_iso())

    model_config = {"populate_by_name": True}


class UserCreate(BaseModel):
    """Payload for user registration."""

    username: str
    password: str

    @field_validator("username")
    @classmethod
    def _check_username(cls, v: str) -> str:
        try:
            return validate_username(v)
        except GuardianValidationError as exc:
            raise ValueError(exc.detail) from exc

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        try:
            return validate_password(v)
        except GuardianValidationError as exc:
            errs = exc.extra.get("errors", [exc.detail]) if exc.extra else [exc.detail]
            raise ValueError("; ".join(errs)) from exc


class UserLogin(BaseModel):
    """Payload for user authentication."""

    username: str
    password: str


class UserResponse(BaseModel):
    """Safe user representation for API responses."""

    id: str
    username: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: str

    @field_validator("id", mode="before")
    @classmethod
    def _derive_id(cls, v, info):
        if not v and "username" in info.data:
            return info.data["username"]
        return v


class TokenResponse(BaseModel):
    """Authentication response containing JWT pair and user metadata."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: UserResponse


def _normalize_created_at(value: Any) -> str:
    if value is None:
        return _utc_iso()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def user_doc_to_user(doc: Dict[str, Any]) -> User:
    """Reconstruct a User from a MongoDB document."""
    return User(
        username=str(doc["username"]),
        hashed_password=str(doc.get("hashed_password", doc.get("password_hash", ""))),
        is_active=bool(doc.get("is_active", True)),
        is_verified=bool(doc.get("is_verified", False)),
        role=UserRole(str(doc.get("role", "patient"))),
        created_at=_normalize_created_at(doc.get("created_at")),
    )


def user_to_response(user: User) -> UserResponse:
    """Convert an internal User to a safe API-facing UserResponse."""
    return UserResponse(
        id=user.username,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


def user_doc_to_response(doc: Dict[str, Any]) -> UserResponse:
    """Build a UserResponse directly from a MongoDB user document."""
    return user_to_response(user_doc_to_user(doc))


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
