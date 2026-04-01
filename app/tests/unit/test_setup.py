"""Tests for consolidated client setup."""

import json
from pathlib import Path

import pytest

from cli.discovery import ClientDetection
from cli.models import ClientType
from cli.setup import SetupAction, execute_setup, plan_setup


def _create_test_workspace(ws: Path) -> None:
    """Create a minimal workspace with configs and bridge file."""
    configs_dir = ws / "app" / "configs"
    configs_dir.mkdir(parents=True)

    (configs_dir / "api-keys.json").write_text(
        json.dumps(
            {
                "keys": {
                    "sk-test-claude-001": {
                        "client_name": "claude-desktop",
                        "description": "Test",
                        "enhance": False,
                    },
                    "sk-test-raycast-001": {
                        "client_name": "raycast",
                        "description": "Test",
                        "enhance": False,
                    },
                    "sk-test-openwebui-001": {
                        "client_name": "open-webui",
                        "description": "Test",
                        "enhance": False,
                    },
                }
            }
        )
    )

    (configs_dir / "enhancement-rules.json").write_text(
        json.dumps(
            {
                "default": {
                    "enabled": True,
                    "model": "test-model",
                    "system_prompt": "test",
                    "temperature": 0.3,
                    "max_tokens": 500,
                    "privacy_level": "local_only",
                },
                "clients": {},
            }
        )
    )

    bridge_dir = ws / "mcps"
    bridge_dir.mkdir(parents=True)
    (bridge_dir / "prompthub-bridge.js").write_text("// test bridge")


class TestPlanSetup:
    """Test setup planning logic."""

    def test_symlink_safe_clients_get_symlink_strategy(
        self, tmp_path: Path
    ) -> None:
        """Raycast and Open WebUI get symlink strategy."""
        detected = [
            ClientDetection(
                client_type=ClientType.raycast, installed=True
            ),
            ClientDetection(
                client_type=ClientType.open_webui, installed=True
            ),
        ]

        actions = plan_setup(detected, central_dir=tmp_path / "clients")

        for action in actions:
            assert action.strategy == "symlink"

    def test_mixed_config_clients_get_merge_strategy(
        self, tmp_path: Path
    ) -> None:
        """Claude Desktop, VS Code, Cursor get merge strategy."""
        detected = [
            ClientDetection(
                client_type=ClientType.claude_desktop, installed=True
            ),
            ClientDetection(
                client_type=ClientType.vscode, installed=True
            ),
            ClientDetection(
                client_type=ClientType.cursor, installed=True
            ),
        ]

        actions = plan_setup(detected, central_dir=tmp_path / "clients")

        for action in actions:
            assert action.strategy == "merge"

    def test_central_paths_use_configured_dir(
        self, tmp_path: Path
    ) -> None:
        """Central path includes client name under the central dir."""
        detected = [
            ClientDetection(
                client_type=ClientType.raycast, installed=True
            ),
        ]
        central = tmp_path / "my-configs"

        actions = plan_setup(detected, central_dir=central)

        assert actions[0].central_path == central / "raycast.json"

    def test_default_central_dir(self) -> None:
        """Default central dir is ~/.prompthub/clients/."""
        detected = [
            ClientDetection(
                client_type=ClientType.raycast, installed=True
            ),
        ]

        actions = plan_setup(detected)

        expected = Path.home() / ".prompthub" / "clients" / "raycast.json"
        assert actions[0].central_path == expected


