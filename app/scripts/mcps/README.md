# MCP Server Wrapper Scripts

Secure wrapper scripts for MCP servers that require API keys or special environment configuration.

## Overview

These scripts follow a **secure API key pattern** using macOS Keychain:

1. **Retrieve** API key from Keychain (no plaintext storage)
2. **Validate** key exists before proceeding
3. **Export** as environment variable
4. **Exec** MCP server (replaces shell process for security)

This pattern ensures API keys never appear in:
- ✅ Shell history
- ✅ Process listings (`ps aux`)
- ✅ Git repositories
- ✅ Log files

## Scripts

### `obsidian-mcp-tools.sh`
Wrapper for Obsidian MCP server with API key from Keychain.

**Purpose:** Securely runs Obsidian MCP server with API authentication.

**Setup:**
```bash
# 1. Add API key to Keychain
security add-generic-password \
  -a $USER \
  -s "obsidian_api_key" \
  -w "YOUR_OBSIDIAN_API_KEY"

# 2. Make script executable
chmod +x scripts/mcps/obsidian-mcp-tools.sh

# 3. Configure in mcp-servers.json
# {
#   "obsidian": {
#     "command": "./scripts/mcps/obsidian-mcp-tools.sh",
#     "args": [],
#     "auto_start": true
#   }
# }
```

**Usage:**
```bash
# Direct invocation
scripts/mcps/obsidian-mcp-tools.sh

# Via AgentHub (auto-started)
curl -X POST http://localhost:9090/servers/obsidian/start

# Test manually
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | \
  scripts/mcps/obsidian-mcp-tools.sh
```

**Environment variables:**
- `OBSIDIAN_API_KEY` - Retrieved from Keychain
- `OBSIDIAN_VAULT_PATH` - Optional vault location

**Features:**
- Semantic search across Obsidian vault
- Template rendering
- File management (create, update, delete)
- Tag-based organization
- Backlink resolution

### `obsidian.sh`
Legacy Obsidian MCP wrapper (basic version).

**Purpose:** Simplified Obsidian wrapper without advanced features.

**Differences from obsidian-mcp-tools.sh:**
- No template support
- Basic file operations only
- Lighter weight

**When to use:**
- Need minimal Obsidian integration
- Don't require template features
- Want faster startup time

### `obsidian-rest.sh`
REST API wrapper for Obsidian MCP (example implementation).

**Purpose:** Demonstrates HTTP-based MCP server wrapper pattern.

**Usage:**
```bash
# Start REST server
scripts/mcps/obsidian-rest.sh --port 8080

# Query via HTTP
curl -X POST http://localhost:8080/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "search", "arguments": {"query": "neural networks"}}'
```

**Features:**
- HTTP transport (alternative to stdio)
- CORS support for web clients
- REST-style endpoints
- JSON request/response

**Note:** This is a **reference implementation**. For production, use stdio transport with AgentHub.

## Security Pattern

### Wrapper Script Template

```bash
#!/bin/bash
# Generic MCP wrapper with Keychain API key
# Replace SERVICE_NAME, KEY_NAME, ENV_VAR, and MCP_COMMAND

set -euo pipefail

# Configuration
SERVICE_NAME="myservice"
KEY_NAME="${SERVICE_NAME}_api_key"
ENV_VAR="MYSERVICE_API_KEY"
MCP_COMMAND="npx -y @myservice/mcp-server"

# Retrieve API key from Keychain
API_KEY="$(security find-generic-password -a "${USER}" -s "${KEY_NAME}" -w 2>/dev/null)"

# Validate key exists
if [[ -z "${API_KEY}" ]]; then
    echo "Error: ${KEY_NAME} not found in Keychain" >&2
    echo "" >&2
    echo "Add it with:" >&2
    echo "  security add-generic-password -a \$USER -s \"${KEY_NAME}\" -w \"YOUR_KEY\"" >&2
    echo "" >&2
    echo "Or use the key manager:" >&2
    echo "  python3 scripts/security/manage-keys.py --add ${KEY_NAME}" >&2
    exit 1
fi

# Export as environment variable
export "${ENV_VAR}=${API_KEY}"

# Audit log (optional)
# python3 -c "from router.audit import audit_credential_access; \
#             audit_credential_access('get', '${KEY_NAME}', 'success')"

# Execute MCP server (replaces shell process)
exec ${MCP_COMMAND} "$@"
```

