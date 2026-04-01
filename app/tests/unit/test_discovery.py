"""Tests for client auto-discovery."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from cli.discovery import (
    ClientDetection,
    _check_prompthub_configured,
    discover_clients,
    discover_installed,
)
from cli.models import ClientType


class TestDiscoverClients:
    """Test the full discovery scan."""

    def test_detects_app_bundle(self, tmp_path: Path) -> None:
        """App bundle in /Applications is detected."""
        fake_bundle = tmp_path / "Claude.app"
        fake_bundle.mkdir()

        with patch(
            "cli.discovery._APP_BUNDLES",
            {ClientType.claude_desktop: [str(fake_bundle)]},
        ):
            results = discover_clients()
            match = next(
                r
                for r in results
                if r.client_type == ClientType.claude_desktop
            )
            assert match.installed is True
            assert "Claude.app" in match.detection_method

    def test_detects_cli_binary(self) -> None:
        """CLI binary on PATH is detected."""
        with patch("shutil.which", return_value="/usr/local/bin/claude"):
            with patch("cli.discovery._APP_BUNDLES", {}):
                results = discover_clients()
                match = next(
                    r
                    for r in results
                    if r.client_type == ClientType.claude_code
                )
                assert match.installed is True
                assert "binary" in match.detection_method

    def test_detects_config_indicator(self, tmp_path: Path) -> None:
        """Config directory indicator is detected as fallback."""
        config_dir = tmp_path / ".open-webui"
        config_dir.mkdir()

        with patch("cli.discovery._APP_BUNDLES", {}):
            with patch("cli.discovery._CLI_BINARIES", {}):
                with patch(
                    "cli.discovery._CONFIG_INDICATORS",
                    {ClientType.open_webui: [config_dir]},
                ):
                    results = discover_clients()
                    match = next(
                        r
                        for r in results
                        if r.client_type == ClientType.open_webui
                    )
                    assert match.installed is True
                    assert "config" in match.detection_method

    def test_not_installed_when_nothing_found(self) -> None:
        """Client reports not installed when no detection rule matches."""
        with patch("cli.discovery._APP_BUNDLES", {}):
            with patch("cli.discovery._CLI_BINARIES", {}):
                with patch("cli.discovery._CONFIG_INDICATORS", {}):
                    results = discover_clients()
                    for r in results:
                        assert r.installed is False

    def test_app_bundle_takes_priority_over_binary(
        self, tmp_path: Path
    ) -> None:
        """App bundle detection wins over CLI binary."""
        fake_bundle = tmp_path / "Claude.app"
        fake_bundle.mkdir()

        with patch(
            "cli.discovery._APP_BUNDLES",
            {ClientType.claude_code: [str(fake_bundle)]},
        ):
            with patch("shutil.which", return_value="/usr/bin/claude"):
                results = discover_clients()
                match = next(
                    r
                    for r in results
                    if r.client_type == ClientType.claude_code
                )
                # Should use app bundle, not binary
                assert "Claude.app" in match.detection_method

    def test_returns_all_client_types(self) -> None:
        """Every ClientType has a detection result."""
        with patch("cli.discovery._APP_BUNDLES", {}):
            with patch("cli.discovery._CLI_BINARIES", {}):
                with patch("cli.discovery._CONFIG_INDICATORS", {}):
                    results = discover_clients()
                    result_types = {r.client_type for r in results}
                    expected = set(ClientType)
                    assert result_types == expected


class TestDiscoverInstalled:
    """Test the installed-only filter."""

    def test_filters_to_installed_only(self) -> None:
        """discover_installed() drops uninstalled clients."""
        with patch(
            "cli.discovery.discover_clients",
            return_value=[
                ClientDetection(
                    client_type=ClientType.claude_desktop, installed=True
                ),
                ClientDetection(
                    client_type=ClientType.cursor, installed=False
                ),
                ClientDetection(
                    client_type=ClientType.raycast, installed=True
                ),
            ],
        ):
            results = discover_installed()
            assert len(results) == 2
            types = {r.client_type for r in results}
            assert types == {ClientType.claude_desktop, ClientType.raycast}


class TestCheckPromptHubConfigured:
    """Test PromptHub config detection in client files."""

    def test_detects_mcpservers_format(self, tmp_path: Path) -> None:
        """Finds prompthub in mcpServers (Claude Desktop format)."""
        config = {"mcpServers": {"prompthub": {"command": "node"}}}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        with patch.object(
            ClientType.claude_desktop, "config_path", return_value=config_path
        ):
            assert (
                _check_prompthub_configured(ClientType.claude_desktop)
                is True
            )

    def test_detects_vscode_format(self, tmp_path: Path) -> None:
        """Finds prompthub in mcp.servers (VS Code format)."""
        config = {
            "mcp": {"servers": {"prompthub": {"command": "node"}}}
        }
        config_path = tmp_path / "mcp.json"
        config_path.write_text(json.dumps(config))

        with patch.object(
            ClientType.vscode, "config_path", return_value=config_path
        ):
            assert _check_prompthub_configured(ClientType.vscode) is True

    def test_returns_false_when_missing(self, tmp_path: Path) -> None:
        """Returns False when config file does not exist."""
        missing = tmp_path / "nonexistent.json"
        with patch.object(
            ClientType.cursor, "config_path", return_value=missing
        ):
            assert _check_prompthub_configured(ClientType.cursor) is False

    def test_returns_false_when_no_prompthub(
        self, tmp_path: Path
    ) -> None:
        """Returns False when config exists but has no prompthub entry."""
        config = {"mcpServers": {"other-server": {}}}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        with patch.object(
            ClientType.claude_desktop, "config_path", return_value=config_path
        ):
            assert (
                _check_prompthub_configured(ClientType.claude_desktop)
                is False
            )
