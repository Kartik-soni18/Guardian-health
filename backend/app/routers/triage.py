"""GuardianHealth v2 Triage Router — Symptom checking endpoint."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Request

from app.config import get_settings
from app.core.dependencies import get_current_user_optional, get_dynamodb_manager, limiter
from app.models.triage import TriageRequest, TriageResponse
from app.schemas.chat import ConversationMessage
from app.schemas.user import UserResponse
from app.services.chat_service import ChatService
from app.services.triage_service import TriageService

router = APIRouter(prefix="/api/v1/triage", tags=["triage"])


def _triage_service() -> TriageService:
    return TriageService()


def _chat_service(db=Depends(get_dynamodb_manager)) -> ChatService:
    return ChatService(db)


# ---------------------------------------------------------------------------
# POST /api/v1/triage — Rate limit: 10/min per IP
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=TriageResponse,
    summary="Submit symptoms for triage assessment",
    response_description="Triage level and recommended actions",
)
@limiter.limit(get_settings().rate_limit_triage)
async def triage(
    request: Request,
    triage_req: TriageRequest,
    current_user: Optional[UserResponse] = Depends(get_current_user_optional),
    triage_svc: TriageService = Depends(_triage_service),
    chat_svc: ChatService = Depends(_chat_service),
) -> TriageResponse:
    """
    Assess symptoms and return triage level with recommendations.

    If authenticated, automatically saves/updates the associated chat
    in DynamoDB.
    """
    # Invoke the triage pipeline
    response = await triage_svc.invoke_graph(triage_req)

    # If user is authenticated, persist chat history
    if current_user is not None:
        chat_id = triage_req.chat_id
        messages: List[dict] = []

        # Build message list
        if triage_req.conversation_history:
            for msg in triage_req.conversation_history:
                ts = msg.get("timestamp", "") if isinstance(msg, dict) else getattr(msg, "timestamp", "")
                role = msg.get("role", "user") if isinstance(msg, dict) else getattr(msg, "role", "user")
                content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
                messages.append({
                    "role": role,
                    "content": content,
                    "timestamp": ts or datetime.now(timezone.utc).isoformat(),
                })
        messages.append({
            "role": "user",
            "content": triage_req.query,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        messages.append({
            "role": "assistant",
            "content": response.care_advice or response.reasoning,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        if chat_id:
            # Update existing chat
            existing = await chat_svc.get_chat(chat_id)
            if existing and chat_svc.is_owner(existing, current_user.id):
                await chat_svc.update_messages(chat_id, messages)
                response.chat_id = chat_id
            else:
                # Not owner or not found — create new
                new_chat = await chat_svc.create_chat(
                    user_id=current_user.id,
                    title=triage_req.query[:60] or "Triage",
                    messages=messages,
                )
                response.chat_id = new_chat.get("id")
        else:
            # Create new chat
            new_chat = await chat_svc.create_chat(
                user_id=current_user.id,
                title=triage_req.query[:60] or "Triage",
                messages=messages,
            )
            response.chat_id = new_chat.get("id")

    return response
