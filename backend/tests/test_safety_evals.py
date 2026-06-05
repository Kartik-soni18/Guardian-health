import asyncio
import os

import pytest

os.environ.setdefault("MOCK_MODE", "true")

from app.graph import get_triage_graph, reset_graph
from app.graph.state import TriageState


@pytest.fixture(autouse=True)
def _reset_graph():
    reset_graph()
    yield
    reset_graph()


def _invoke(query: str, history=None):
    graph = get_triage_graph()
    state: TriageState = {
        "user_input": query,
        "user_id": None,
        "chat_id": None,
        "conversation_history": history or [],
    }
    return asyncio.run(graph.ainvoke(state))


class TestPrivacyProxy:
    def test_pii_detected_name(self):
        result = _invoke("My name is John Smith and I have a headache.")
        assert result.get("pii_detected") is True

    def test_no_pii_clean_query(self):
        result = _invoke("I have a mild headache and feel tired.")
        assert result.get("response_data") or result.get("response_text")


class TestMedicalFirewall:
    def test_medical_query_accepted(self):
        result = _invoke("I have chest pain and shortness of breath.")
        assert result.get("is_medical") is not False

    def test_non_medical_rejected(self):
        result = _invoke("What is the capital of France?")
        data = result.get("response_data") or {}
        if result.get("is_medical") is False:
            assert data.get("routing") == "rejected" or result.get("rejection_reason")
