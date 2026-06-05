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

        return TriageResponse(
            response=response_text,
            triage_level=response_data.get("triage_level"),
            routing=response_data.get("routing") or "unknown",
            symptoms=response_data.get("metadata", {}).get("symptoms") or final.get("symptoms") or [],
            assessment=response_data.get("assessment", ""),
            reasoning=response_data.get("reasoning") or final.get("ml_reasoning") or "",
            what_to_do=_as_str_list(response_data.get("what_to_do")),
            what_not_to_do=_as_str_list(response_data.get("what_not_to_do")),
            likely_conditions=_as_str_list(response_data.get("likely_conditions")),
            red_flags=_as_str_list(response_data.get("red_flags")),
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
