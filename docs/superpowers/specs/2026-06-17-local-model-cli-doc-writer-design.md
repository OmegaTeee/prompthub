---
type: design-spec
resource: local-model-cli-doc-writer
tags: [goose, aider, codex, okf, obsidian, llm-wiki, prompthub, local-models]
timestamp: 2026-06-17
status: draft
---

# Local-Model CLI Doc-Writer for the Obsidian Wiki

## Problem

The user wants a terminal CLI agent that writes and edits documents — specifically
**PR briefs/drafts** in the `~/Vault/LLM/` llm-wiki — driven by **local models** (via
PromptHub / LM Studio), not cloud Claude. The Max-plan `claude` command must stay
untouched for normal use; this is a *separate, deliberately-invoked* local-model writer.

A prior attempt (`claude-code-router`, now uninstalled) silently hijacked `claude` to
route everything through local models. This design replaces that anti-pattern with a
purpose-built, explicitly-invoked agent.

## Goal

Configure **Goose** (primary) plus **aider** and **codex** (comparison set) to:

1. Run on local models served through **PromptHub `/v1`** (`127.0.0.1:9090`).
2. Read and write Markdown notes in an Obsidian vault.
3. Emit notes in **OKF** (Open Knowledge Format): markdown + YAML frontmatter,
   git-versionable, graph-shaped via `[[wikilinks]]`.
4. Be **tested in `~/Vault/Scratch/`** (throwaway sandbox), then run for real against
   **`~/Vault/LLM/`** (the llm-wiki for PR briefs/drafts).

Out of scope (deferred to a separate project): **NotebookLM** content enhancement —
feeding finished OKF docs into NotebookLM for synthesis/audio. No public CLI/API for
the consumer product; it is a downstream workflow, not an engine to configure.

## Key Decisions (defaults — confirm at build time)

| Decision | Choice | Rationale |
|---|---|---|
| Backend | PromptHub `/v1` with a dedicated `api-keys.json` entry `enhance: false` | Keeps audit/privacy/model-routing; `enhance:false` stops PromptHub rewriting the agent's structured edit-loop messages mid-conversation |
| Agent model | `qwen3-coder-30b` (strongest local instruction-follower) | Edit-format / tool-call compliance needs headroom the 4B lacks |
| Primary engine | **Goose** | MCP-native (extensions = MCP servers → can use PromptHub bridge + Obsidian MCP directly), local-model friendly, already installed and explicitly requested |
| Comparison engines | aider (`--edit-format whole`), codex | Weaker-model-tolerant edit modes; A/B against Goose |
| Document format | **OKF** | markdown+YAML frontmatter, git-friendly, Obsidian-native; matches the wiki already |
| Conventions source | Derived from existing `~/Vault/LLM/` notes + OKF core keys | Fair, accurate to the real wiki |

## Architecture

```
┌─────────────┐   OpenAI /v1 (enhance:false)   ┌──────────────┐   ┌───────────┐
│  Goose CLI  │ ─────────────────────────────▶ │  PromptHub   │ ─▶│ LM Studio │
│ aider/codex │                                │  router 9090 │   │   :1234   │
└──────┬──────┘                                └──────────────┘   └───────────┘
       │ reads/writes .md (OKF)
       ▼
┌──────────────────────────┐        renders live
│ Vault (Scratch → LLM)    │ ──────────────────────▶  Obsidian
│  OKF markdown + frontmtr │
└──────────────────────────┘
```

Each engine is an independent unit with one purpose (write OKF notes into a vault dir),
configured through its own config file, sharing one conventions doc and one backend.

### Components

1. **PromptHub backend client** — a new `api-keys.json` entry (e.g.
   `client_name: "vault-writer"`, `enhance: false`) and matching `enhancement-rules.json`
   privacy entry (`local_only`). This is the only PromptHub-side change.

2. **Goose config** (`~/.config/goose/config.yaml`) — provider = OpenAI-compatible
   pointing at PromptHub `/v1`, model = `qwen3-coder-30b`, plus an Obsidian/PromptHub
   MCP extension. Hints in `.goosehints`.

3. **aider config** — `.aider.conf.yml` (or flags in the wrapper): `--openai-api-base`
   = PromptHub, `--model openai/qwen3-coder-30b`, `--edit-format whole`. Conventions in
   `CONVENTIONS.md`.

4. **codex config** — extend `~/prompthub/clients/codex/config.toml` with a
   `model_provider` block pointing at PromptHub. Conventions in `AGENTS.md`.

5. **Shared OKF conventions doc** — one source of truth (the OKF frontmatter contract +
   PR-brief body structure), surfaced to each engine via its native hints file
   (symlink or generated copies so the A/B is fair).

6. **Wrapper scripts** — `vault-goose`, `vault-aider`, `vault-codex`: `cd` into the
   chosen vault, launch the engine pre-configured. Default to Scratch; `--llm` flag (or
   env) targets `~/Vault/LLM/`.

## Data Flow

1. User runs `vault-goose` (or the wrapper picks the vault dir).
2. User prompts: "draft a PR brief for X."
3. Engine calls PromptHub `/v1` (raw, no enhancement) → LM Studio local model.
4. Engine writes/edits an OKF `.md` file in the vault dir.
5. Obsidian hot-reloads and renders the note live.
6. (aider) the edit is auto-committed to the vault's git repo for easy undo.

## Error Handling / Risks

- **Weak-model edit failures** — mitigated by Goose's robust loop + aider `whole` mode +
  using the 30B, not the 4B. If still unreliable, fall back to a larger local model or
  accept Goose-only.
- **Enhancement mangling the loop** — prevented by `enhance:false` on the backend client.
  Verify by inspecting PromptHub audit log for unrewritten passthrough.
- **Vault git state** — aider prefers a git repo; if the vault dir isn't one, either
  `git init` it or run aider `--no-git`. Decide per vault at build time.
- **Two-vault safety** — all destructive testing happens in Scratch; LLM vault only after
  an engine proves reliable.

## Testing / Acceptance

- A/B task: same scratch prompt ("draft a PR brief for <real change>") through all three
  engines.
- Judge on: (a) **valid OKF** (frontmatter keys present, parseable), (b) edit reliability
  (no broken/aborted writes), (c) prose quality.
- Acceptance: at least one engine reliably produces valid OKF PR-brief drafts in Scratch;
  user picks the winner; winner pointed at `~/Vault/LLM/`.

## Assumptions to verify at build time

- Goose is installed and uses `~/.config/goose/config.yaml`.
- LM Studio exposes `qwen3-coder-30b` (or the chosen id) and PromptHub routes to it.
- `~/prompthub/app/configs/api-keys.json` and `enhancement-rules.json` accept a new
  client entry in the documented shape.
- Whether Scratch / LLM vaults are git repos (affects aider).

## Sequencing

1. **This project** — configure Goose + aider + codex, OKF conventions, wrappers, A/B.
2. **Next project (separate brainstorm)** — NotebookLM enhancement over finished OKF docs.
