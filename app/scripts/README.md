# PromptHub Scripts

This directory contains utility scripts for PromptHub development, deployment, and operations.

## Directory Structure

```
scripts/
├── README.md                 # This file
├── router/                   # Router and MCP server management
│   ├── README.md
│   ├── restart-mcp-servers.py
│   └── validate-mcp-servers.sh
├── dev/                      # Development and testing
│   ├── README.md
│   ├── run-tests.sh
│   ├── docker.sh
│   └── release.sh
├── security/                 # Credentials and key management
│   ├── README.md
│   ├── manage-keys.py
│   └── github-api-key.sh
├── system/                   # System integration and monitoring
│   ├── README.md
│   ├── audit-maintenance.sh
│   └── siem-forwarder.sh
└── mcps/                     # MCP server-specific wrappers
    ├── README.md
    ├── obsidian.sh
    ├── obsidian-rest.sh
    └── obsidian-mcp-tools.sh
```

## Script Categories

### ⚙️ Router Scripts (`router/`)
Scripts for managing PromptHub router and MCP servers.

**Use when:** Restarting servers, validating configurations, troubleshooting MCP issues.

### 🔧 Development Scripts (`dev/`)
Scripts for testing, building, and releasing PromptHub.

**Use when:** Running tests, building Docker images, preparing releases.

### 🔐 Security Scripts (`security/`)
Scripts for managing API keys and credentials via macOS Keychain.

**Use when:** Adding/updating API keys, rotating credentials, managing secrets.

### 🖥️ System Scripts (`system/`)
Scripts for system-level operations like audit log management and SIEM integration.

**Use when:** Maintaining audit logs, forwarding events to SIEM, system monitoring.

### 📦 MCP Scripts (`mcps/`)
Wrapper scripts for MCP servers that require special configuration or API keys.

**Use when:** Running MCP servers with Keychain-based API key management.

## Quick Reference

### Common Operations

**Validate MCP servers:**
```bash
scripts/router/validate-mcp-servers.sh
```

**Restart MCP servers:**
```bash
python3 scripts/router/restart-mcp-servers.py
```

**Run tests:**
```bash
scripts/dev/run-tests.sh
```

**Manage API keys:**
```bash
python3 scripts/security/manage-keys.py
```

**Maintain audit logs:**
```bash
scripts/system/audit-maintenance.sh
```

## API Key Management Pattern

All MCP wrapper scripts in `mcps/` follow a secure pattern using macOS Keychain:

1. **Retrieve key from Keychain**: Uses `security find-generic-password`
2. **Export as environment variable**: Sets the appropriate variable
3. **Exec the MCP server**: Replaces the shell process with the server binary

### Example: Obsidian MCP

```bash
#!/bin/bash
# Retrieve API key from Keychain
OBSIDIAN_API_KEY="$(security find-generic-password -a "${USER}" -s "obsidian_api_key" -w 2>/dev/null)"
export OBSIDIAN_API_KEY

# Validate key exists
if [[ -z "${OBSIDIAN_API_KEY}" ]]; then
    echo "Error: OBSIDIAN_API_KEY not found in Keychain" >&2
    echo "Add it with: security add-generic-password -a \$USER -s obsidian_api_key -w YOUR_KEY" >&2
    exit 1
fi

# Execute MCP server
exec "${HOME}/.local/share/prompthub/mcps/obsidian-mcp-tools/bin/mcp-server" "$@"
```

## Security Best Practices

1. **Never commit API keys**: Always use Keychain or environment variables
2. **Use restrictive permissions**: Scripts should be `chmod 700` (owner-only)
3. **Validate keys exist**: Check retrieval success before executing servers
4. **Use exec**: Replace shell process to avoid sensitive data in memory
5. **Audit access**: Use `scripts/system/audit-maintenance.sh` to track key usage

## Integration with PromptHub

Scripts reference configuration files:

- **MCP servers**: `configs/mcp-servers.json` references `mcps/*.sh` wrappers
- **Client configs**: `clients/` (at workspace root) contains setup scripts and configs
- **Enhancement rules**: `configs/enhancement-rules.json` affects client behavior
- **Audit logs**: `system/audit-maintenance.sh` manages logs in `logs/`

## Adding New Scripts

When adding new scripts, follow this organization:

1. **Determine category**: router, dev, security, system, or mcps
2. **Add to appropriate folder**: Place script in categorized subfolder
3. **Update README**: Document in both main and subfolder README
4. **Set permissions**: `chmod +x script-name.sh` and `chmod 700` for sensitive scripts
5. **Add tests**: Update `dev/run-tests.sh` if applicable

## Script Naming Conventions

- **Bash scripts**: Use kebab-case with `.sh` extension (`validate-mcp-servers.sh`)
- **Python scripts**: Use snake_case with `.py` extension (`manage_keys.py`)
- **Executables**: Mark with `chmod +x`
- **Wrappers**: MCP wrappers use descriptive names (`obsidian-mcp-tools.sh`)

## Documentation

For detailed usage of each category:
- [Client Scripts & Setup](../../clients/README.md)
- [Router Scripts](router/README.md)
- [Development Scripts](dev/README.md)
- [Security Scripts](security/README.md)
- [System Scripts](system/README.md)
- [MCP Scripts](mcps/README.md)

## Maintenance

- **Audit logs**: Rotated daily, kept for 30 days (see `system/audit-maintenance.sh`)
- **Test suite**: Run before each release (see `dev/run-tests.sh`)
- **Security review**: Review key access quarterly (see `security/manage-keys.py`)
- **Dependency updates**: Check for updates monthly (see `dev/docker.sh`)
