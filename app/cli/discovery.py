"""
Client auto-discovery for PromptHub CLI.

Detects installed AI clients on macOS by checking app bundles,
CLI binaries, and config directories. Detection priority:
app bundle > CLI binary > config directory.
"""

import json
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from cli.models import ClientType

logger = logging.getLogger(__name__)

# ── Detection rules ─────────────────────────────────────────────────

# macOS app bundle paths (checked first — most reliable signal)
_APP_BUNDLES: dict[ClientType, list[str]] = {
    ClientType.claude_desktop: ["/Applications/Claude.app"],
    ClientType.vscode: [
        "/Applications/Visual Studio Code.app",
        "/Applications/Visual Studio Code - Insiders.app",
    ],
    ClientType.cursor: ["/Applications/Cursor.app"],
    ClientType.raycast: ["/Applications/Raycast.app"],
}

# CLI binaries on PATH (checked second)
_CLI_BINARIES: dict[ClientType, list[str]] = {
    ClientType.claude_code: ["claude"],
}

# Config directory indicators (checked last — fallback)
_CONFIG_INDICATORS: dict[ClientType, list[Path]] = {
    ClientType.claude_code: [Path.home() / ".claude"],
    ClientType.open_webui: [Path.home() / ".open-webui"],
}


# ── Data model ──────────────────────────────────────────────────────


@dataclass
class ClientDetection:
    """Detection result for a single client."""

    client_type: ClientType
    installed: bool = False
    app_path: Path | None = None
    config_exists: bool = False
    prompthub_configured: bool = False
    detection_method: str = ""


# ── Detection logic ─────────────────────────────────────────────────


def _check_prompthub_configured(client_type: ClientType) -> bool:
    """Check if PromptHub bridge is already configured for this client."""
    path = client_type.config_path()
    if not path.exists():
        return False
    try:
        config = json.loads(path.read_text())
        # Standard mcpServers format (Claude Desktop, Cursor, Raycast)
        if "prompthub" in config.get("mcpServers", {}):
            return True
        # VS Code format (mcp.servers)
        if "prompthub" in config.get("mcp", {}).get("servers", {}):
            return True
        # Open WebUI format
        if "open_webui" in config:
            return True
    except (json.JSONDecodeError, OSError):
        pass
    return False


def discover_clients() -> list[ClientDetection]:
    """
    Scan the system for installed AI clients.

    Returns a detection result for every ClientType, with ``installed``
    set to True when the client is found via app bundle, CLI binary,
    or config directory.
    """
    results = []

    for client_type in ClientType:
        detection = ClientDetection(
            client_type=client_type,
            config_exists=client_type.config_path().exists(),
        )

        # 1. App bundles (most reliable on macOS)
        for bundle_path in _APP_BUNDLES.get(client_type, []):
            if Path(bundle_path).exists():
                detection.installed = True
                detection.app_path = Path(bundle_path)
                detection.detection_method = bundle_path
                break

        # 2. CLI binaries
        if not detection.installed:
            for binary in _CLI_BINARIES.get(client_type, []):
                which_path = shutil.which(binary)
                if which_path:
                    detection.installed = True
                    detection.detection_method = f"binary: {which_path}"
                    break

        # 3. Config directory indicators (fallback)
        if not detection.installed:
            for indicator in _CONFIG_INDICATORS.get(client_type, []):
                if indicator.exists():
                    detection.installed = True
                    detection.detection_method = f"config: {indicator}"
                    break

        detection.prompthub_configured = _check_prompthub_configured(
            client_type
        )
        results.append(detection)

    return results


def discover_installed() -> list[ClientDetection]:
    """Return only detected (installed) clients."""
    return [d for d in discover_clients() if d.installed]
