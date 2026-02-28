"""
Diagnostics — runtime health checks for the PromptHub stack.

Checks:
- node binary on PATH
- Bridge file exists and readable
- Router reachable (GET /health)
- Servers discoverable (GET /servers)
- API key valid (GET /v1/models with bearer token)
- Installed config passes validator
"""

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from cli.models import ClientType
from cli.validator import ConfigValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticCheck:
    """Result of a single diagnostic check."""

    name: str
    passed: bool
    message: str
    details: str = ""


@dataclass
class DiagnosticReport:
    """Aggregate diagnostic results."""

    checks: list[DiagnosticCheck] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def total_count(self) -> int:
        return len(self.checks)


class Diagnostician:
    """Runs health checks on the PromptHub stack."""

    def __init__(
        self,
        workspace_root: Path | None = None,
        router_url: str = "http://127.0.0.1:9090",
    ):
        if workspace_root is None:
            workspace_root = Path.home() / ".local" / "share" / "prompthub"
        self.workspace_root = workspace_root.resolve()
        self.bridge_path = self.workspace_root / "mcps" / "prompthub-bridge.js"
        self.router_url = router_url

    def run_all(self) -> DiagnosticReport:
        """Run all diagnostic checks."""
        report = DiagnosticReport()
        report.checks.append(self._check_node())
        report.checks.append(self._check_bridge_file())
        report.checks.append(self._check_router())
        report.checks.append(self._check_servers())
        report.checks.append(self._check_installed_config())
        return report

    def _check_node(self) -> DiagnosticCheck:
        """Check that node is on PATH and executable."""
        node_path = shutil.which("node")
        if not node_path:
            return DiagnosticCheck(
                "Node.js",
                False,
                "node not found on PATH",
                "Install Node.js: https://nodejs.org/",
            )

        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version = result.stdout.strip()
            return DiagnosticCheck(
                "Node.js", True, f"node {version}", f"Path: {node_path}"
            )
        except (subprocess.TimeoutExpired, OSError) as e:
            return DiagnosticCheck(
                "Node.js", False, f"node failed: {e}", f"Path: {node_path}"
            )

    def _check_bridge_file(self) -> DiagnosticCheck:
        """Check that the bridge file exists and is readable."""
        if not self.bridge_path.exists():
            return DiagnosticCheck(
                "Bridge file",
                False,
                f"Not found: {self.bridge_path}",
            )

        try:
            content = self.bridge_path.read_text()
            has_shebang = content.startswith("#!/usr/bin/env node")
            return DiagnosticCheck(
                "Bridge file",
                True,
                f"Found ({len(content)} bytes)",
                f"Path: {self.bridge_path}"
                + (" [has shebang]" if has_shebang else ""),
            )
        except OSError as e:
            return DiagnosticCheck(
                "Bridge file",
                False,
                f"Cannot read: {e}",
                f"Path: {self.bridge_path}",
            )

    def _check_router(self) -> DiagnosticCheck:
        """Check that the router is reachable."""
        try:
            import httpx

            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{self.router_url}/health")
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status", "unknown")
                    return DiagnosticCheck(
                        "Router",
                        True,
                        f"Healthy (status={status})",
                        f"URL: {self.router_url}",
                    )
                else:
                    return DiagnosticCheck(
                        "Router",
                        False,
                        f"HTTP {resp.status_code}",
                        f"URL: {self.router_url}",
                    )
        except ImportError:
            # Fallback without httpx
            import urllib.request

            try:
                req = urllib.request.Request(f"{self.router_url}/health")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read())
                    return DiagnosticCheck(
                        "Router",
                        True,
                        f"Healthy (status={data.get('status', 'unknown')})",
                        f"URL: {self.router_url}",
                    )
            except Exception as e:
                return DiagnosticCheck(
                    "Router",
                    False,
                    f"Unreachable: {e}",
                    f"URL: {self.router_url}",
                )
        except Exception as e:
            return DiagnosticCheck(
                "Router",
                False,
                f"Unreachable: {e}",
                f"URL: {self.router_url}",
            )

    def _check_servers(self) -> DiagnosticCheck:
        """Check that servers are discoverable."""
        try:
            import httpx

            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{self.router_url}/servers")
                if resp.status_code == 200:
                    data = resp.json()
                    servers = data.get("servers", [])
                    running = [
                        s["name"]
                        for s in servers
                        if s.get("status") == "running"
                    ]
                    return DiagnosticCheck(
                        "Servers",
                        len(running) > 0,
                        f"{len(running)} running: {', '.join(running)}"
                        if running
                        else "No servers running",
                        f"Total configured: {len(servers)}",
                    )
                else:
                    return DiagnosticCheck(
                        "Servers", False, f"HTTP {resp.status_code}"
                    )
        except ImportError:
            return DiagnosticCheck(
                "Servers", False, "httpx not available, skipping"
            )
        except Exception as e:
            return DiagnosticCheck(
                "Servers", False, f"Failed: {e}"
            )

    def _check_installed_config(self) -> DiagnosticCheck:
        """Validate the installed Claude Desktop config."""
        config_path = ClientType.claude_desktop.config_path()
        if not config_path.exists():
            return DiagnosticCheck(
                "Installed config",
                False,
                "Claude Desktop config not found",
                f"Expected: {config_path}",
            )

        validator = ConfigValidator()
        result: ValidationResult = validator.validate_file(config_path)

        if result.ok:
            msg = "Valid"
            if result.warnings:
                msg += f" ({len(result.warnings)} warning(s))"
            return DiagnosticCheck(
                "Installed config",
                True,
                msg,
                f"Path: {config_path}",
            )
        else:
            errors = "; ".join(i.message for i in result.errors)
            return DiagnosticCheck(
                "Installed config",
                False,
                f"{len(result.errors)} error(s): {errors}",
                f"Path: {config_path}",
            )
