# Development Scripts

## Scripts

### `run-tests.sh`

Test runner with mode selection.

```bash
scripts/dev/run-tests.sh              # All tests (skips integration if router not running)
scripts/dev/run-tests.sh unit         # Unit tests only
scripts/dev/run-tests.sh integration  # Integration tests (requires router on :9090)
scripts/dev/run-tests.sh coverage     # All tests with coverage report
scripts/dev/run-tests.sh quick        # Unit tests, skip slow markers
```

### `cleanup.sh`

Remove temporary files, caches, and build artifacts.

```bash
scripts/dev/cleanup.sh --dry-run      # Preview what would be deleted
scripts/dev/cleanup.sh                # Actually delete
```

Targets: `__pycache__`, `.pyc`, `.DS_Store`, `.pytest_cache`, temp logs, editor swap files.

### `release.sh`

Automate version bumps, changelog generation, and GitHub releases.

```bash
scripts/dev/release.sh 0.2.0 "Add per-client tool filtering"
```

Steps: validate clean tree, update CHANGELOG.md, bump pyproject.toml version, commit, tag, push, create GitHub release via `gh`.
