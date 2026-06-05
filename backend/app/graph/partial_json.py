"""Incremental JSON field extraction for streaming LLM responses."""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import json_repair

logger = logging.getLogger("guardian.partial_json")

PARTIAL_TRIAGE_FIELDS = frozenset({
    "response_mode",
    "triage_level",
    "level_title",
    "level_justification",
    "immediate_actions",
    "crucial_warnings",
    "resource_recommendations",
    "required_follow_up",
    "assessment",
    "likely_conditions",
    "care_setting",
    "follow_up_questions",
    "preliminary_assessment",
    "assumptions",
})

LIST_FIELDS = frozenset({
    "immediate_actions",
    "crucial_warnings",
    "resource_recommendations",
    "required_follow_up",
    "likely_conditions",
    "follow_up_questions",
    "assumptions",
})

OnPartial = Callable[[dict[str, Any]], Awaitable[None] | None]


def _normalize_value(key: str, value: Any) -> Any:
    if key in LIST_FIELDS:
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []
    if isinstance(value, str):
        return value.strip()
    return value


def _extract_fields(obj: dict[str, Any]) -> dict[str, Any]:
    extracted: dict[str, Any] = {}
    for key in PARTIAL_TRIAGE_FIELDS:
        if key not in obj:
            continue
        value = _normalize_value(key, obj[key])
        if value in (None, "", []):
            continue
        extracted[key] = value
    return extracted


def _diff_fields(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    delta: dict[str, Any] = {}
    for key, value in current.items():
        if previous.get(key) != value:
            delta[key] = value
    return delta


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.split("\n", 1)
    if len(lines) < 2:
        return stripped
    body = lines[1]
    if body.endswith("```"):
        body = body.rsplit("```", 1)[0]
    return body.strip()


def try_parse_partial(buffer: str) -> dict[str, Any] | None:
    text = _strip_code_fence(buffer)
    if not text:
        return None
    try:
        repaired = json_repair.repair_json(text)
        if isinstance(repaired, str):
            parsed = json.loads(repaired)
        else:
            parsed = repaired
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


class PartialJSONAccumulator:
    """Accumulate streamed tokens and emit newly parseable JSON fields."""

    def __init__(self, on_partial: OnPartial | None = None) -> None:
        self._buffer = ""
        self._emitted: dict[str, Any] = {}
        self._on_partial = on_partial

    @property
    def buffer(self) -> str:
        return self._buffer

    async def feed(self, token: str) -> None:
        self._buffer += token
        parsed = try_parse_partial(self._buffer)
        if not parsed:
            return
        fields = _extract_fields(parsed)
        delta = _diff_fields(self._emitted, fields)
        if not delta or not self._on_partial:
            return
        self._emitted.update(delta)
        result = self._on_partial(delta)
        if hasattr(result, "__await__"):
            await result

    def finalize(self, parse_raw: Callable[[str], dict[str, Any]]) -> dict[str, Any]:
        return parse_raw(self._buffer)
