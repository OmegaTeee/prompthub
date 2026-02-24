# Credential Management

PromptHub uses the Python `keyring` library for all credential management. Credentials are stored in macOS Keychain and accessed via `KeyringManager` at runtime, with full audit logging.

## manage-keys.py

CLI wrapper for `KeyringManager`. All operations go through the router's keyring module.

```bash
# From app/ directory with venv active
source .venv/bin/activate

# Set a credential (prompts securely for value)
python scripts/security/manage-keys.py set obsidian_api_key

# Set with value directly (less secure — shows in shell history)
python scripts/security/manage-keys.py set obsidian_api_key YOUR_KEY

# Retrieve a credential
python scripts/security/manage-keys.py get obsidian_api_key

# List all known keys and their status
python scripts/security/manage-keys.py list

# Delete a credential
python scripts/security/manage-keys.py delete obsidian_api_key

# Migrate from old macOS security CLI to keyring
python scripts/security/manage-keys.py migrate obsidian_api_key
```

## Keyring Architecture

```
manage-keys.py (CLI)  ──┐
                        ├──▶  KeyringManager  ──▶  macOS Keychain
router (runtime)  ──────┘         │
                              audit.py (logs every access)
```

- **Service name**: `prompthub`
- **Backend**: macOS Keychain via `keyring` library
- **Audit**: Every `get`, `set`, `delete` operation is logged via `audit_credential_access()`

## MCP Server Configuration

Credentials are resolved at server startup via `resolve_server_env()` in `supervisor.py`:

```json
{
  "obsidian": {
    "env": {
      "OBSIDIAN_API_KEY": {
        "source": "keyring",
        "service": "prompthub",
        "key": "obsidian_api_key"
      }
    }
  }
}
```

## Programmatic Access

```python
from router.keyring_manager import get_keyring_manager

km = get_keyring_manager()
api_key = km.get_credential("obsidian_api_key")
```

## Related

- [KeyringManager](../../router/keyring_manager.py) — core credential module
- [Audit System](../../docs/audit/AUDIT-IMPLEMENTATION-COMPLETE.md) — credential access logging
- [MCP Server Config](../../configs/mcp-servers.json) — keyring references in server env
