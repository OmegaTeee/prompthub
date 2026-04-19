 # Rewrite verification report — Glossary alignment

Generated: 2026-04-14

Editor quick-reference (canonical mapping): enhancement → `qwen3-4b-instruct-2507`, orchestrator (thinking) → `qwen3-4b-thinking-2507`.
When updating historical model names in prose, prefer adding parenthetical mappings
(e.g., "llama3.2 (now qwen3-4b-instruct-2507) (now qwen3-4b-instruct-2507)") instead of editing code blocks or
env keys. See `docs/architecture/ADR-008-task-specific-models.md` for the source of truth.

Summary
-------
- Files scanned: 94 (all files under `docs/`)
- Stale token scan: searched for `LLM`, `llm`, `gemma3`, `llama3.2`, `qwen2.5-coder`, `qwen3:14b` (case-insensitive)
- Grep results (partial due to tool result caps): 200+ matches found across the docs tree. Many `LLM`/`llm` occurrences remain and several model tokens flagged for manual review.

High-level findings
-------------------
- `LLM` / `llm` references are widespread (architecture ADRs, superpowers plans/specs, guides, templates). Many occurrences are deliberate migration notes (plans that mention old names) and some are in code-like examples that require careful edits.
- Model tokens found and flagged for manual review: `gemma3`, `llama3.2`, `qwen2.5-coder`, `qwen3:14b`. These appear in ADRs and model-selection docs and often require manual attention (benchmarks, tables, or migration notes).

Model tokens found and flagged for manual review: `gemma3`, `llama3.2`,
`qwen2.5-coder`, `qwen3:14b`. These appear in ADRs and model-selection docs and
often require manual attention (benchmarks, tables, or migration notes).

> NOTE: These model tokens are historical. The active enhancement/orchestrator
> models are documented in ADR-008 (`docs/architecture/ADR-008-task-specific-models.md`).
> Review the flagged files before applying automated replacements.

Current model mapping (for reviewer convenience): enhancement =
`qwen3-4b-instruct-2507`, orchestrator (thinking) = `qwen3-4b-thinking-2507`
(see `docs/architecture/ADR-008-task-specific-models.md`). These are the
canonical targets to prefer when migrating historical model names in prose.

Example parenthetical mappings (do not edit code blocks or env keys):

- `llama3.2 (now qwen3-4b-instruct-2507)`
- `gemma3 (now qwen3-4b-instruct-2507)`
- `qwen2.5-coder (now qwen3-4b-instruct-2507)`
- `qwen3:14b (now qwen3-4b-thinking-2507)`

Files with notable matches (non-exhaustive sample)
------------------------------------------------
- `docs/superpowers/specs/2026-03-24-lm-studio-backend-design.md` — numerous `LLM` references, route renames, and variable aliases (`OLLAMA_*`), plus instructions to rename templates. (manual rewrite candidate)
- `docs/superpowers/plans/2026-03-24-lm-studio-backend.md` — many `ollama_*` identifiers, code snippets, and TODOs referencing renames. (manual review)
- `docs/architecture/ADR-003-per-client-enhancement.md` — model assignments (`qwen2.5-coder`, `llama3.2`) and `/llm/enhance` route references. (requires verification of current model mapping)
- `docs/architecture/ADR-004-modular-monolith.md` — references to `OllamaClient` and enhancement module naming. (code-docs update)
- `docs/architecture/ADR-005-async-first.md` — examples using `ollama_client.generate(...)` (example code needs update).
- `docs/architecture/ADR-008-task-specific-models.md` — `gemma3` and `llama3.2` mentions in model rationale and tables. (manual review)
- `docs/architecture/ADR-009-orchestrator-agent.md` — notes that `qwen3:14b` was replaced; confirm final wording.
- `docs/guides/*` and `docs/notes/*` — scattered legacy mentions and environment-variable examples.

Manual-review candidates
------------------------
These files should be reviewed manually because automated token replacement would either be unsafe or insufficient (code samples, templates, diagrams, migration notes):

- `docs/superpowers/specs/2026-03-24-lm-studio-backend-design.md`
- `docs/superpowers/plans/2026-03-24-lm-studio-backend.md`
- `docs/architecture/ADR-003-per-client-enhancement.md`
- `docs/architecture/ADR-004-modular-monolith.md`
- `docs/architecture/ADR-005-async-first.md`
- `docs/architecture/ADR-008-task-specific-models.md`
- `docs/architecture/ADR-009-orchestrator-agent.md`
- Any `docs/*.yaml` (OpenAPI) entries referencing `/llm/*` paths

Automatable replacements (safe to script)
--------------------------------------
- Plain prose occurrences of the whole word `LLM` → `LLM` and `llm` → `llm` outside fenced code blocks and outside YAML keys where `OLLAMA_*` env vars must remain as documented legacy aliases.
- Update superficial UI strings in templates: `LLM Models` → `Local Models` (but preserve context where message explains backwards-compatibility).

Next actions performed (requested)
---------------------------------
You approved the verification step. I prepared and ran an initial scan and compiled this report. Because some environments/tooling blocked running the repository-side replacement script directly here, I did not apply automated edits yet.

Recommended next steps (pick one)
--------------------------------
1. Apply safe automated replacements now for prose-only occurrences (I can run patches to replace whole-word `LLM`→`LLM`, `llm`→`llm` outside fenced code blocks and skip the manual-review candidates). I will commit the changes and produce a second verification pass.
2. I generate a conservative PR that: (a) applies automated replacements, (b) lists manual-review files with short notes and TODO markers, and (c) leaves complex files untouched for manual editing.
3. Do nothing yet — you (or your team) manually review the files listed above and tell me which ones to change.

If you want me to proceed with (1) or (2), reply with "apply patches" or "make PR" and I will implement automated edits and produce a follow-up verification pass and commit/PR.

Appendix — tool note
--------------------
The on-repo script `scripts/docs_auto_replace.py` was created and is available to run locally; it performs replacements outside fenced code blocks and produces a JSON summary. Running it locally (from repo root):

```bash
python3 scripts/docs_auto_replace.py
```

This report is intentionally conservative: it highlights manual-review candidates and suggests a safe automation path rather than performing blind global replacements.
