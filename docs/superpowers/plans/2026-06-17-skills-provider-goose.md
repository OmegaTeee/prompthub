# Skills Provider (Goose-first) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve the 56-skill curated long-tail to Goose **lazily** via `skills-mcp` (discover-then-load) instead of eagerly injecting a ~56K-token catalog, and prove Goose discovers + loads + *follows* a skill **autonomously** (no per-tool directive).

**Architecture:** `skills-mcp` (an MCP server, `npx -y skills-mcp -s <root>`) is wired into Goose as a stdio **extension** in the repo-managed `clients/goose/config.yaml`, scoped to the curated root + `~/.claude/skills`. It exposes `list_skills` / `get_skill`. Because Goose exposes MCP tools directly (no `tool_search` gating — the qwen-code friction the source Work Order hit), the two-step discover→load chain is expected to work autonomously. Validation is an *obedience proof*: a skill whose body demands an unguessable file write.

**Tech Stack:** Goose 1.37, `skills-mcp` (Node/npx, github.com/skills-mcp/skills-mcp), MCP stdio transport, local model `qwen3-coder-30b-a3b-instruct` via PromptHub `/v1`.

**Source Work Order:** `~/Vault/LLM/work-orders/skills-provider-mcp.md` (Goose-first path; the FastMCP-build + bridge-tier-1 + qwen-directive scope from the WO is intentionally OUT of this plan).

## Global Constraints

- **Goose-first only** — do NOT build a FastMCP server, register in `prompthub-bridge.js`, or add qwen `system_prompt` directives. Those are deferred (cross-client serving) until the Goose mechanism is proven.
- **Reuse, don't reimplement** — use `skills-mcp` as-is via `npx`; do not write skill-scanning/manifest code.
- **Superpowers skills stay native/eager** — this plan only affects the curated long-tail served to Goose; it does not change how Superpowers loads.
- **Definitions only** — the provider exposes skill text; it does not execute bundled scripts.
- **Proven invocation** (from `clients/claude/mcp.json`): `npx -y skills-mcp -s <dir>`; `-s` repeats for multiple scopes.
- Use `~/prompthub` (symlink) in docs/scripts, not `~/.local/share/prompthub`.

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `clients/goose/config.yaml` | Add `skills-mcp` stdio extension scoped to curated + claude roots | Modify |
| `~/.local/share/prompthub/skills-curated/test-obedience/SKILL.md` | Throwaway proof skill (unguessable token); removed after Task 2 | Create→delete |
| `mcps/README.md` | Document the Goose skills-mcp extension + how to add scopes | Modify |
| `~/Vault/LLM/Raw/skills-provider-goose-outcome.md` | Durable outcome note for wiki ingestion (closes the work-order loop) | Create |

---

## Task 1: Wire skills-mcp into Goose and confirm the tools appear

**Files:**
- Modify: `clients/goose/config.yaml` (add a `skills-mcp` entry under `extensions:`)

**Interfaces:**
- Produces: a running `skills-mcp` stdio extension exposing tools `list_skills` and `get_skill` to Goose.

- [ ] **Step 1: Add the extension to the Goose config**

Add this block under the top-level `extensions:` map in `clients/goose/config.yaml` (sibling to `developer`, `todo`, `prompthub-bridge`):

```yaml
  skills-mcp:
    enabled: true
    type: stdio
    name: skills-mcp
    cmd: npx
    args:
      - -y
      - skills-mcp
      - -s
      - /Users/visualval/.local/share/prompthub/skills-curated
      - -s
      - /Users/visualval/.claude/skills
    timeout: 300
    bundled: false
    available_tools: []
```

- [ ] **Step 2: Verify the YAML parses and the extension is present**

Run: `python3 -c "import yaml; d=yaml.safe_load(open('clients/goose/config.yaml')); e=d['extensions']['skills-mcp']; print('cmd', e['cmd'], '| scopes', [a for a in e['args'] if a.startswith('/')])"`
Expected: `cmd npx | scopes ['/Users/visualval/.local/share/prompthub/skills-curated', '/Users/visualval/.claude/skills']`

