"""GuardianHealth v2 Auth Router — Registration, Login, Refresh, Me."""

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.dependencies import get_current_user, get_dynamodb_manager, limiter
from app.core.security import create_token_pair
from app.schemas.token import RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def _auth_service(db=Depends(get_dynamodb_manager)) -> AuthService:
    return AuthService(db)


def _token_response(access: str, refresh: str) -> TokenResponse:
    settings = get_settings()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register — Rate limit: 5/min
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
)
@limiter.limit(get_settings().rate_limit_register)
async def register(
    request: Request,
    user_create: UserCreate = Body(...),
    auth_svc: AuthService = Depends(_auth_service),
) -> TokenResponse:
    """Create a new user account. Returns JWT token pair on success."""
    try:
        user = await auth_svc.register(user_create)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    access, refresh = create_token_pair(
        user["username"],
        extra_claims={"uid": user["id"]},
    )
    return _token_response(access, refresh)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login — Rate limit: 10/min
# ---------------------------------------------------------------------------
class _LoginBody(BaseModel):
    """Login request body (separate from UserCreate to avoid password rules)."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive tokens",
)
@limiter.limit(get_settings().rate_limit_login)
async def login(
    request: Request,
    body: _LoginBody = Body(...),
    auth_svc: AuthService = Depends(_auth_service),
) -> TokenResponse:
    """
    Authenticate with username and password.
    Error messages are intentionally vague to prevent user enumeration.
    """
    try:
        access, refresh = await auth_svc.login(body.username, body.password)
    except ValueError:
        # Vague error — do not reveal whether user exists or password is wrong
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _token_response(access, refresh)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/refresh — Rate limit: 20/min
# ---------------------------------------------------------------------------
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
@limiter.limit(get_settings().rate_limit_refresh)
async def refresh(
    request: Request,
    body: RefreshRequest = Body(...),
    auth_svc: AuthService = Depends(_auth_service),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access token."""
    try:
        new_access = await auth_svc.refresh_access_token(body.refresh_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from exc

    # Return same refresh token alongside new access token
    settings = get_settings()
    return TokenResponse(
        access_token=new_access,
        refresh_token=body.refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me — Require auth
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    response_description="Authenticated user details",
)
async def get_me(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Return the authenticated user's profile."""
    return current_user
