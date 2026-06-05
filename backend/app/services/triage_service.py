"""Triage service — runs the LangGraph pipeline with LLM calls."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

from app.graph import get_triage_graph, reset_graph
from app.graph.state import TriageState
from app.graph.stream_context import reset_stream_emit, set_stream_emit
from app.graph.streaming import NODE_STATUS_MESSAGES, chunk_text
from app.schemas.triage import TriageRequest, TriageResponse

logger = logging.getLogger("guardian.triage_service")


class TriageService:
    async def invoke_graph(
        self,
        request: TriageRequest,
        user_id: Optional[str] = None,
    ) -> TriageResponse:
        graph = get_triage_graph()
        state = self._initial_state(request, user_id)
        final: Dict[str, Any] = await graph.ainvoke(state)
        return self._build_response(final)

    async def stream_graph(
        self,
        request: TriageRequest,
        user_id: Optional[str] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        graph = get_triage_graph()
        state = self._initial_state(request, user_id)
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        tokens_emitted = False

        async def emit(event: dict[str, Any]) -> None:
            nonlocal tokens_emitted
            if event.get("type") == "token":
                tokens_emitted = True
            await queue.put(event)

        async def run_graph() -> None:
            nonlocal tokens_emitted
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
                if not tokens_emitted:
                    text = response.response or response.assessment
                    if text:
                        async for chunk in chunk_text(text):
                            await queue.put({"type": "token", "chunk": chunk})

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

    @staticmethod
    def _initial_state(
        request: TriageRequest,
        user_id: Optional[str],
    ) -> TriageState:
        return {
            "user_input": request.query,
            "user_id": user_id,
            "chat_id": request.chat_id,
            "conversation_history": request.conversation_history or [],
            "force_phrase_used": False,
        }

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
