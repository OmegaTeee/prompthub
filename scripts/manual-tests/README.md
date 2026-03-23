# Manual Test Scripts

This directory contains standalone Python scripts for manual testing and debugging.

## Overview

These scripts are **not** run by pytest - they're interactive tools for developers to verify functionality during development.

## Available Scripts

### [test_keyring_integration.py](test_keyring_integration.py)

Tests macOS Keychain integration for credential management.

**Usage:**
```bash
source .venv/bin/activate
python scripts/manual-tests/test_keyring_integration.py
```

**What it tests:**
- Basic keyring functionality
- Credential retrieval
- Environment config processing
- MCP server config with keyring references

**Prerequisites:**
- API keys stored in macOS Keychain (see Obsidian vault: `~/Vault/PromptHub/Core Setup/Keychain.md`)

---

### [test_security_alerts.py](test_security_alerts.py)

Triggers security alert patterns to verify anomaly detection.

**Usage:**
```bash
source .venv/bin/activate
python scripts/manual-tests/test_security_alerts.py
```

**What it tests:**
- Repeated failed operations (3+ failures → alert)
- Excessive credential access (5+ accesses/minute → alert)
- Credential probing attempts

**Output:**
Prints alerts to console with severity, description, and context.

---

## Automated Tests

For automated testing with pytest, see [tests/integration/](../../tests/integration/).

The scripts in this directory correspond to pytest tests:
- `test_keyring_integration.py` → `tests/integration/test_keyring_integration.py`
- `test_security_alerts.py` → `tests/integration/test_security_alerts.py`

---

## When to Use Manual Scripts

Use these scripts when:
- **Debugging** keychain or security issues interactively
- **Verifying** credentials are properly stored
- **Testing** alert thresholds with real-time output
- **Demonstrating** security features to stakeholders

For CI/CD and regression testing, use `pytest tests/` instead.
