#!/usr/bin/env python3
"""
AgentHub Key Manager

Manage API keys and credentials for MCP servers using system keyring.

NOTE: Run with venv active: source .venv/bin/activate && python scripts/manage-keys.py
Or use: .venv/bin/python scripts/manage-keys.py

Usage:
    ./scripts/manage-keys.py set <key_name>         # Prompt for value
    ./scripts/manage-keys.py set <key_name> <value> # Set directly
    ./scripts/manage-keys.py get <key_name>         # Retrieve value
    ./scripts/manage-keys.py list                    # List all keys
    ./scripts/manage-keys.py delete <key_name>      # Delete key
    ./scripts/manage-keys.py migrate                 # Migrate from security CLI

Examples:
    # Set API key (will prompt for value)
    ./scripts/manage-keys.py set obsidian_api_key

    # Set with value directly (less secure, shows in shell history)
    ./scripts/manage-keys.py set obsidian_api_key YOUR_API_KEY

    # Get API key
    ./scripts/manage-keys.py get obsidian_api_key

    # Migrate from macOS Keychain (security CLI)
    ./scripts/manage-keys.py migrate obsidian_api_key
"""

import sys
import getpass
import subprocess
from pathlib import Path

# Add router to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from router.keyring_manager import get_keyring_manager

SERVICE_NAME = "agenthub"

# Known keys for AgentHub
KNOWN_KEYS = [
    "obsidian_api_key",
    "github_api_key",
    # Add more as needed
]


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


def list_keys():
    """List all known keys and their status."""
    km = get_keyring_manager(SERVICE_NAME)

    print(f"\nAgentHub Keys (service: {SERVICE_NAME}):")
    print("-" * 50)

    for key_name in KNOWN_KEYS:
        value = km.get_credential(key_name)
        status = "✓ SET" if value else "✗ NOT SET"
        print(f"{key_name:30s} {status}")

    print("-" * 50)
    print(f"\nTo set a key: ./scripts/manage-keys.py set <key_name>")
    return 0


def delete_key(key_name: str):
    """Delete a credential from the keyring."""
    km = get_keyring_manager(SERVICE_NAME)

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
        return list_keys()

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
