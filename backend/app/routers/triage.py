"""Triage router — LangGraph + LLM symptom assessment."""

from typing import Optional

from fastapi import APIRouter, Depends, Request

from app.config import get_settings
from app.core.dependencies import get_current_user_optional, limiter
from app.schemas.triage import TriageRequest, TriageResponse
from app.schemas.user import UserResponse
from app.services.triage_service import TriageService

router = APIRouter(prefix="/api/v1/triage", tags=["triage"])


@router.post("", response_model=TriageResponse)
@limiter.limit(get_settings().rate_limit_triage)
async def triage(
    request: Request,
    triage_req: TriageRequest,
    current_user: Optional[UserResponse] = Depends(get_current_user_optional),
    triage_svc: TriageService = Depends(TriageService),
) -> TriageResponse:
    user_id = current_user.id if current_user else None
    return await triage_svc.invoke_graph(triage_req, user_id=user_id)
