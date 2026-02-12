"""
Supervisor for monitoring MCP server health and auto-restart.

The supervisor:
- Starts servers configured with auto_start=true
- Periodically checks if processes are alive
- Restarts crashed servers (if restart_on_failure=true)
- Respects max_restarts limit before marking as FAILED
"""

import asyncio
import logging
from typing import TYPE_CHECKING

from router.servers.bridge import StdioBridge
from router.servers.models import ServerStatus, ServerTransport

if TYPE_CHECKING:
    from router.servers.process import ProcessManager
    from router.servers.registry import ServerRegistry

logger = logging.getLogger(__name__)


class Supervisor:
    """
    Monitors server health and handles auto-restart.

    The supervisor runs as a background task that periodically
    checks on all managed servers and restarts any that have died.
    """

    def __init__(
        self,
        registry: "ServerRegistry",
        process_manager: "ProcessManager",
        check_interval: float = 10.0,
    ):
        """
        Initialize the supervisor.

        Args:
            registry: Server registry for config and state
            process_manager: Process manager for starting/stopping
            check_interval: Seconds between health checks
        """
        self.registry = registry
        self.process_manager = process_manager
        self.check_interval = check_interval

        self._running = False
        self._task: asyncio.Task | None = None
        self._bridges: dict[str, StdioBridge] = {}

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

        # Close all bridges
        for name, bridge in list(self._bridges.items()):
            try:
                await bridge.close()
            except Exception as e:
                logger.error(f"Error closing bridge for {name}: {e}")
        self._bridges.clear()

        # Stop all servers
        await self.process_manager.stop_all()

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
        Start a server and initialize its bridge.

        Args:
            name: Name of server to start
        """
        config = self.registry.get(name)
        if not config:
            raise ValueError(f"Server {name} not found")

        # Start the process
        await self.process_manager.start(name)

        # For stdio servers, create and initialize bridge
        if config.transport == ServerTransport.STDIO:
            process = self.process_manager.get_process(name)
            if process:
                bridge = StdioBridge(process, name)
                await bridge.start()

                # Initialize MCP protocol
                try:
                    capabilities = await bridge.initialize()
                    logger.info(f"Initialized {name}, capabilities: {capabilities}")
                except Exception as e:
                    logger.warning(f"Failed to initialize {name}: {e}")
                    # Don't fail - some servers might not support initialize

                self._bridges[name] = bridge

    async def stop_server(self, name: str) -> None:
        """
        Stop a server and close its bridge.

        Args:
            name: Name of server to stop
        """
        # Close bridge first
        if name in self._bridges:
            try:
                await self._bridges[name].close()
            except Exception as e:
                logger.error(f"Error closing bridge for {name}: {e}")
            del self._bridges[name]

        # Stop process
        await self.process_manager.stop(name)

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

    def get_bridge(self, name: str) -> StdioBridge | None:
        """Get the stdio bridge for a server."""
        return self._bridges.get(name)

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
        """Check health of all running servers."""
        running_servers = self.process_manager.get_running_servers()

        for name in running_servers:
            try:
                await self._check_server(name)
            except Exception as e:
                logger.error(f"Error checking server {name}: {e}")

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

        # Check if process is still alive
        is_alive = await self.process_manager.check_process(name)

        if is_alive:
            return  # Server is healthy

        # Server died
        logger.warning(f"Server {name} has died")

        # Close the bridge if it exists
        if name in self._bridges:
            try:
                await self._bridges[name].close()
            except Exception:
                pass
            del self._bridges[name]

        # Check if we should restart
        if not config.restart_on_failure:
            logger.info(f"Server {name} restart disabled, marking as stopped")
            self.registry.update_process_info(name, status=ServerStatus.STOPPED)
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
