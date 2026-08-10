# Local-Model CLI Doc-Writer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure Goose (primary), aider, and codex to write OKF-formatted Markdown documents in an Obsidian vault using local models served through PromptHub, testable in `~/Vault/Scratch/` and promotable to `~/Vault/LLM/`.

**Architecture:** Each engine is configured independently to call PromptHub `/v1` (`127.0.0.1:9090`) with a dedicated `enhance:false` API key, and to write OKF notes (markdown + YAML frontmatter) into a vault directory. A single canonical conventions doc is shared to all three via their native hint mechanisms. Wrappers (`vault-goose`/`vault-aider`/`vault-codex`) default to the Scratch sandbox; a flag targets the LLM vault. None of the changes alter the engines' default (non-vault) behavior.

**Tech Stack:** Goose 1.37, aider, codex, PromptHub router (FastAPI, OpenAI-compat `/v1`), LM Studio (`qwen3-coder-30b-a3b-instruct`), OKF (markdown+YAML), Obsidian.

**Verification model:** This is configuration work, not application code, so the test loop is **apply config → invoke the engine on a real scratch prompt → assert a valid OKF file appears**, not pytest. Each task ends with a concrete invocation and an OKF-validity check.

**Conventions about paths:** Use `~/prompthub` (the symlink) in all scripts and docs, never `~/.local/share/prompthub`.

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `~/prompthub/clients/goose/config.yaml` | Restore Goose's repo-managed config (provider→PromptHub, model, prompthub-bridge ext) | Create |
| `~/prompthub/app/configs/api-keys.json` | Add `vault-writer` client key (`enhance:false`) | Modify |
| `~/prompthub/clients/vault-writer/OKF-CONVENTIONS.md` | Canonical OKF + PR-brief conventions (single source of truth) | Create |
| `~/prompthub/clients/vault-writer/vault-goose` | Wrapper: Goose against local model, OKF, vault cwd | Create |
| `~/prompthub/clients/vault-writer/vault-aider` | Wrapper: aider `--no-git --edit-format whole`, OKF | Create |
| `~/prompthub/clients/vault-writer/vault-codex` | Wrapper: codex `--profile vault-writer` in vault cwd | Create |
| `~/prompthub/clients/vault-writer/okf-validate.py` | Tiny OKF frontmatter validator for the A/B test | Create |
| `~/prompthub/clients/codex/config.toml` | Add `[profiles.vault-writer]` + local `[model_providers.*]` (default `gpt-5.2` untouched) | Modify |
| `~/prompthub/clients/dotfiles/shell_common.sh` | Add `vault-goose`/`vault-aider`/`vault-codex` aliases to PATH | Modify |
| `~/Vault/Scratch/.goosehints`, `~/Vault/Scratch/AGENTS.md` | Symlinks → canonical conventions (engine-native hint files) | Create |

---

## Task 1: Restore Goose's repo-managed config

**Files:**
- Create: `~/prompthub/clients/goose/config.yaml`

The active symlink `~/.config/goose/config.yaml → ~/prompthub/clients/goose/config.yaml` is dangling. Recreate the target so Goose loads a valid config that routes model calls through PromptHub and keeps the prompthub-bridge extension. (Extension/permission blocks mirror the working `~/.config/goose/config.yaml.bak`.)

- [ ] **Step 1: Write the config file**

