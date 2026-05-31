"""Triage API routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.triage import TriageRequest
from app.services.auth_service import get_current_user_optional
from app.services.triage_service import TriageService

router = APIRouter(prefix="/triage", tags=["triage"])


@router.post("")
async def triage(request: TriageRequest, user=Depends(get_current_user_optional)):
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty.",
        )

    chat_id = request.chat_id
    if user and not chat_id:
        chat_id = str(uuid.uuid4())

    result = await TriageService.invoke_graph(
        user_query=request.query,
        user=user,
        chat_id=chat_id,
        conversation_history=request.conversation_history,
    )

    if isinstance(result.get("status"), int) and result["status"] >= 400:
        raise HTTPException(
            status_code=result["status"],
            detail=result.get("error"),
        )

    result["chat_id"] = chat_id
    return result
