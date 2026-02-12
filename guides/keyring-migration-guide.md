# Keyring Migration Guide

This guide explains how to migrate from bash wrapper scripts + `security` CLI to Python keyring integration for improved reliability.

## Problem Statement

**Current Architecture:**
```
Router → Bash script → security CLI → Keychain → Returns to script → MCP server
```

**Issues:**
- ❌ Bash scripts can fail in non-interactive contexts
- ❌ `security` CLI may not work without user session
- ❌ Complex error propagation
- ❌ macOS-only solution

**New Architecture:**
```
Router (Python) → keyring → Keychain → Directly to MCP server
```

**Benefits:**
- ✅ Router retrieves credentials in same process
- ✅ Better error handling and logging
- ✅ No bash script layer to fail
- ✅ Cross-platform support
- ✅ More reliable for dashboard/auto-start

---

## Prerequisites

1. **Install keyring package:**
```bash
# Uncomment in requirements.txt
sed -i '' 's/# keyring>=24.0.0/keyring>=24.0.0/' requirements.txt

# Install
source .venv/bin/activate
pip install keyring
```

2. **Test keyring access:**
```bash
source .venv/bin/activate
python -c "import keyring; print('Keyring available:', keyring.get_keyring())"
```

---

## Migration Steps

### 1. Migrate Existing Keys

Use the key manager CLI to migrate from `security` CLI to keyring:

```bash
# Make script executable
chmod +x scripts/manage-keys.py

# Migrate obsidian API key
./scripts/manage-keys.py migrate obsidian_api_key

# Verify migration
./scripts/manage-keys.py get obsidian_api_key
```

Or set keys directly:

```bash
# Interactive (secure - won't show in shell history)
./scripts/manage-keys.py set obsidian_api_key

# Direct (WARNING: will show in shell history)
./scripts/manage-keys.py set obsidian_api_key YOUR_KEY_HERE
```

### 2. Update Server Configuration

Change from bash wrapper to direct command with keyring env:

**Before:**
```json
{
  "obsidian": {
    "command": "./scripts/obsidian-mcp-tools.sh",
    "args": [],
    "env": {}
  }
}
```

**After:**
```json
{
  "obsidian": {
    "command": "./mcps/obsidian-mcp-tools/bin/mcp-server",
    "args": [],
    "env": {
      "OBSIDIAN_API_KEY": {
        "source": "keyring",
        "service": "agenthub",
        "key": "obsidian_api_key"
      },
      "OBSIDIAN_HOST": "https://127.0.0.1",
      "OBSIDIAN_PORT": "27124"
    }
  }
}
```

### 3. Update Router Code

The router needs to process keyring references in the env config.

**In `router/servers/manager.py` (or wherever you spawn MCP servers):**

```python
from router.keyring_manager import get_keyring_manager

def start_mcp_server(server_config: dict):
    """Start an MCP server with keyring credential resolution."""
    km = get_keyring_manager()

    # Process environment variables, retrieving from keyring as needed
    env = km.process_env_config(server_config.get("env", {}))

    # Spawn MCP server with resolved credentials
    process = subprocess.Popen(
        [server_config["command"]] + server_config["args"],
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return process
```

### 4. Test Configuration

```bash
# Check all keys are set
./scripts/manage-keys.py list

# Test router startup
uvicorn router.main:app --reload --port 9090

# Verify dashboard
curl http://localhost:9090/health
open http://localhost:9090/dashboard
```

---

## Managing Keys

### List All Keys
```bash
./scripts/manage-keys.py list
```

Output:
```
AgentHub Keys (service: agenthub):
--------------------------------------------------
obsidian_api_key               ✓ SET
github_api_key                 ✗ NOT SET
--------------------------------------------------
```

### Set a Key
```bash
# Interactive (secure)
./scripts/manage-keys.py set github_api_key
# Enter value for github_api_key: [hidden input]
# ✓ Stored: github_api_key

# Direct (shows in history - less secure)
./scripts/manage-keys.py set github_api_key ghp_xxxxxxxxxxxxx
```

### Get a Key
```bash
./scripts/manage-keys.py get obsidian_api_key
# YOUR_API_KEY_VALUE
```

### Delete a Key
```bash
./scripts/manage-keys.py delete obsidian_api_key
# Delete obsidian_api_key? (y/N): y
# ✓ Deleted: obsidian_api_key
```

---

## Configuration Examples

### Server with Single API Key

```json
{
  "my-mcp-server": {
    "command": "node",
    "args": ["./mcps/node_modules/my-mcp/index.js"],
    "env": {
      "API_KEY": {
        "source": "keyring",
        "service": "agenthub",
        "key": "my_mcp_api_key"
      }
    }
  }
}
```

### Server with Multiple Secrets

```json
{
  "complex-mcp": {
    "command": "python",
    "args": ["-m", "complex_mcp"],
    "env": {
      "API_KEY": {
        "source": "keyring",
        "service": "agenthub",
        "key": "complex_api_key"
      },
      "SECRET_TOKEN": {
        "source": "keyring",
        "service": "agenthub",
        "key": "complex_token"
      },
      "STATIC_CONFIG": "https://api.example.com"
    }
  }
}
```

### Python MCP Server

```json
{
  "python-mcp": {
    "command": "python",
    "args": ["-m", "mcp_module"],
    "env": {
      "PYTHON_API_KEY": {
        "source": "keyring",
        "service": "agenthub",
        "key": "python_mcp_key"
      }
    }
  }
}
```

---

## Troubleshooting

### Keyring Not Available
```bash
# Install keyring
pip install keyring

# Check backend
python -c "import keyring; print(keyring.get_keyring())"
```

### Key Not Found
```bash
# Verify key exists
./scripts/manage-keys.py get obsidian_api_key

# Set if missing
./scripts/manage-keys.py set obsidian_api_key
```

### Router Can't Access Keyring
```bash
# Ensure router runs in user session context
# Check logs for keyring errors
tail -f /path/to/router.log | grep keyring
```

### Migration from security CLI Failed
```bash
# Manually retrieve from security CLI
security find-generic-password -a $USER -s obsidian_api_key -w

# Set in keyring manually
./scripts/manage-keys.py set obsidian_api_key
```

---

## Backward Compatibility

During migration, you can support both approaches:

1. **Keep bash wrappers for manual testing:**
   - `scripts/obsidian-mcp-tools.sh` still works for standalone testing
   - Useful for debugging outside router context

2. **Router uses keyring:**
   - More reliable for dashboard/auto-start
   - Better error handling

3. **Gradual migration:**
   - Migrate servers one at a time
   - Test each before moving to next

---

## Security Considerations

### macOS Keychain Access
- keyring uses macOS Keychain as backend
- Requires same permissions as `security` CLI
- First access may prompt for keychain password

### Service Name
- All keys stored under service: `agenthub`
- Keeps keys organized and separate from other apps
- Can be changed in `keyring_manager.py`

### Key Storage
- Keys never stored in code or config files
- Retrieved at runtime from system keychain
- Stored in memory only during MCP server lifetime

### Cross-Platform
- macOS: Uses Keychain
- Windows: Uses Windows Credential Manager
- Linux: Uses Secret Service API (GNOME Keyring, KWallet)

---

## References

- [keyring Documentation](https://pypi.org/project/keyring/)
- [router/keyring_manager.py](../router/keyring_manager.py) - Implementation
- [scripts/manage-keys.py](../scripts/manage-keys.py) - Key management CLI
- [configs/mcp-servers-keyring.json.example](../configs/mcp-servers-keyring.json.example) - Configuration examples
