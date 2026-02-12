# Security Scripts

Scripts for managing API keys and credentials via macOS Keychain.

## Scripts

### `manage-keys.py`
Interactive tool for managing API keys in macOS Keychain and syncing with AgentHub configuration.

**Purpose:** Centralized credential management with secure Keychain storage.

**Usage:**
```bash
# Interactive mode (recommended)
python3 scripts/security/manage-keys.py

# List all keys
python3 scripts/security/manage-keys.py --list

# Add key
python3 scripts/security/manage-keys.py --add obsidian_api_key

# Get key value
python3 scripts/security/manage-keys.py --get obsidian_api_key

# Delete key
python3 scripts/security/manage-keys.py --delete obsidian_api_key

# Rotate key (delete + re-add)
python3 scripts/security/manage-keys.py --rotate obsidian_api_key

# Export keys (encrypted backup)
python3 scripts/security/manage-keys.py --export keys-backup.enc

# Import keys (from backup)
python3 scripts/security/manage-keys.py --import keys-backup.enc

# Sync with mcp-servers-keyring.json
python3 scripts/security/manage-keys.py --sync
```

**Interactive menu:**
```
🔐 AgentHub Key Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Select operation:
  1. List all keys
  2. Add new key
  3. Update existing key
  4. Delete key
  5. Rotate key
  6. Test key (verify with service)
  7. Export keys (encrypted backup)
  8. Import keys (restore from backup)
  9. Sync with configuration
  0. Exit

> 2

Enter key name: github_api_key
Enter key value: **********************
Confirm (y/n): y

✓ Key added to Keychain
✓ Updated mcp-servers-keyring.json
✓ Validated with GitHub API

Next: Restart MCP servers to use new key
  python3 scripts/router/restart-mcp-servers.py
```

**Features:**
- Stores keys securely in macOS Keychain
- Validates key format before saving
- Tests keys against APIs (optional)
- Generates `mcp-servers-keyring.json` automatically
- Creates encrypted backups
- Audit logging of key access

**Dependencies:**
- Python 3.8+
- `keyring` library
- `cryptography` for backups
- macOS Keychain

**Keychain entries:**
- Service: `agenthub`
- Account: `<key_name>` (e.g., `obsidian_api_key`)
- Password: `<key_value>`

### `github-api-key.sh`
Template wrapper script for GitHub MCP server with API key from Keychain.

**Purpose:** Example of secure API key wrapper pattern.

**Usage:**
```bash
# Add key first
security add-generic-password -a $USER -s github_api_key -w YOUR_TOKEN

# Run GitHub MCP server
scripts/security/github-api-key.sh

# Or configure in mcp-servers.json:
# {
#   "github": {
#     "command": "./scripts/security/github-api-key.sh",
#     "args": []
#   }
# }
```

**Script anatomy:**
```bash
#!/bin/bash
# Secure API key wrapper pattern

# 1. Retrieve from Keychain
GITHUB_TOKEN="$(security find-generic-password -a "${USER}" -s "github_api_key" -w 2>/dev/null)"

# 2. Validate key exists
if [[ -z "${GITHUB_TOKEN}" ]]; then
    echo "Error: github_api_key not found in Keychain" >&2
    echo "Add it with: security add-generic-password -a \$USER -s github_api_key -w YOUR_TOKEN" >&2
    exit 1
fi

# 3. Export as environment variable
export GITHUB_TOKEN

# 4. Exec MCP server (replaces shell process)
exec npx -y @github/mcp-server "$@"
```

**Security features:**
- Never stores key in plaintext
- Key only in memory during exec
- Process replacement prevents shell exposure
- Audit trail in system logs

## Key Management Best Practices

### Adding Keys

```bash
# Method 1: Using manage-keys.py (recommended)
python3 scripts/security/manage-keys.py --add obsidian_api_key

# Method 2: Direct Keychain access
security add-generic-password \
  -a $USER \
  -s "obsidian_api_key" \
  -w "your-secret-key" \
  -T ""  # Allow all apps to access

# Method 3: Interactive prompt (avoids shell history)
read -sp "Enter API key: " KEY
security add-generic-password -a $USER -s "obsidian_api_key" -w "$KEY"
unset KEY
```

### Retrieving Keys

```bash
# Safe retrieval (doesn't log to terminal)
KEY=$(security find-generic-password -a $USER -s "obsidian_api_key" -w 2>/dev/null)
export OBSIDIAN_API_KEY="$KEY"

# Validate key exists
if [[ -z "$KEY" ]]; then
  echo "Key not found" >&2
  exit 1
fi
```

### Rotating Keys

```bash
# 1. Generate new key from service
# 2. Test new key
curl -H "Authorization: Bearer NEW_KEY" https://api.service.com/test

# 3. Update Keychain
security delete-generic-password -a $USER -s "service_api_key"
security add-generic-password -a $USER -s "service_api_key" -w "NEW_KEY"

# 4. Restart MCP servers
python3 scripts/router/restart-mcp-servers.py

# 5. Revoke old key at service
```

### Backing Up Keys

```bash
# Create encrypted backup
python3 scripts/security/manage-keys.py --export keys-$(date +%Y%m%d).enc

# Store backup securely
# ✓ Password manager (1Password, LastPass)
# ✓ Encrypted USB drive
# ✓ Secure cloud storage (with encryption)

# Never store backups:
# ✗ In git repositories
# ✗ On unencrypted drives
# ✗ In email or chat
```

## Integration with AgentHub

### Configuration Files

**configs/mcp-servers-keyring.json**
```json
{
  "servers": {
    "obsidian": {
      "keyring_keys": {
        "OBSIDIAN_API_KEY": "obsidian_api_key"
      }
    },
    "github": {
      "keyring_keys": {
        "GITHUB_TOKEN": "github_api_key"
      }
    }
  }
}
```

