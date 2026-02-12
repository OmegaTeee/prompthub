"""
AgentHub Client Configuration Generators.

Generates configuration files for various applications to connect
to the AgentHub router.
"""

from router.clients.generators import (
    generate_claude_desktop_config,
    generate_raycast_script,
    generate_vscode_config,
    generate_vscode_tasks,
)

__all__ = [
    "generate_claude_desktop_config",
    "generate_vscode_config",
    "generate_vscode_tasks",
    "generate_raycast_script",
]
