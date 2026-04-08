# Credential Management

PromptHub uses the Python `keyring` library for all credential management. Credentials are stored in macOS Keychain and accessed via `KeyringManager` at runtime, with full audit logging.

## manage-keys.py

CLI wrapper for `KeyringManager`. All operations go through the router's keyring module.

The `list` command auto-discovers keys by scanning `mcp-servers.json` for `{"source": "keyring"}` references — no hardcoded key list to maintain.

```bash
# From project root with venv active
source app/.venv/bin/activate

# List all keys referenced in mcp-servers.json and their status
python scripts/security/manage-keys.py list

# Set a credential (prompts securely for value)
python scripts/security/manage-keys.py set obsidian_api_key

# Set with value directly (less secure — shows in shell history)
python scripts/security/manage-keys.py set obsidian_api_key YOUR_KEY

# Retrieve a credential
python scripts/security/manage-keys.py get obsidian_api_key

# Delete a credential (safe if already gone)
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
- **Key discovery**: `list` scans `app/configs/mcp-servers.json` for `{"source": "keyring"}` entries

## Adding a New Keyring Credential

1. Add the keyring reference to `app/configs/mcp-servers.json`:
   ```json
   {
     "my-server": {
       "env": {
         "MY_API_KEY": {
           "source": "keyring",
           "service": "prompthub",
           "key": "my_api_key"
         }
       }
     }
   }
   ```
2. Store the value: `python scripts/security/manage-keys.py set my_api_key`
3. Verify: `python scripts/security/manage-keys.py list`

The key will appear automatically in `list` output — no code changes needed.

## Programmatic Access

```python
from router.keyring_manager import get_keyring_manager

km = get_keyring_manager()
api_key = km.get_credential("obsidian_api_key")
```

## Related

- [KeyringManager](../../app/router/keyring_manager.py) — core credential module
- [Audit System](../../docs/audit/AUDIT-IMPLEMENTATION-COMPLETE.md) — credential access logging
- [MCP Server Config](../../app/configs/mcp-servers.json) — keyring references in server env
