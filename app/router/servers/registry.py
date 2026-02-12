"""
Server registry for managing MCP server configurations and runtime state.

The registry:
- Loads server configs from JSON file
- Tracks runtime ProcessInfo for each server
- Provides CRUD operations for server management
"""

import json
import logging
from pathlib import Path

from router.servers.models import (
    ProcessInfo,
    ServerConfig,
    ServerState,
    ServerStatus,
    ServerTransport,
)

logger = logging.getLogger(__name__)


class ServerRegistry:
    """
    Manages server configurations and runtime state.

    Configurations are persisted to JSON file.
    Runtime state (ProcessInfo) is kept in memory only.
    """

    def __init__(self, config_path: str | Path):
        """
        Initialize the registry.

        Args:
            config_path: Path to mcp-servers.json config file
        """
        self.config_path = Path(config_path)
        self._servers: dict[str, ServerConfig] = {}
        self._processes: dict[str, ProcessInfo] = {}

    def load(self) -> None:
        """
        Load server configurations from JSON file.

        Creates empty config file if it doesn't exist.
        """
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}, creating empty")
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.save()
            return

        try:
            with open(self.config_path) as f:
                data = json.load(f)

            servers_data = data.get("servers", {})
            for name, config_dict in servers_data.items():
                try:
                    # Add name to config dict if not present
                    config_dict["name"] = name
                    config = ServerConfig(**config_dict)
                    self._servers[name] = config
                    # Initialize process info as stopped
                    self._processes[name] = ProcessInfo()
                    logger.info(f"Loaded server config: {name}")
                except Exception as e:
                    logger.error(f"Failed to load server {name}: {e}")

            logger.info(f"Loaded {len(self._servers)} server configurations")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            raise

    def save(self) -> None:
        """Save server configurations to JSON file."""
        servers_data = {}
        for name, config in self._servers.items():
            # Convert to dict, excluding 'name' since it's the key
            config_dict = config.model_dump(exclude={"name"})
            # Convert enum to string
            config_dict["transport"] = config.transport.value
            servers_data[name] = config_dict

        data = {"servers": servers_data}

        try:
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self._servers)} server configurations")
        except Exception as e:
            logger.error(f"Failed to save config file: {e}")
            raise

    def get(self, name: str) -> ServerConfig | None:
        """Get a server configuration by name."""
        return self._servers.get(name)

    def get_process_info(self, name: str) -> ProcessInfo | None:
        """Get runtime process info for a server."""
        return self._processes.get(name)

    def get_state(self, name: str) -> ServerState | None:
        """Get combined config and process info for a server."""
        config = self.get(name)
        if not config:
            return None
        process = self._processes.get(name, ProcessInfo())
        return ServerState(config=config, process=process)

    def list_all(self) -> list[ServerState]:
        """List all servers with their current state."""
        states = []
        for name, config in self._servers.items():
            process = self._processes.get(name, ProcessInfo())
            states.append(ServerState(config=config, process=process))
        return states

    def list_names(self) -> list[str]:
        """List all server names."""
        return list(self._servers.keys())

    def add(self, config: ServerConfig) -> None:
        """
        Add a new server configuration.

        Args:
            config: Server configuration to add

        Raises:
            ValueError: If server with same name already exists
        """
        if config.name in self._servers:
            raise ValueError(f"Server {config.name} already exists")

        self._servers[config.name] = config
        self._processes[config.name] = ProcessInfo()
        self.save()
        logger.info(f"Added server: {config.name}")

    def remove(self, name: str) -> None:
        """
        Remove a server configuration.

        Args:
            name: Name of server to remove

        Raises:
            ValueError: If server doesn't exist or is running
        """
        if name not in self._servers:
            raise ValueError(f"Server {name} not found")

        process = self._processes.get(name)
        if process and process.is_running():
            raise ValueError(f"Cannot remove running server {name}, stop it first")

        del self._servers[name]
        if name in self._processes:
            del self._processes[name]
        self.save()
        logger.info(f"Removed server: {name}")

    def update_process_info(
        self,
        name: str,
        *,
        pid: int | None = None,
        status: ServerStatus | None = None,
        started_at: float | None = None,
        restart_count: int | None = None,
        last_error: str | None = None,
    ) -> ProcessInfo:
        """
        Update runtime process info for a server.

        Only provided fields are updated.

        Returns:
            Updated ProcessInfo
        """
        if name not in self._servers:
            raise ValueError(f"Server {name} not found")

        info = self._processes.get(name, ProcessInfo())

        if pid is not None:
            info.pid = pid
        if status is not None:
            info.status = status
        if started_at is not None:
            info.started_at = started_at
        if restart_count is not None:
            info.restart_count = restart_count
        if last_error is not None:
            info.last_error = last_error

        self._processes[name] = info
        return info

    def reset_process_info(self, name: str) -> ProcessInfo:
        """Reset process info to stopped state."""
        if name not in self._servers:
            raise ValueError(f"Server {name} not found")

        info = ProcessInfo()
        self._processes[name] = info
        return info

    def get_auto_start_servers(self) -> list[ServerConfig]:
        """Get list of servers configured for auto-start."""
        return [config for config in self._servers.values() if config.auto_start]

    def get_stdio_servers(self) -> list[ServerConfig]:
        """Get list of servers using stdio transport."""
        return [
            config
            for config in self._servers.values()
            if config.transport == ServerTransport.STDIO
        ]
