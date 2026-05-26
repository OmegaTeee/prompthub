# Coder-first rollout: Progressive Tool Disclosure + Separate Tool/Model Profiles + 3-slot model set (v3 creative deferred)

## Summary
Ship Progressive Tool Disclosure **Phase 1 first**, then ship a **combined PR** that implements Tool Profiles Phase 2 + Model Profiles (coder-first) together for easier testing. Model strategy is locked to a clean 3-slot setup (creative/design `Qwopus3.5-9B-v3-GGUF` explicitly deferred).

---

## Locked model set (3-slot)
- **Claude-feel (LobeChat / planning):** `Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-v2-GGUF`
- **Primary coding + tools worker (VS Code + MCP code tasks):** `Qwopus3.5-9B-Coder-GGUF`
- **Router daemon / always-on:** `Qwopus3.5-4B-v3-GGUF` (replaces `qwen3-4b-instruct-2507`)
- **Note:** Orchestrator uses `Qwopus3.5-4B-v3-GGUF` (with `/no_think`) to keep the 3-slot set clean.

---

## PR 1 — Progressive Tool Disclosure Phase 1 (bridge-only)
**Goal:** Reduce initial tool context while keeping all tools reachable in-session.

**Implementation (in `mcps/prompthub-bridge.js`)**
- Add env:
  - `TOOL_DISCLOSURE=full|progressive` (default `full`)
  - `TIER1_SERVERS=serverA,serverB` (default empty)
- Add per-session state: `activeServers: Set<string>` seeded with `tier1Servers`.
- Add meta-tools (short names, as chosen):
  - `discover_tools({ server?: string, query?: string })` → returns `{server, tool, description}` only (no schemas).
  - `load_server_tools({ server: string })` → adds to `activeServers` and emits `notifications/tools/list_changed`.
- Modify `tools/list`:
  - `full`: unchanged behavior + meta-tools
  - `progressive`: only tier-1 + loaded servers + meta-tools

**Acceptance checks**
- Progressive mode returns only tier-1 + the 2 new meta-tools.
- Loading a server triggers refresh and makes its tools callable.
- Manual client verification: Claude Desktop, Cherry Studio, VS Code.

**Docs**
- Update `docs/notes/plans/progressive-tool-disclosure.md` with Phase 1 tool names + env examples.

---

## PR 2 (combined) — Tool Profiles Phase 2 + Model Profiles (coder-first) + Dashboard read-only
### A) Tool Profiles (separate from model profiles)
- Extend `app/configs/enhancement-rules.json` per client:
  - `tool_profile: { disclosure: "full"|"progressive", tier1_servers: string[] }`
- Add endpoint:
  - `GET /clients/{name}/tool-profile` (new router module, e.g. `app/router/routes/clients.py`)
- Bridge startup behavior:
  - Prefer router profile when env vars not set; if router unreachable, fall back to `full`.

### B) Model Profiles (separate track, same config file)
- Add top-level in `app/configs/enhancement-rules.json`:
  - `model_profiles: { [name]: { model: string } }`
- Add per client:
  - `model_profile: string`
- Add endpoint:
  - `GET /clients/{name}/model-profile` returning `{ model_profile, resolved_model }`
- Wire into enhancement:
  - Update `app/router/enhancement/service.py` so the effective per-client `model` resolves via `model_profile` when present.

### C) Daemon model swap
- Update defaults and docs so router’s daemon model becomes `Qwopus3.5-4B-v3-GGUF` instead of `qwen3-4b-instruct-2507`.
- Ensure any repo-tracked client configs never contain real secrets (placeholders only).

### D) Dashboard (read-only)
- Update dashboard partial(s) that already parse `enhancement-rules.json` to display:
  - tool disclosure mode + tier-1 servers
  - model profile + resolved model
- No PATCH/write UI in this PR.

**Acceptance checks**
- Unit tests for `/clients/{name}/tool-profile` and `/clients/{name}/model-profile`.
- Unit test proving `EnhancementService.get_rule("vscode").model` resolves from `model_profile`.
- Manual sanity: `/llm/enhance` responds and reports expected model usage per client.

---

## Housekeeping deliverables (alongside PR 2 or as a tiny PR 0)
1) **Model downloader script**
- Add `scripts/models/download-qwen-distilled.sh` using `huggingface-cli download`.
- Configurable via `--config` pointing to an `.env`-style file (add `scripts/models/qwen-distilled.env.example`).
- Auth: prefer `HF_TOKEN`, also accept `HUGGINGFACE_API_KEY`.
2) **LM_API_TOKEN cleanup (keep alias)**
- Keep router code accepting `LM_API_TOKEN` as alias to `LLM_API_KEY`.
- Remove “legacy duplication” wording and docs that recommend `LM_API_TOKEN`; recommend `LLM_API_KEY` everywhere.
- Optional one-time startup warning when only `LM_API_TOKEN` is set.

---

## Assumptions / Defaults
- Creative/design option `Qwopus3.5-9B-v3-GGUF` is not implemented or referenced in profiles yet (deferred).
- We will treat Hugging Face model identifiers as configurable strings; the script/config will be the single swap point for deployment changes.
