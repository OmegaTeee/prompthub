"""
PromptHub CLI — MCP Config Manager.

Commands:
    generate    Print config JSON for a client
    install     Merge config into client's active config file
    validate    Check installed config for issues
    diff        Compare installed vs. generated config
    list        Show all clients and config paths
    diagnose    Full health check (router, bridge, node)
"""

import difflib
import json
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from cli.diagnostics import Diagnostician
from cli.generator import ConfigGenerator
from cli.installer import ConfigInstaller
from cli.models import ClientType
from cli.profiles import ProfileLoader
from cli.validator import ConfigValidator

app = typer.Typer(
    name="prompthub",
    help="PromptHub CLI — MCP Config Manager",
    no_args_is_help=True,
)


def _resolve_workspace(workspace: Path | None) -> Path:
    if workspace:
        return workspace.resolve()
    return Path.home() / ".local" / "share" / "prompthub"


# ── generate ─────────────────────────────────────────────────────────


@app.command()
def generate(
    client: Annotated[
        ClientType, typer.Argument(help="Target client to generate config for")
    ],
    servers: Annotated[
        Optional[str],
        typer.Option(
            help="Comma-separated server filter (e.g. 'context7,desktop-commander')"
        ),
    ] = None,
    exclude_tools: Annotated[
        Optional[str],
        typer.Option(
            "--exclude-tools",
            help="Comma-separated tool names to exclude",
        ),
    ] = None,
    api_key: Annotated[
        Optional[str],
        typer.Option("--api-key", help="Bearer token for AUTHORIZATION"),
    ] = None,
    workspace: Annotated[
        Optional[Path],
        typer.Option(
            "--workspace", "-w", help="PromptHub workspace root"
        ),
    ] = None,
    use_profile: Annotated[
        bool,
        typer.Option(
            "--profile/--no-profile",
            help="Load settings from api-keys.json and enhancement-rules.json",
        ),
    ] = True,
) -> None:
    """Generate MCP config JSON for a desktop client."""
    ws = _resolve_workspace(workspace)
    gen = ConfigGenerator(workspace_root=ws)

    profile = None
    if use_profile:
        loader = ProfileLoader(configs_dir=ws / "app" / "configs")
        profile = loader.load(client)

    # CLI flags override profile
    server_list = (
        [s.strip() for s in servers.split(",") if s.strip()]
        if servers
        else None
    )
    tool_list = (
        [s.strip() for s in exclude_tools.split(",") if s.strip()]
        if exclude_tools
        else None
    )

    extra_env: dict[str, str] = {}
    if api_key:
        extra_env["AUTHORIZATION"] = f"Bearer {api_key}"

    try:
        output = gen.generate_json(
            client,
            profile=profile,
            servers=server_list,
            exclude_tools=tool_list,
            extra_env=extra_env if extra_env else None,
        )
        typer.echo(output)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# ── install ──────────────────────────────────────────────────────────


@app.command()
def install(
    client: Annotated[
        ClientType, typer.Argument(help="Target client")
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f", help="Replace entire mcpServers section"
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", "-n", help="Show merged config without writing"
        ),
    ] = False,
    config_path: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Override config file path"),
    ] = None,
    workspace: Annotated[
        Optional[Path],
        typer.Option("--workspace", "-w", help="PromptHub workspace root"),
    ] = None,
) -> None:
    """Install PromptHub config into client's active config file."""
    ws = _resolve_workspace(workspace)
    gen = ConfigGenerator(workspace_root=ws)
    loader = ProfileLoader(configs_dir=ws / "app" / "configs")
    profile = loader.load(client)

    try:
        generated = gen.generate(client, profile=profile)
    except ValueError as e:
        typer.echo(f"Error generating config: {e}", err=True)
        raise typer.Exit(1)

    installer = ConfigInstaller()
    merged = installer.install(
        client, generated, config_path=config_path, force=force, dry_run=dry_run
    )

    if dry_run:
        typer.echo(json.dumps(merged, indent=2))
        typer.echo("\n(dry run — no files written)", err=True)
    else:
        target = config_path or client.config_path()
        typer.echo(f"Config installed to: {target}")


# ── validate ─────────────────────────────────────────────────────────


