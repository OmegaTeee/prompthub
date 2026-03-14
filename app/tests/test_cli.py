"""
Tests for the PromptHub CLI — MCP Config Manager.

Covers: models (path safety), generator, validator, installer, profiles.
"""

import json
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from cli.generator import ConfigGenerator
from cli.installer import ConfigInstaller
from cli.models import BridgeConfig, ClientType, build_open_webui_config, wrap_for_client
from cli.profiles import ProfileLoader
from cli.validator import ConfigValidator


# ── BridgeConfig path safety ────────────────────────────────────────


class TestBridgeConfigPathSafety:
    """BridgeConfig rejects unexpanded shell patterns at construction."""

    def test_rejects_tilde_in_args(self):
        with pytest.raises(ValidationError, match="tilde"):
            BridgeConfig(
                args=["~/path/to/bridge.js"],
                env={"PROMPTHUB_URL": "http://127.0.0.1:9090"},
            )

    def test_rejects_dollar_brace_in_args(self):
        with pytest.raises(ValidationError, match="shell variable"):
            BridgeConfig(
                args=["${HOME}/path/to/bridge.js"],
                env={"PROMPTHUB_URL": "http://127.0.0.1:9090"},
            )

    def test_rejects_dollar_HOME_in_args(self):
        with pytest.raises(ValidationError, match="shell variable"):
            BridgeConfig(
                args=["$HOME/path/to/bridge.js"],
                env={"PROMPTHUB_URL": "http://127.0.0.1:9090"},
            )

    def test_rejects_relative_js_path(self):
        with pytest.raises(ValidationError, match="Relative path"):
            BridgeConfig(
                args=["mcps/prompthub-bridge.js"],
                env={"PROMPTHUB_URL": "http://127.0.0.1:9090"},
            )

    def test_rejects_localhost_in_url(self):
        with pytest.raises(ValidationError, match="localhost"):
            BridgeConfig(
                args=["/absolute/path/bridge.js"],
                env={"PROMPTHUB_URL": "http://localhost:9090"},
            )

    def test_accepts_valid_config(self):
        config = BridgeConfig(
            args=["/Users/test/.local/share/prompthub/mcps/bridge.js"],
            env={"PROMPTHUB_URL": "http://127.0.0.1:9090"},
        )
        assert config.command == "node"
        assert len(config.args) == 1
        assert config.args[0].startswith("/")

    def test_accepts_non_js_relative_args(self):
        """Non-JS arguments (like flags) don't need to be absolute."""
        config = BridgeConfig(
            args=["/abs/bridge.js", "--verbose"],
            env={"PROMPTHUB_URL": "http://127.0.0.1:9090"},
        )
        assert "--verbose" in config.args


# ── ClientType ──────────────────────────────────────────────────────


class TestClientType:
    """ClientType enum provides config paths and string values."""

    def test_config_path_claude_desktop(self):
        path = ClientType.claude_desktop.config_path()
        assert "Claude" in str(path)
        assert path.name == "claude_desktop_config.json"

    def test_config_path_vscode(self):
        path = ClientType.vscode.config_path()
        assert "Code" in str(path)

    def test_all_clients_have_paths(self):
        for ct in ClientType:
            path = ct.config_path()
            assert path.is_absolute()

    def test_string_values(self):
        assert ClientType.claude_desktop.value == "claude-desktop"
        assert ClientType.claude_code.value == "claude-code"
        assert ClientType.raycast.value == "raycast"
        assert ClientType.open_webui.value == "open-webui"

    def test_config_path_open_webui(self):
        path = ClientType.open_webui.config_path()
        assert path.name == "open-webui.json"
        assert ".prompthub" in str(path)


# ── Open WebUI config ──────────────────────────────────────────────


