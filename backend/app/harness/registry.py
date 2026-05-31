"""Agent registry for discovery and lookup."""

from app.harness.base_agent import BaseAgent

_registry: dict[str, BaseAgent] = {}


class AgentRegistry:
    """Simple global registry for GuardianHealth agents."""

    @staticmethod
    def register(agent: BaseAgent) -> BaseAgent:
        _registry[agent.name] = agent
        return agent

    @staticmethod
    def get(name: str) -> BaseAgent | None:
        return _registry.get(name)

    @staticmethod
    def list_agents() -> list[str]:
        return list(_registry.keys())

    @staticmethod
    def clear() -> None:
        _registry.clear()
