import sys
import json
import logging

logger = logging.getLogger(__name__)

try:
    from mcp.server.fastmcp import FastMCP
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    logger.warning("mcp package not installed — running in direct-call mode (pip install mcp[cli])")

from app.disease_predictor import predict_disease as _predict


def predict_disease_tool(symptoms: list) -> dict:
    return _predict(symptoms, verbose=False)


if _MCP_AVAILABLE:
    mcp = FastMCP(name="Guardian-ML")

    @mcp.tool(
        name="predict_disease",
        description="Predict disease from symptom strings using the trained Random Forest classifier.",
    )
    def _mcp_predict(symptoms: list) -> dict:
        return predict_disease_tool(symptoms)


class GuardianMLClient:

    async def predict(self, symptoms: list) -> dict:
        if _MCP_AVAILABLE:
            return await self._call_via_mcp(symptoms)
        return self._call_direct(symptoms)

    async def _call_via_mcp(self, symptoms: list) -> dict:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.ml_mcp_server"],
        )
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool("predict_disease", {"symptoms": symptoms})
                    for item in (result.content or []):
                        if getattr(item, "type", None) == "text":
                            return json.loads(item.text)
                        if isinstance(item, dict) and item.get("type") == "text":
                            return json.loads(item["text"])
        except Exception as exc:
            logger.warning("MCP call failed (%s) — direct fallback", exc)
        return self._call_direct(symptoms)

    def _call_direct(self, symptoms: list) -> dict:
        return predict_disease_tool(symptoms)


if __name__ == "__main__":
    if not _MCP_AVAILABLE:
        print("ERROR: mcp package not installed. Run: pip install 'mcp[cli]'", file=sys.stderr)
        sys.exit(1)
    mcp.run()
