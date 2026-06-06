"""Chat persistence service — MongoDB-backed conversations."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.core.privacy import scrub_pii
from app.db.mongodb import MongoDBManager
from app.schemas.chat import ChatDetailResponse, ChatResponse, MessageResponse

logger = logging.getLogger("guardian.chat_service")

_DEFAULT_TITLE = "New chat"
_MAX_TITLE_LEN = 48


def _build_title(text: Optional[str]) -> str:
    if not text:
        return _DEFAULT_TITLE
    trimmed = text.strip()
    if not trimmed:
        return _DEFAULT_TITLE
    return trimmed[:_MAX_TITLE_LEN] + ("…" if len(trimmed) > _MAX_TITLE_LEN else "")


def _chat_to_response(doc: Dict[str, Any]) -> ChatResponse:
    return ChatResponse(
        id=doc["id"],
        title=doc.get("title", _DEFAULT_TITLE),
        user_id=doc["user_id"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _message_to_response(doc: Dict[str, Any]) -> MessageResponse:
    return MessageResponse(
        id=doc["id"],
        chat_id=doc["chat_id"],
        role=doc["role"],
        content=doc["content"],
        triage=doc.get("triage"),
        created_at=doc["created_at"],
    )


class ChatService:
    def __init__(self, db: MongoDBManager) -> None:
        self._db = db

    async def create_chat(
        self,
        user_id: str,
        initial_message: Optional[str] = None,
    ) -> ChatResponse:
        title = _build_title(initial_message)
        doc = await self._db.create_chat(user_id, title)
        return _chat_to_response(doc)

    async def list_chats(self, user_id: str, limit: int = 50) -> List[ChatResponse]:
        docs = await self._db.list_chats(user_id, limit=limit)
        return [_chat_to_response(doc) for doc in docs]

    async def get_chat_detail(self, chat_id: str, user_id: str) -> Optional[ChatDetailResponse]:
        chat = await self._db.get_chat(chat_id, user_id)
        if chat is None:
            return None
        messages = await self._db.list_messages(chat_id, user_id)
        return ChatDetailResponse(
            id=chat["id"],
            title=chat.get("title", _DEFAULT_TITLE),
            user_id=chat["user_id"],
            created_at=chat["created_at"],
            updated_at=chat["updated_at"],
            messages=[_message_to_response(m) for m in messages],
        )

    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        return await self._db.delete_chat(chat_id, user_id)

    async def build_conversation_history(
        self,
        chat_id: str,
        user_id: str,
    ) -> List[Dict[str, str]]:
        messages = await self._db.list_messages(chat_id, user_id)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
            if msg.get("role") in ("user", "assistant", "system")
        ]

    async def save_turn(
        self,
        chat_id: str,
        user_id: str,
        user_content: str,
        assistant_content: str,
        triage_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        scrub_result = await scrub_pii(user_content)
        scrubbed_user = scrub_result["scrubbed_text"]

        triage_payload = None
        if triage_data and not triage_data.get("needs_follow_up"):
            triage_payload = triage_data

        try:
            await self._db.append_messages(
                chat_id,
                user_id,
                [
                    {"role": "user", "content": scrubbed_user},
                    {
                        "role": "assistant",
                        "content": assistant_content,
                        "triage": triage_payload,
                    },
                ],
            )
            chat = await self._db.get_chat(chat_id, user_id)
            if chat and chat.get("title") == _DEFAULT_TITLE:
                await self._db.update_chat_title(
                    chat_id,
                    user_id,
                    _build_title(user_content),
                )
            logger.info(
                "Saved chat turn chat_id=%s user_id=%s user_len=%d assistant_len=%d",
                chat_id,
                user_id,
                len(scrubbed_user),
                len(assistant_content),
            )
        except Exception as exc:
            logger.error(
                "Failed to persist chat turn chat_id=%s user_id=%s error=%s",
                chat_id,
                user_id,
                exc,
            )
            raise