- [ ] **Step 3: Confirm skills-mcp starts and Goose sees its tools**

Run: `OPENAI_API_KEY=sk-prompthub-vault-writer-001 GOOSE_PROVIDER=openai GOOSE_MODEL=qwen3-coder-30b-a3b-instruct goose run -t "List the names of the tools provided by the skills-mcp extension." 2>&1 | tail -20`
Expected: output references `list_skills` and `get_skill` (Goose enumerates them). If `npx` must fetch `skills-mcp` first run, allow up to ~60s. If it errors `command not found: npx`, install Node or use the absolute npx path from `which npx`.

- [ ] **Step 4: Commit**

```bash
git add clients/goose/config.yaml
git commit -m "feat(goose): add skills-mcp extension (lazy skill discovery over curated roots)"
```

---

## Task 2: Obedience proof — Goose discovers, loads, and FOLLOWS a skill autonomously

This is the make-or-break task: it tests the Work Order's open hypothesis that a **non-gating** agent (Goose) succeeds where qwen-code failed.

**Files:**
- Create (throwaway): `~/.local/share/prompthub/skills-curated/test-obedience/SKILL.md`

- [ ] **Step 1: Create the proof skill (unguessable action)**

Write `~/.local/share/prompthub/skills-curated/test-obedience/SKILL.md` with exactly:

```markdown
---
name: test-obedience
description: Use when asked to run the skills obedience proof.
---

# Obedience Proof

Write the exact text `OBEDIENCE-OK-9F3K2Q` into a file named `obedience-proof.txt`
in the current working directory. Write the file to disk with your tools — do not
print the token in chat.
```

- [ ] **Step 2: Run the test FROM A CLEAN DIRECTORY with a purpose-only prompt (no tool names)**

The prompt must NOT name `list_skills`/`get_skill`/`test-obedience` — autonomous discovery means Goose finds it from the *purpose*.

Run:
```bash
rm -rf /tmp/skc-proof && mkdir -p /tmp/skc-proof && cd /tmp/skc-proof && \
OPENAI_API_KEY=sk-prompthub-vault-writer-001 GOOSE_PROVIDER=openai GOOSE_MODEL=qwen3-coder-30b-a3b-instruct GOOSE_MODE=auto \
  goose run -t "Run the skills obedience proof." 2>&1 | tail -20
```
Expected: Goose calls `list_skills`, then `get_skill` for `test-obedience`, then writes the file.

- [ ] **Step 3: Verify the proof passed (the token file exists with the exact token)**

Run: `cat /tmp/skc-proof/obedience-proof.txt`
Expected: `OBEDIENCE-OK-9F3K2Q`
- PASS → Goose autonomously discovered + loaded + followed the skill (hypothesis confirmed).
- FAIL (no file / wrong content) → capture the Goose output tail; record whether Goose (a) never called `list_skills` (discovery gap), (b) loaded but didn't act (obedience gap), or (c) the model stalled. This is a real finding, not a config error — report it before proceeding.

- [ ] **Step 4: Measure the context win (no eager catalog)**

Run: `cd /tmp/skc-proof && OPENAI_API_KEY=sk-prompthub-vault-writer-001 GOOSE_PROVIDER=openai GOOSE_MODEL=qwen3-coder-30b-a3b-instruct goose run -t "Reply with exactly: OK" 2>&1 | grep -iE "token|context|exceed" | tail -5; echo "exit ok"`
Expected: no `exceed_context_size_error` — baseline carries only the `list_skills`/`get_skill` schemas, not the ~56K skill catalog. (Goose does not eagerly aggregate `SKILL.md` files the way Claude Code / qwen-code do, so the bloat the WO describes should simply be absent here.)

- [ ] **Step 5: Remove the throwaway proof skill**

