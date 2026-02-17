"""
Supervisor for monitoring MCP server health and auto-restart.

The supervisor:
- Starts servers configured with auto_start=true
- Periodically checks if processes are alive
- Restarts crashed servers (if restart_on_failure=true)
- Respects max_restarts limit before marking as FAILED

Uses FastMCPBridge for stdio communication (subprocess + MCP protocol).
"""

import asyncio
import logging
import os
import time
from typing import TYPE_CHECKING

from router.config import get_settings
from router.keyring_manager import get_keyring_manager
from router.servers.fastmcp_bridge import FastMCPBridge
from router.servers.models import ServerConfig, ServerStatus, ServerTransport

if TYPE_CHECKING:
    from router.servers.registry import ServerRegistry

logger = logging.getLogger(__name__)


def resolve_server_env(config: ServerConfig) -> dict[str, str]:
    """
    Resolve environment variables for a server, including keyring references.

    Merges the current process environment with server-specific vars,
    resolving any {"source": "keyring"} entries via macOS Keychain.

    Args:
        config: Server configuration with env dict

    Returns:
        Complete environment dict ready for subprocess
    """
    env = os.environ.copy()

    km = get_keyring_manager()
    resolved_env = km.process_env_config(config.env)

    # Log credential retrieval status
    keyring_keys = [
        k
        for k, v in config.env.items()
        if isinstance(v, dict) and v.get("source") == "keyring"
    ]
    if keyring_keys:
        logger.info(
            f"Server {config.name}: Resolved {len(keyring_keys)} "
            f"credential(s) from keyring"
        )

    env.update(resolved_env)
    return env


