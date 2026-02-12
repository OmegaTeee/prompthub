# Keychain Integration Guide

> **For**: Secure credential storage across the AI Agent Hub and integrated applications

---

## Overview

The AI Agent Hub uses macOS Keychain to securely store sensitive credentials:

- API keys (Context7, custom integrations)
- Authentication tokens
- Database passwords
- Sensitive configuration values

Keychain provides:

- ✅ Secure storage (encrypted, OS-level)
- ✅ Transparent access (apps ask, user confirms once)
- ✅ No plaintext in config files
- ✅ Automatic encryption at rest

---

## What Gets Stored in Keychain

### Router-Level Credentials

| Credential              | Service             | Account              | Purpose                     |
| ----------------------- | ------------------- | -------------------- | --------------------------- |
| Context7 API Token      | `agenthub-context7` | `default`            | Library doc fetching        |
| DeepSeek API Token      | `agenthub-deepseek` | `default`            | Local reasoning (if cloud)  |
| Custom Integration Keys | `agenthub-custom`   | `{integration_name}` | User-defined MCP servers    |
| Database Credentials    | `agenthub-db`       | `{database_name}`    | If using persistent storage |

### App-Level Credentials

| App            | Service                 | Account   | Purpose                   |
| -------------- | ----------------------- | --------- | ------------------------- |
| Claude Desktop | `claude-desktop-router` | `default` | MCP server authentication |
| VS Code        | `vscode-router`         | `default` | MCP server authentication |
| Raycast        | `raycast-router`        | `default` | MCP server authentication |
| Obsidian       | `obsidian-router`       | `default` | MCP server authentication |

---

## Setup Instructions

### Step 1: Create Keychain Items (CLI)

Use the `security` command to add items to Keychain:

```bash
# Add Context7 API token
security add-generic-password \
  -s "agenthub-context7" \
  -a "default" \
  -w "your-context7-api-key-here" \
  ~/Library/Keychains/login.keychain-db

# Add custom integration token
security add-generic-password \
  -s "agenthub-custom" \
  -a "my-integration" \
  -w "your-custom-token-here" \
  ~/Library/Keychains/login.keychain-db

# Add database credentials
security add-generic-password \
  -s "agenthub-db" \
  -a "memory-store" \
  -w "db-password-here" \
  ~/Library/Keychains/login.keychain-db
```

### Step 2: Retrieve from Router Code

The router retrieves credentials programmatically:

```python
# Python example (router uses this pattern)
import subprocess
import json

def get_keychain_item(service: str, account: str) -> str:
    """Retrieve credential from Keychain"""
    cmd = [
        'security', 'find-generic-password',
        '-s', service,
        '-a', account,
        '-w',
        os.path.expanduser('~/Library/Keychains/login.keychain-db')
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    raise ValueError(f"Keychain item not found: {service}/{account}")

# Usage
context7_token = get_keychain_item("agenthub-context7", "default")
```

### Step 3: Reference in Router Config

Router config file (`~/.agenthub/config.json`) references Keychain:

```json
{
  "credentials": {
    "context7": {
      "type": "keychain",
      "service": "agenthub-context7",
      "account": "default"
    },
    "custom_integrations": [
      {
        "type": "keychain",
        "service": "agenthub-custom",
        "account": "my-integration"
      }
    ]
  }
}
```

---

## Managing Keychain Items

### View All Items

```bash
# Show all MCP-related Keychain entries
security dump-keychain -d login | grep agenthub
```

### Update a Credential

```bash
# Update existing Context7 token
security add-generic-password \
  -s "agenthub-context7" \
  -a "default" \
  -w "new-token-value" \
  -U \
  ~/Library/Keychains/login.keychain-db
```

### Delete a Credential

```bash
# Remove a Keychain item
security delete-generic-password \
  -s "agenthub-context7" \
  -a "default" \
  ~/Library/Keychains/login.keychain-db
```

### List Items (Human-Readable)

```bash
# Show Keychain Access GUI for manual inspection
open /Applications/Utilities/Keychain\ Access.app
# Search for "agenthub" to see all router credentials
```

---

## Security Best Practices

### ✅ DO

- ✅ Store all API keys in Keychain, never in config files
- ✅ Use Keychain Access app to verify items are encrypted
- ✅ Rotate credentials periodically (update Keychain item)
- ✅ Use unique services/accounts for different integrations
- ✅ Back up your Keychain when backing up your Mac

### ❌ DON'T

- ❌ Store credentials in JSON config files
- ❌ Commit API keys to Git
- ❌ Share Keychain passwords
- ❌ Use generic service names (be specific)
- ❌ Copy credentials in plaintext for debugging

---

## Troubleshooting

### "Keychain Item not found"

**Problem**: Router can't find credential in Keychain

**Solution**:

```bash
# Check if item exists
security find-generic-password \
  -s "agenthub-context7" \
  ~/Library/Keychains/login.keychain-db

# If not found, add it with Step 1 commands above
```

### "Permission denied" / Unlock Keychain

**Problem**: Keychain is locked

**Solution**:

```bash
# Unlock Keychain for 3600 seconds (1 hour)
security unlock-keychain ~/Library/Keychains/login.keychain-db

# Or open Keychain Access and unlock manually
```

### Router Can't Access Keychain After Update

**Problem**: macOS security prompt appears repeatedly

**Solution**: Grant permanent access via Keychain Access app:

1. Open Keychain Access (`/Applications/Utilities/`)
2. Select "login" keychain
3. Find `agenthub-*` items
4. Double-click each item → "Access Control" tab
5. Set "Allow all applications to access this item"

---

## Integration with LaunchAgent

When the router starts via LaunchAgent, it needs Keychain access without user interaction.

See **launchagent-setup.md** for configuration details on background access.

---

## Reference: Keychain Command Syntax

```bash
# Add generic password
security add-generic-password \
  -s <service> \
  -a <account> \
  -w <password> \
  [-U] \
  [keychain_path]

# Find password (returns password to stdout)
security find-generic-password \
  -s <service> \
  -a <account> \
  [-w] \
  [keychain_path]

# Delete password
security delete-generic-password \
  -s <service> \
  -a <account> \
  [keychain_path]
```

---

## See Also

- **launchagent-setup.md** — Background credential access
- **app-configs.md** — How apps use Keychain-stored credentials
- **comparison-table.md** — AI Agent Hub vs alternatives
