# PromptHub Scripts

Utility scripts for PromptHub development and operations.

## Directory Structure

```
scripts/
├── dev/                             # Development and maintenance helpers
│   ├── cleanup.sh                   # Remove temp files, caches (.DS_Store, __pycache__, etc.)
│   ├── release.sh                   # Version bump, changelog, git tag, GitHub release
│   └── README.md                    # Dev-script notes
├── launch-agents/                   # macOS LaunchAgent plist files
│   ├── com.prompthub.router.plist   # Auto-start router on login
│   └── com.prompthub.openwebui.plist
├── manual-tests/                    # Interactive debugging scripts
│   ├── test_keyring_integration.py  # Verify Keychain credential access
│   └── test_security_alerts.py      # Trigger and verify alert patterns
├── open-webui/                      # Open WebUI lifecycle helpers
│   ├── start.sh
│   └── stop.sh
├── router/                          # Router and MCP server management
│   ├── restart_mcp_servers.py       # Restart and verify servers (dynamic)
│   ├── validate-mcp-servers.sh      # Check server binaries exist on disk
│   └── README.md
├── security/                        # Credential management
│   ├── manage-keys.py               # Add/remove/list keys in macOS Keychain
│   └── README.md
├── system/                          # System maintenance
│   ├── audit-maintenance.sh         # Log status, backup, rotation, integrity checks
│   └── README.md
├── diagnose.sh                      # Full stack health check (node, bridge, router, servers, clients)
├── prompthub-start.zsh              # Start the PromptHub router workflow
├── prompthub-kill.zsh               # Stop PromptHub router-related processes
├── test.sh                          # Primary repo test runner
└── README.md
```

## Quick Reference

```bash
# Start / stop PromptHub
./scripts/prompthub-start.zsh
./scripts/prompthub-kill.zsh

# Validate all MCP server binaries exist
./scripts/router/validate-mcp-servers.sh

# Restart all auto_start servers and verify
python3 scripts/router/restart_mcp_servers.py

# Restart a specific server
python3 scripts/router/restart_mcp_servers.py obsidian

# Diagnose the full stack
./scripts/diagnose.sh

# Run tests
./scripts/test.sh                 # Unit tests only by default
./scripts/test.sh unit            # Unit only
./scripts/test.sh integration     # Integration tests (requires live server)
./scripts/test.sh all             # Full test flow
./scripts/test.sh coverage        # With coverage
./scripts/test.sh watch           # Watch mode

# Manage API keys
python3 scripts/security/manage-keys.py list
python3 scripts/security/manage-keys.py set obsidian_api_key

# Audit log maintenance
./scripts/system/audit-maintenance.sh status
./scripts/system/audit-maintenance.sh backup

# Clean temp files
./scripts/dev/cleanup.sh --dry-run
```

## Notes

- `./scripts/test.sh` is the primary test wrapper currently present in the repo.
- Router-management scripts under `scripts/router/` assume the PromptHub router is reachable on `localhost:9090` when they call the HTTP API.

## LaunchAgent Setup

To auto-start the router on login:

```bash
cp scripts/launch-agents/com.prompthub.router.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.prompthub.router.plist
```
