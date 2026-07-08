---
slug: secrets-management-patterns
section: sources
status: archived-to-wiki
related: docs/features/MEMORY-SYSTEM-COMPLETE.md
---
# Secrets Management Patterns in PromptHub

**Date**: February 17, 2026
**Context**: Migration from bash `security` CLI to Python-native solutions

## Current Architecture

### Before (Bash Wrapper)

```bash
# Router spawns external script:
python router/main.py \
    "$(security find-generic-password -s MCP_SERVER_NAME)" \
    "$(security find-generic-password -s MCP_SERVER_PASSWORD)"
```

**Problems**:
- Non-deterministic timing (OSX security policy changes)
- Race conditions on concurrent spawns
- Error messages leak to stdout/stderr
- No circuit breaker for failed retrievals

### After: Keyring Integration

```python
# router/credential_resolver.py
def resolve_server_env(name: str) -> ServerConfig:
    """Resolve credentials using keyring with fallback chain."""
    keyring_secret = get_from_keyring(name)  # System keychain
    if keyring_secret:
        return keyring_secret

    env_secret = get_from_dotenv(name + "_KEY")  # Dev override
    if env_secret:
        return env_secret

    raise_cannot_resolve(name)  # Fail fast
```

## Best Practices Implemented

1. **Fail-fast with clear messages**: Don't leak secrets in errors; say "cannot resolve credentials" not the actual failure reason.

2. **Environment-aware fallbacks**:
   ```python
   import os
   if os.getenv("KEYRING_DISABLED"):
       return get_from_dotenv(name + "_KEY")
   ```

3. **Audit logging**: Every credential resolution is logged with PII-level redaction.

4. **No caching across sessions**: Fresh retrieval every time to prevent stale credential issues, but batched I/O within a single request for performance.

## Related Patterns

- `docs/architecture/ADR-008-task-specific-models.md` — Model assignment conventions (same principle: annotate historical names)
- `features/MEMORY-SYSTEM-COMPLETE.md` — Storage-boundary input guards for sensitive data