class TestOpenWebUI:
    """Open WebUI produces connection settings, not bridge configs."""

    def test_build_open_webui_config(self):
        config = build_open_webui_config()
        assert "open_webui" in config
        ow = config["open_webui"]
        assert "api_base_url" in ow
        assert "mcp_endpoint" in ow
        assert "api_key" in ow
        assert "127.0.0.1" in ow["api_base_url"]

    def test_build_open_webui_config_custom_url(self):
        config = build_open_webui_config(
            router_url="http://127.0.0.1:8080",
            api_key="sk-custom",
            port=8000,
        )
        ow = config["open_webui"]
        assert "8080" in ow["api_base_url"]
        assert ow["api_key"] == "sk-custom"
        assert ow["port"] == 8000

    def test_generate_open_webui(self, tmp_path):
        """ConfigGenerator.generate() returns connection settings for open_webui."""
        bridge = tmp_path / "mcps" / "prompthub-bridge.js"
        bridge.parent.mkdir(parents=True)
        bridge.write_text("#!/usr/bin/env node\n")

        gen = ConfigGenerator(workspace_root=tmp_path)
        config = gen.generate(ClientType.open_webui)

        assert "open_webui" in config
        assert "mcpServers" not in config
        assert "mcp" not in config

    def test_validate_open_webui_valid(self, tmp_path):
        """Validate a correct Open WebUI config."""
        # Create api-keys.json
        configs = tmp_path / "configs"
        configs.mkdir()
        keys = {
            "keys": {
                "sk-prompthub-openwebui-001": {
                    "client_name": "open-webui",
                    "enhance": True,
                }
            }
        }
        (configs / "api-keys.json").write_text(json.dumps(keys))

        config = {
            "open_webui": {
                "api_base_url": "http://127.0.0.1:9090/v1",
                "mcp_endpoint": "http://127.0.0.1:9090/mcp-direct/mcp",
                "api_key": "sk-prompthub-openwebui-001",
                "port": 3000,
            }
        }

        validator = ConfigValidator()
        result = validator.validate_open_webui(config, configs_dir=configs)
        assert result.ok

    def test_validate_open_webui_missing_key(self):
        """Missing api_key is an error."""
        config = {
            "open_webui": {
                "api_base_url": "http://127.0.0.1:9090/v1",
                "api_key": "",
            }
        }

        validator = ConfigValidator()
        result = validator.validate_open_webui(config)
        assert not result.ok
        assert any("api_key" in i.message for i in result.errors)

    def test_validate_open_webui_localhost_warning(self):
        """localhost in api_base_url is a warning."""
        config = {
            "open_webui": {
                "api_base_url": "http://localhost:9090/v1",
                "api_key": "sk-test",
            }
        }

        validator = ConfigValidator()
        result = validator.validate_open_webui(config)
        assert result.warnings
        assert any("localhost" in w.message for w in result.warnings)

    def test_validate_open_webui_key_not_in_registry(self, tmp_path):
        """API key not found in api-keys.json is an error."""
        configs = tmp_path / "configs"
        configs.mkdir()
        keys = {"keys": {"sk-other": {"client_name": "other"}}}
        (configs / "api-keys.json").write_text(json.dumps(keys))

        config = {
            "open_webui": {
                "api_base_url": "http://127.0.0.1:9090/v1",
                "api_key": "sk-missing",
            }
        }

        validator = ConfigValidator()
        result = validator.validate_open_webui(config, configs_dir=configs)
        assert not result.ok
        assert any("not found" in i.message for i in result.errors)


# ── wrap_for_client ─────────────────────────────────────────────────


class TestWrapForClient:
    """Config wrapping uses correct schema per client."""

    @pytest.fixture
    def bridge(self):
        return BridgeConfig(
            args=["/abs/bridge.js"],
            env={"PROMPTHUB_URL": "http://127.0.0.1:9090"},
        )

    def test_claude_desktop_uses_mcpServers(self, bridge):
        result = wrap_for_client(ClientType.claude_desktop, bridge)
        assert "mcpServers" in result
        assert "prompthub" in result["mcpServers"]

    def test_vscode_uses_mcp_servers(self, bridge):
        result = wrap_for_client(ClientType.vscode, bridge)
        assert "mcp" in result
        assert "servers" in result["mcp"]
        assert "prompthub" in result["mcp"]["servers"]

    def test_raycast_uses_mcpServers(self, bridge):
        result = wrap_for_client(ClientType.raycast, bridge)
        assert "mcpServers" in result

    def test_cursor_uses_mcpServers(self, bridge):
        result = wrap_for_client(ClientType.cursor, bridge)
        assert "mcpServers" in result


# ── ConfigGenerator ─────────────────────────────────────────────────


