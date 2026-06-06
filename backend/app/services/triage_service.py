"""Triage service — runs the LangGraph pipeline with LLM calls."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

from app.core.exceptions import NotFoundError
from app.graph import get_triage_graph, reset_graph
from app.graph.state import TriageState
from app.graph.stream_context import reset_stream_emit, set_stream_emit
from app.graph.streaming import NODE_STATUS_MESSAGES
from app.schemas.triage import TriageRequest, TriageResponse
from app.services.chat_service import ChatService

logger = logging.getLogger("guardian.triage_service")


class TriageService:
    def __init__(self, chat_svc: Optional[ChatService] = None) -> None:
        self._chat_svc = chat_svc

    async def invoke_graph(
        self,
        request: TriageRequest,
        user_id: Optional[str] = None,
    ) -> TriageResponse:
        graph = get_triage_graph()
        state = await self._resolve_state(request, user_id)
        final: Dict[str, Any] = await graph.ainvoke(state)
        response = self._build_response(final)
        await self._persist_turn(request, user_id, response)
        return response

    async def stream_graph(
        self,
        request: TriageRequest,
        user_id: Optional[str] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        graph = get_triage_graph()
        state = await self._resolve_state(request, user_id)
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

        async def emit(event: dict[str, Any]) -> None:
            await queue.put(event)

        async def run_graph() -> None:
            ctx_token = set_stream_emit(emit)
            merged: Dict[str, Any] = dict(state)
            try:
                async for update in graph.astream(state, stream_mode="updates"):
                    for node_name, node_output in update.items():
                        if node_output:
                            merged.update(node_output)
                        message = NODE_STATUS_MESSAGES.get(
                            node_name,
                            f"Processing {node_name.replace('_', ' ')}...",
                        )
                        await queue.put({"type": "status", "message": message})

                response = self._build_response(merged)
                await self._persist_turn(request, user_id, response)
                await queue.put({
                    "type": "done",
                    "triage": response.model_dump(),
                })
            except Exception as exc:
                logger.error("Stream graph error: %s", exc)
                await queue.put({"type": "error", "message": str(exc)})
            finally:
                reset_stream_emit(ctx_token)
                await queue.put(None)

        task = asyncio.create_task(run_graph())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event
                if event.get("type") == "error":
                    break
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def _resolve_state(
        self,
        request: TriageRequest,
        user_id: Optional[str],
    ) -> TriageState:
        history: List[Dict[str, str]] = request.conversation_history or []

        if user_id and request.chat_id and self._chat_svc:
            if request.conversation_history:
                logger.debug(
                    "Ignoring client conversation_history for chat_id=%s",
                    request.chat_id,
                )
            chat = await self._chat_svc.get_chat_detail(request.chat_id, user_id)
            if chat is None:
                raise NotFoundError("Chat not found.")
            history = await self._chat_svc.build_conversation_history(
                request.chat_id,
                user_id,
            )

        return {
            "user_input": request.query,
            "user_id": user_id,
            "chat_id": request.chat_id,
            "conversation_history": history,
            "force_phrase_used": False,
        }

    async def _persist_turn(
        self,
        request: TriageRequest,
        user_id: Optional[str],
        response: TriageResponse,
    ) -> None:
        if not user_id or not request.chat_id or not self._chat_svc:
            return

        assistant_content = response.response or response.assessment
        try:
            await self._chat_svc.save_turn(
                chat_id=request.chat_id,
                user_id=user_id,
                user_content=request.query,
                assistant_content=assistant_content,
                triage_data=response.model_dump(),
            )
        except Exception as exc:
            logger.error(
                "Triage completed but persist failed chat_id=%s user_id=%s error=%s",
                request.chat_id,
                user_id,
                exc,
            )

    @staticmethod
    def _build_response(final: Dict[str, Any]) -> TriageResponse:
        response_data = final.get("response_data") or {}
        response_text = response_data.get("response") or final.get("response_text") or ""

        return TriageResponse(
            response=response_text,
            triage_level=response_data.get("triage_level"),
            level_title=response_data.get("level_title"),
            level_justification=response_data.get("level_justification", ""),
            response_mode=response_data.get("response_mode", "triage_report"),
            needs_follow_up=bool(response_data.get("needs_follow_up", False)),
            follow_up_questions=_as_str_list(response_data.get("follow_up_questions")),
            routing=response_data.get("routing") or "unknown",
            symptoms=(response_data.get("metadata") or {}).get("symptoms") or final.get("symptoms") or [],
            assessment=response_data.get("assessment", ""),
            reasoning=response_data.get("reasoning") or final.get("ml_reasoning") or "",
            immediate_actions=_as_str_list(response_data.get("immediate_actions")),
            crucial_warnings=_as_str_list(response_data.get("crucial_warnings")),
            resource_recommendations=_as_str_list(response_data.get("resource_recommendations")),
            required_follow_up=_as_str_list(response_data.get("required_follow_up")),
            assumptions=_as_str_list(response_data.get("assumptions")),
            what_to_do=_as_str_list(response_data.get("what_to_do")),
            what_not_to_do=_as_str_list(response_data.get("what_not_to_do")),
            likely_conditions=_as_str_list(response_data.get("likely_conditions")),
            red_flags=_as_str_list(response_data.get("red_flags")),
            care_setting=response_data.get("care_setting"),
            confidence=float(response_data.get("confidence", 0.0)),
            dataset_used=bool(response_data.get("dataset_used", False)),
            compliance_passed=final.get("compliance_passed", True),
            audit_hash=final.get("audit_hash"),
        )

    @staticmethod
    def reset() -> None:
        reset_graph()


def _as_str_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(item).strip() for item in value if str(item).strip()]
