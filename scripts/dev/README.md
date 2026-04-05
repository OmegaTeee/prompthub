# Development Scripts

## Scripts

### `test.sh`

Primary test runner with mode selection.

```bash
./scripts/test.sh              # Unit tests only by default
./scripts/test.sh unit         # Unit tests only
./scripts/test.sh integration  # Integration tests (requires router on :9090)
./scripts/test.sh all          # Full test flow
./scripts/test.sh coverage     # Unit tests with coverage report
./scripts/test.sh watch        # Re-run unit tests on file change
```

Notes:

- `./scripts/test.sh` is the current test wrapper present in the repository.
- Running `./scripts/test.sh` with no argument defaults to unit tests.
- Integration mode requires a live PromptHub router on port 9090.
- Watch mode requires `watchexec` to be installed.

### `cleanup.sh`

Remove temporary files, caches, and build artifacts.

```bash
./scripts/dev/cleanup.sh --dry-run      # Preview what would be deleted
./scripts/dev/cleanup.sh                # Actually delete
```

Targets: `__pycache__`, `.pyc`, `.DS_Store`, `.pytest_cache`, temp logs, editor swap files.

### `release.sh`

Automate version bumps, changelog generation, and GitHub releases.

```bash
./scripts/dev/release.sh 0.2.0 "Add per-client tool filtering"
```

Steps: validate clean tree, update CHANGELOG.md, bump pyproject.toml version, commit, tag, push, create GitHub release via `gh`.
