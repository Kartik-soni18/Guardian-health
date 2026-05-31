"""Chat history API routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.auth_service import get_current_user_optional
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("")
async def get_chats(user=Depends(get_current_user_optional)):
    if not user:
        return []
    return await ChatService.list_chats(user["id"])


@router.get("/{chat_id}")
async def get_chat_history(chat_id: str, user=Depends(get_current_user_optional)):
    user_id = user["id"] if user else None
    return await ChatService.get_chat_history(chat_id, user_id)


@router.delete("/{chat_id}")
async def delete_chat(chat_id: str, user=Depends(get_current_user_optional)):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    deleted = await ChatService.delete_chat(chat_id, user["id"])
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found.",
        )
    return {"status": "deleted"}
