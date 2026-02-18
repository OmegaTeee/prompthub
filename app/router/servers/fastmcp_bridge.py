"""
FastMCP bridge for MCP server communication.

Drop-in replacement for StdioBridge that uses FastMCP's Client + StdioTransport
instead of raw JSON-RPC over stdin/stdout. Preserves the same public interface
so Supervisor, the proxy endpoint, and all consumers work unchanged.

Migration: StdioBridge → FastMCPBridge
  - Constructor takes command/args/env instead of a pre-spawned process
  - initialize() is a no-op (FastMCP does handshake on connect)
  - send() dispatches by method name to typed FastMCP Client methods
  - Health checks use Client.is_connected() and Client.ping()
"""

import asyncio
import logging
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

logger = logging.getLogger(__name__)


class FastMCPBridgeError(Exception):
    """Error in FastMCP bridge communication."""

    pass


class FastMCPBridge:
    """
    Bridges HTTP JSON-RPC to MCP servers via FastMCP Client.

    This is a drop-in replacement for StdioBridge. It owns its subprocess
    lifecycle (spawn on start, kill on close) via FastMCP's StdioTransport.
    """

    def __init__(
        self,
        command: str,
        args: list[str],
        env: dict[str, str] | None = None,
        cwd: str | None = None,
        name: str = "unknown",
    ):
        self.name = name
        self._command = command
        self._args = args
        self._env = env
        self._cwd = cwd
        self._transport = StdioTransport(
            command=command, args=args, env=env, cwd=cwd
        )
        self._client = Client(self._transport)
        self._closed = False

    async def start(self) -> None:
        """Connect to the MCP server (spawns subprocess + protocol handshake)."""
        try:
            await self._client.__aenter__()
            logger.info(f"[{self.name}] FastMCP bridge connected")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to connect: {e}")
            raise FastMCPBridgeError(f"Failed to connect to {self.name}: {e}") from e

    async def close(self) -> None:
        """Disconnect and cleanup subprocess."""
        if self._closed:
            return
        self._closed = True
        try:
            await self._client.close()
            logger.debug(f"[{self.name}] FastMCP bridge closed")
        except Exception as e:
            logger.warning(f"[{self.name}] Error during close: {e}")

    async def send(
        self,
        method: str,
        params: dict | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """
        Send a JSON-RPC request and return response dict.

        Dispatches to typed FastMCP Client methods based on the method name,
        then wraps the result in JSON-RPC envelope format for backward
        compatibility with the proxy endpoint.

        Args:
            method: JSON-RPC method name (e.g., "tools/list", "tools/call")
            params: Method parameters
            timeout: Timeout in seconds

        Returns:
            JSON-RPC response dict with "jsonrpc", "result", and "id" keys
        """
        if self._closed:
            raise FastMCPBridgeError("Bridge is closed")

        params = params or {}

        try:
            result = await asyncio.wait_for(
                self._dispatch(method, params, timeout),
                timeout=timeout,
            )
            return {"jsonrpc": "2.0", "result": result, "id": 1}

        except TimeoutError:
            logger.warning(f"[{self.name}] Timeout on {method}")
            raise
        except Exception as e:
            logger.error(f"[{self.name}] Error on {method}: {e}")
            raise FastMCPBridgeError(f"{method} failed: {e}") from e

    async def _dispatch(
        self, method: str, params: dict, timeout: float
    ) -> dict[str, Any]:
        """Route a method call to the appropriate FastMCP Client method."""

        if method == "tools/list":
            mcp_result = await self._client.list_tools_mcp()
            return mcp_result.model_dump(exclude_none=True)

        elif method == "tools/call":
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            mcp_result = await self._client.call_tool_mcp(
                name=name, arguments=arguments, timeout=timeout
            )
            return mcp_result.model_dump(exclude_none=True)

        elif method == "resources/list":
            mcp_result = await self._client.list_resources_mcp()
            return mcp_result.model_dump(exclude_none=True)

        elif method == "resources/read":
            uri = params.get("uri", "")
            mcp_result = await self._client.read_resource_mcp(uri=uri)
            return mcp_result.model_dump(exclude_none=True)

        elif method == "prompts/list":
            mcp_result = await self._client.list_prompts_mcp()
            return mcp_result.model_dump(exclude_none=True)

        elif method == "prompts/get":
            name = params.get("name", "")
            arguments = params.get("arguments")
            mcp_result = await self._client.get_prompt_mcp(
                name=name, arguments=arguments
            )
            return mcp_result.model_dump(exclude_none=True)

        elif method == "initialize":
            # FastMCP handles initialization on connect — return cached capabilities
            return {}

        elif method == "ping":
            await self._client.ping()
            return {}

        else:
            raise FastMCPBridgeError(f"Unsupported method: {method}")

    async def initialize(self) -> dict:
        """
        MCP protocol handshake.

        FastMCP handles this automatically during start(). This method
        exists for interface compatibility with StdioBridge.
        """
        return {}

    async def list_tools(self) -> list[dict]:
        """List available tools from the MCP server."""
        tools = await self._client.list_tools()
        return [tool.model_dump(exclude_none=True) for tool in tools]

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call a tool on the MCP server."""
        result = await self._client.call_tool_mcp(name=name, arguments=arguments)
        return result.model_dump(exclude_none=True)

    @property
    def client(self) -> Client:
        """Expose the underlying FastMCP Client (for proxy/gateway use)."""
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if the client is currently connected."""
        return not self._closed and self._client.is_connected()

    async def ping(self) -> bool:
        """Send a ping to verify the server is responsive."""
        try:
            return await self._client.ping()
        except Exception:
            return False

    async def send_notification(
        self, method: str, params: dict | None = None
    ) -> None:
        """
        Send a notification (no response expected).

        Interface compatibility with StdioBridge. FastMCP handles
        protocol notifications internally.
        """
        # Most notifications (like initialized) are handled by FastMCP.
        # Log for debugging but no action needed.
        logger.debug(f"[{self.name}] Notification: {method} (handled by FastMCP)")