```yaml
# ~/prompthub/clients/goose/config.yaml
GOOSE_PROVIDER: openai
GOOSE_MODEL: qwen3-coder-30b-a3b-instruct
# Route model calls through PromptHub /v1 (audit + privacy), enhance disabled via the key below
OPENAI_HOST: http://127.0.0.1:9090
OPENAI_BASE_PATH: v1/chat/completions
OPENAI_TIMEOUT: '600'

extensions:
  developer:
    enabled: true
    type: platform
    name: developer
    bundled: true
    available_tools: []
  todo:
    enabled: true
    type: platform
    name: todo
    bundled: true
    available_tools: []
  prompthub-bridge:
    enabled: true
    type: stdio
    name: prompthub-bridge
    cmd: node
    args:
      - /Users/visualval/prompthub/mcps/prompthub-bridge.js
    timeout: 300
    envs:
      AUTHORIZATION: Bearer sk-prompthub-vault-writer-001
      CLIENT_NAME: vault-writer
      PROMPTHUB_URL: http://127.0.0.1:9090
      SERVERS: memory,sequential-thinking,desktop-commander,context7
    bundled: false
    available_tools: []
```

- [ ] **Step 2: Set the OpenAI API key Goose uses for the provider**

Goose reads `OPENAI_API_KEY` from env or its secrets store. Set it in the shell for the session (the wrappers in later tasks export it too):

Run: `export OPENAI_API_KEY=sk-prompthub-vault-writer-001`

- [ ] **Step 3: Verify the symlink now resolves and Goose parses the config**

Run: `ls -lL ~/.config/goose/config.yaml && goose info 2>&1 | head -20`
Expected: symlink resolves to the new file (no "No such file"); `goose info` prints provider `openai` and model `qwen3-coder-30b-a3b-instruct` without a parse error.

> NOTE: this Step depends on Task 2 (the `vault-writer` key) existing in `api-keys.json` for live calls, but config *parsing* works standalone. Do Task 2 before any live `goose session`.

- [ ] **Step 4: Commit**

```bash
git add clients/goose/config.yaml
git commit -m "fix(goose): restore repo-managed config routed through PromptHub vault-writer key"
```

---

## Task 2: Add the `vault-writer` PromptHub backend key

**Files:**
- Modify: `~/prompthub/app/configs/api-keys.json`

Add one client key with `enhance:false` so PromptHub passes the agents' edit-loop messages through raw (no prompt rewriting) while still logging to audit and applying the privacy boundary.

- [ ] **Step 1: Add the key entry**

Insert into the `"keys"` object (after the `codex` entry):

```json
    "sk-prompthub-vault-writer-001": {
      "client_name": "vault-writer",
      "description": "Local-model CLI doc-writer (Goose/aider/codex → OKF)",
      "enhance": false
    },
```

- [ ] **Step 2: Verify the router accepts the key end-to-end**

Run:
```bash
curl -s http://127.0.0.1:9090/v1/chat/completions \
  -H "Authorization: Bearer sk-prompthub-vault-writer-001" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3-coder-30b-a3b-instruct","messages":[{"role":"user","content":"Reply with the single word: OK"}],"max_tokens":5}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```
Expected: prints `OK` (a 401 means the router needs a restart to reload `api-keys.json` — restart via `launchctl kickstart -k gui/$(id -u)/com.prompthub.router` and retry).

- [ ] **Step 3: Commit**

```bash
git add app/configs/api-keys.json
git commit -m "feat(config): add vault-writer api key (enhance:false) for local-model doc agents"
```

---

## Task 3: Write the canonical OKF conventions doc

**Files:**
- Create: `~/prompthub/clients/vault-writer/OKF-CONVENTIONS.md`

