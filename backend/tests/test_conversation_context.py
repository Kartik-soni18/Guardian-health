"""Tests for multi-turn triage conversation context."""

from app.graph.conversation_context import (
    build_effective_query,
    is_follow_up_turn,
)


class TestConversationContext:
    def test_follow_up_turn_detected(self):
        history = [
            {"role": "user", "content": "I have a swelling in left ankle"},
            {"role": "assistant", "content": "How long? Is it painful?"},
            {"role": "user", "content": "1- One day 2- No Nope"},
        ]
        assert is_follow_up_turn("1- One day 2- No Nope", history) is True

    def test_build_effective_query_merges_context(self):
        history = [
            {"role": "user", "content": "I have a swelling in left ankle"},
            {"role": "assistant", "content": "How long have you had the swelling?"},
            {"role": "user", "content": "One day, not painful"},
        ]
        result = build_effective_query("One day, not painful", history)
        assert "swelling in left ankle" in result
        assert "One day" in result

    def test_single_message_not_follow_up(self):
        assert is_follow_up_turn("I have a headache", []) is False
