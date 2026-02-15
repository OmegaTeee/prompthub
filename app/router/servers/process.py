"""
Process manager for MCP server subprocesses.

Handles:
- Spawning new server processes
- Stopping running processes (graceful + force)
- Tracking process state
"""

import asyncio
import logging
import os
import time
from typing import TYPE_CHECKING

from router.config import get_settings
from router.keyring_manager import get_keyring_manager
from router.servers.models import ProcessInfo, ServerStatus

if TYPE_CHECKING:
    from router.servers.registry import ServerRegistry

logger = logging.getLogger(__name__)


class ProcessManager:
    """
    Manages subprocess lifecycle for stdio MCP servers.

    Each server process is spawned as a subprocess with stdin/stdout
    pipes for JSON-RPC communication.
    """

    def __init__(self, registry: "ServerRegistry"):
        """
        Initialize the process manager.

        Args:
            registry: Server registry for config and state tracking
        """
        self.registry = registry
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._shutdown_timeout = 5.0  # Seconds to wait for graceful shutdown

    async def start(self, name: str) -> ProcessInfo:
        """
        Start a server process.

        Args:
            name: Name of server to start

        Returns:
            Updated ProcessInfo with PID and status

        Raises:
            ValueError: If server not found or already running
            RuntimeError: If process fails to start
        """
        config = self.registry.get(name)
        if not config:
            raise ValueError(f"Server {name} not found")

        # Check if already running
        if name in self._processes:
            process = self._processes[name]
            if process.returncode is None:  # Still running
                raise ValueError(f"Server {name} is already running")
            # Clean up dead process
            del self._processes[name]

        # Update status to starting
        self.registry.update_process_info(name, status=ServerStatus.STARTING)

        try:
            # Build command
            cmd = config.get_full_command()
            logger.info(f"Starting server {name}: {' '.join(cmd)}")

            # Merge environment with keyring credential resolution
            env = os.environ.copy()

            # Process env config, resolving keyring references
            km = get_keyring_manager()
            resolved_env = km.process_env_config(config.env)

            # Log credential retrieval status
            keyring_keys = [
                k for k, v in config.env.items()
                if isinstance(v, dict) and v.get("source") == "keyring"
            ]
            if keyring_keys:
                logger.info(
                    f"Server {name}: Resolved {len(keyring_keys)} credential(s) from keyring"
                )

            env.update(resolved_env)

            # Spawn process (cwd=workspace_root so ./mcps/ paths resolve)
            settings = get_settings()
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=settings.workspace_root,
            )

            self._processes[name] = process

            # Update registry with process info
            info = self.registry.update_process_info(
                name,
                pid=process.pid,
                status=ServerStatus.RUNNING,
                started_at=time.time(),
                last_error=None,
            )

            logger.info(f"Started server {name} with PID {process.pid}")
            return info

        except Exception as e:
            error_msg = f"Failed to start server {name}: {e}"
            logger.error(error_msg)
            self.registry.update_process_info(
                name,
                status=ServerStatus.FAILED,
                last_error=error_msg,
            )
            raise RuntimeError(error_msg) from e

    async def stop(self, name: str, force: bool = False) -> None:
        """
        Stop a server process.

        Args:
            name: Name of server to stop
            force: If True, use SIGKILL immediately

        Raises:
            ValueError: If server not found or not running
        """
        if name not in self._processes:
            # Check if it's in registry but not tracked
            info = self.registry.get_process_info(name)
            if info and info.status == ServerStatus.STOPPED:
                return  # Already stopped
            raise ValueError(f"Server {name} is not running")

        process = self._processes[name]

        # Update status
        self.registry.update_process_info(name, status=ServerStatus.STOPPING)

        try:
            if force:
                # Force kill
                logger.warning(f"Force killing server {name}")
                process.kill()
            else:
                # Graceful shutdown
                logger.info(f"Stopping server {name} gracefully")
                process.terminate()

                try:
                    # Wait for graceful shutdown
                    await asyncio.wait_for(
                        process.wait(), timeout=self._shutdown_timeout
                    )
                except TimeoutError:
                    # Force kill after timeout
                    logger.warning(
                        f"Server {name} did not stop gracefully, force killing"
                    )
                    process.kill()
                    await process.wait()

            # Clean up
            del self._processes[name]

            # Update status
            self.registry.update_process_info(
                name,
                pid=None,
                status=ServerStatus.STOPPED,
            )

            logger.info(f"Stopped server {name}")

        except Exception as e:
            logger.error(f"Error stopping server {name}: {e}")
            raise

    async def restart(self, name: str) -> ProcessInfo:
        """
        Restart a server process.

        Args:
            name: Name of server to restart

        Returns:
            Updated ProcessInfo
        """
        # Stop if running
        if name in self._processes:
            await self.stop(name)

        # Start fresh
        return await self.start(name)

    def is_running(self, name: str) -> bool:
        """Check if a server process is running."""
        if name not in self._processes:
            return False

        process = self._processes[name]
        return process.returncode is None

    def get_process(self, name: str) -> asyncio.subprocess.Process | None:
        """Get the subprocess for a server (for stdio bridge)."""
        return self._processes.get(name)

    async def check_process(self, name: str) -> bool:
        """
        Check if a process is still alive and update status.

        Returns:
            True if process is alive, False otherwise
        """
        if name not in self._processes:
            return False

        process = self._processes[name]

        if process.returncode is not None:
            # Process has exited
            exit_code = process.returncode
            stderr_output = ""

            # Try to read stderr for error info
            if process.stderr:
                try:
                    # Increased timeout from 0.1s to 1.0s to capture full error output
                    stderr_bytes = await asyncio.wait_for(
                        process.stderr.read(1024), timeout=1.0
                    )
                    stderr_output = stderr_bytes.decode("utf-8", errors="replace")
                except (TimeoutError, Exception):
                    pass

            error_msg = f"Process exited with code {exit_code}"
            if stderr_output:
                error_msg += f": {stderr_output[:200]}"

            logger.warning(f"Server {name} process died: {error_msg}")

            # Clean up
            del self._processes[name]

            # Update status
            self.registry.update_process_info(
                name,
                pid=None,
                status=ServerStatus.STOPPED,
                last_error=error_msg,
            )

            return False

        return True

    async def stop_all(self) -> None:
        """Stop all running server processes."""
        names = list(self._processes.keys())
        for name in names:
            try:
                await self.stop(name)
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")

    def get_running_servers(self) -> list[str]:
        """Get names of all running servers."""
        return [name for name in self._processes.keys() if self.is_running(name)]
