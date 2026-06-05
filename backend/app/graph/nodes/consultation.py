"""Consultation node — LLM reasoning when dataset confidence is low."""

import logging

from app.agents.llm_client import AsyncLLMClient
from app.agents.triage_agent import consult
from app.graph.response_builder import build_from_consultation
from app.graph.state import TriageState

logger = logging.getLogger("guardian.nodes.consultation")

_llm: AsyncLLMClient | None = None


def _get_llm() -> AsyncLLMClient:
    global _llm
    if _llm is None:
        _llm = AsyncLLMClient()
    return _llm


async def consultation_node(state: TriageState) -> dict:
    if state.get("error"):
        return {}

    scrubbed = state.get("scrubbed_input", state["user_input"])
    history = state.get("conversation_history", [])
    top_predictions = state.get("top_predictions", [])
    ml_confidence = state.get("ml_confidence", 0.0)

    llm = _get_llm()

    try:
        result = await consult(
            scrubbed=scrubbed,
            history=history,
            top_predictions=top_predictions,
            ml_confidence=ml_confidence,
            llm=llm,
            clinical_entities={
                "symptoms": state.get("symptoms", []),
                "duration": state.get("duration"),
                "severity": state.get("severity"),
            },
            scratchpad=state.get("scratchpad"),
        )

        structured = build_from_consultation(result, state)

        return {
            "consultation_result": result,
            "response_text": structured["response"],
            "structured_response": structured,
            "final_routing": "consultation",
        }
    except Exception as exc:
        logger.error("Consultation node error: %s", exc)
        fallback = {
            "assessment": "Unable to generate detailed guidance at this time.",
            "what_to_do": ["Consult a healthcare provider for personalized advice."],
            "what_not_to_do": ["Do not self-medicate without professional guidance."],
            "triage_level": "routine",
        }
        structured = build_from_consultation(fallback, state)
        return {
            "consultation_result": fallback,
            "response_text": structured["response"],
            "structured_response": structured,
            "final_routing": "consultation",
            "error": f"Consultation node: {type(exc).__name__}",
        }
