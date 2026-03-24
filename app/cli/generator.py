"""
Config generator for PromptHub MCP bridge.

Builds BridgeConfig instances with guaranteed-absolute paths for each
supported desktop client. The bridge env var interface mirrors
mcps/prompthub-bridge.js:
    PROMPTHUB_URL, CLIENT_NAME, AUTHORIZATION, SERVERS, EXCLUDE_TOOLS
"""

import json
from pathlib import Path
from typing import Any

from cli.models import (
    BridgeConfig,
    ClientProfile,
    ClientType,
    build_open_webui_config,
    wrap_for_client,
)


class ConfigGenerator:
    """
    Generates MCP client configurations for the PromptHub bridge.

    All paths are resolved to absolute at construction time via
    Path.resolve(), making broken paths impossible.
    """

    def __init__(
        self,
        workspace_root: Path | None = None,
        router_url: str = "http://127.0.0.1:9090",
    ):
        if workspace_root is None:
            # Default: prompthub lives at ~/prompthub
            workspace_root = Path.home() / "prompthub"

        self.workspace_root = workspace_root.resolve()
        self.bridge_path = (
            self.workspace_root / "mcps" / "prompthub-bridge.js"
        ).resolve()
        self.router_url = router_url

    def _build_env(
        self,
        client_type: ClientType,
        profile: ClientProfile | None = None,
        servers: list[str] | None = None,
        exclude_tools: list[str] | None = None,
    ) -> dict[str, str]:
        """Build the env dict for the bridge process."""
        env: dict[str, str] = {
            "PROMPTHUB_URL": self.router_url,
            "CLIENT_NAME": client_type.value,
        }

        # API key from profile or explicit
        api_key = profile.api_key if profile else None
        if api_key:
            env["AUTHORIZATION"] = f"Bearer {api_key}"

        # Server filter
        server_list = servers or (profile.servers if profile else None)
        if server_list:
            env["SERVERS"] = ",".join(server_list)

        # Tool exclusions
        tool_list = exclude_tools or (
            profile.exclude_tools if profile else None
        )
        if tool_list:
            env["EXCLUDE_TOOLS"] = ",".join(tool_list)

        return env

    def generate(
        self,
        client_type: ClientType,
        profile: ClientProfile | None = None,
        servers: list[str] | None = None,
        exclude_tools: list[str] | None = None,
        extra_env: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate a complete config for the given client type.

        Returns the client-specific JSON structure (e.g. {"mcpServers": {...}}
        for Claude Desktop, {"mcp": {"servers": {...}}} for VS Code).
        Open WebUI returns connection settings (HTTP-based, no bridge).

        Raises:
            ValueError: If path validation fails (unexpanded vars, relative paths)
        """
        if client_type == ClientType.open_webui:
            # Open WebUI connects via HTTP, not the stdio bridge.
            # Return connection settings directly instead of a BridgeConfig.
            api_key = (
                profile.api_key if profile else "sk-prompthub-openwebui-001"
            )
            return build_open_webui_config(
                router_url=self.router_url,
                api_key=api_key or "sk-prompthub-openwebui-001",
            )

        env = self._build_env(client_type, profile, servers, exclude_tools)

        if extra_env:
            env.update(extra_env)

        bridge = BridgeConfig(
            command="node",
            args=[str(self.bridge_path)],
            env=env,
        )

        return wrap_for_client(client_type, bridge)

    def generate_json(
        self,
        client_type: ClientType,
        profile: ClientProfile | None = None,
        servers: list[str] | None = None,
        exclude_tools: list[str] | None = None,
        extra_env: dict[str, str] | None = None,
        indent: int = 2,
    ) -> str:
        """Generate config and return as formatted JSON string."""
        config = self.generate(
            client_type, profile, servers, exclude_tools, extra_env
        )
        return json.dumps(config, indent=indent)