class TestConfigGenerator:
    """ConfigGenerator produces valid bridge configs."""

    @pytest.fixture
    def generator(self, tmp_path):
        # Create a dummy bridge file
        bridge = tmp_path / "mcps" / "prompthub-bridge.js"
        bridge.parent.mkdir(parents=True)
        bridge.write_text("#!/usr/bin/env node\n")
        return ConfigGenerator(workspace_root=tmp_path)

    def test_generate_claude_desktop(self, generator):
        config = generator.generate(ClientType.claude_desktop)
        assert "mcpServers" in config
        entry = config["mcpServers"]["prompthub"]
        assert entry["command"] == "node"
        assert Path(entry["args"][0]).is_absolute()
        assert "127.0.0.1" in entry["env"]["PROMPTHUB_URL"]

    def test_generate_vscode(self, generator):
        config = generator.generate(ClientType.vscode)
        assert "mcp" in config
        entry = config["mcp"]["servers"]["prompthub"]
        assert entry["command"] == "node"

    def test_generate_with_servers_filter(self, generator):
        config = generator.generate(
            ClientType.claude_desktop,
            servers=["context7", "desktop-commander"],
        )
        entry = config["mcpServers"]["prompthub"]
        assert entry["env"]["SERVERS"] == "context7,desktop-commander"

    def test_generate_with_exclude_tools(self, generator):
        config = generator.generate(
            ClientType.claude_desktop,
            exclude_tools=["duckduckgo", "perplexity"],
        )
        entry = config["mcpServers"]["prompthub"]
        assert entry["env"]["EXCLUDE_TOOLS"] == "duckduckgo,perplexity"

    def test_generate_with_extra_env(self, generator):
        config = generator.generate(
            ClientType.claude_desktop,
            extra_env={"OBSIDIAN_PORT": "27124"},
        )
        entry = config["mcpServers"]["prompthub"]
        assert entry["env"]["OBSIDIAN_PORT"] == "27124"

    def test_generate_json_returns_string(self, generator):
        result = generator.generate_json(ClientType.claude_desktop)
        parsed = json.loads(result)
        assert "mcpServers" in parsed


# ── ConfigValidator ─────────────────────────────────────────────────


