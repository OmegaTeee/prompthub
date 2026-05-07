# Credential Management

PromptHub uses the Python `keyring` library for all credential management. Credentials are stored in macOS Keychain and accessed via `KeyringManager` at runtime, with full audit logging.

## manage-keys.py

CLI wrapper for `KeyringManager`. All operations go through the router's keyring module.

The `list` command auto-discovers keys by scanning `mcp-servers.json` for `{"source": "keyring"}` references — no hardcoded key list to maintain.

```bash
# From the app/ directory with venv active
source .venv/bin/activate

# List all keys referenced in mcp-servers.json and their status
python scripts/manage-keys.py list --all

# Set a credential (prompts securely for value)
python scripts/manage-keys.py set obsidian_api_key

# Set with value directly (less secure — shows in shell history)
python scripts/manage-keys.py set obsidian_api_key YOUR_KEY

# Retrieve a credential
python scripts/manage-keys.py get obsidian_api_key

# Delete a credential (safe if already gone)
python scripts/manage-keys.py delete obsidian_api_key

# Migrate from old macOS security CLI to keyring
python scripts/manage-keys.py migrate obsidian_api_key
```

## Keyring Architecture

```
manage-keys.py (CLI)  ──┐
                        ├──▶  KeyringManager  ──▶  macOS Keychain
router (runtime)  ──────┘         │
                              audit.py (logs every access)
```

- **Naming convention**: each credential lives at service=`prompthub:<key>`, account=`$USER` — one Keychain entry per credential, distinguishable in Keychain Access
- **Backend**: macOS Keychain via `keyring` library
- **Audit**: Every `get`, `set`, `delete` operation is logged via `audit_credential_access()`
- **Key discovery**: `list` scans `app/configs/mcp-servers.json` for `{"source": "keyring"}` entries; `list --all` also enumerates Keychain directly

## Adding a New Keyring Credential

1. Add the keyring reference to `app/configs/mcp-servers.json`:
   ```json
   {
     "my-server": {
       "env": {
         "MY_API_KEY": {
           "source": "keyring",
           "key": "my_api_key"
         }
       }
     }
   }
   ```
2. Store the value: `python scripts/manage-keys.py set my_api_key`
3. Verify: `python scripts/manage-keys.py list`

The key will appear automatically in `list` output — no code changes needed.
The actual Keychain entry is created at service=`prompthub:my_api_key`, account=`$USER`.

## Programmatic Access

```python
from router.keyring_manager import get_keyring_manager

km = get_keyring_manager()
api_key = km.get_credential("obsidian_api_key")
```

## Directly add to keychain <small>*(not recommended)*</small>

```bash
security add-generic-password -U -s "prompthub:my_api_key" -a "$USER" -w "YOUR_VALUE"
```

## Related

- [KeyringManager](../router/keyring_manager.py) — core credential module
- [Audit System](../../docs/audit/AUDIT-IMPLEMENTATION-COMPLETE.md) — credential access logging
- [MCP Server Config](../configs/mcp-servers.json) — keyring references in server env