class Supervisor:
    """
    Monitors server health and handles auto-restart.

    The supervisor runs as a background task that periodically
    checks on all managed servers and restarts any that have died.
    """

    def __init__(
        self,
        registry: "ServerRegistry",
        check_interval: float = 10.0,
    ):
        """
        Initialize the supervisor.

        Args:
            registry: Server registry for config and state
            check_interval: Seconds between health checks
        """
        self.registry = registry
        self.check_interval = check_interval

        self._running = False
        self._task: asyncio.Task | None = None
        self._bridges: dict[str, FastMCPBridge] = {}

    async def start(self) -> None:
        """Start the supervisor background task."""
        if self._running:
            logger.warning("Supervisor is already running")
            return

        self._running = True
        logger.info("Starting supervisor")

        # Start auto-start servers
        await self.start_auto_servers()

        # Start health check loop
        self._task = asyncio.create_task(self._health_check_loop())

    async def stop(self) -> None:
        """Stop the supervisor and all managed servers."""
        logger.info("Stopping supervisor")
        self._running = False

        # Cancel health check task
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        # Close all bridges (each bridge cleans up its own subprocess)
        for name, bridge in list(self._bridges.items()):
            try:
                await bridge.close()
            except Exception as e:
                logger.error(f"Error closing bridge for {name}: {e}")
        self._bridges.clear()

        # Update all server statuses to stopped
        for state in self.registry.list_all():
            if state.process.status in (
                ServerStatus.RUNNING,
                ServerStatus.STARTING,
            ):
                self.registry.update_process_info(
                    state.name, status=ServerStatus.STOPPED, pid=None
                )

        logger.info("Supervisor stopped")

    async def start_auto_servers(self) -> None:
        """Start all servers configured with auto_start=true."""
        auto_start_configs = self.registry.get_auto_start_servers()

        if not auto_start_configs:
            logger.info("No servers configured for auto-start")
            return

        logger.info(f"Auto-starting {len(auto_start_configs)} servers")

        for config in auto_start_configs:
            try:
                await self.start_server(config.name)
            except Exception as e:
                logger.error(f"Failed to auto-start {config.name}: {e}")

    async def start_server(self, name: str) -> None:
        """
        Start a server and initialize its FastMCP bridge.

        The bridge owns the subprocess lifecycle — it spawns the process
        on start() and kills it on close().

        Args:
            name: Name of server to start
        """
        config = self.registry.get(name)
        if not config:
            raise ValueError(f"Server {name} not found")

        # Close existing bridge if any
        if name in self._bridges:
            try:
                await self._bridges[name].close()
            except Exception:
                pass
            del self._bridges[name]

        # Update status to starting
        self.registry.update_process_info(name, status=ServerStatus.STARTING)

        if config.transport == ServerTransport.STDIO:
            if not config.command:
                raise ValueError(f"Server {name} has no command configured")

            try:
                # Resolve environment (including keyring credentials)
                resolved_env = resolve_server_env(config)

                # Create and start FastMCP bridge
                bridge = FastMCPBridge(
                    command=config.command,
                    args=config.args,
                    env=resolved_env,
                    name=name,
                )
                await bridge.start()

                self._bridges[name] = bridge

                # Update registry with running status
                self.registry.update_process_info(
                    name,
                    status=ServerStatus.RUNNING,
                    started_at=time.time(),
                    last_error=None,
                )

                logger.info(f"Started server {name} via FastMCP bridge")

            except Exception as e:
                error_msg = f"Failed to start server {name}: {e}"
                logger.error(error_msg)
                self.registry.update_process_info(
                    name,
                    status=ServerStatus.FAILED,
                    last_error=error_msg,
                )
                raise RuntimeError(error_msg) from e

    async def stop_server(self, name: str) -> None:
        """
        Stop a server and close its bridge.

        Args:
            name: Name of server to stop
        """
        # Close bridge (handles subprocess cleanup)
        if name in self._bridges:
            try:
                await self._bridges[name].close()
            except Exception as e:
                logger.error(f"Error closing bridge for {name}: {e}")
            del self._bridges[name]

        # Update registry
        self.registry.update_process_info(
            name, pid=None, status=ServerStatus.STOPPED
        )

        # Reset restart count on manual stop
        self.registry.update_process_info(name, restart_count=0)

    async def restart_server(self, name: str) -> None:
        """
        Restart a server.

        Args:
            name: Name of server to restart
        """
        await self.stop_server(name)
        await self.start_server(name)

    def get_bridge(self, name: str) -> FastMCPBridge | None:
        """Get the FastMCP bridge for a server."""
        return self._bridges.get(name)

    def iter_bridges(self) -> list[tuple[str, FastMCPBridge]]:
        """Return list of (name, bridge) pairs for all active bridges."""
        return list(self._bridges.items())

    async def _health_check_loop(self) -> None:
        """Background task for periodic health checks."""
        logger.info(f"Starting health check loop (interval: {self.check_interval}s)")

        try:
            while self._running:
                await asyncio.sleep(self.check_interval)

                if not self._running:
                    break

                await self._check_all_servers()

        except asyncio.CancelledError:
            logger.debug("Health check loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Health check loop error: {e}")

    async def _check_all_servers(self) -> None:
        """Check health of all servers that should be running."""
        for state in self.registry.list_all():
            if state.process.status == ServerStatus.RUNNING:
                try:
                    await self._check_server(state.name)
                except Exception as e:
                    logger.error(f"Error checking server {state.name}: {e}")

    async def _check_server(self, name: str) -> None:
        """
        Check health of a single server.

        If the server has died and restart_on_failure is enabled,
        attempt to restart it (respecting max_restarts).
        """
        config = self.registry.get(name)
        if not config:
            return

        process_info = self.registry.get_process_info(name)
        if not process_info:
            return

        # Check if bridge is still connected
        bridge = self._bridges.get(name)
        is_alive = bridge is not None and bridge.is_connected

        if is_alive:
            return  # Server is healthy

        # Server died
        logger.warning(f"Server {name} has died (bridge disconnected)")

        # Clean up dead bridge
        if name in self._bridges:
            try:
                await self._bridges[name].close()
            except Exception:
                pass
            del self._bridges[name]

        # Update status
        self.registry.update_process_info(
            name,
            pid=None,
            status=ServerStatus.STOPPED,
            last_error="Bridge disconnected (process may have crashed)",
        )

        # Check if we should restart
        if not config.restart_on_failure:
            logger.info(f"Server {name} restart disabled, marking as stopped")
            return

        # Check restart count
        current_restarts = process_info.restart_count
        if current_restarts >= config.max_restarts:
            logger.error(
                f"Server {name} exceeded max restarts ({config.max_restarts}), "
                f"marking as FAILED"
            )
            self.registry.update_process_info(name, status=ServerStatus.FAILED)
            return

        # Attempt restart
        new_restart_count = current_restarts + 1
        logger.info(
            f"Restarting server {name} "
            f"(attempt {new_restart_count}/{config.max_restarts})"
        )

        try:
            await self.start_server(name)
            self.registry.update_process_info(name, restart_count=new_restart_count)
        except Exception as e:
            logger.error(f"Failed to restart {name}: {e}")
            self.registry.update_process_info(
                name,
                status=ServerStatus.FAILED,
                last_error=str(e),
                restart_count=new_restart_count,
            )

    def get_status_summary(self) -> dict:
        """Get a summary of all server statuses."""
        states = self.registry.list_all()
        summary = {
            "total": len(states),
            "running": 0,
            "stopped": 0,
            "failed": 0,
            "servers": {},
        }

        for state in states:
            status = state.process.status
            summary["servers"][state.name] = {
                "status": status.value,
                "pid": state.process.pid,
                "restart_count": state.process.restart_count,
            }

            if status == ServerStatus.RUNNING:
                summary["running"] += 1
            elif status == ServerStatus.FAILED:
                summary["failed"] += 1
            else:
                summary["stopped"] += 1

        return summary
