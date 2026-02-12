"""
Integration-style tests for keyring functionality.

These were moved from the repository root into `tests/integration/` so pytest
can discover them consistently.
"""

import sys
from pathlib import Path

# Ensure package imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

from router.keyring_manager import get_keyring_manager


def test_keyring_basic():
    km = get_keyring_manager()
    assert hasattr(km, "service_name")


def test_process_env_config():
    km = get_keyring_manager()

    test_config = {
        "OBSIDIAN_API_KEY": {"source": "keyring", "service": "agenthub", "key": "obsidian_api_key"},
        "OBSIDIAN_HOST": "https://127.0.0.1",
        "OBSIDIAN_PORT": "27124",
        "_comment": "This should be skipped",
    }

    processed = km.process_env_config(test_config)
    assert "OBSIDIAN_API_KEY" in processed
    assert "OBSIDIAN_HOST" in processed
    assert "OBSIDIAN_PORT" in processed


def test_mcp_server_config():
    import json

    # Point to repository-level configs directory
    config_path = Path(__file__).parent.parent.parent / "configs" / "mcp-servers.json"
    with open(config_path) as f:
        config = json.load(f)

    assert "servers" in config
