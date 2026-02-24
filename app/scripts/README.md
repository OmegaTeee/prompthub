# PromptHub Scripts

Utility scripts for PromptHub development and operations.

## Directory Structure

```
scripts/
├── dev/                      # Development and testing
│   ├── cleanup.sh            # Remove temp files, caches (.DS_Store, __pycache__, etc.)
│   ├── run-tests.sh          # Test runner (unit, integration, coverage modes)
│   └── release.sh            # Version bump, changelog, git tag, GitHub release
├── launch_agents/            # macOS LaunchAgent plist
│   └── com.prompthub.router.plist  # Auto-start router on login
├── manual-tests/             # Interactive debugging scripts
│   ├── test_keyring_integration.py  # Verify Keychain credential access
│   └── test_security_alerts.py      # Trigger and verify alert patterns
├── router/                   # Router and MCP server management
│   ├── restart_mcp_servers.py       # Restart and verify servers (dynamic)
│   └── validate-mcp-servers.sh      # Check server binaries exist on disk
├── security/                 # Credential management
│   ├── manage-keys.py        # Add/remove/list keys in macOS Keychain
│   └── README.md
└── system/                   # System maintenance
    └── audit-maintenance.sh  # Log status, backup, rotation, integrity checks
```

## Quick Reference

```bash
# Validate all MCP server binaries exist
scripts/router/validate-mcp-servers.sh

# Restart all auto_start servers and verify
python3 scripts/router/restart_mcp_servers.py

# Restart a specific server
python3 scripts/router/restart_mcp_servers.py obsidian

# Run tests
scripts/dev/run-tests.sh              # All tests
scripts/dev/run-tests.sh unit         # Unit only
scripts/dev/run-tests.sh coverage     # With coverage

# Manage API keys
python3 scripts/security/manage-keys.py list
python3 scripts/security/manage-keys.py set obsidian_api_key

# Audit log maintenance
scripts/system/audit-maintenance.sh status
scripts/system/audit-maintenance.sh backup

# Clean temp files
scripts/dev/cleanup.sh --dry-run
```

## LaunchAgent Setup

To auto-start the router on login:

```bash
cp scripts/launch_agents/com.prompthub.router.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.prompthub.router.plist
```
