"""Clinical reasoning node — LLM scratchpad synthesis."""

import logging
from pathlib import Path

from app.agents.llm_client import AsyncLLMClient
from app.graph.state import TriageState

logger = logging.getLogger("guardian.nodes.reasoning")

_llm: AsyncLLMClient | None = None
PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents" / "prompts"
REASONING_PROMPT_PATH = PROMPTS_DIR / "scratchpad.txt"


def _get_llm() -> AsyncLLMClient:
    global _llm
    if _llm is None:
        _llm = AsyncLLMClient()
    return _llm


async def reasoner_node(state: TriageState) -> dict:
    if state.get("error"):
        return {}

    symptoms = state.get("symptoms", [])
    duration = state.get("duration")
    severity = state.get("severity")
    history = state.get("conversation_history", [])
    extra_context = state.get("extra_context", "")

    context_lines = [f"Symptoms: {', '.join(symptoms)}"]
    if duration:
        context_lines.append(f"Duration: {duration}")
    if severity:
        context_lines.append(f"Severity: {severity}")
    if extra_context:
        context_lines.append(f"Notes: {extra_context[:120]}")

    dataset = state.get("dataset_matches") or []
    if dataset:
        refs = [
            f"{m['symptom']}→{', '.join(m['possible_diseases'][:2])} ({m['severity']})"
            for m in dataset[:3]
        ]
        context_lines.append(f"Dataset: {'; '.join(refs)}")

    if history:
        recent = " | ".join(
            f"{msg.get('role', '?')}: {msg.get('content', '')[:80]}"
            for msg in history[-2:]
        )
        context_lines.append(f"History: {recent}")

    context = "\n".join(context_lines)
    llm = _get_llm()

    try:
        prompt_text = REASONING_PROMPT_PATH.read_text(encoding="utf-8")
        result = await llm.parse_json(
            system_prompt=prompt_text,
            user_content=f"{context}\n\nProvide clinical reasoning for this case.",
            node_type="reasoning",
            max_tokens=768,
        )
        return {
            "scratchpad": {
                "observations": result.get("observations", ""),
                "differentials": result.get("differentials", []),
                "red_flags": result.get("red_flags", []),
                "missing_info": result.get("missing_info", []),
                "heuristic_notes": result.get("heuristic_notes", ""),
            },
            "ml_reasoning": result.get("observations", ""),
            "discrepancy_note": result.get("discrepancy_note", ""),
            "reasoning_confidence": float(result.get("confidence", 0.5)),
        }
    except Exception as exc:
        logger.error("Reasoner node LLM error: %s", exc)
        confidence = 0.5 if symptoms else 0.2
        return {
            "scratchpad": {
                "observations": f"Symptoms: {', '.join(symptoms)}",
                "differentials": [],
                "red_flags": [],
                "missing_info": ["Duration?", "Severity?"],
                "heuristic_notes": "Fallback reasoning.",
            },
            "ml_reasoning": f"Symptom-based review: {', '.join(symptoms)}",
            "discrepancy_note": "LLM reasoning unavailable.",
            "reasoning_confidence": confidence,
        }