@app.command()
def validate(
    client: Annotated[
        ClientType, typer.Argument(help="Client to validate")
    ],
    config_path: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Override config file path"),
    ] = None,
    workspace: Annotated[
        Optional[Path],
        typer.Option("--workspace", "-w", help="PromptHub workspace root"),
    ] = None,
) -> None:
    """
    Validate installed MCP config for common issues.

    For bridge-based clients, checks path safety, env vars, and bridge
    file existence.  For Open WebUI, validates connection settings
    (api_base_url, api_key) and cross-checks the key against
    api-keys.json.
    """
    path = config_path or client.config_path()
    validator = ConfigValidator()

    if client == ClientType.open_webui:
        # Open WebUI uses HTTP connection settings, not a stdio bridge.
        # Delegate to the dedicated validator instead of validate_file().
        if not path.exists():
            typer.echo(f"  Config file not found: {path}")
            raise typer.Exit(1)
        try:
            config = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            typer.echo(f"  Invalid JSON: {e}")
            raise typer.Exit(1)

        ws = _resolve_workspace(workspace)
        result = validator.validate_open_webui(
            config, configs_dir=ws / "app" / "configs"
        )
    else:
        result = validator.validate_file(path)

    if result.ok and not result.warnings:
        typer.echo(f"  {path}")
        typer.echo(f"  {result.summary()}")
        return

    for issue in result.issues:
        prefix = "ERROR" if issue.level == "error" else "WARN "
        typer.echo(f"  [{prefix}] {issue.message}")
        if issue.path:
            typer.echo(f"          at {issue.path}")

    typer.echo(f"\n  {result.summary()}")

    if not result.ok:
        raise typer.Exit(1)


# ── diff ─────────────────────────────────────────────────────────────


@app.command(name="diff")
def diff_cmd(
    client: Annotated[
        ClientType, typer.Argument(help="Client to compare")
    ],
    config_path: Annotated[
        Optional[Path],
        typer.Option("--config", "-c", help="Override config file path"),
    ] = None,
    workspace: Annotated[
        Optional[Path],
        typer.Option("--workspace", "-w", help="PromptHub workspace root"),
    ] = None,
) -> None:
    """Compare installed config vs. what would be generated."""
    ws = _resolve_workspace(workspace)
    gen = ConfigGenerator(workspace_root=ws)
    loader = ProfileLoader(configs_dir=ws / "app" / "configs")
    profile = loader.load(client)

    try:
        generated = gen.generate(client, profile=profile)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    installer = ConfigInstaller()
    installed_str, generated_str = installer.diff(
        client, generated, config_path=config_path
    )

    if installed_str == generated_str:
        typer.echo("No differences found.")
        return

    path = config_path or client.config_path()
    diff_lines = difflib.unified_diff(
        installed_str.splitlines(keepends=True),
        generated_str.splitlines(keepends=True),
        fromfile=f"installed ({path})",
        tofile="generated",
    )
    sys.stdout.writelines(diff_lines)


# ── list ─────────────────────────────────────────────────────────────


@app.command(name="list")
def list_cmd() -> None:
    """Show all supported clients and their config paths."""
    loader = ProfileLoader()

    for ct in ClientType:
        path = ct.config_path()
        exists = path.exists()
        status = "found" if exists else "not found"
        typer.echo(f"  {ct.value:<20} {status:<12} {path}")

        # Show profile info
        profile = loader.load(ct)
        if profile.api_key:
            key_preview = profile.api_key[:20] + "..."
            typer.echo(f"  {'':20} key: {key_preview}")
        if profile.privacy_level != "local_only":
            typer.echo(
                f"  {'':20} privacy: {profile.privacy_level}"
            )
        typer.echo()


# ── diagnose ─────────────────────────────────────────────────────────


@app.command()
def diagnose(
    workspace: Annotated[
        Optional[Path],
        typer.Option("--workspace", "-w", help="PromptHub workspace root"),
    ] = None,
) -> None:
    """Run full health check on the PromptHub stack."""
    ws = _resolve_workspace(workspace)
    diag = Diagnostician(workspace_root=ws)
    report = diag.run_all()

    for check in report.checks:
        icon = "PASS" if check.passed else "FAIL"
        typer.echo(f"  [{icon}] {check.name}: {check.message}")
        if check.details:
            typer.echo(f"         {check.details}")

    typer.echo()
    typer.echo(
        f"  {report.passed_count}/{report.total_count} checks passed"
    )

    if not report.all_passed:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
