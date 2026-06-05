"""Build structured triage responses for API and frontend rendering."""

from typing import Any

from app.models.enums import TRIAGE_LEVEL_TITLES, TriageLevel

_LEVEL_NUMBERS = {
    "level_1": "1",
    "level_2": "2",
    "level_3": "3",
    "level_4": "4",
    "level_5": "5",
}

_LEGACY_LEVEL_MAP = {
    "emergent": TriageLevel.LEVEL_2,
    "emergency": TriageLevel.LEVEL_1,
    "urgent": TriageLevel.LEVEL_3,
    "routine": TriageLevel.LEVEL_4,
    "less_urgent": TriageLevel.LEVEL_4,
    "prompt": TriageLevel.LEVEL_3,
    "non_urgent": TriageLevel.LEVEL_5,
    "self_care": TriageLevel.LEVEL_5,
}


def _as_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _normalize_level(raw: Any) -> str:
    if not raw:
        return TriageLevel.UNKNOWN
    key = str(raw).lower().strip()
    if key in {e.value for e in TriageLevel}:
        return key
    if key in _LEGACY_LEVEL_MAP:
        return _LEGACY_LEVEL_MAP[key].value
    if key.startswith("level_"):
        return key
    return TriageLevel.UNKNOWN


def _level_title(level: str, explicit: str | None = None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    return TRIAGE_LEVEL_TITLES.get(level, "Unclassified")  # type: ignore[arg-type]


def _format_bullets(items: list[str]) -> str:
    return "\n".join(f"• {item}" for item in items)


def format_triage_report(result: dict[str, Any]) -> str:
    """Render the user-facing triage report in the required section format."""
    level = _normalize_level(result.get("triage_level") or result.get("level"))
    title = _level_title(level, result.get("level_title"))
    level_num = _LEVEL_NUMBERS.get(level, "?")
    justification = (
        result.get("level_justification")
        or result.get("explanation")
        or ""
    )

    sections = [
        f"🚨 **Triage Level: Level {level_num} — {title}**",
        f"*{justification}*" if justification else "",
    ]

    immediate = _as_list(result.get("immediate_actions") or result.get("what_to_do"))
    if immediate:
        sections.append("**🛑 Immediate Actions (What to Do):**")
        sections.append(_format_bullets(immediate))

    warnings = _as_list(result.get("crucial_warnings") or result.get("what_not_to_do"))
    if warnings:
        sections.append("**⚠️ Crucial Warnings (What to PREVENT Doing):**")
        sections.append(_format_bullets(warnings))

    resources = _as_list(result.get("resource_recommendations"))
    if not resources and result.get("care_setting"):
        care = str(result["care_setting"]).replace("_", " ").title()
        resources = [f"Recommended setting: {care}"]
    if resources:
        sections.append("**⚕️ Resource & Care Recommendations:**")
        sections.append(_format_bullets(resources))

    follow_up = _as_list(result.get("required_follow_up"))
    if follow_up:
        sections.append("**❓ Required Follow-Up (If condition changes):**")
        sections.append(_format_bullets(follow_up))

    assumptions = _as_list(result.get("assumptions"))
    if assumptions:
        sections.append("**ℹ️ Assumptions made:**")
        sections.append(_format_bullets(assumptions))

    return "\n\n".join(section for section in sections if section)


def format_follow_up(result: dict[str, Any]) -> str:
    """Render follow-up questions before a full triage report."""
    questions = _as_list(result.get("follow_up_questions"))
    preamble = result.get("preliminary_assessment") or result.get("assessment") or ""

    parts = []
    if preamble:
        parts.append(preamble)
    if questions:
        parts.append("To assess your situation accurately, I need a few details:")
        parts.append(_format_bullets(questions))
    return "\n\n".join(parts) if parts else "Can you describe your symptoms in more detail?"


def build_triage_response(result: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Unified builder for consultation and triage LLM outputs."""
    scratchpad = state.get("scratchpad") or {}
    mode = (result.get("response_mode") or "triage_report").lower()

    if mode == "follow_up":
        assessment = result.get("preliminary_assessment") or scratchpad.get("observations") or ""
        return {
            "response": format_follow_up(result),
            "response_mode": "follow_up",
            "needs_follow_up": True,
            "follow_up_questions": _as_list(result.get("follow_up_questions")),
            "triage_level": None,
            "level_title": None,
            "level_justification": "",
            "assessment": assessment,
            "immediate_actions": [],
            "crucial_warnings": [],
            "resource_recommendations": [],
            "required_follow_up": [],
            "assumptions": [],
            "what_to_do": [],
            "what_not_to_do": [],
            "likely_conditions": _as_list(result.get("likely_conditions")) or _as_list(scratchpad.get("differentials"))[:3],
            "red_flags": _as_list(scratchpad.get("red_flags")),
            "reasoning": assessment,
            "confidence": _resolve_confidence(state, result, prefer_reasoning=True),
            "dataset_used": float(state.get("ml_confidence", 0.0)) >= 0.5,
            "care_setting": None,
        }

    level = _normalize_level(result.get("triage_level") or result.get("level"))
    title = _level_title(level, result.get("level_title"))
    justification = result.get("level_justification") or result.get("explanation") or ""

    immediate = _as_list(result.get("immediate_actions") or result.get("what_to_do"))
    if not immediate and result.get("action"):
        immediate = [str(result["action"])]
    if result.get("timeframe"):
        immediate.append(f"Timeframe: {result['timeframe']}")
    if result.get("safety_net"):
        immediate.append(str(result["safety_net"]))

    warnings = _as_list(result.get("crucial_warnings") or result.get("what_not_to_do"))
    resources = _as_list(result.get("resource_recommendations"))
    if not resources and result.get("care_setting"):
        care = str(result["care_setting"]).replace("_", " ").title()
        resources = [f"Recommended setting: {care}"]
    if result.get("when_to_seek"):
        resources.append(f"Escalate if: {result['when_to_seek']}")

    required_follow_up = _as_list(result.get("required_follow_up"))
    assumptions = _as_list(result.get("assumptions"))

    differentials = _as_list(scratchpad.get("differentials"))
    likely = _as_list(result.get("likely_conditions")) or differentials[:3]

    assessment = (
        result.get("assessment")
        or justification
        or scratchpad.get("observations")
        or ""
    )

    report_body = format_triage_report({
        **result,
        "triage_level": level,
        "level_title": title,
        "level_justification": justification,
        "immediate_actions": immediate,
        "crucial_warnings": warnings,
        "resource_recommendations": resources,
        "required_follow_up": required_follow_up,
        "assumptions": assumptions,
    })

    return {
        "response": report_body,
        "response_mode": "triage_report",
        "needs_follow_up": False,
        "follow_up_questions": [],
        "triage_level": level,
        "level_title": title,
        "level_justification": justification,
        "assessment": assessment,
        "immediate_actions": immediate,
        "crucial_warnings": warnings,
        "resource_recommendations": resources,
        "required_follow_up": required_follow_up,
        "assumptions": assumptions,
        "what_to_do": immediate,
        "what_not_to_do": warnings,
        "likely_conditions": likely,
        "red_flags": _as_list(result.get("red_flags")) or _as_list(scratchpad.get("red_flags")),
        "reasoning": scratchpad.get("heuristic_notes") or state.get("ml_reasoning") or assessment,
        "confidence": _resolve_confidence(state, result),
        "dataset_used": float(state.get("ml_confidence", 0.0)) >= 0.5,
        "care_setting": result.get("care_setting"),
    }


def build_from_triage(result: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    return build_triage_response(result, state)


def build_from_consultation(result: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    return build_triage_response(result, state)


def _infer_level(state: dict[str, Any]) -> str:
    severity = (state.get("severity") or "").lower()
    if severity == "severe":
        return TriageLevel.LEVEL_2.value
    if severity == "moderate":
        return TriageLevel.LEVEL_3.value
    return TriageLevel.LEVEL_5.value


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
