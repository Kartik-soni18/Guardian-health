"""Triage service layer — orchestrates LangGraph invocation."""

import uuid
from datetime import datetime
from typing import Optional

from app.graph import get_triage_graph
from app.graph.state import TriageState


class TriageService:
    @staticmethod
    async def invoke_graph(
        user_query: str,
        user: dict | None = None,
        chat_id: Optional[str] = None,
        conversation_history: Optional[list] = None,
    ) -> dict:
        """Run the full LangGraph triage pipeline and return the response."""
        graph = get_triage_graph()
        initial_state: TriageState = {
            "user_input": user_query,
            "user": user,
            "chat_id": chat_id,
            "conversation_history": conversation_history or [],
        }
        final_state = await graph.ainvoke(initial_state)
        response = final_state.get("response_data", {})
        if response.get("status") == 400 or response.get("error"):
            return {"error": response.get("error", "Unknown error"), "status": 400}
        return response

    @staticmethod
    def generate_chat_id(user: dict | None = None) -> str:
        """Generate a new chat ID for authenticated users."""
        return str(uuid.uuid4())
