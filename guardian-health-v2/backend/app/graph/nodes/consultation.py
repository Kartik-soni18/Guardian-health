"""
Consultation node: Provides clinical consultation when triage confidence is medium.
"""


import logging

from app.agents.llm_client import AsyncLLMClient
from app.agents.triage_agent import consult
from app.graph.state import TriageState

logger = logging.getLogger("guardian.nodes.consultation")

_llm: AsyncLLMClient | None = None

def _get_llm() -> AsyncLLMClient:
    global _llm
    if _llm is None:
        _llm = AsyncLLMClient()
    return _llm


async def consultation_node(state: TriageState) -> dict:
    """
    Provide a consultation response when reasoning confidence is moderate.
    """
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
        )

        # Build response text from structured fields
        response_parts = []
        if result.get("assessment"):
            response_parts.append(f"Assessment: {result['assessment']}")
        if result.get("key_concerns"):
            response_parts.append(f"Key concerns: {', '.join(result['key_concerns'])}")
        if result.get("plan"):
            response_parts.append(f"Plan: {result['plan']}")
        if result.get("when_to_seek"):
            response_parts.append(f"When to seek care: {result['when_to_seek']}")
        if result.get("disclaimer"):
            response_parts.append(f"\n{result['disclaimer']}")
        if result.get("references"):
            response_parts.append(f"\nReferences: {', '.join(result['references'])}")

        response_text = "\n\n".join(response_parts)

        return {
            "consultation_result": result,
            "response_text": response_text,
            "final_routing": "consultation",
        }
    except Exception as exc:
        logger.error("Consultation node error: %s", exc)
        return {
            "consultation_result": {
                "assessment": "Consultation service temporarily unavailable.",
                "plan": "Please consult a healthcare provider directly.",
                "disclaimer": "This is not medical advice.",
            },
            "response_text": (
                "I'm unable to provide a detailed consultation at this moment. "
                "Please contact your healthcare provider for personalized medical advice."
            ),
            "final_routing": "consultation",
            "error": f"Consultation node: {type(exc).__name__}",
        }
