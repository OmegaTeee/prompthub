"""
Data models for PromptHub CLI config generation.

Core types:
- ClientType: Supported MCP desktop clients
- BridgeConfig: MCP server entry with path-safety guarantees
- ClientProfile: Merged view of a client's keys, enhancement rules, and config path
"""

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator


class ClientType(str, Enum):
    """Supported MCP desktop clients."""

    claude_desktop = "claude-desktop"
    claude_code = "claude-code"
    cursor = "cursor"
    vscode = "vscode"
    raycast = "raycast"
    open_webui = "open-webui"

    def config_path(self) -> Path:
        """Default macOS config file path for this client."""
        home = Path.home()
        paths = {
            ClientType.claude_desktop: (
                home
                / "Library"
                / "Application Support"
                / "Claude"
                / "claude_desktop_config.json"
            ),
            ClientType.claude_code: home / ".claude.json",
            ClientType.cursor: (
                home
                / "Library"
                / "Application Support"
                / "Cursor"
                / "User"
                / "globalStorage"
                / "cursor.mcp"
                / "mcp.json"
            ),
            ClientType.vscode: (
                home
                / "Library"
                / "Application Support"
                / "Code"
                / "User"
                / "globalStorage"
                / "rooveterinaryinc.roo-cline"
                / "settings"
                / "mcp_settings.json"
            ),
            ClientType.raycast: home / ".config" / "raycast" / "mcp.json",
            ClientType.open_webui: home / ".prompthub" / "open-webui.json",
        }
        return paths[self]


class BridgeConfig(BaseModel):
    """
    MCP server configuration entry for the PromptHub bridge.

    Path safety is enforced at construction time: any arg containing
    '~', '${', or '$HOME' raises a ValidationError immediately.
    This makes it impossible to generate broken configs.
    """

    command: str = "node"
    args: list[str]
    env: dict[str, str] = {}

    @field_validator("args")
    @classmethod
    def no_unexpanded_paths(cls, v: list[str]) -> list[str]:
        """Reject shell variables and tildes that Node.js cannot expand."""
        for arg in v:
            if "~" in arg:
                raise ValueError(
                    f"Unexpanded tilde in path: {arg!r}. "
                    "Use an absolute path instead."
                )
            if "${" in arg or "$HOME" in arg:
                raise ValueError(
                    f"Unexpanded shell variable in path: {arg!r}. "
                    "Use an absolute path instead."
                )
        return v

    @field_validator("args")
    @classmethod
    def must_be_absolute(cls, v: list[str]) -> list[str]:
        """Ensure file path arguments are absolute."""
        for arg in v:
            # Only validate args that look like file paths
            if arg.endswith(".js") or arg.endswith(".mjs"):
                p = Path(arg)
                if not p.is_absolute():
                    raise ValueError(
                        f"Relative path in args: {arg!r}. "
                        "Use an absolute path instead."
                    )
        return v

    @field_validator("env")
    @classmethod
    def validate_url_format(cls, v: dict[str, str]) -> dict[str, str]:
        """Warn about 'localhost' vs '127.0.0.1' in PROMPTHUB_URL."""
        url = v.get("PROMPTHUB_URL", "")
        if "localhost" in url:
            raise ValueError(
                f"PROMPTHUB_URL uses 'localhost': {url!r}. "
                "Use '127.0.0.1' to avoid DNS/IPv6 resolution issues."
            )
        return v


class ClientProfile(BaseModel):
    """
    Merged view of a client's configuration from api-keys.json
    and enhancement-rules.json.
    """

    client_name: str
    client_type: ClientType
    api_key: str | None = None
    enhance: bool = False
    privacy_level: str = "local_only"
    model: str = "llama3.2:latest"
    system_prompt: str | None = None
    servers: list[str] | None = None
    exclude_tools: list[str] | None = None


def build_open_webui_config(
    router_url: str = "http://127.0.0.1:9090",
    api_key: str = "sk-prompthub-openwebui-001",
    port: int = 3000,
) -> dict[str, Any]:
    """
    Build Open WebUI connection settings (HTTP-based, no bridge).

    Unlike stdio-bridge clients, Open WebUI connects directly over HTTP
    via the OpenAI-compatible proxy and Streamable HTTP MCP endpoint.

    Args:
        router_url: PromptHub router base URL (use 127.0.0.1, not localhost)
        api_key: Bearer token registered in api-keys.json
        port: Open WebUI listen port (for reference only, not set by us)

    Returns:
        Config dict keyed by ``"open_webui"`` with connection fields.
    """
    return {
        "open_webui": {
            "api_base_url": f"{router_url}/v1",
            "mcp_endpoint": f"{router_url}/mcp-direct/mcp",
            "api_key": api_key,
            "port": port,
            "data_dir": "~/.open-webui",
        }
    }


def wrap_for_client(
    client_type: ClientType,
    bridge: BridgeConfig,
    server_name: str = "prompthub",
) -> dict[str, Any]:
    """
    Wrap a BridgeConfig in the client-specific JSON structure.

    Different clients use different schemas:
    - Claude Desktop / Cursor / Raycast: {"mcpServers": {"name": {...}}}
    - VS Code: {"mcp": {"servers": {"name": {...}}}}
    - Open WebUI: connection settings (no bridge — use build_open_webui_config)
    """
    entry = bridge.model_dump(exclude_none=True)

    if client_type == ClientType.vscode:
        return {"mcp": {"servers": {server_name: entry}}}
    else:
        # Claude Desktop, Claude Code, Cursor, Raycast all use mcpServers
        return {"mcpServers": {server_name: entry}}