class TestExecuteSetup:
    """Test setup execution."""

    def test_dry_run_generates_but_writes_nothing(
        self, tmp_path: Path
    ) -> None:
        """Dry run populates generated config but creates no files."""
        central = tmp_path / "clients" / "raycast.json"
        target = tmp_path / "target" / "mcp.json"

        actions = [
            SetupAction(
                client_type=ClientType.raycast,
                strategy="symlink",
                central_path=central,
                target_path=target,
            ),
        ]

        ws = tmp_path / "workspace"
        _create_test_workspace(ws)

        results = execute_setup(actions, workspace_root=ws, dry_run=True)

        assert results[0].success is True
        assert results[0].message == "dry run"
        assert results[0].generated is not None
        assert not central.exists()
        assert not target.exists()

    def test_symlink_creates_link_and_central_file(
        self, tmp_path: Path
    ) -> None:
        """Symlink strategy writes central file and creates symlink."""
        central = tmp_path / "clients" / "raycast.json"
        target = tmp_path / "target" / "mcp.json"

        actions = [
            SetupAction(
                client_type=ClientType.raycast,
                strategy="symlink",
                central_path=central,
                target_path=target,
            ),
        ]

        ws = tmp_path / "workspace"
        _create_test_workspace(ws)

        results = execute_setup(actions, workspace_root=ws, dry_run=False)

        assert results[0].success is True
        assert central.exists()
        assert target.is_symlink()
        assert target.resolve() == central.resolve()

        # Verify content is valid JSON with expected structure
        config = json.loads(central.read_text())
        assert "mcpServers" in config
        assert "prompthub" in config["mcpServers"]

    def test_symlink_backs_up_existing_file(
        self, tmp_path: Path
    ) -> None:
        """Existing non-symlink file is backed up before symlinking."""
        central = tmp_path / "clients" / "raycast.json"
        target = tmp_path / "target" / "mcp.json"
        target.parent.mkdir(parents=True)
        target.write_text('{"old": true}')

        actions = [
            SetupAction(
                client_type=ClientType.raycast,
                strategy="symlink",
                central_path=central,
                target_path=target,
            ),
        ]

        ws = tmp_path / "workspace"
        _create_test_workspace(ws)

        execute_setup(actions, workspace_root=ws)

        backup = target.with_suffix(".json.pre-setup.bak")
        assert backup.exists()
        assert json.loads(backup.read_text()) == {"old": True}
        assert target.is_symlink()

    def test_symlink_updates_existing_symlink(
        self, tmp_path: Path
    ) -> None:
        """Existing symlink is replaced (no backup needed)."""
        central = tmp_path / "clients" / "raycast.json"
        old_target_file = tmp_path / "old-central.json"
        old_target_file.write_text("{}")
        target = tmp_path / "target" / "mcp.json"
        target.parent.mkdir(parents=True)
        target.symlink_to(old_target_file)

        actions = [
            SetupAction(
                client_type=ClientType.raycast,
                strategy="symlink",
                central_path=central,
                target_path=target,
            ),
        ]

        ws = tmp_path / "workspace"
        _create_test_workspace(ws)

        results = execute_setup(actions, workspace_root=ws)

        assert results[0].success is True
        assert target.is_symlink()
        assert target.resolve() == central.resolve()
        # No .bak file for symlink replacement
        assert not target.with_suffix(".json.pre-setup.bak").exists()

    def test_merge_preserves_existing_servers(
        self, tmp_path: Path
    ) -> None:
        """Merge strategy keeps other mcpServers entries."""
        central = tmp_path / "clients" / "claude-desktop.json"
        target = tmp_path / "config.json"
        target.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "other-mcp": {
                            "command": "node",
                            "args": ["/other.js"],
                        }
                    },
                    "preferences": {"theme": "dark"},
                }
            )
        )

        actions = [
            SetupAction(
                client_type=ClientType.claude_desktop,
                strategy="merge",
                central_path=central,
                target_path=target,
            ),
        ]

        ws = tmp_path / "workspace"
        _create_test_workspace(ws)

        results = execute_setup(actions, workspace_root=ws)

        assert results[0].success is True
        merged = json.loads(target.read_text())
        # Original server preserved
        assert "other-mcp" in merged["mcpServers"]
        # PromptHub added
        assert "prompthub" in merged["mcpServers"]
        # Preferences preserved
        assert merged["preferences"]["theme"] == "dark"

    def test_merge_creates_new_config_when_missing(
        self, tmp_path: Path
    ) -> None:
        """Merge creates config file when it doesn't exist yet."""
        central = tmp_path / "clients" / "claude-desktop.json"
        target = tmp_path / "nonexistent" / "config.json"

        actions = [
            SetupAction(
                client_type=ClientType.claude_desktop,
                strategy="merge",
                central_path=central,
                target_path=target,
            ),
        ]

        ws = tmp_path / "workspace"
        _create_test_workspace(ws)

        results = execute_setup(actions, workspace_root=ws)

        assert results[0].success is True
        assert target.exists()
        config = json.loads(target.read_text())
        assert "prompthub" in config["mcpServers"]

    def test_graceful_fallback_with_missing_configs(
        self, tmp_path: Path
    ) -> None:
        """Workspace without config files uses defaults (no crash)."""
        central = tmp_path / "clients" / "raycast.json"
        target = tmp_path / "target" / "mcp.json"

        actions = [
            SetupAction(
                client_type=ClientType.raycast,
                strategy="symlink",
                central_path=central,
                target_path=target,
            ),
        ]

        # Workspace without api-keys.json — ProfileLoader warns
        # but falls back to defaults
        sparse_ws = tmp_path / "sparse"
        bridge_dir = sparse_ws / "mcps"
        bridge_dir.mkdir(parents=True)
        (bridge_dir / "prompthub-bridge.js").write_text("// bridge")

        results = execute_setup(actions, workspace_root=sparse_ws)

        # Should succeed with default profile (no API key)
        assert results[0].success is True
        assert target.is_symlink()
        config = json.loads(central.read_text())
        assert "prompthub" in config["mcpServers"]
