#!/usr/bin/env python3
"""
PromptHub Key Manager

Manage API keys and credentials for MCP servers using system keyring.

Canonical invocation (from the app/ directory with venv active):
    source .venv/bin/activate
    python scripts/manage-keys.py <command>

Usage:
    python scripts/manage-keys.py set <key_name>          # Prompt for value
    python scripts/manage-keys.py set <key_name> <value>  # Set directly
    python scripts/manage-keys.py get <key_name>          # Retrieve value
    python scripts/manage-keys.py list [--all]            # List configured keys (--all also shows orphaned + legacy)
    python scripts/manage-keys.py delete <key_name>       # Delete key
    python scripts/manage-keys.py migrate <key_name>      # Migrate from legacy security CLI

Examples:
    python scripts/manage-keys.py set perplexity_api_key
    python scripts/manage-keys.py set perplexity_api_key YOUR_API_KEY
    python scripts/manage-keys.py get perplexity_api_key
    python scripts/manage-keys.py migrate perplexity_api_key
"""

import json
import logging
import os
import re
import sys
import getpass
import subprocess
from pathlib import Path

# Resolve project paths (script lives at app/scripts/manage-keys.py)
SCRIPT_DIR = Path(__file__).parent
APP_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = APP_DIR.parent
MCP_SERVERS_JSON = APP_DIR / "configs" / "mcp-servers.json"

# Add app/ to path so `from router.keyring_manager` resolves
sys.path.insert(0, str(APP_DIR))

# Suppress audit log JSON output for CLI usage
logging.getLogger("audit").setLevel(logging.CRITICAL)
logging.getLogger("router").setLevel(logging.CRITICAL)

from router.keyring_manager import get_keyring_manager

SERVICE_NAME = "prompthub"

# Keys resolved by Settings (not in mcp-servers.json, but stored in keyring)
SETTINGS_KEYS: dict[str, str] = {
    "openrouter_api_key": "Settings → cloud fallback",
    "hf_api_key": "Settings → Hugging Face",
    "lm_api_token": "Settings → LM Studio (llm_api_key fallback)",
}


def discover_keys() -> dict[str, list[str]]:
    """
    Discover all keyring-managed keys from two sources:
      1. mcp-servers.json  — {"source": "keyring"} env references
      2. SETTINGS_KEYS     — keys resolved by Settings.model_post_init

    Returns:
        Dict mapping key_name -> list of consumers that use it.
        Example: {"obsidian_api_key": ["obsidian-mcp-tools"],
                  "openrouter_api_key": ["Settings → cloud fallback"]}
    """
    keys: dict[str, list[str]] = {}

    # 1. Scan mcp-servers.json
    if MCP_SERVERS_JSON.exists():
        try:
            config = json.loads(MCP_SERVERS_JSON.read_text())
            servers = config.get("servers", config)
            for server_name, server_config in servers.items():
                env = server_config.get("env", {})
                for env_var, env_value in env.items():
                    if isinstance(env_value, dict) and env_value.get("source") == "keyring":
                        key_name = env_value.get("key")
                        if key_name:
                            keys.setdefault(key_name, []).append(server_name)
        except (json.JSONDecodeError, OSError):
            pass

    # 2. Add Settings-managed keys
    for key_name, consumer in SETTINGS_KEYS.items():
        keys.setdefault(key_name, []).append(consumer)

    return keys


def discover_keychain_keys() -> tuple[list[str], list[str]]:
    """
    Enumerate Keychain entries by shelling out to `security dump-keychain`.

    Returns:
        (current_keys, legacy_keys) where:
          current_keys  = accounts under svce='prompthub:<key>' (new convention)
          legacy_keys   = accounts under svce='prompthub' (pre-migration)
    """
    try:
        result = subprocess.run(
            ["security", "dump-keychain"],
            capture_output=True, text=True, check=False, timeout=15,
        )
    except (subprocess.SubprocessError, OSError):
        return [], []

    current, legacy = set(), set()
    for block in result.stdout.split("keychain:"):
        svce_m = re.search(r'"svce"<blob>="([^"]+)"', block)
        acct_m = re.search(r'"acct"<blob>="([^"]*)"', block)
        if not svce_m:
            continue
        svce = svce_m.group(1)
        acct = acct_m.group(1) if acct_m else ""
        if svce.startswith(f"{SERVICE_NAME}:"):
            current.add(svce[len(SERVICE_NAME) + 1:])  # strip "prompthub:"
        elif svce == SERVICE_NAME and acct:
            legacy.add(acct)
    return sorted(current), sorted(legacy)


def set_key(key_name: str, value: str = None):
    """Set a credential in the keyring."""
    km = get_keyring_manager(SERVICE_NAME)

    if value is None:
        # Prompt securely
        value = getpass.getpass(f"Enter value for {key_name}: ")

    if not value:
        print("Error: Empty value not allowed", file=sys.stderr)
        return 1

    if km.set_credential(key_name, value):
        print(f"✓ Stored: {key_name}")
        return 0
    else:
        print(f"✗ Failed to store: {key_name}", file=sys.stderr)
        return 1


