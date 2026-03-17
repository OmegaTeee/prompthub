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
    """Parse the ``GATEWAY_SERVERS`` setting into a list of server names.

    Splits on commas, strips whitespace, and drops empty segments so that
    trailing commas or extra spaces are harmless.

    Args:
        gateway_servers: Raw value of the ``GATEWAY_SERVERS`` env var /
            settings field (e.g. ``"context7, duckduckgo"``).

    Returns:
        A list of trimmed server names, or an empty list when the input
        is empty or blank (meaning "all servers").
    """
    if not gateway_servers or not gateway_servers.strip():
        return []
    return [s.strip() for s in gateway_servers.split(",") if s.strip()]


def build_mcp_gateway(
    supervisor: "Supervisor",
    registry: "ServerRegistry",
    server_filter: list[str] | None = None,
) -> FastMCP:
    """Build a FastMCP gateway that proxies to configured MCP servers.

    Iterates over every server in the registry (optionally narrowed by
    *server_filter*), creates a dynamic client factory via
    :func:`_make_client_factory`, wraps it in a ``FastMCPProxy``, and
    mounts it on the gateway under the server's name prefix.

    Servers that fail to mount (e.g. import errors in proxy setup) are
    logged and skipped -- they do not prevent the remaining servers from
    being exposed.

    Args:
        supervisor: The :class:`~router.servers.supervisor.Supervisor`
            holding active bridges for all running servers.
        registry: The :class:`~router.servers.registry.ServerRegistry`
            containing every configured server (running or not).
        server_filter: Allowlist of server names to include.  ``None``
            or an empty list means *all* servers.  Typically produced by
            :func:`_parse_server_filter` from the ``GATEWAY_SERVERS``
            setting.

    Returns:
        A :class:`~fastmcp.FastMCP` gateway instance ready to be served
        via ``gateway.http_app(path="/mcp")``.
    """
    gateway = FastMCP("PromptHub Gateway")
    mounted = 0

    for state in registry.list_all():
        name = state.config.name
        # Falsy server_filter (None or []) means "mount everything"
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
