"""Build structured triage responses for API and frontend rendering."""

from typing import Any


def _as_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def build_from_triage(result: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    scratchpad = state.get("scratchpad") or {}
    differentials = _as_list(scratchpad.get("differentials"))
    if differentials and not result.get("likely_conditions"):
        result = {**result, "likely_conditions": differentials[:3]}

    what_to_do = _as_list(result.get("what_to_do"))
    if not what_to_do and result.get("action"):
        what_to_do = [result["action"]]
    if result.get("timeframe"):
        what_to_do.append(f"Timeframe: {result['timeframe']}")
    if result.get("safety_net"):
        what_to_do.append(result["safety_net"])

    what_not_to_do = _as_list(result.get("what_not_to_do"))
    assessment = (
        result.get("assessment")
        or result.get("explanation")
        or scratchpad.get("observations")
        or ""
    )

    summary_parts = []
    if assessment:
        summary_parts.append(assessment)
    level = result.get("level", "unknown")
    care = result.get("care_setting", "").replace("_", " ").title()
    if level != "unknown":
        summary_parts.append(f"Recommended care: {care or level}")

    return {
        "response": "\n\n".join(summary_parts) if summary_parts else "Health guidance based on your symptoms.",
        "triage_level": result.get("level"),
        "assessment": assessment,
        "what_to_do": what_to_do,
        "what_not_to_do": what_not_to_do,
        "likely_conditions": _as_list(result.get("likely_conditions")) or differentials[:3],
        "red_flags": _as_list(result.get("red_flags")) or _as_list(scratchpad.get("red_flags")),
        "reasoning": scratchpad.get("heuristic_notes") or state.get("ml_reasoning") or assessment,
        "confidence": _resolve_confidence(state, result),
        "dataset_used": float(state.get("ml_confidence", 0.0)) >= 0.5,
    }


def build_from_consultation(result: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    scratchpad = state.get("scratchpad") or {}
    what_to_do = _as_list(result.get("what_to_do"))
    if not what_to_do and result.get("plan"):
        what_to_do = _as_list(result["plan"])
    if result.get("when_to_seek"):
        what_to_do.append(f"Seek care if: {result['when_to_seek']}")

    assessment = result.get("assessment") or scratchpad.get("observations") or ""
    likely = _as_list(result.get("likely_conditions")) or _as_list(scratchpad.get("differentials"))

    return {
        "response": assessment or "Clinical guidance based on your description.",
        "triage_level": result.get("triage_level") or _infer_level(state),
        "assessment": assessment,
        "what_to_do": what_to_do,
        "what_not_to_do": _as_list(result.get("what_not_to_do")),
        "likely_conditions": likely[:3],
        "red_flags": _as_list(scratchpad.get("red_flags")),
        "reasoning": scratchpad.get("observations") or assessment,
        "confidence": _resolve_confidence(state, result, prefer_reasoning=True),
        "dataset_used": False,
    }


def _infer_level(state: dict[str, Any]) -> str:
    severity = (state.get("severity") or "").lower()
    if severity == "severe":
        return "urgent"
    if severity == "moderate":
        return "routine"
    return "self_care"


def _resolve_confidence(
    state: dict[str, Any],
    result: dict[str, Any],
    prefer_reasoning: bool = False,
) -> float:
    if prefer_reasoning or float(state.get("ml_confidence", 0.0)) < 0.5:
        return float(state.get("reasoning_confidence", 0.5))
    ml_conf = float(state.get("ml_confidence", 0.0))
    reasoning_conf = float(state.get("reasoning_confidence", 0.5))
    return round(max(ml_conf, reasoning_conf * 0.7), 2)
