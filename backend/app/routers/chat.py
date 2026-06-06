"""Chat router — CRUD for persisted conversations."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import get_settings
from app.core.dependencies import get_current_user, get_mongodb_manager, limiter
from app.db.mongodb import MongoDBManager
from app.schemas.chat import ChatCreate, ChatDetailResponse, ChatResponse
from app.schemas.user import UserResponse
from app.services.chat_service import ChatService

logger = logging.getLogger("guardian.routers.chat")

router = APIRouter(prefix="/api/v1/chats", tags=["chats"])


def _chat_service(db: MongoDBManager = Depends(get_mongodb_manager)) -> ChatService:
    return ChatService(db)


@router.get("", response_model=list[ChatResponse], response_model_by_alias=True)
@limiter.limit(get_settings().rate_limit_chats)
async def list_chats(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    chat_svc: ChatService = Depends(_chat_service),
) -> list[ChatResponse]:
    return await chat_svc.list_chats(current_user.id)


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED, response_model_by_alias=True)
@limiter.limit(get_settings().rate_limit_chats)
async def create_chat(
    request: Request,
    body: ChatCreate,
    current_user: UserResponse = Depends(get_current_user),
    chat_svc: ChatService = Depends(_chat_service),
) -> ChatResponse:
    return await chat_svc.create_chat(current_user.id, body.initial_message)


@router.get("/{chat_id}", response_model=ChatDetailResponse, response_model_by_alias=True)
@limiter.limit(get_settings().rate_limit_chats)
async def get_chat(
    request: Request,
    chat_id: str,
    current_user: UserResponse = Depends(get_current_user),
    chat_svc: ChatService = Depends(_chat_service),
) -> ChatDetailResponse:
    chat = await chat_svc.get_chat_detail(chat_id, current_user.id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(get_settings().rate_limit_chats)
async def delete_chat(
    request: Request,
    chat_id: str,
    current_user: UserResponse = Depends(get_current_user),
    chat_svc: ChatService = Depends(_chat_service),
) -> None:
    deleted = await chat_svc.delete_chat(chat_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