### Router Integration

```python
# router/keyring_manager.py
from router.keyring_manager import KeyringManager

km = KeyringManager()

# Retrieve key
api_key = km.get_credential("obsidian_api_key")

# Set as environment variable
os.environ["OBSIDIAN_API_KEY"] = api_key

# Start MCP server with key
start_server("obsidian")
```

### Wrapper Script Pattern

```bash
#!/bin/bash
# Generic MCP wrapper template

SERVICE_NAME="myservice"
KEY_NAME="${SERVICE_NAME}_api_key"
ENV_VAR="${SERVICE_NAME^^}_API_KEY"  # Uppercase

# Retrieve from Keychain
KEY="$(security find-generic-password -a "${USER}" -s "${KEY_NAME}" -w 2>/dev/null)"

if [[ -z "${KEY}" ]]; then
    echo "Error: ${KEY_NAME} not found in Keychain" >&2
    echo "Add with: python3 scripts/security/manage-keys.py --add ${KEY_NAME}" >&2
    exit 1
fi

export "${ENV_VAR}=${KEY}"
exec npx -y "@myservice/mcp-server" "$@"
```

## Security Considerations

### Keychain Access Control

```bash
# Allow specific app to access key
security add-generic-password \
  -a $USER \
  -s "api_key" \
  -w "secret" \
  -T "/path/to/app"

# Deny access from terminal
security set-generic-password-partition-list \
  -S "api_key" \
  -k "keychain-password"
```

### Audit Logging

All key access is logged via AgentHub's audit system:

```python
# router/audit.py
audit_credential_access(
    action="get",
    credential_key="obsidian_api_key",
    status="success",
    client_id="claude-desktop"
)
```

View audit logs:
```bash
# Recent key access
tail -f logs/audit.log | grep "credential_access"

# Key access by client
jq '.event_type == "credential_access" and .client_id == "claude-desktop"' logs/audit.log
```

### Key Rotation Schedule

| Service | Rotation Frequency | Method |
|---------|-------------------|--------|
| GitHub | 90 days | PAT regeneration |
| Obsidian | 180 days | API key refresh |
| OpenAI | 30 days | New secret key |
| Anthropic | 90 days | Rotate in Console |

```bash
# Set reminder
launchctl submit -l com.agenthub.key-rotation -- \
  osascript -e 'display notification "Time to rotate API keys" with title "AgentHub Security"'
```

## Troubleshooting

### Key Not Found

**Problem:** `security find-generic-password` returns empty

**Diagnosis:**
```bash
# List all agenthub keys
security find-generic-password -a $USER -s "obsidian_api_key"

# Check keychain contents
security dump-keychain ~/Library/Keychains/login.keychain-db | grep -A5 "obsidian"
```

**Solution:**
```bash
# Re-add key
python3 scripts/security/manage-keys.py --add obsidian_api_key

# Verify
security find-generic-password -a $USER -s "obsidian_api_key" -w
```

### Permission Denied

**Problem:** Keychain access prompts for password repeatedly

**Solution:**
```bash
# Unlock keychain
security unlock-keychain ~/Library/Keychains/login.keychain-db

# Set timeout (1 hour)
security set-keychain-settings -t 3600 ~/Library/Keychains/login.keychain-db

# Allow terminal access
security set-key-partition-list \
  -S apple-tool:,apple: \
  -k "" \
  ~/Library/Keychains/login.keychain-db
```

### MCP Server Fails with Invalid Key

**Problem:** MCP server starts but fails authentication

**Diagnosis:**
```bash
# Test key manually
KEY=$(security find-generic-password -a $USER -s "obsidian_api_key" -w)
curl -H "Authorization: Bearer $KEY" https://api.obsidian.md/test

# Check key format
echo -n "$KEY" | wc -c  # Should be expected length
```

**Solution:**
```bash
# Rotate key
python3 scripts/security/manage-keys.py --rotate obsidian_api_key

# Test with new key
python3 scripts/security/manage-keys.py --test obsidian_api_key
```

## Advanced Usage

### Encrypted Key Export

```python
# Export with password
./manage-keys.py --export backup.enc --password "strong-password"

# Import with password
./manage-keys.py --import backup.enc --password "strong-password"
```

### Key Validation

```python
# validate_keys.py
import requests
from router.keyring_manager import KeyringManager

km = KeyringManager()

def validate_github_key():
    key = km.get_credential("github_api_key")
    r = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {key}"}
    )
    return r.status_code == 200

if __name__ == "__main__":
    if validate_github_key():
        print("✓ GitHub key valid")
    else:
        print("✗ GitHub key invalid")
```

### Automated Key Rotation

```bash
# rotate-keys.sh
#!/bin/bash
set -euo pipefail

SERVICES=("github" "obsidian" "openai")

for service in "${SERVICES[@]}"; do
  echo "Rotating ${service} key..."

  # Generate new key (service-specific logic)
  NEW_KEY=$(generate_new_key "$service")

  # Update Keychain
  python3 scripts/security/manage-keys.py --rotate "${service}_api_key" --value "$NEW_KEY"

  # Test new key
  python3 scripts/security/manage-keys.py --test "${service}_api_key"

  # Restart MCP servers
  python3 scripts/router/restart-mcp-servers.py "$service"

  echo "✓ ${service} key rotated"
done
```

## Related Documentation

- [Keyring Manager](../../router/keyring_manager.py)
- [Audit System](../../docs/audit/AUDIT-IMPLEMENTATION-COMPLETE.md)
- [MCP Server Configuration](../../configs/mcp-servers.json)
- [Security Best Practices](../../docs/security.md)
