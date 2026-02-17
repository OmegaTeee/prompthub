"""
MCP Gateway — Streamable HTTP access to managed MCP servers.

Creates a FastMCP composite server that proxies to all running MCP server
bridges. Mounted as an ASGI sub-application alongside FastAPI, this gives
MCP clients a standards-compliant Streamable HTTP endpoint:

    Client → HTTP POST /mcp-direct/mcp → FastMCP Gateway → Bridge → Stdio subprocess

Each running server's tools, resources, and prompts are namespaced by
server name (e.g., "context7_resolve-library-id") to avoid collisions.

The gateway is rebuilt dynamically whenever servers start or stop, so it
always reflects the current set of running MCP servers.
"""

import logging

from fastmcp import FastMCP

from router.servers.supervisor import Supervisor

logger = logging.getLogger(__name__)


def build_mcp_gateway(supervisor: Supervisor) -> FastMCP:
    """
    Build a FastMCP gateway that proxies to all running MCP server bridges.

    Creates a composite FastMCP server by mounting proxy sub-servers for
    each connected bridge. The proxy reuses the existing Client session
    (already connected via StdioTransport) so no new subprocesses are spawned.

    Args:
        supervisor: Supervisor with active bridges

    Returns:
        FastMCP gateway server (can be served via .http_app())
    """
    gateway = FastMCP("PromptHub Gateway")

    for name, bridge in supervisor.iter_bridges():
        if not bridge.is_connected:
            logger.debug(f"Skipping {name} — bridge not connected")
            continue

        try:
            proxy = FastMCP.as_proxy(bridge.client, name=name)
            gateway.mount(proxy, prefix=name)
            logger.info(f"Mounted proxy for {name}")
        except Exception as e:
            logger.warning(f"Failed to mount proxy for {name}: {e}")

    return gateway
