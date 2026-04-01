"""
Config validator — checks installed MCP configs for common issues.

Validates:
- Path safety (no ~, ${HOME}, $HOME, relative paths)
- Required env vars
- Bridge file existence
- URL format (127.0.0.1, not localhost)
- Open WebUI connection settings (api_base_url, api_key cross-check)
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """A single validation finding."""

    level: str  # "error" or "warning"
    message: str
    path: str = ""  # JSON path to the problematic field


@dataclass
class ValidationResult:
    """Aggregate result of config validation."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]

    def summary(self) -> str:
        if self.ok and not self.warnings:
            return "All checks passed"
        parts = []
        if self.errors:
            parts.append(f"{len(self.errors)} error(s)")
        if self.warnings:
            parts.append(f"{len(self.warnings)} warning(s)")
        return ", ".join(parts)


class ConfigValidator:
    """Validates MCP client configuration files."""

    UNSAFE_PATTERNS = ["~", "${", "$HOME"]

    def validate_file(self, config_path: Path) -> ValidationResult:
        """Validate a config file on disk."""
        result = ValidationResult()

        if not config_path.exists():
            result.issues.append(
                ValidationIssue(
                    "error",
                    f"Config file not found: {config_path}",
                    str(config_path),
                )
            )
            return result

        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError as e:
            result.issues.append(
                ValidationIssue(
                    "error", f"Invalid JSON: {e}", str(config_path)
                )
            )
            return result

        self.validate_config(config, result)
        return result

    def validate_config(
        self, config: dict, result: ValidationResult | None = None
    ) -> ValidationResult:
        """Validate a config dict (already parsed)."""
        if result is None:
            result = ValidationResult()

        # Find the server entries regardless of structure
        servers = config.get("mcpServers", {})
        if not servers:
            # VS Code format
            mcp = config.get("mcp", {})
            servers = mcp.get("servers", {})

        if not servers:
            result.issues.append(
                ValidationIssue(
                    "warning",
                    "No MCP server entries found",
                    "mcpServers",
                )
            )
            return result

        for name, entry in servers.items():
            self._validate_entry(name, entry, result)

        return result

    def _validate_entry(
        self, name: str, entry: dict, result: ValidationResult
    ) -> None:
        """Validate a single MCP server entry."""
        # Check command path
        command = entry.get("command", "")
        for pattern in self.UNSAFE_PATTERNS:
            if pattern in command:
                result.issues.append(
                    ValidationIssue(
                        "error",
                        f"Unexpanded pattern '{pattern}' in command: "
                        f"{command!r}",
                        f"mcpServers.{name}.command",
                    )
                )

        # Check args for unsafe paths
        for i, arg in enumerate(entry.get("args", [])):
            for pattern in self.UNSAFE_PATTERNS:
                if pattern in arg:
                    result.issues.append(
                        ValidationIssue(
                            "error",
                            f"Unexpanded pattern '{pattern}' in arg: "
                            f"{arg!r}",
                            f"mcpServers.{name}.args[{i}]",
                        )
                    )

            # Check relative paths for .js files
            if (arg.endswith(".js") or arg.endswith(".mjs")) and not Path(
                arg
            ).is_absolute():
                result.issues.append(
                    ValidationIssue(
                        "error",
                        f"Relative path in arg: {arg!r}",
                        f"mcpServers.{name}.args[{i}]",
                    )
                )

        # Check env vars
        env = entry.get("env", {})

        # PROMPTHUB_URL should use 127.0.0.1
        url = env.get("PROMPTHUB_URL", "")
        if "localhost" in url:
            result.issues.append(
                ValidationIssue(
                    "warning",
                    f"PROMPTHUB_URL uses 'localhost': {url!r}. "
                    "Use '127.0.0.1' to avoid DNS/IPv6 issues.",
                    f"mcpServers.{name}.env.PROMPTHUB_URL",
                )
            )

        # Check for wrong env var names (legacy)
        if "AGENTHUB_URL" in env:
            result.issues.append(
                ValidationIssue(
                    "error",
                    "Legacy env var 'AGENTHUB_URL' found. "
                    "Use 'PROMPTHUB_URL' instead.",
                    f"mcpServers.{name}.env.AGENTHUB_URL",
                )
            )

        # Bridge file should exist
        args = entry.get("args", [])
        for arg in args:
            if arg.endswith(".js") and Path(arg).is_absolute():
                if not Path(arg).exists():
                    result.issues.append(
                        ValidationIssue(
                            "warning",
                            f"Bridge file not found: {arg}",
                            f"mcpServers.{name}.args",
                        )
                    )

    def validate_open_webui(
        self,
        config: dict[str, Any],
        configs_dir: Path | None = None,
    ) -> ValidationResult:
        """
        Validate Open WebUI connection settings.

        Checks performed:
        - ``open_webui`` section exists
        - ``api_base_url`` is present and uses 127.0.0.1 (not localhost)
        - ``api_key`` is present
        - ``api_key`` exists in ``api-keys.json`` (when *configs_dir*
          is provided)

        Args:
            config: Parsed JSON from the Open WebUI settings file.
            configs_dir: Path to the ``app/configs/`` directory.
                When supplied, the API key is cross-checked against
                ``api-keys.json``.

        Returns:
            ValidationResult with any errors or warnings found.
        """
        result = ValidationResult()

        ow = config.get("open_webui", {})
        if not ow:
            result.issues.append(
                ValidationIssue(
                    "error",
                    "Missing 'open_webui' section in config",
                    "open_webui",
                )
            )
            return result

        # Check API base URL uses 127.0.0.1
        api_url = ow.get("api_base_url", "")
        if "localhost" in api_url:
            result.issues.append(
                ValidationIssue(
                    "warning",
                    f"api_base_url uses 'localhost': {api_url!r}. "
                    "Use '127.0.0.1' to avoid DNS/IPv6 issues.",
                    "open_webui.api_base_url",
                )
            )

        if not api_url:
            result.issues.append(
                ValidationIssue(
                    "error",
                    "api_base_url is missing",
                    "open_webui.api_base_url",
                )
            )

        # Check API key is present
        api_key = ow.get("api_key", "")
        if not api_key:
            result.issues.append(
                ValidationIssue(
                    "error",
                    "api_key is missing",
                    "open_webui.api_key",
                )
            )

        # Check API key exists in api-keys.json
        if api_key and configs_dir:
            keys_path = configs_dir / "api-keys.json"
            if keys_path.exists():
                try:
                    keys_data = json.loads(keys_path.read_text())
                    if api_key not in keys_data.get("keys", {}):
                        result.issues.append(
                            ValidationIssue(
                                "error",
                                f"API key {api_key!r} not found in api-keys.json",
                                "open_webui.api_key",
                            )
                        )
                except json.JSONDecodeError:
                    result.issues.append(
                        ValidationIssue(
                            "warning",
                            "Could not parse api-keys.json",
                            "api-keys.json",
                        )
                    )

        return result
