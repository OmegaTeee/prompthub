"""
Data models for MCP server configuration and status.

These models define the structure for:
- Server configuration (how to start/connect to a server)
- Server status (runtime state of a server)
- Process information (details about running processes)
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class ServerTransport(StrEnum):
    """Transport protocol for MCP server communication."""

    STDIO = "stdio"  # Communicate via stdin/stdout
    HTTP = "http"  # Communicate via HTTP/SSE


class ServerStatus(StrEnum):
    """Runtime status of an MCP server."""

    STOPPED = "stopped"  # Not running
    STARTING = "starting"  # Process is starting up
    RUNNING = "running"  # Process is running and healthy
    FAILED = "failed"  # Process failed and won't be restarted
    STOPPING = "stopping"  # Process is shutting down


class ServerConfig(BaseModel):
    """
    Configuration for an MCP server.

    For stdio transport:
        - command and args are required
        - url is ignored

    For http transport:
        - url is required
        - command and args are ignored
    """

    name: str = Field(..., description="Unique server identifier")
    package: str = Field(..., description="npm package name")
    transport: ServerTransport = Field(..., description="Communication protocol")

    # Stdio transport settings
    command: str | None = Field(None, description="Command to run (e.g., 'npx', 'node')")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str | dict] = Field(
        default_factory=dict,
        description="Environment variables (supports keyring references)",
    )

    # HTTP transport settings
    url: str | None = Field(None, description="Server URL for HTTP transport")
    health_endpoint: str = Field("/health", description="Health check endpoint path")

    # Lifecycle settings
    auto_start: bool = Field(False, description="Start server when router starts")
    restart_on_failure: bool = Field(True, description="Restart if process crashes")
    max_restarts: int = Field(3, description="Max restart attempts before marking FAILED")
    health_check_interval: int = Field(30, description="Seconds between health checks")

    # Proxy behavior
    proxy_timeout: float | None = Field(
        default=None,
        gt=0,
        description=(
            "Per-server proxy timeout in seconds for tools/call and other "
            "bridge dispatches. Must be > 0 when set; falls back to the "
            "proxy default when unset. Raise this for servers whose tools "
            "block on external I/O (e.g. agentic browsing, long research)."
        ),
    )

    # Metadata
    description: str = Field("", description="Human-readable description")

    def get_full_command(self) -> list[str]:
        """Get the full command as a list for subprocess."""
        if not self.command:
            raise ValueError(f"Server {self.name} has no command configured")
        return [self.command, *self.args]


class ProcessInfo(BaseModel):
    """
    Runtime information about a server process.

    This is ephemeral data that tracks the current state
    of a running (or recently stopped) server process.
    """

    pid: int | None = Field(None, description="Process ID if running")
    status: ServerStatus = Field(ServerStatus.STOPPED, description="Current status")
    started_at: float | None = Field(None, description="Unix timestamp when started")
    restart_count: int = Field(0, description="Number of restarts since last manual start")
    last_error: str | None = Field(None, description="Last error message if failed")

    def is_running(self) -> bool:
        """Check if server is in a running state."""
        return self.status in (ServerStatus.RUNNING, ServerStatus.STARTING)


class ServerState(BaseModel):
    """
    Combined server configuration and runtime state.

    Used for API responses that need both config and status.
    """

    config: ServerConfig
    process: ProcessInfo = Field(default_factory=ProcessInfo)

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def status(self) -> ServerStatus:
        return self.process.status