class TestConfigValidator:
    """ConfigValidator catches common config errors."""

    @pytest.fixture
    def validator(self):
        return ConfigValidator()

    def test_valid_config_passes(self, validator):
        config = {
            "mcpServers": {
                "prompthub": {
                    "command": "node",
                    "args": ["/abs/bridge.js"],
                    "env": {"PROMPTHUB_URL": "http://127.0.0.1:9090"},
                }
            }
        }
        result = validator.validate_config(config)
        assert result.ok

    def test_catches_tilde_in_args(self, validator):
        config = {
            "mcpServers": {
                "prompthub": {
                    "command": "node",
                    "args": ["~/bridge.js"],
                    "env": {},
                }
            }
        }
        result = validator.validate_config(config)
        assert not result.ok
        assert any("~" in i.message for i in result.errors)

    def test_catches_dollar_brace_in_args(self, validator):
        config = {
            "mcpServers": {
                "prompthub": {
                    "command": "node",
                    "args": ["${HOME}/bridge.js"],
                    "env": {},
                }
            }
        }
        result = validator.validate_config(config)
        assert not result.ok

    def test_catches_tilde_in_command(self, validator):
        config = {
            "mcpServers": {
                "prompthub": {
                    "command": "~/bridge.js",
                    "args": [],
                    "env": {},
                }
            }
        }
        result = validator.validate_config(config)
        assert not result.ok

    def test_catches_localhost_url(self, validator):
        config = {
            "mcpServers": {
                "prompthub": {
                    "command": "node",
                    "args": ["/abs/bridge.js"],
                    "env": {"PROMPTHUB_URL": "http://localhost:9090"},
                }
            }
        }
        result = validator.validate_config(config)
        assert result.warnings  # localhost is a warning, not error

    def test_catches_legacy_env_var(self, validator):
        config = {
            "mcpServers": {
                "prompthub": {
                    "command": "node",
                    "args": ["/abs/bridge.js"],
                    "env": {"AGENTHUB_URL": "http://127.0.0.1:9090"},
                }
            }
        }
        result = validator.validate_config(config)
        assert not result.ok
        assert any("AGENTHUB_URL" in i.message for i in result.errors)

    def test_catches_relative_js_path(self, validator):
        config = {
            "mcpServers": {
                "prompthub": {
                    "command": "node",
                    "args": ["mcps/bridge.js"],
                    "env": {},
                }
            }
        }
        result = validator.validate_config(config)
        assert not result.ok

    def test_validate_file_not_found(self, validator, tmp_path):
        result = validator.validate_file(tmp_path / "nonexistent.json")
        assert not result.ok

    def test_validate_file_invalid_json(self, validator, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json{{{")
        result = validator.validate_file(bad_file)
        assert not result.ok

    def test_validate_vscode_format(self, validator):
        config = {
            "mcp": {
                "servers": {
                    "prompthub": {
                        "command": "node",
                        "args": ["/abs/bridge.js"],
                        "env": {},
                    }
                }
            }
        }
        result = validator.validate_config(config)
        assert result.ok

    def test_summary_messages(self, validator):
        config = {
            "mcpServers": {
                "test": {
                    "command": "node",
                    "args": ["--version"],
                    "env": {},
                }
            }
        }
        result = validator.validate_config(config)
        assert result.summary() == "All checks passed"


# ── ConfigInstaller ─────────────────────────────────────────────────


class TestConfigInstaller:
    """ConfigInstaller merges configs without clobbering."""

    @pytest.fixture
    def installer(self):
        return ConfigInstaller()

    def test_merge_preserves_preferences(self, installer, tmp_path):
        """Install should keep existing preferences."""
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({
            "mcpServers": {"other-server": {"command": "other"}},
            "preferences": {"theme": "dark"},
        }))

        generated = {
            "mcpServers": {
                "prompthub": {
                    "command": "node",
                    "args": ["/abs/bridge.js"],
                }
            }
        }

        merged = installer.install(
            ClientType.claude_desktop,
            generated,
            config_path=config_path,
        )

        assert "preferences" in merged
        assert merged["preferences"]["theme"] == "dark"
        assert "other-server" in merged["mcpServers"]
        assert "prompthub" in merged["mcpServers"]

    def test_merge_updates_prompthub_only(self, installer, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({
            "mcpServers": {
                "other": {"command": "other"},
                "prompthub": {"command": "old"},
            },
        }))

        generated = {
            "mcpServers": {
                "prompthub": {"command": "node", "args": ["/new/bridge.js"]},
            }
        }

        merged = installer.install(
            ClientType.claude_desktop,
            generated,
            config_path=config_path,
        )

        assert merged["mcpServers"]["prompthub"]["command"] == "node"
        assert merged["mcpServers"]["other"]["command"] == "other"

    def test_force_replaces_all_servers(self, installer, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({
            "mcpServers": {"other": {"command": "other"}},
            "preferences": {"keep": True},
        }))

        generated = {
            "mcpServers": {
                "prompthub": {"command": "node", "args": ["/bridge.js"]},
            }
        }

        merged = installer.install(
            ClientType.claude_desktop,
            generated,
            config_path=config_path,
            force=True,
        )

        assert "other" not in merged["mcpServers"]
        assert "prompthub" in merged["mcpServers"]
        assert merged["preferences"]["keep"] is True

    def test_dry_run_does_not_write(self, installer, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text("{}")

        generated = {
            "mcpServers": {
                "prompthub": {"command": "node"},
            }
        }

        installer.install(
            ClientType.claude_desktop,
            generated,
            config_path=config_path,
            dry_run=True,
        )

        # File should still be empty {}
        assert json.loads(config_path.read_text()) == {}

    def test_creates_backup(self, installer, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text('{"original": true}')

        generated = {"mcpServers": {"prompthub": {"command": "node"}}}

        installer.install(
            ClientType.claude_desktop,
            generated,
            config_path=config_path,
        )

        backup = config_path.with_suffix(".json.bak")
        assert backup.exists()
        assert json.loads(backup.read_text()) == {"original": True}

    def test_vscode_merge(self, installer, tmp_path):
        config_path = tmp_path / "mcp.json"
        config_path.write_text(json.dumps({
            "mcp": {"servers": {"other": {"command": "other"}}},
        }))

        generated = {
            "mcp": {
                "servers": {
                    "prompthub": {"command": "node"},
                }
            }
        }

        merged = installer.install(
            ClientType.vscode,
            generated,
            config_path=config_path,
        )

        assert "other" in merged["mcp"]["servers"]
        assert "prompthub" in merged["mcp"]["servers"]

    def test_diff_detects_changes(self, installer, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(
            {"mcpServers": {"prompthub": {"command": "old"}}},
            indent=2,
            sort_keys=True,
        ))

        generated = {"mcpServers": {"prompthub": {"command": "new"}}}

        installed, gen = installer.diff(
            ClientType.claude_desktop,
            generated,
            config_path=config_path,
        )

        assert installed != gen
        assert "old" in installed
        assert "new" in gen

    def test_diff_no_changes(self, installer, tmp_path):
        config = {"mcpServers": {"prompthub": {"command": "node"}}}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config, indent=2, sort_keys=True))

        installed, gen = installer.diff(
            ClientType.claude_desktop,
            config,
            config_path=config_path,
        )

        assert installed == gen


# ── ProfileLoader ───────────────────────────────────────────────────


class TestProfileLoader:
    """ProfileLoader reads api-keys.json and enhancement-rules.json."""

    @pytest.fixture
    def configs_dir(self, tmp_path):
        """Create a temporary configs directory with test data."""
        configs = tmp_path / "configs"
        configs.mkdir()

        keys = {
            "keys": {
                "sk-test-key": {
                    "client_name": "claude-desktop",
                    "enhance": False,
                    "description": "Test key",
                }
            }
        }
        (configs / "api-keys.json").write_text(json.dumps(keys))

        rules = {
            "default": {
                "model": "llama3.2:latest",
                "system_prompt": "Default prompt",
            },
            "clients": {
                "claude-desktop": {
                    "model": "llama3.2:latest",
                    "system_prompt": "Structured responses.",
                    "privacy_level": "local_only",
                },
                "raycast": {
                    "model": "llama3.2:latest",
                    "privacy_level": "free_ok",
                },
            },
        }
        (configs / "enhancement-rules.json").write_text(json.dumps(rules))

        return configs

    def test_load_profile_with_key(self, configs_dir):
        loader = ProfileLoader(configs_dir=configs_dir)
        profile = loader.load(ClientType.claude_desktop)

        assert profile.client_name == "claude-desktop"
        assert profile.api_key == "sk-test-key"
        assert profile.privacy_level == "local_only"

    def test_load_profile_without_key(self, configs_dir):
        loader = ProfileLoader(configs_dir=configs_dir)
        profile = loader.load(ClientType.cursor)

        assert profile.api_key is None
        assert profile.privacy_level == "local_only"  # default

    def test_load_profile_with_privacy(self, configs_dir):
        loader = ProfileLoader(configs_dir=configs_dir)
        profile = loader.load(ClientType.raycast)

        assert profile.privacy_level == "free_ok"

    def test_list_profiles(self, configs_dir):
        loader = ProfileLoader(configs_dir=configs_dir)
        profiles = loader.list_profiles()

        assert len(profiles) == len(ClientType)
        names = {p.client_name for p in profiles}
        assert "claude-desktop" in names
        assert "raycast" in names

    def test_missing_config_files(self, tmp_path):
        """Gracefully handle missing config files."""
        loader = ProfileLoader(configs_dir=tmp_path / "nonexistent")
        profile = loader.load(ClientType.claude_desktop)

        assert profile.api_key is None
        assert profile.client_name == "claude-desktop"


# ── Integration: real config files ──────────────────────────────────


class TestRealConfigs:
    """Integration tests using the actual PromptHub config files."""

    CONFIGS_DIR = (
        Path(__file__).parent.parent / "configs"
    )

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "configs" / "api-keys.json").exists(),
        reason="api-keys.json not found",
    )
    def test_real_profile_load(self):
        loader = ProfileLoader(configs_dir=self.CONFIGS_DIR)
        profile = loader.load(ClientType.claude_desktop)
        assert profile.api_key is not None
        assert profile.client_name == "claude-desktop"

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "configs" / "api-keys.json").exists(),
        reason="api-keys.json not found",
    )
    def test_real_generate(self):
        gen = ConfigGenerator()
        loader = ProfileLoader(configs_dir=self.CONFIGS_DIR)
        profile = loader.load(ClientType.claude_desktop)
        config = gen.generate(ClientType.claude_desktop, profile=profile)

        entry = config["mcpServers"]["prompthub"]
        assert Path(entry["args"][0]).is_absolute()
        assert "~" not in entry["args"][0]
        assert "${" not in entry["args"][0]
        assert "127.0.0.1" in entry["env"]["PROMPTHUB_URL"]
