"""Triage service — runs the LangGraph pipeline with LLM calls."""

from typing import Any, Dict, List, Optional

from app.graph import get_triage_graph, reset_graph
from app.graph.state import TriageState
from app.schemas.triage import TriageRequest, TriageResponse


class TriageService:
    async def invoke_graph(
        self,
        request: TriageRequest,
        user_id: Optional[str] = None,
    ) -> TriageResponse:
        graph = get_triage_graph()

        state: TriageState = {
            "user_input": request.query,
            "user_id": user_id,
            "chat_id": request.chat_id,
            "conversation_history": request.conversation_history or [],
            "force_phrase_used": False,
        }

        final: Dict[str, Any] = await graph.ainvoke(state)
        response_data = final.get("response_data") or {}
        response_text = response_data.get("response") or final.get("response_text") or ""

        triage_level = response_data.get("triage_level")
        routing = response_data.get("routing") or "unknown"
        metadata = response_data.get("metadata") or {}

        return TriageResponse(
            response=response_text,
            triage_level=triage_level,
            routing=routing,
            symptoms=metadata.get("symptoms") or final.get("symptoms") or [],
            reasoning=final.get("ml_reasoning") or "",
            compliance_passed=final.get("compliance_passed", True),
            audit_hash=final.get("audit_hash"),
        )

    @staticmethod
    def reset() -> None:
        reset_graph()