def get_key(key_name: str):
    """Retrieve a credential from the keyring."""
    km = get_keyring_manager(SERVICE_NAME)

    value = km.get_credential(key_name)
    if value:
        print(value)
        return 0
    else:
        print(f"✗ Not found: {key_name}", file=sys.stderr)
        return 1


def list_keys(show_all: bool = False):
    """List configured keyring keys and their status.

    With show_all=True, also enumerate Keychain entries directly:
    - 'orphaned' = stored at prompthub:<key> but not referenced anywhere
    - 'legacy'   = stored at svce='prompthub' (pre-migration convention)
    """
    km = get_keyring_manager(SERVICE_NAME)
    keys = discover_keys()
    # Match KeyringManager: getpass.getuser() works in non-interactive shells too.
    user = getpass.getuser()

    print(f"\nPromptHub Keys (service prefix: {SERVICE_NAME!r}, account: {user!r}):")
    print("-" * 70)

    if keys:
        for key_name, consumers in sorted(keys.items()):
            value = km.get_credential(key_name)
            status = "✓ SET" if value else "✗ NOT SET"
            used_by = ", ".join(consumers)
            print(f"  {key_name:30s} {status:10s} → {used_by}")
    else:
        print("  (no configured keys found)")

    if show_all:
        current, legacy = discover_keychain_keys()
        configured = set(keys.keys())

        orphaned = [k for k in current if k not in configured]
        if orphaned:
            print("\nOrphaned in Keychain (no consumer references):")
            for k in orphaned:
                print(f"  {k:30s} ✓ SET      → (unused)")

        if legacy:
            print(f"\nLegacy entries (svce='{SERVICE_NAME}', pre-migration):")
            for k in legacy:
                print(f"  {k:30s} ⚠ legacy   → run migration or delete")

    print("-" * 70)
    print("\nTo set a key:    python scripts/manage-keys.py set <key_name>")
    print("To see all:      python scripts/manage-keys.py list --all")
    return 0


def delete_key(key_name: str):
    """Delete a credential from the keyring."""
    km = get_keyring_manager(SERVICE_NAME)

    # Check if key exists first
    exists = km.get_credential(key_name) is not None

    if not exists:
        print(f"✓ Already gone: {key_name} (not in keyring)")
        return 0

    confirm = input(f"Delete {key_name}? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled")
        return 0

    if km.delete_credential(key_name):
        print(f"✓ Deleted: {key_name}")
        return 0
    else:
        print(f"✗ Failed to delete: {key_name}", file=sys.stderr)
        return 1


def migrate_from_security_cli(key_name: str):
    """Migrate a key from macOS security CLI to keyring."""
    print(f"Migrating {key_name} from macOS Keychain...")

    # Try to retrieve from security CLI
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-a", subprocess.check_output(["whoami"]).decode().strip(),
                "-s", key_name,
                "-w"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        value = result.stdout.strip()

        if value:
            km = get_keyring_manager(SERVICE_NAME)
            if km.set_credential(key_name, value):
                print(f"✓ Migrated: {key_name}")
                print(f"  Old location: macOS Keychain (security CLI)")
                print(f"  New location: {SERVICE_NAME} keyring")
                return 0

    except subprocess.CalledProcessError:
        print(f"✗ Not found in macOS Keychain: {key_name}", file=sys.stderr)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)

    return 1


def print_usage():
    """Print usage information."""
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_usage()
        return 1

    command = sys.argv[1]

    if command == "set":
        if len(sys.argv) < 3:
            print("Error: Missing key name", file=sys.stderr)
            print("Usage: manage-keys.py set <key_name> [value]", file=sys.stderr)
            return 1
        key_name = sys.argv[2]
        value = sys.argv[3] if len(sys.argv) > 3 else None
        return set_key(key_name, value)

    elif command == "get":
        if len(sys.argv) < 3:
            print("Error: Missing key name", file=sys.stderr)
            print("Usage: manage-keys.py get <key_name>", file=sys.stderr)
            return 1
        key_name = sys.argv[2]
        return get_key(key_name)

    elif command == "list":
        show_all = "--all" in sys.argv[2:]
        return list_keys(show_all=show_all)

    elif command == "delete":
        if len(sys.argv) < 3:
            print("Error: Missing key name", file=sys.stderr)
            print("Usage: manage-keys.py delete <key_name>", file=sys.stderr)
            return 1
        key_name = sys.argv[2]
        return delete_key(key_name)

    elif command == "migrate":
        if len(sys.argv) < 3:
            print("Error: Missing key name", file=sys.stderr)
            print("Usage: manage-keys.py migrate <key_name>", file=sys.stderr)
            return 1
        key_name = sys.argv[2]
        return migrate_from_security_cli(key_name)

    else:
        print(f"Error: Unknown command: {command}", file=sys.stderr)
        print_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())
