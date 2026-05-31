"""GuardianHealth LangGraph orchestration.

Provides a compiled StateGraph that mirrors the existing supervisor pipeline
with explicit nodes, edges, and conditional routing.

Usage:
    from app.graph import get_triage_graph
    graph = get_triage_graph()
    result = await graph.ainvoke(initial_state)
"""

from app.graph.builder import build_graph

_graph_instance = None


def get_triage_graph():
    """Return the compiled triage graph (singleton)."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_graph()
    return _graph_instance


def reset_graph():
    """Clear the singleton (useful in tests)."""
    global _graph_instance
    _graph_instance = None
