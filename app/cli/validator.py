"""
Config validator — checks installed MCP configs for common issues.

Validates:
- Path safety (no ~, ${HOME}, $HOME, relative paths)
- Required env vars
- Bridge file existence
- URL format (127.0.0.1, not localhost)
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

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
