"""Build effective clinical context from multi-turn triage conversations."""

from typing import Any

_MEDICAL_HINTS = (
    "symptom", "pain", "swell", "fever", "cough", "headache", "nausea",
    "breath", "bleed", "rash", "hurt", "ache", "dizzy", "vomit", "injury",
    "ankle", "knee", "chest", "stomach", "throat", "medical", "health",
    "doctor", "hospital", "medication", "diagnos",
)


def has_prior_exchange(history: list[dict[str, Any]] | None) -> bool:
    """True when the user is replying in an ongoing conversation."""
    if not history or len(history) < 2:
        return False
    roles = {m.get("role") for m in history}
    return "user" in roles and "assistant" in roles


def first_user_message(history: list[dict[str, Any]] | None) -> str:
    if not history:
        return ""
    for msg in history:
        if msg.get("role") == "user":
            return str(msg.get("content", "")).strip()
    return ""


def looks_medical(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in _MEDICAL_HINTS)


def is_follow_up_turn(user_input: str, history: list[dict[str, Any]] | None) -> bool:
    """Detect short answers to prior triage follow-up questions."""
    if not has_prior_exchange(history):
        return False
    initial = first_user_message(history)
    if not initial or initial.strip() == user_input.strip():
        return False
    # Prior turn established medical context; current message is the reply
    return looks_medical(initial) or len(user_input.strip()) < 300


def build_effective_query(
    user_input: str,
    history: list[dict[str, Any]] | None,
) -> str:
    """
    Merge initial complaint with follow-up answers so downstream nodes
    see the full clinical picture.
    """
    if not is_follow_up_turn(user_input, history):
        return user_input

    initial = first_user_message(history)
    assistant_msgs = [
        str(m.get("content", "")).strip()
        for m in (history or [])
        if m.get("role") == "assistant"
    ]
    last_assistant = assistant_msgs[-1] if assistant_msgs else ""

    parts = [f"Initial complaint: {initial}"]
    if last_assistant:
        parts.append(f"Prior assistant questions: {last_assistant[:600]}")
    parts.append(f"Patient follow-up answers: {user_input}")
    return "\n".join(parts)
