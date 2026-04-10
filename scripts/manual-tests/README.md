# Manual Test Scripts

Standalone scripts for interactive debugging. **Not** run by pytest — these are developer tools for verifying functionality with real-time output.

## Available Scripts

### [test_security_alerts.py](test_security_alerts.py)

Triggers security alert patterns to verify anomaly detection.

```bash
source app/.venv/bin/activate
python scripts/manual-tests/test_security_alerts.py
```

Tests: repeated failed operations (3+ failures), excessive credential access (5+ per minute), credential probing attempts.

## Automated Tests

For pytest-based testing, see `app/tests/integration/`. The keyring integration test was moved there (`app/tests/integration/test_keyring_integration.py`).

## When to Use

- Debugging keychain or security issues interactively
- Verifying alert thresholds with real-time output
- Demonstrating security features

For CI/CD, use `cd app && pytest tests/` instead.
