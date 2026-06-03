"""GuardianHealth v2 Chat Router — List, Get, Delete user chats."""


from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.deps import get_current_user, get_dynamodb_manager, limiter
from app.schemas.chat import ChatListResponse, ChatResponse
from app.schemas.user import UserResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/v1/chats", tags=["chat"])


def _chat_service(db=Depends(get_dynamodb_manager)) -> ChatService:
    return ChatService(db)


# ---------------------------------------------------------------------------
# GET /api/v1/chats — List user's chats
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=ChatListResponse,
    summary="List current user's chats",
    response_description="Paginated list of chats",
)
@limiter.limit(settings.RATE_LIMIT_CHAT)
async def list_chats(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    chat_svc: ChatService = Depends(_chat_service),
) -> ChatListResponse:
    """Return all chats belonging to the authenticated user."""
    raw_items = await chat_svc.list_user_chats(current_user.id)
    chats = [ChatResponse.model_validate(item) for item in raw_items]
    return ChatListResponse(items=chats, total=len(chats))


# ---------------------------------------------------------------------------
# GET /api/v1/chats/{chat_id} — Get chat details
# ---------------------------------------------------------------------------
@router.get(
    "/{chat_id}",
    response_model=ChatResponse,
    summary="Get a specific chat",
    responses={
        403: {"description": "Not owner of this chat"},
        404: {"description": "Chat not found"},
    },
)
@limiter.limit(settings.RATE_LIMIT_CHAT)
async def get_chat(
    request: Request,
    chat_id: str,
    current_user: UserResponse = Depends(get_current_user),
    chat_svc: ChatService = Depends(_chat_service),
) -> ChatResponse:
    """Retrieve a single chat by ID. Verifies ownership."""
    chat = await chat_svc.get_chat(chat_id)
    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    if not chat_svc.is_owner(chat, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not owner of this chat",
        )
    return ChatResponse.model_validate(chat)


# ---------------------------------------------------------------------------
# DELETE /api/v1/chats/{chat_id} — Delete chat
# ---------------------------------------------------------------------------
@router.delete(
    "/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a chat",
    responses={
        403: {"description": "Not owner of this chat"},
        404: {"description": "Chat not found"},
    },
)
@limiter.limit(settings.RATE_LIMIT_CHAT)
async def delete_chat(
    request: Request,
    chat_id: str,
    current_user: UserResponse = Depends(get_current_user),
    chat_svc: ChatService = Depends(_chat_service),
) -> None:
    """Delete a chat. Verifies ownership before deletion."""
    chat = await chat_svc.get_chat(chat_id)
    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    if not chat_svc.is_owner(chat, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not owner of this chat",
        )
    await chat_svc.delete_chat(chat_id)
