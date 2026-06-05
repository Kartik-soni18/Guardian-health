"""Triage router — LangGraph + LLM symptom assessment."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.core.dependencies import get_current_user_optional, limiter
from app.graph.streaming import format_sse_event
from app.schemas.triage import TriageRequest, TriageResponse
from app.schemas.user import UserResponse
from app.services.triage_service import TriageService

logger = logging.getLogger("guardian.routers.triage")

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


@router.post("/stream")
@limiter.limit(get_settings().rate_limit_triage)
async def triage_stream(
    request: Request,
    triage_req: TriageRequest,
    current_user: Optional[UserResponse] = Depends(get_current_user_optional),
    triage_svc: TriageService = Depends(TriageService),
) -> StreamingResponse:
    user_id = current_user.id if current_user else None

    async def event_generator():
        try:
            async for event in triage_svc.stream_graph(triage_req, user_id=user_id):
                yield format_sse_event(event)
                if event.get("type") == "error":
                    return
            yield "data: [DONE]\n\n"
        except Exception as exc:
            logger.error("Triage stream endpoint error: %s", exc)
            yield format_sse_event({"type": "error", "message": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
