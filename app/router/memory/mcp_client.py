"""
Memory MCP client for optional graph synchronization.

Uses httpx to call /mcp/memory/* endpoints. Gracefully degrades when
Memory MCP server is unavailable (returns None / empty results).
"""

import logging

import httpx

logger = logging.getLogger(__name__)


class MemoryMCPClient:
    """
    Optional sync layer to Memory MCP server.

    Calls PromptHub's /mcp/memory/* proxy endpoints to sync session
    entities and facts with a Memory MCP server running behind PromptHub.

    When no ``base_url`` is provided, the URL is derived from
    ``Settings.host`` / ``Settings.port`` via lazy ``get_settings()``
    (same deferred-import pattern used by storage classes to avoid
    circular imports).
    """

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize with base URL to PromptHub.

        Args:
            base_url: Explicit base URL (e.g. ``http://127.0.0.1:9090``).
                If ``None``, derived from ``Settings.host`` and
                ``Settings.port``. A bind address of ``0.0.0.0`` is
                rewritten to ``127.0.0.1`` since the wildcard address
                is not connectable as a client target.
        """
        if base_url is None:
            from router.config import get_settings

            settings = get_settings()
            # 0.0.0.0 is a bind address, not connectable — use loopback
            host = (
                "127.0.0.1" if settings.host == "0.0.0.0" else settings.host
            )
            base_url = f"http://{host}:{settings.port}"
        self.base_url = base_url
        self.memory_mcp_path = "/mcp/memory"

    async def sync_session_entity(self, session_id: str, client_id: str) -> bool:
        """
        Create a session entity in Memory MCP.

        Args:
            session_id: Session ID
            client_id: Client ID

        Returns:
            True if successful, False if Memory MCP unavailable
        """
        result = await self._call_tool(
            "create_entities",
            {
                "entities": [
                    {
                        "name": f"Session {session_id}",
                        "type": "session",
                        "attributes": {
                            "session_id": session_id,
                            "client_id": client_id,
                        },
                    }
                ]
            },
        )
        return result is not None

    async def add_observation(self, session_id: str, fact: str) -> bool:
        """
        Add a fact as an observation in Memory MCP.

        Args:
            session_id: Session ID
            fact: Fact text

        Returns:
            True if successful, False if Memory MCP unavailable
        """
        result = await self._call_tool(
            "add_observations",
            {
                "observations": [
                    {
                        "type": "fact",
                        "content": fact,
                        "related_entity_id": session_id,
                    }
                ]
            },
        )
        return result is not None

    async def get_session_graph(self, session_id: str) -> dict | None:
        """
        Get the knowledge graph for a session.

        Args:
            session_id: Session ID

        Returns:
            Graph dict or None if unavailable
        """
        result = await self._call_tool(
            "read_graph",
            {
                "entity_id": session_id,
            },
        )
        return result

    async def search_facts(self, query: str) -> list[dict]:
        """
        Search facts across all sessions.

        Args:
            query: Search query

        Returns:
            List of matching facts (empty if unavailable)
        """
        result = await self._call_tool(
            "search_nodes",
            {
                "query": query,
            },
        )
        if result is None:
            return []

        # Expect result to be {"nodes": [...]} or similar
        if isinstance(result, dict):
            return result.get("nodes", [])

        return []

    async def _call_tool(
        self, tool_name: str, arguments: dict
    ) -> dict | None:
        """
        Call a Memory MCP tool via PromptHub's /mcp/memory endpoint.

        Args:
            tool_name: Tool name (e.g., "create_entities")
            arguments: Tool arguments

        Returns:
            Tool result or None if unavailable
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # POST to /mcp/memory/call_tool
                response = await client.post(
                    f"{self.base_url}{self.memory_mcp_path}/call_tool",
                    json={
                        "name": tool_name,
                        "arguments": arguments,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    # Expect {"result": {...}} or similar
                    return data.get("result") or data
                else:
                    logger.debug(
                        f"Memory MCP tool {tool_name} failed: {response.status_code}"
                    )
                    return None

        except (httpx.RequestError, httpx.TimeoutException) as e:
            # Memory MCP unavailable — graceful degradation
            logger.debug(f"Memory MCP unavailable: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error calling Memory MCP: {e}")
            return None
