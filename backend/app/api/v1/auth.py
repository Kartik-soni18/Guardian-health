"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, status

from app.models.user import UserCreate, UserLogin
from app.services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user_optional,
)
from app import db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(user_data: UserCreate):
    users_coll = await db.get_user_collection()
    if await users_coll.find_one({"username": user_data.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please try a different username.",
        )
    new_user = {
        "username": user_data.username,
        "hashed_password": get_password_hash(user_data.password),
        "created_at": __import__("datetime").datetime.utcnow(),
    }
    await users_coll.insert_one(new_user)
    access_token = create_access_token(data={"sub": user_data.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user_data.username,
    }


@router.post("/login")
async def login(user_data: UserLogin):
    try:
        users_coll = await db.get_user_collection()
        user = await users_coll.find_one({"username": user_data.username})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database inaccessible.",
        )
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user["username"],
    }