### Why Use `exec`?

The `exec` command replaces the shell process with the MCP server:

**Without exec:**
```
bash wrapper.sh
  └─ node mcp-server.js   # Child process
     └─ API_KEY visible in shell environment
```

**With exec:**
```
node mcp-server.js   # Replaces shell directly
└─ API_KEY only in process environment
```

**Benefits:**
- No shell process lingering in memory
- Reduced attack surface
- Cleaner process tree
- Immediate resource cleanup on exit

## Adding New MCP Wrappers

### Step 1: Create Wrapper Script

```bash
# Create new wrapper
cat > scripts/mcps/github-mcp.sh << 'EOF'
#!/bin/bash
set -euo pipefail

GITHUB_TOKEN="$(security find-generic-password -a "${USER}" -s "github_api_key" -w 2>/dev/null)"

if [[ -z "${GITHUB_TOKEN}" ]]; then
    echo "Error: github_api_key not found in Keychain" >&2
    exit 1
fi

export GITHUB_TOKEN
exec npx -y @github/mcp-server "$@"
EOF

chmod +x scripts/mcps/github-mcp.sh
```

### Step 2: Add API Key

```bash
# Method 1: Direct Keychain
security add-generic-password \
  -a $USER \
  -s "github_api_key" \
  -w "ghp_YOUR_GITHUB_TOKEN"

# Method 2: Using key manager
python3 scripts/security/manage-keys.py --add github_api_key
```

### Step 3: Configure in AgentHub

```json
// configs/mcp-servers.json
{
  "github": {
    "package": "@github/mcp-server",
    "transport": "stdio",
    "command": "./scripts/mcps/github-mcp.sh",
    "args": [],
    "env": {},
    "auto_start": true,
    "restart_on_failure": true,
    "description": "GitHub repository access and code search"
  }
}
```

### Step 4: Test Wrapper

```bash
# Validate configuration
scripts/router/validate-mcp-servers.sh github

# Start server
curl -X POST http://localhost:9090/servers/github/start

# Test tool call
curl -X POST http://localhost:9090/mcp/github/tools/call \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: test" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## Integration with AgentHub

### Configuration Flow

```
configs/mcp-servers.json
  └─ command: "./scripts/mcps/obsidian-mcp-tools.sh"
      └─ Retrieves: obsidian_api_key from Keychain
          └─ Exports: OBSIDIAN_API_KEY
              └─ Executes: obsidian-mcp-tools binary
```

### Keyring Integration

```json
// configs/mcp-servers-keyring.json
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

AgentHub's KeyringManager automatically:
1. Reads `mcp-servers-keyring.json`
2. Retrieves keys from Keychain
3. Sets environment variables before starting MCP servers

## Troubleshooting

### Key Not Found Error

**Problem:**
```
Error: obsidian_api_key not found in Keychain
```

**Solution:**
```bash
# Add key
python3 scripts/security/manage-keys.py --add obsidian_api_key

# Or manually
security add-generic-password -a $USER -s "obsidian_api_key" -w "YOUR_KEY"

# Verify
security find-generic-password -a $USER -s "obsidian_api_key" -w
```

### MCP Server Fails to Start

**Problem:** Wrapper script runs but MCP server fails

**Diagnosis:**
```bash
# Check if binary exists
which npx

# Check Node.js version
node --version

# Test MCP package
npx -y @upstash/obsidian-mcp-tools --version

# Run wrapper with debug
bash -x scripts/mcps/obsidian-mcp-tools.sh
```

**Solution:**
```bash
# Install dependencies
cd mcps && npm install

# Check permissions
chmod +x scripts/mcps/*.sh

# Verify API key
KEY=$(security find-generic-password -a $USER -s "obsidian_api_key" -w)
echo "Key length: ${#KEY}"
```

### Authentication Failures

**Problem:** MCP server starts but API calls fail with 401 Unauthorized

