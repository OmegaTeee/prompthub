# Keyring vs Security CLI: Architecture Comparison

## Quick Answer

**For the dashboard reliability issues: Yes, use keyring!**

The router spawning bash scripts is causing failures. Moving credential retrieval into the Python router process will be significantly more reliable.

---

## Architecture Comparison

### Current: Bash Wrapper + Security CLI

```
┌─────────────────────────────────────────────────┐
│ Router (Python - FastAPI)                       │
│ http://localhost:9090/dashboard                 │
└─────────────────┬───────────────────────────────┘
                  │
                  │ subprocess.Popen()
                  ↓
┌─────────────────────────────────────────────────┐
│ Bash Script (obsidian-mcp-tools.sh)             │
│ - New process/environment                       │
│ - Different PATH, shell context                 │
└─────────────────┬───────────────────────────────┘
                  │
                  │ subprocess.run()
                  ↓
┌─────────────────────────────────────────────────┐
│ security CLI                                     │
│ - Requires user session                         │
│ - May fail in background context                │
│ - macOS-only                                    │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
           Keychain Access
                  │
                  ↓
        ❌ Multiple failure points
        ❌ Complex error propagation
        ❌ Session-dependent
```

### Proposed: Router + Keyring

```
┌─────────────────────────────────────────────────┐
│ Router (Python - FastAPI)                       │
│ http://localhost:9090/dashboard                 │
│                                                  │
│  1. Read config with keyring references         │
│  2. keyring.get_password("agenthub", "key")     │
│  3. Set environment variables                   │
│  4. Spawn MCP server directly                   │
└─────────────────┬───────────────────────────────┘
                  │ ✅ Same process
                  │ ✅ Direct keychain access
                  │ ✅ Better error handling
                  ↓
           Keychain Access
                  │
                  ↓
        ✅ Single, reliable path
        ✅ Cross-platform
        ✅ Session-independent (once unlocked)
```

---

## Why Dashboard Failures Occur

### Problem 1: Process Context
```bash
# When you run manually:
$ ./scripts/obsidian-mcp-tools.sh
✓ Works - has your user session, PATH, environment

# When router spawns it:
Router → subprocess → bash script
✗ Different environment, may lack session context
```

### Problem 2: Security CLI Requirements
```bash
# security CLI needs:
- User session active
- Keychain unlocked
- Proper permissions

# May fail when:
- Router runs as service/daemon
- No active terminal session
- SSH session or background process
```

### Problem 3: Error Propagation
```bash
Router spawns bash script
  → Bash calls security CLI
    → security fails (no error to router)
      → Bash script exits 1
        → Router sees "failed" but not why
          → Dashboard shows generic error
```

---

## Reliability Comparison

| Aspect | Bash + security CLI | Router + keyring |
|--------|---------------------|------------------|
| **Failure Points** | 3 layers (router → bash → security) | 1 layer (router → keyring) |
| **Error Handling** | ❌ Poor (lost across processes) | ✅ Excellent (Python exceptions) |
| **Session Dependency** | ❌ High (security CLI needs session) | ✅ Low (keyring more robust) |
| **Auto-start Reliability** | ❌ May fail on boot | ✅ Reliable |
| **Dashboard Reliability** | ❌ Often fails | ✅ Should work consistently |
| **Logging** | ❌ Hard to debug | ✅ Full Python logging |
| **Cross-platform** | ❌ macOS only | ✅ Works everywhere |

---

## Migration Recommendation

### Phase 1: Install and Test (Safe)
```bash
# 1. Install keyring
pip install keyring

# 2. Migrate one key
./scripts/manage-keys.py migrate obsidian_api_key

# 3. Test retrieval
./scripts/manage-keys.py get obsidian_api_key

# No changes to router yet - fully backward compatible
```

### Phase 2: Update Configuration (Low Risk)
```bash
# Update mcp-servers.json for one server
# Change from wrapper to direct command + keyring env

# Test manually before router integration
```

### Phase 3: Router Integration (Requires Code)
```python
# Add keyring_manager.py to router
# Update server spawning code to use process_env_config()

# Test thoroughly before production
```

### Phase 4: Complete Migration
```bash
# Migrate all servers
# Keep bash wrappers for manual testing
# Remove from auto-start config
```

---

## Cost-Benefit Analysis

### Effort Required
- **Low**: 2-3 hours
  - Install keyring: 5 minutes
  - Migrate keys: 10 minutes
  - Update configs: 30 minutes
  - Update router code: 1 hour
  - Testing: 1 hour

### Benefits Gained
- **High Value**:
  - ✅ Fixes dashboard startup issues
  - ✅ Reliable auto-start
  - ✅ Better error messages
  - ✅ Cross-platform support
  - ✅ Easier key management
  - ✅ Production-ready architecture

### Risks
- **Very Low**:
  - keyring uses same underlying Keychain
  - Keys don't need to move (same storage)
  - Bash wrappers can coexist during migration
  - Easy to rollback if issues

---

## Decision Matrix

| Your Priority | Recommendation |
|---------------|----------------|
| "Dashboard must work reliably" | ✅ **Migrate to keyring now** |
| "Need cross-platform support" | ✅ **Migrate to keyring now** |
| "Current setup works fine manually" | ⚠️ **Keep bash wrappers for now** |
| "macOS-only, manual testing only" | ⚠️ **Keep bash wrappers for now** |
| "Production deployment planned" | ✅ **Migrate to keyring now** |

---

## Quick Start: Test Keyring Now

```bash
# 1. Install (5 minutes)
pip install keyring

# 2. Test basic functionality (2 minutes)
./scripts/manage-keys.py set test_key
./scripts/manage-keys.py get test_key
./scripts/manage-keys.py delete test_key

# 3. Migrate one real key (2 minutes)
./scripts/manage-keys.py migrate obsidian_api_key
./scripts/manage-keys.py list

# 4. Test retrieval from Python (1 minute)
python3 << 'EOF'
from router.keyring_manager import get_keyring_manager
km = get_keyring_manager()
print("Key value:", km.get_credential("obsidian_api_key"))
EOF
```

If all tests pass, you have a reliable keyring setup and can proceed with router integration.

---

## Conclusion

**For your dashboard reliability issue: Yes, keyring will help significantly!**

The problem isn't the keychain storage itself, but the **architectural layer** where credentials are retrieved. Moving from:

```
Router → Bash → security CLI → Keychain
```

To:

```
Router → keyring → Keychain
```

Eliminates multiple failure points and makes the system much more reliable for background/service contexts like the dashboard.

**Recommended**: Proceed with keyring migration for production reliability.