Run: `rm -rf ~/.local/share/prompthub/skills-curated/test-obedience && ls ~/.local/share/prompthub/skills-curated/ | wc -l`
Expected: `56` (curated set restored, no test residue).

- [ ] **Step 6: Commit (no repo files changed by the test — record the result in Task 3)**

No commit here; the proof is a runtime verification. Proceed to Task 3 to document the outcome.

---

## Task 3: Document the outcome and close the work-order loop

**Files:**
- Modify: `mcps/README.md` (add a "Goose skills-mcp extension" subsection)
- Create: `~/Vault/LLM/Raw/skills-provider-goose-outcome.md` (durable knowledge → Karpathy ingestion)

**Interfaces:**
- Consumes: the Task 2 proof result (pass/fail + observed behavior).

- [ ] **Step 1: Add a README section**

Append to `mcps/README.md`:

```markdown
## Goose skills-mcp extension (lazy skill loading)

Goose loads the curated skill long-tail on demand via `skills-mcp` (configured in
`clients/goose/config.yaml`), instead of eagerly injecting the ~56K-token catalog.
It exposes `list_skills` / `get_skill` over two scopes:
`~/.local/share/prompthub/skills-curated/` (56 skills) and `~/.claude/skills`.

Add a scope: append another `-s <dir>` pair to the extension's `args`.
Because Goose exposes MCP tools directly (no `tool_search` gating), an agent can
discover a skill by purpose and load only that skill's body — verified by the
obedience proof (`test-obedience` skill → token file).
```

- [ ] **Step 2: Write the durable outcome note for the wiki (Track A → Raw/)**

Per `wiki/schema/work-order-lifecycle.md`, durable knowledge goes to `Raw/` for plugin ingestion (NOT hand-authored into `wiki/`). Create `~/Vault/LLM/Raw/skills-provider-goose-outcome.md`:

```markdown
# Skills Provider — Goose lazy-loading outcome

The skills-provider Work Order's Goose-first path: skills-mcp wired as a Goose
extension over the curated 56-skill root serves skills lazily (`list_skills` /
`get_skill`), avoiding the ~56K eager catalog that overflowed local context on
Claude Code / qwen-code.

Key result: Goose (non-gating) <PASS|FAIL — fill from Task 2 Step 3> autonomous
discovery+load+obey — the friction in the original spike was qwen-code's
`tool_search` gating, not the server. With Goose, the single-tool / mandatory-
directive workarounds the Work Order designed for qwen were unnecessary.

Deferred (separate Work Order): promoting skills-mcp into prompthub-bridge as a
tier-1 meta-tool for cross-client serving (Cherry's empty Resources tab).
```
Replace `<PASS|FAIL ...>` with the actual Task 2 result before saving.

- [ ] **Step 3: Verify both files are well-formed**

Run: `tail -12 mcps/README.md && echo "---" && head -3 ~/Vault/LLM/Raw/skills-provider-goose-outcome.md`
Expected: the README section and the Raw note's H1 are present.

- [ ] **Step 4: Commit the repo doc (the vault Raw note is outside the repo)**

```bash
git add mcps/README.md
git commit -m "docs(mcps): document Goose skills-mcp lazy-loading extension"
```

- [ ] **Step 5: Update the Work Order status**

In `~/Vault/LLM/work-orders/skills-provider-mcp.md`, change `status: draft` → `status: in-progress` (Goose path landed; cross-client serving still open). This is the work-order-lifecycle transition.

---

## Notes / Out of scope (tracked for a future Work Order)

- **Cross-client serving** (FastMCP `SkillsDirectoryProvider` or skills-mcp promoted to `prompthub-bridge.js` tier-1) so Cherry / qwen-code / Open WebUI get skills too — fills the empty Resources tab in the bridge. Revisit after the Goose path is proven.
- **Ranking** beyond skills-mcp's built-in match (tag/substring v1 vs nomic@768 via Cherry KB) — deferred.
- **qwen-code directive + single `apply_playbook` tool** — only needed for the gated qwen-code path, not Goose.
