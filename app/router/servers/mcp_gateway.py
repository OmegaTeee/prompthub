"""
MCP Gateway — Streamable HTTP access to managed MCP servers.

Creates a FastMCP composite server that proxies to all configured MCP server
bridges. Mounted as an ASGI sub-application alongside FastAPI, this gives
MCP clients a standards-compliant Streamable HTTP endpoint::

    Client --> HTTP POST /mcp-direct/mcp --> FastMCP Gateway --> Bridge --> Stdio subprocess

Each server's tools, resources, and prompts are namespaced by server name
(e.g., ``context7_resolve-library-id``) to avoid collisions.

**Dynamic client factories** — Server restarts, late starts, and stop/start
cycles are handled transparently. The gateway only needs rebuilding for
topology changes (server installed or deleted), not lifecycle changes.

**Server filtering** — The ``GATEWAY_SERVERS`` env var (comma-separated)
controls which servers are exposed through the gateway. When empty or unset,
all configured servers are mounted. The raw setting string is parsed by
:func:`_parse_server_filter` and passed as the ``server_filter`` parameter
to :func:`build_mcp_gateway`.

Example::

    # Expose only three servers
    GATEWAY_SERVERS="context7,duckduckgo,sequential-thinking"

Functions:
    _parse_server_filter: Parse ``GATEWAY_SERVERS`` string into a name list.
    _make_client_factory: Build a per-server callable that resolves the
        current bridge at request time.
    build_mcp_gateway: Assemble the FastMCP gateway with proxy mounts.
"""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from fastmcp import Client, FastMCP
from fastmcp.server.proxy import FastMCPProxy

if TYPE_CHECKING:
    from router.servers.registry import ServerRegistry
    from router.servers.supervisor import Supervisor

logger = logging.getLogger(__name__)


def _make_client_factory(
    supervisor: "Supervisor", server_name: str
) -> Callable[[], Client]:
    """Create a client factory that dynamically resolves the current bridge.

    Returns a zero-argument callable that FastMCPProxy invokes on every tool
    listing or tool call.  The callable looks up the live bridge from the
    supervisor at call time, so server restarts are picked up without
    rebuilding the gateway.

    Args:
        supervisor: The Supervisor holding active bridges.
        server_name: Name of the MCP server (must match a key in
            ``mcp-servers.json``).

    Returns:
        A callable returning the bridge's :class:`~fastmcp.Client`.

    Raises:
        RuntimeError: (from the returned callable) If the server has no
            bridge or the bridge is disconnected.  FastMCPProxy catches
            this and gracefully omits the server's tools from the
            aggregated listing.
    """

    def client_factory() -> Client:
        bridge = supervisor.get_bridge(server_name)
        if bridge is None or not bridge.is_connected:
            raise RuntimeError(f"Server {server_name!r} is not running")
        return bridge.client

    return client_factory


def _parse_server_filter(gateway_servers: str) -> list[str]:
    """Parse comma-separated server filter into a list of names."""
    if not gateway_servers or not gateway_servers.strip():
        return []
    return [s.strip() for s in gateway_servers.split(",") if s.strip()]


def build_mcp_gateway(
    supervisor: "Supervisor",
    registry: "ServerRegistry",
    server_filter: list[str] | None = None,
) -> FastMCP:
    """
    Build a FastMCP gateway that proxies to configured MCP servers.

    Mounts a proxy for configured servers (filtered by server_filter if
    provided). Each proxy uses a dynamic client factory that resolves the
    current bridge at request time, so server restarts are handled
    transparently.

    Args:
        supervisor: Supervisor with active bridges
        registry: Registry with all configured servers
        server_filter: Optional list of server names to include.
                       Empty list or None = all servers.

    Returns:
        FastMCP gateway server (can be served via .http_app())
    """
    gateway = FastMCP("PromptHub Gateway")
    mounted = 0

    for state in registry.list_all():
        name = state.config.name
        if server_filter and name not in server_filter:
            logger.debug(f"Skipping {name} (not in gateway_servers filter)")
            continue
        try:
            factory = _make_client_factory(supervisor, name)
            proxy = FastMCPProxy(client_factory=factory, name=name)
            gateway.mount(proxy, prefix=name)
            mounted += 1
            logger.info(f"Mounted dynamic proxy for {name}")
        except Exception as e:
            logger.warning(f"Failed to mount proxy for {name}: {e}")

    if server_filter:
        logger.info(
            f"Gateway filter active: {mounted} of {len(list(registry.list_all()))} "
            f"servers mounted (filter: {', '.join(server_filter)})"
        )

    return gateway
