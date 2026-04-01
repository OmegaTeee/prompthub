"""
Config installer — merges PromptHub bridge config into client config files.

Merge semantics:
- Only touches the 'prompthub' key inside mcpServers (or mcp.servers for VS Code)
- Preserves all other server entries and preferences
- Creates .bak backup before writing
- --force replaces entire mcpServers but keeps preferences
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Any

from cli.models import ClientType

logger = logging.getLogger(__name__)


class ConfigInstaller:
    """Safely installs PromptHub config into client config files."""

    def install(
        self,
        client_type: ClientType,
        generated: dict[str, Any],
        config_path: Path | None = None,
        force: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Merge generated config into the client's config file.

        For bridge-based clients the generated ``prompthub`` entry is
        merged into the existing ``mcpServers`` (or ``mcp.servers``)
        section.  Open WebUI is an exception -- its config is a
        standalone settings file written without merge.

        Args:
            client_type: Target client
            generated: Output from ConfigGenerator.generate()
            config_path: Override config file path (uses client default)
            force: Replace entire mcpServers section (ignored for
                Open WebUI, which always overwrites)
            dry_run: Return merged config without writing

        Returns:
            The merged config dict
        """
        path = config_path or client_type.config_path()

        # Load existing config
        existing = {}
        if path.exists():
            try:
                existing = json.loads(path.read_text())
            except json.JSONDecodeError:
                logger.warning(
                    "Existing config at %s is invalid JSON, will overwrite",
                    path,
                )

        # Merge based on client type
        if client_type == ClientType.open_webui:
            # Open WebUI: standalone settings file, no merge needed
            merged = generated
        elif client_type == ClientType.vscode:
            merged = self._merge_vscode(existing, generated, force)
        else:
            merged = self._merge_standard(existing, generated, force)

        if dry_run:
            return merged

        # Backup before writing
        if path.exists():
            backup = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, backup)
            logger.info("Backup created: %s", backup)

        # Write merged config
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(merged, indent=2) + "\n")
        logger.info("Config written to: %s", path)

        return merged

    def _merge_standard(
        self,
        existing: dict[str, Any],
        generated: dict[str, Any],
        force: bool,
    ) -> dict[str, Any]:
        """Merge for Claude Desktop, Cursor, Raycast (mcpServers format)."""
        merged = dict(existing)

        if force:
            # Replace entire mcpServers but keep everything else
            merged["mcpServers"] = generated.get("mcpServers", {})
        else:
            # Only update the prompthub entry
            merged.setdefault("mcpServers", {})
            gen_servers = generated.get("mcpServers", {})
            for name, entry in gen_servers.items():
                merged["mcpServers"][name] = entry

        return merged

    def _merge_vscode(
        self,
        existing: dict[str, Any],
        generated: dict[str, Any],
        force: bool,
    ) -> dict[str, Any]:
        """Merge for VS Code (mcp.servers format)."""
        merged = dict(existing)

        gen_mcp = generated.get("mcp", {})
        gen_servers = gen_mcp.get("servers", {})

        if force:
            merged.setdefault("mcp", {})
            merged["mcp"]["servers"] = gen_servers
        else:
            merged.setdefault("mcp", {})
            merged["mcp"].setdefault("servers", {})
            for name, entry in gen_servers.items():
                merged["mcp"]["servers"][name] = entry

        return merged

    def diff(
        self,
        client_type: ClientType,
        generated: dict[str, Any],
        config_path: Path | None = None,
    ) -> tuple[str, str]:
        """
        Compare installed config vs generated config.

        Returns:
            (installed_json, generated_json) for comparison
        """
        path = config_path or client_type.config_path()

        installed = "{}"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                installed = json.dumps(data, indent=2, sort_keys=True)
            except json.JSONDecodeError:
                installed = path.read_text()

        generated_str = json.dumps(generated, indent=2, sort_keys=True)

        return installed, generated_str