**Diagnosis:**
```bash
# Test API key directly
KEY=$(security find-generic-password -a $USER -s "obsidian_api_key" -w)
curl -H "Authorization: Bearer $KEY" https://api.obsidian.md/test

# Check key format
echo -n "$KEY" | wc -c  # Should match expected length
echo "$KEY" | grep -E '^[a-zA-Z0-9]+$'  # Should be alphanumeric
```

**Solution:**
```bash
# Rotate key
python3 scripts/security/manage-keys.py --rotate obsidian_api_key

# Test new key
python3 scripts/security/manage-keys.py --test obsidian_api_key

# Restart MCP server
python3 scripts/router/restart-mcp-servers.py obsidian
```

## Advanced Patterns

### Multi-Key Wrappers

Some MCP servers require multiple API keys:

```bash
#!/bin/bash
# multi-key-wrapper.sh
set -euo pipefail

# Primary API key
API_KEY="$(security find-generic-password -a "${USER}" -s "service_api_key" -w 2>/dev/null)"
# Secondary secret
API_SECRET="$(security find-generic-password -a "${USER}" -s "service_api_secret" -w 2>/dev/null)"

if [[ -z "${API_KEY}" ]] || [[ -z "${API_SECRET}" ]]; then
    echo "Error: Missing API credentials" >&2
    exit 1
fi

export SERVICE_API_KEY="${API_KEY}"
export SERVICE_API_SECRET="${API_SECRET}"

exec npx -y @service/mcp-server "$@"
```

### Conditional Configuration

```bash
#!/bin/bash
# conditional-wrapper.sh
set -euo pipefail

API_KEY="$(security find-generic-password -a "${USER}" -s "api_key" -w 2>/dev/null)"
export API_KEY

# Development vs Production
if [[ "${AGENTHUB_ENV}" == "dev" ]]; then
    export SERVICE_URL="https://dev.service.com"
    export LOG_LEVEL="debug"
else
    export SERVICE_URL="https://api.service.com"
    export LOG_LEVEL="info"
fi

exec npx -y @service/mcp-server "$@"
```

### Health Check Integration

```bash
#!/bin/bash
# wrapper-with-health-check.sh
set -euo pipefail

API_KEY="$(security find-generic-password -a "${USER}" -s "api_key" -w 2>/dev/null)"
export API_KEY

# Pre-flight health check
if ! curl -sf -H "Authorization: Bearer $API_KEY" https://api.service.com/health > /dev/null; then
    echo "Error: Service health check failed" >&2
    exit 1
fi

exec npx -y @service/mcp-server "$@"
```

### Fallback API Keys

```bash
#!/bin/bash
# wrapper-with-fallback.sh
set -euo pipefail

# Try primary key
API_KEY="$(security find-generic-password -a "${USER}" -s "primary_api_key" -w 2>/dev/null)"

# Fallback to secondary
if [[ -z "${API_KEY}" ]]; then
    API_KEY="$(security find-generic-password -a "${USER}" -s "secondary_api_key" -w 2>/dev/null)"
fi

if [[ -z "${API_KEY}" ]]; then
    echo "Error: No API key found (tried primary and secondary)" >&2
    exit 1
fi

export API_KEY
exec npx -y @service/mcp-server "$@"
```

## Testing Wrappers

### Unit Test

```bash
# test-wrapper.sh
#!/bin/bash
set -euo pipefail

# Add test key
security add-generic-password -a $USER -s "test_api_key" -w "test-key-value"

# Run wrapper
output=$(scripts/mcps/test-wrapper.sh 2>&1)

if [[ "$output" == *"Error"* ]]; then
    echo "❌ Wrapper test failed"
    exit 1
fi

echo "✅ Wrapper test passed"

# Cleanup
security delete-generic-password -a $USER -s "test_api_key"
```

### Integration Test

```bash
# Test full MCP workflow
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | \
  scripts/mcps/obsidian-mcp-tools.sh | \
  jq -e '.result.tools | length > 0'
```

## Related Documentation

- [Security Scripts](../security/README.md)
- [MCP Server Configuration](../../configs/mcp-servers.json)
- [Keyring Manager](../../router/keyring_manager.py)
- [API Key Management Best Practices](../../docs/security.md)