One source of truth, shared to all three engines. Encodes the OKF frontmatter contract plus the PR-brief body shape. (Derived from the OKF spec's core keys; PR-brief sections are a sensible default — reconcile with real `~/Vault/LLM/` notes during Task 7 if they differ.)

- [ ] **Step 1: Write the conventions file**

````markdown
# OKF Conventions for Vault Documents

All documents you create or edit are **OKF** (Open Knowledge Format): a Markdown
file with YAML frontmatter. Follow these rules exactly.

## Required frontmatter (every file)

```yaml
---
type: <pr-brief | note | concept | reference>
resource: <kebab-case-stable-id>      # unique, stable, matches filename stem
tags: [<topic>, <topic>]              # 1-6 lowercase kebab tags
timestamp: <YYYY-MM-DD>               # date authored/last revised
---
```

Extra keys are allowed (e.g. `status`, `pr`, `author`) but the four above are mandatory.

## Body conventions

- First line after frontmatter is an `# H1` matching the document's human title.
- Use `[[wikilinks]]` to reference other notes (graph-shaped knowledge).
- Prefer short sections with `##` headers. No HTML.

## PR-brief body structure (`type: pr-brief`)

```markdown
# <Title>

## Summary
<2-3 sentences: what changes and why>

## Motivation
<the problem / context>

## Changes
- <bullet per notable change>

## Risks & Mitigations
- <risk> → <mitigation>

## Links
- [[related-note]]
```

## Hard rules

- Never write a file without complete required frontmatter.
- `resource` must equal the filename without `.md`.
- Keep prose tight; this is a brief, not an essay.
````

- [ ] **Step 2: Verify it is itself valid OKF (dogfood)**

Run: `head -6 ~/prompthub/clients/vault-writer/OKF-CONVENTIONS.md`
Expected: the file is documentation *about* OKF; it does not need its own frontmatter, but confirm the example block shows all four required keys.

- [ ] **Step 3: Commit**

```bash
git add clients/vault-writer/OKF-CONVENTIONS.md
git commit -m "docs(vault-writer): canonical OKF + PR-brief conventions"
```

---

## Task 4: OKF validator (shared A/B check)

**Files:**
- Create: `~/prompthub/clients/vault-writer/okf-validate.py`

A 30-line validator used as the "test" for every engine: does the produced file have the four required OKF keys and a matching `resource`?

- [ ] **Step 1: Write the validator**

```python
#!/usr/bin/env python3
"""Validate that a Markdown file is well-formed OKF. Exit 0 = valid."""
import sys, pathlib
try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

REQUIRED = {"type", "resource", "tags", "timestamp"}

def main(path: str) -> int:
    p = pathlib.Path(path)
    text = p.read_text(encoding="utf-8")
    if not text.startswith("---"):
        print(f"FAIL {p.name}: no YAML frontmatter"); return 1
    _, fm, _ = text.split("---", 2)
    meta = yaml.safe_load(fm) or {}
    missing = REQUIRED - set(meta)
    if missing:
        print(f"FAIL {p.name}: missing keys {sorted(missing)}"); return 1
    if meta["resource"] != p.stem:
        print(f"FAIL {p.name}: resource '{meta['resource']}' != filename stem '{p.stem}'"); return 1
    print(f"OK   {p.name}: valid OKF ({meta['type']})"); return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
```

- [ ] **Step 2: Verify it rejects a non-OKF file and accepts a good one**

Run:
```bash
printf '# no frontmatter\n' > /tmp/bad.md
python3 ~/prompthub/clients/vault-writer/okf-validate.py /tmp/bad.md; echo "exit=$?"
printf -- '---\ntype: note\nresource: good\ntags: [t]\ntimestamp: 2026-06-17\n---\n# Good\n' > /tmp/good.md
python3 ~/prompthub/clients/vault-writer/okf-validate.py /tmp/good.md; echo "exit=$?"
```
Expected: first prints `FAIL ... no YAML frontmatter` `exit=1`; second prints `OK   good.md: valid OKF (note)` `exit=0`.

- [ ] **Step 3: Commit**

```bash
git add clients/vault-writer/okf-validate.py
git commit -m "test(vault-writer): OKF frontmatter validator for engine A/B"
```

---

## Task 5: Goose wrapper + scratch smoke test

**Files:**
- Create: `~/prompthub/clients/vault-writer/vault-goose`
- Create: `~/Vault/Scratch/.goosehints` (symlink → conventions)

- [ ] **Step 1: Symlink the conventions as Goose's hint file in Scratch**

Run: `ln -sf ~/prompthub/clients/vault-writer/OKF-CONVENTIONS.md ~/Vault/Scratch/.goosehints`
Expected: `ls -lL ~/Vault/Scratch/.goosehints` shows it resolves to the conventions doc.

- [ ] **Step 2: Write the wrapper**

```bash
#!/usr/bin/env bash
# vault-goose — run Goose as the OKF doc-writer in a vault (default: Scratch sandbox)
set -euo pipefail
VAULT="${1:-$HOME/Vault/Scratch}"
[ "$VAULT" = "--llm" ] && VAULT="$HOME/Vault/LLM"
export OPENAI_API_KEY=sk-prompthub-vault-writer-001
export GOOSE_PROVIDER=openai
export GOOSE_MODEL=qwen3-coder-30b-a3b-instruct
cd "$VAULT"
exec goose session
```

- [ ] **Step 3: Make it executable**

Run: `chmod +x ~/prompthub/clients/vault-writer/vault-goose`

- [ ] **Step 4: Smoke test — drive Goose to write one OKF note in Scratch**

Run (non-interactive one-shot):
```bash
cd ~/Vault/Scratch && OPENAI_API_KEY=sk-prompthub-vault-writer-001 GOOSE_PROVIDER=openai GOOSE_MODEL=qwen3-coder-30b-a3b-instruct \
  goose run -t "Create a file scratch-okf-test.md following the OKF conventions in .goosehints. type: note, resource: scratch-okf-test, tags: [test], timestamp: 2026-06-17. One sentence body."
```
Expected: `~/Vault/Scratch/scratch-okf-test.md` exists.

- [ ] **Step 5: Validate the output is real OKF**

Run: `python3 ~/prompthub/clients/vault-writer/okf-validate.py ~/Vault/Scratch/scratch-okf-test.md`
Expected: `OK   scratch-okf-test.md: valid OKF (note)`

- [ ] **Step 6: Commit**

```bash
git add clients/vault-writer/vault-goose
git commit -m "feat(vault-writer): vault-goose wrapper (Goose → OKF, Scratch default)"
```

---

## Task 6: aider wrapper + scratch smoke test

**Files:**
- Create: `~/prompthub/clients/vault-writer/vault-aider`

aider needs `--no-git` (vaults are not git repos) and `--edit-format whole` (tolerant of local models). Conventions are passed read-only via `--read`.

- [ ] **Step 1: Write the wrapper**

```bash
#!/usr/bin/env bash
# vault-aider — run aider as the OKF doc-writer in a vault (default: Scratch sandbox)
set -euo pipefail
VAULT="${1:-$HOME/Vault/Scratch}"
[ "$VAULT" = "--llm" ] && VAULT="$HOME/Vault/LLM"
CONV="$HOME/prompthub/clients/vault-writer/OKF-CONVENTIONS.md"
cd "$VAULT"
exec aider \
  --no-git \
  --edit-format whole \
  --openai-api-base http://127.0.0.1:9090/v1 \
  --openai-api-key sk-prompthub-vault-writer-001 \
  --model openai/qwen3-coder-30b-a3b-instruct \
  --read "$CONV" \
  --yes-always
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x ~/prompthub/clients/vault-writer/vault-aider`

- [ ] **Step 3: Smoke test — drive aider to write one OKF note in Scratch**

Run (one-shot message mode):
```bash
cd ~/Vault/Scratch && aider --no-git --edit-format whole \
  --openai-api-base http://127.0.0.1:9090/v1 --openai-api-key sk-prompthub-vault-writer-001 \
  --model openai/qwen3-coder-30b-a3b-instruct \
  --read ~/prompthub/clients/vault-writer/OKF-CONVENTIONS.md --yes-always \
  --message "Create aider-okf-test.md as OKF. type: note, resource: aider-okf-test, tags: [test], timestamp: 2026-06-17. One sentence body."
```
Expected: `~/Vault/Scratch/aider-okf-test.md` exists.

- [ ] **Step 4: Validate the output**

Run: `python3 ~/prompthub/clients/vault-writer/okf-validate.py ~/Vault/Scratch/aider-okf-test.md`
Expected: `OK   aider-okf-test.md: valid OKF (note)`

- [ ] **Step 5: Commit**

```bash
git add clients/vault-writer/vault-aider
git commit -m "feat(vault-writer): vault-aider wrapper (aider → OKF, --no-git/whole)"
```

---

## Task 7: codex `vault-writer` profile + wrapper + scratch smoke test

**Files:**
- Modify: `~/prompthub/clients/codex/config.toml`
- Create: `~/prompthub/clients/vault-writer/vault-codex`
- Create: `~/Vault/Scratch/AGENTS.md` (symlink → conventions)

Add a local model provider and a profile; leave the global `model = "gpt-5.2"` untouched so normal `codex` is unaffected. Invoke via `codex --profile vault-writer`.

- [ ] **Step 1: Append the provider + profile to config.toml**

```toml
[model_providers.prompthub-local]
name = "PromptHub local"
base_url = "http://127.0.0.1:9090/v1"
env_key = "PROMPTHUB_VAULT_KEY"
wire_api = "chat"

[profiles.vault-writer]
model = "qwen3-coder-30b-a3b-instruct"
model_provider = "prompthub-local"
model_reasoning_effort = "low"
```

- [ ] **Step 2: Symlink conventions as codex's AGENTS.md in Scratch**

Run: `ln -sf ~/prompthub/clients/vault-writer/OKF-CONVENTIONS.md ~/Vault/Scratch/AGENTS.md`
Expected: resolves to the conventions doc.

- [ ] **Step 3: Write the wrapper**

```bash
#!/usr/bin/env bash
# vault-codex — run codex (vault-writer profile) in a vault (default: Scratch sandbox)
set -euo pipefail
VAULT="${1:-$HOME/Vault/Scratch}"
[ "$VAULT" = "--llm" ] && VAULT="$HOME/Vault/LLM"
export PROMPTHUB_VAULT_KEY=sk-prompthub-vault-writer-001
cd "$VAULT"
exec codex --profile vault-writer
```

- [ ] **Step 4: Make it executable**

Run: `chmod +x ~/prompthub/clients/vault-writer/vault-codex`

- [ ] **Step 5: Smoke test — drive codex to write one OKF note in Scratch**

Run (non-interactive exec mode):
```bash
cd ~/Vault/Scratch && PROMPTHUB_VAULT_KEY=sk-prompthub-vault-writer-001 \
  codex --profile vault-writer exec \
  "Create codex-okf-test.md as OKF per AGENTS.md. type: note, resource: codex-okf-test, tags: [test], timestamp: 2026-06-17. One sentence body."
```
Expected: `~/Vault/Scratch/codex-okf-test.md` exists.

- [ ] **Step 6: Validate the output**

Run: `python3 ~/prompthub/clients/vault-writer/okf-validate.py ~/Vault/Scratch/codex-okf-test.md`
Expected: `OK   codex-okf-test.md: valid OKF (note)`

- [ ] **Step 7: Commit**

```bash
git add clients/codex/config.toml clients/vault-writer/vault-codex
git commit -m "feat(vault-writer): codex vault-writer profile + wrapper (default gpt-5.2 untouched)"
```

---

## Task 8: PATH aliases

**Files:**
- Modify: `~/prompthub/clients/dotfiles/shell_common.sh`

- [ ] **Step 1: Append aliases**

```bash
# --- vault-writer: local-model OKF doc agents -------------------------------
alias vault-goose="$HOME/prompthub/clients/vault-writer/vault-goose"
alias vault-aider="$HOME/prompthub/clients/vault-writer/vault-aider"
alias vault-codex="$HOME/prompthub/clients/vault-writer/vault-codex"
```

- [ ] **Step 2: Verify they resolve in a fresh shell**

Run: `zsh -ic 'source ~/prompthub/clients/dotfiles/shell_common.sh; type vault-goose vault-aider vault-codex'`
Expected: each prints `... is an alias for .../clients/vault-writer/vault-<engine>`.

- [ ] **Step 3: Commit**

```bash
git add clients/dotfiles/shell_common.sh
git commit -m "feat(dotfiles): vault-goose/aider/codex aliases"
```

---

## Task 9: A/B comparison + promote winner to the LLM vault

**Files:**
- (No new files; uses the three test notes + validator.)

- [ ] **Step 1: Run the same real prompt through all three engines in Scratch**

Use a real upcoming change as the brief subject. For each engine, run its one-shot mode (as in Tasks 5–7) with the message:
`"Draft pr-brief-demo.md as an OKF pr-brief for: <describe a real recent change>. Fill every PR-brief section."`
(Write to distinct filenames per engine, e.g. `pr-brief-demo-goose.md`, `-aider.md`, `-codex.md`.)

- [ ] **Step 2: Validate all three and compare**

Run: `for f in ~/Vault/Scratch/pr-brief-demo-*.md; do python3 ~/prompthub/clients/vault-writer/okf-validate.py "$f"; done`
Expected: note which engines produced valid OKF. Then read the three files and judge prose quality + section completeness.

- [ ] **Step 3: Record the decision**

Decide the winner on (a) valid-OKF reliability, (b) prose quality, (c) edit smoothness. If prose is weak across the board, retry the winner with an Opus-distilled model by exporting `GOOSE_MODEL=qwopus3.6-27b-v2` (Goose) / changing `--model openai/qwopus3.6-27b-v2` (aider) / the profile `model` (codex), and re-judge.

- [ ] **Step 4: Point the winner at the real vault and confirm conventions match**

Run: `ln -sf ~/prompthub/clients/vault-writer/OKF-CONVENTIONS.md ~/Vault/LLM/.goosehints && ln -sf ~/prompthub/clients/vault-writer/OKF-CONVENTIONS.md ~/Vault/LLM/AGENTS.md`
Then read 1-2 existing `~/Vault/LLM/` PR briefs; if their frontmatter differs from the OKF contract, update `OKF-CONVENTIONS.md` to reconcile and commit.

- [ ] **Step 5: Real run + validate**

Run `vault-<winner> --llm`, draft a real PR brief, then validate it with `okf-validate.py`.
Expected: a valid OKF PR brief lands in `~/Vault/LLM/`, rendered live in Obsidian.

- [ ] **Step 6: Commit any conventions reconciliation**

```bash
git add clients/vault-writer/OKF-CONVENTIONS.md
git commit -m "docs(vault-writer): reconcile OKF conventions with live LLM vault briefs"
```

---

## Deferred (separate project)

**NotebookLM content enhancement** — feed finished OKF docs into NotebookLM for synthesis/audio overviews. No public CLI/API for the consumer product; design as its own brainstorm once OKF docs exist to feed it.

## Notes / Open choices surfaced during planning

- **Backend:** plan uses PromptHub `/v1` (audit + privacy). The pre-existing Goose `.bak` pointed straight at LM Studio `:1234`; if PromptHub adds latency or trouble, swap `OPENAI_HOST`/`--openai-api-base`/`base_url` to `http://127.0.0.1:1234/v1` to go direct.
- **Model:** default `qwen3-coder-30b-a3b-instruct` for edit-reliability; Opus-distilled `qwopus3.6-27b-v2` / `qwen3.5-27b-claude-4.6-opus-reasoning-distilled-v2` are prose-stronger alternates (Task 9 Step 3).
- **git in vaults:** neither vault is a git repo; aider runs `--no-git`. If you later want per-note undo history, `git init` the LLM vault and drop `--no-git`.
