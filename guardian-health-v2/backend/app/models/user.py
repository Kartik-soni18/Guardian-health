"""Pydantic models for User domain — DynamoDB-native.

Contains validation, serialization helpers, and DynamoDB item converters.
NO Beanie / ODM — everything is explicit dict mapping for aioboto3.
"""


from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from app.core.exceptions import ValidationError as GuardianValidationError
from app.core.validators import validate_email, validate_password, validate_username
from app.models.enums import UserRole


# ------------------------------------------------------------------------------
# Internal model (full database representation)
# ------------------------------------------------------------------------------


class User(BaseModel):
    """Complete user record as stored in DynamoDB.

    The hashed_password field is present here but NEVER serialized to API
    consumers — use UserResponse for that.
    """

    username: str
    email: str
    full_name: str
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    role: UserRole = UserRole.PATIENT
    created_at: str = Field(default_factory=lambda: _utc_iso())

    model_config = {"populate_by_name": True}


# ------------------------------------------------------------------------------
# Request / creation models
# ------------------------------------------------------------------------------


class UserCreate(BaseModel):
    """Payload for user registration."""

    username: str
    email: str
    password: str
    full_name: str

    @field_validator("username")
    @classmethod
    def _check_username(cls, v: str) -> str:
        try:
            return validate_username(v)
        except GuardianValidationError as exc:
            raise ValueError(exc.detail) from exc

    @field_validator("email")
    @classmethod
    def _check_email(cls, v: str) -> str:
        try:
            return validate_email(v)
        except GuardianValidationError as exc:
            raise ValueError(exc.detail) from exc

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        try:
            return validate_password(v)
        except GuardianValidationError as exc:
            # Flatten nested errors for Pydantic display
            errs = exc.extra.get("errors", [exc.detail]) if exc.extra else [exc.detail]
            raise ValueError("; ".join(errs)) from exc


class UserLogin(BaseModel):
    """Payload for user authentication."""

    username: str
    password: str


# ------------------------------------------------------------------------------
# Response models (no sensitive fields)
# ------------------------------------------------------------------------------


class UserResponse(BaseModel):
    """Safe user representation for API responses."""

    id: str  # same as username — kept as 'id' for frontend consistency
    username: str
    email: str
    full_name: str
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
    expires_in: int = 3600  # seconds
    user: UserResponse


# ------------------------------------------------------------------------------
# DynamoDB serialization helpers
# ------------------------------------------------------------------------------


def user_to_ddb_item(user: User) -> Dict[str, Any]:
    """Serialize a User internal model to a plain dict for DynamoDB.

    The resulting dict can be passed directly to DynamoDB put_item via
    aioboto3 Table.resource, or pre-serialized via dynamodb._serialize_item().
    """
    return {
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": user.hashed_password,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "role": user.role.value,
        "created_at": user.created_at,
    }


def ddb_item_to_user(item: Dict[str, Any]) -> User:
    """Reconstruct a User from a deserialized DynamoDB item dict.

    Handles both aioboto3 Table-style responses (plain values) and
    lower-level client responses (type-wrapped values).
    """
    # Unwrap type wrappers if present
    def _unwrap(v):
        if isinstance(v, dict):
            if "S" in v:
                return v["S"]
            if "N" in v:
                return v["N"]
            if "BOOL" in v:
                return v["BOOL"]
            if "M" in v:
                return {k: _unwrap(val) for k, val in v["M"].items()}
        return v

    unwrapped = {k: _unwrap(v) for k, v in item.items()}

    return User(
        username=str(unwrapped["username"]),
        email=str(unwrapped["email"]),
        full_name=str(unwrapped.get("full_name", "")),
        hashed_password=str(unwrapped["hashed_password"]),
        is_active=bool(unwrapped.get("is_active", True)),
        is_verified=bool(unwrapped.get("is_verified", False)),
        role=UserRole(str(unwrapped.get("role", "patient"))),
        created_at=str(unwrapped.get("created_at", _utc_iso())),
    )


def user_to_response(user: User) -> UserResponse:
    """Convert an internal User to a safe API-facing UserResponse."""
    return UserResponse(
        id=user.username,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


# ------------------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------------------


def _utc_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()