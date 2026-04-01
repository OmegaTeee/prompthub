"""
Consolidated client setup — generates configs and creates symlinks.

Workflow:
1. Generate configs for all discovered clients to ~/.prompthub/clients/
2. For MCP-only config files (Raycast, Open WebUI): symlink from client path
3. For mixed config files (Claude Desktop, etc.): merge PromptHub entry
"""

import json
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cli.discovery import ClientDetection
from cli.generator import ConfigGenerator
from cli.installer import ConfigInstaller
from cli.models import ClientType
from cli.profiles import ProfileLoader

logger = logging.getLogger(__name__)


# Clients whose config file is MCP-only (safe to symlink the whole file)
_SYMLINK_SAFE: set[ClientType] = {
    ClientType.raycast,
    ClientType.open_webui,
}


@dataclass
class SetupAction:
    """Planned or completed setup action for a client."""

    client_type: ClientType
    strategy: str  # "symlink" or "merge"
    central_path: Path
    target_path: Path
    generated: dict[str, Any] | None = None
    success: bool = False
    message: str = ""


def plan_setup(
    discovered: list[ClientDetection],
    central_dir: Path | None = None,
) -> list[SetupAction]:
    """
    Plan setup actions for discovered clients.

    Args:
        discovered: Results from discover_installed()
        central_dir: Where to write consolidated configs
                     (default ``~/.prompthub/clients/``)

    Returns:
        List of planned actions (not yet executed).
    """
    if central_dir is None:
        central_dir = Path.home() / ".prompthub" / "clients"

    actions = []
    for detection in discovered:
        ct = detection.client_type
        central_path = central_dir / f"{ct.value}.json"
        target_path = ct.config_path()
        strategy = "symlink" if ct in _SYMLINK_SAFE else "merge"

        actions.append(
            SetupAction(
                client_type=ct,
                strategy=strategy,
                central_path=central_path,
                target_path=target_path,
            )
        )

    return actions


def execute_setup(
    actions: list[SetupAction],
    workspace_root: Path,
    dry_run: bool = False,
) -> list[SetupAction]:
    """
    Execute planned setup actions.

    For each action:
    1. Generate config via ConfigGenerator + ProfileLoader
    2. Write to ``central_path`` (``~/.prompthub/clients/``)
    3. Symlink or merge into ``target_path``

    Args:
        actions: Output from plan_setup()
        workspace_root: PromptHub workspace root (for bridge path + configs)
        dry_run: If True, generate configs but write nothing

    Returns:
        Same action list with ``success`` and ``message`` populated.
    """
    gen = ConfigGenerator(workspace_root=workspace_root)
    loader = ProfileLoader(configs_dir=workspace_root / "app" / "configs")
    installer = ConfigInstaller()

    for action in actions:
        try:
            profile = loader.load(action.client_type)
            config = gen.generate(action.client_type, profile=profile)
            action.generated = config

            if dry_run:
                action.success = True
                action.message = "dry run"
                continue

            # Write consolidated config
            action.central_path.parent.mkdir(parents=True, exist_ok=True)
            action.central_path.write_text(
                json.dumps(config, indent=2) + "\n"
            )

            if action.strategy == "symlink":
                _do_symlink(action)
            else:
                _do_merge(action, config, installer)

            action.success = True

        except Exception as e:
            action.success = False
            action.message = f"error: {e}"
            logger.error(
                "Setup failed for %s: %s",
                action.client_type.value,
                e,
            )

    return actions


def _do_symlink(action: SetupAction) -> None:
    """Symlink client config path → central file."""
    target = action.target_path

    if target.is_symlink():
        target.unlink()
        action.message = "updated symlink"
    elif target.exists():
        backup = target.with_suffix(target.suffix + ".pre-setup.bak")
        shutil.copy2(target, backup)
        target.unlink()
        action.message = f"backed up to {backup.name}"
    else:
        action.message = "created symlink"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(action.central_path)


def _do_merge(
    action: SetupAction,
    config: dict[str, Any],
    installer: ConfigInstaller,
) -> None:
    """Merge PromptHub entry into client's existing config."""
    installer.install(
        action.client_type,
        config,
        config_path=action.target_path,
    )
    action.message = f"merged into {action.target_path}"
