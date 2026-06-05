"""Auth router — register, login, refresh, me."""

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.dependencies import get_current_user, get_mongodb_manager, limiter
from app.core.security import create_token_pair
from app.schemas.token import RefreshRequest
from app.schemas.user import TokenResponse, UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _auth_service(db=Depends(get_mongodb_manager)) -> AuthService:
    return AuthService(db)


def _token_response(access: str, refresh: str, user: UserResponse) -> TokenResponse:
    settings = get_settings()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_settings().rate_limit_register)
async def register(
    request: Request,
    user_create: UserCreate = Body(...),
    auth_svc: AuthService = Depends(_auth_service),
) -> TokenResponse:
    try:
        user = await auth_svc.register(user_create)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    user_response = UserResponse(
        id=user["username"],
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name", ""),
        role=user.get("role", "patient"),
        is_active=user.get("is_active", True),
        is_verified=user.get("is_verified", False),
        created_at=user.get("created_at", ""),
    )
    access, refresh = create_token_pair(user["username"], extra_claims={"uid": user["id"]})
    return _token_response(access, refresh, user_response)


class _LoginBody(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(get_settings().rate_limit_login)
async def login(
    request: Request,
    body: _LoginBody = Body(...),
    auth_svc: AuthService = Depends(_auth_service),
) -> TokenResponse:
    try:
        access, refresh = await auth_svc.login(body.username, body.password)
        user = await auth_svc.get_user(body.username)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    assert user is not None
    user_response = UserResponse(
        id=user["username"],
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name", ""),
        role=user.get("role", "patient"),
        is_active=user.get("is_active", True),
        is_verified=user.get("is_verified", False),
        created_at=user.get("created_at", ""),
    )
    return _token_response(access, refresh, user_response)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(get_settings().rate_limit_refresh)
async def refresh(
    request: Request,
    body: RefreshRequest = Body(...),
    auth_svc: AuthService = Depends(_auth_service),
) -> TokenResponse:
    try:
        payload_user = decode_refresh_user(body.refresh_token)
        new_access = await auth_svc.refresh_access_token(body.refresh_token)
        user = await auth_svc.get_user(payload_user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from exc

    assert user is not None
    user_response = UserResponse(
        id=user["username"],
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name", ""),
        role=user.get("role", "patient"),
        is_active=user.get("is_active", True),
        is_verified=user.get("is_verified", False),
        created_at=user.get("created_at", ""),
    )
    settings = get_settings()
    return TokenResponse(
        access_token=new_access,
        refresh_token=body.refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_response,
    )


def decode_refresh_user(refresh_token: str) -> str:
    from app.core.security import decode_token
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise ValueError("Invalid refresh token")
    username = payload.get("sub")
    if not username:
        raise ValueError("Invalid token payload")
    return username


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user
