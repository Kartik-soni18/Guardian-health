"""
Pre-processing nodes: input_gate, firewall, privacy.

- input_gate_node: Validates and initializes state from user input.
- firewall_node: Runs medical query classification.
- privacy_node: Scrubs PII from user input.
"""


import logging

from app.agents.firewall import firewall_gate
from app.agents.llm_client import AsyncLLMClient
from app.agents.privacy import scrub_pii
from app.graph.conversation_context import build_effective_query
from app.graph.state import TriageState

logger = logging.getLogger("guardian.nodes.preprocess")

# ---------------------------------------------------------------------------
# Shared LLM client (lazy init)
# ---------------------------------------------------------------------------
_llm: AsyncLLMClient | None = None


def _get_llm() -> AsyncLLMClient:
    global _llm
    if _llm is None:
        _llm = AsyncLLMClient()
    return _llm


# ---------------------------------------------------------------------------
# Node: input_gate
# ---------------------------------------------------------------------------
async def input_gate_node(state: TriageState) -> dict:
    """
    Validates incoming state and ensures all required fields are present.
    Logs the incoming request.
    """
    user_input = state.get("user_input", "")
    user_id = state.get("user_id")
    chat_id = state.get("chat_id")

    if not user_input or not user_input.strip():
        logger.error("Empty user_input received")
        return {"error": "Empty user input"}

    logger.info(
        "input_gate: user=%s chat=%s input_len=%d",
        user_id,
        chat_id,
        len(user_input),
    )

    # Check for emergency force phrases
    force_phrases = ["emergency", "911", "call ambulance", "dying", "unconscious"]
    force_used = any(fp in user_input.lower() for fp in force_phrases)

    return {
        "force_phrase_used": force_used,
        "is_emergency": force_used,
    }


# ---------------------------------------------------------------------------
# Node: firewall
# ---------------------------------------------------------------------------
async def firewall_node(state: TriageState) -> dict:
    """
    Classifies query as medical/non-medical using firewall agent.
    """
    if state.get("error"):
        return {}

    user_input = state["user_input"]
    history = state.get("conversation_history", [])
    llm = _get_llm()

    try:
        result = await firewall_gate(user_input, llm, conversation_history=history)
        return {
            "is_medical": result["is_medical"],
            "is_emergency": state.get("is_emergency", False) or result.get("is_emergency", False),
            "rejection_reason": result.get("reason") if not result["is_medical"] else None,
            "rejection_category": result.get("rejection_category"),
        }
    except Exception as exc:
        logger.error("Firewall node error: %s — failing open", exc)
        return {
            "is_medical": True,
            "is_emergency": state.get("is_emergency", False),
            "rejection_reason": None,
            "rejection_category": None,
        }


# ---------------------------------------------------------------------------
# Node: privacy
# ---------------------------------------------------------------------------
async def privacy_node(state: TriageState) -> dict:
    """
    Scrubs PII from user input before further processing.
    """
    if state.get("error"):
        return {}

    if not state.get("is_medical", True):
        # Non-medical query, no need to scrub
        return {"scrubbed_input": state["user_input"]}

    history = state.get("conversation_history", [])
    effective_query = build_effective_query(state["user_input"], history)

    try:
        result = await scrub_pii(effective_query)
        return {
            "scrubbed_input": result["scrubbed_text"],
            "pii_detected": result["pii_detected"],
            "pii_entities": result["entities_found"],
        }
    except Exception as exc:
        logger.error("Privacy scrubbing error: %s — passing through raw", exc)
        return {
            "scrubbed_input": state["user_input"],
            "pii_detected": False,
            "pii_entities": [],
        }
