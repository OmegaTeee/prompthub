# Qwen Code doc-drift setup for PromptHub

This setup assumes:
- Repo: `~/prompthub` (symlink to the actual checkout)
- Qwen home: `~/.qwen`
- Provider: LM Studio at `http://127.0.0.1:1234`
- Model: `qwen3-4b-instruct-2507` (PromptHub's standard Qwen3 chat/enhancement model)
- Primary docs to guard: `AGENTS.md`, `README.md`, `QUICKSTART.md`, `CHANGELOG.md`, `docs/**`, `clients/README.md`, `clients/WORKFLOW.md`, `clients/TOOL_USE.md`, `scripts/README.md`, `app/README.md`, `app/AGENTS.md`

## 1) Qwen Code hook config

Create or merge into `/Users/visualval/.qwen/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/visualval/prompthub/scripts/doc-drift/qwen-stop-hook.sh"
          }
        ]
      }
    ]
  }
}
```

Notes:
- This uses a `Stop` hook so the check runs when Qwen Code is finishing a task.
- Keep the hook script in the repo so CI and local Git hooks can reuse the same logic.

## 2) Local Git hook

Create `.githooks/pre-commit` in the repo:

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
"$REPO_ROOT/scripts/doc-drift/check-doc-drift.sh" --staged
```

Enable it once:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
chmod +x scripts/doc-drift/check-doc-drift.sh
chmod +x scripts/doc-drift/qwen-stop-hook.sh
```

## 3) Shared checker script

The deterministic gate + optional LM Studio second-opinion lives in
[`scripts/doc-drift/check-doc-drift.sh`](../../scripts/doc-drift/check-doc-drift.sh).
Two modes:

- `--staged` — pre-commit mode, diffs `git diff --cached`.
- (no arg) — CI/Qwen mode, diffs against `origin/${GITHUB_BASE_REF:-main}`.

Tunable env vars:

| Var | Default | Purpose |
| --- | --- | --- |
| `DOC_DRIFT_SKIP` | unset | Set `=1` to bypass the check entirely (one-off escape hatch — works in pre-commit and CI). |
| `DOC_DRIFT_LMSTUDIO_URL` | `http://127.0.0.1:1234` | LM Studio OpenAI-compatible endpoint for the optional second-opinion pass. |
| `DOC_DRIFT_MODEL` | `qwen3-4b-instruct-2507` | Model name LM Studio should route to. Must be loaded in LM Studio. |

CI also honors `[doc-drift:ignore]` in the latest commit message — but **not** in pre-commit
mode, since the new commit doesn't exist yet when the hook runs. Use `DOC_DRIFT_SKIP=1` for
pre-commit bypass.

## 4) Qwen hook bridge script

[`scripts/doc-drift/qwen-stop-hook.sh`](../../scripts/doc-drift/qwen-stop-hook.sh) wraps the
shared checker and emits Qwen Code's expected `{"continue":..., "decision":..., "reason":...}`
JSON. The script derives `REPO_ROOT` from its own location, so it works for any checkout
without per-developer hardcoding.

## 5) GitHub Actions workflow

Create `.github/workflows/doc-drift.yml`:

```yaml
name: doc-drift

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  check-doc-drift:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run doc drift check
        run: bash scripts/doc-drift/check-doc-drift.sh
```

## 6) LM Studio endpoint

LM Studio exposes an OpenAI-compatible endpoint at `http://127.0.0.1:1234` by default.
The checker uses that URL with no extra config; override via `DOC_DRIFT_LMSTUDIO_URL` if
LM Studio is running on a non-default port or remote host.

The checker runs two passes:
- **Deterministic gate first** (always runs) — based on `CODE_PATTERNS` / `DOC_PATTERNS` / `IGNORE_PATTERNS`.
- **Optional Qwen review second** (only if curl can reach LM Studio) — fails the commit
  only if the model returns `"fail"`. Connection errors, timeouts (15s cap), and 404s on
  unknown models all silently pass — the deterministic gate is the source of truth.

## 7) PromptHub-specific tuning

The patterns in `check-doc-drift.sh` are the source of truth. As of this writing:

- **Code/runtime/config (triggers gate):** `app/`, `clients/`, `mcps/`, `scripts/`, `.github/workflows/`, `.mcp.json`, `llm.txt`, root README/QUICKSTART/AGENTS.
- **Docs (satisfies gate):** `README.md`, `QUICKSTART.md`, `AGENTS.md`, `CHANGELOG.md`, `docs/`, the various per-area README/AGENTS files.
- **Always exempt:** `docs/archive/`, `logs/`, `app/tests/`, any `*/tests/` directory, `*/test_*.py` files, `scripts/doc-drift/` (self-exemption to avoid the gate gating itself).

Good first rule (deliberately conservative): if anything outside the exempt set changes
without a doc update, the gate fires. Use `DOC_DRIFT_SKIP=1` for genuine no-op cases, or
add a CHANGELOG entry — that satisfies the gate and creates the changelog entry the project
already wants.

## 8) Notes about model choice

`qwen3-4b-instruct-2507` is the project's standard chat/enhancement model (see
`feedback_qwen3_chat_model.md` and `reference_lm_studio_models.md`). It runs comfortably on
an M3 Max with low latency — sufficient for a yes/no doc-drift judgment in JSON.

For fewer false positives at higher latency, swap to a larger Qwen3 instruct variant via
`DOC_DRIFT_MODEL`. The deterministic gate is unchanged regardless.
