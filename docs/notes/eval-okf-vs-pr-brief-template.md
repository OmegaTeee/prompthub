# Evaluation: OKF vs the existing PR-brief template

**Date:** 2026-06-17
**Question:** Should the llm-wiki adopt OKF (Open Knowledge Format) for its documents, or keep the existing `briefs/_pr-brief-template.md` + `wiki/schema/` conventions?
**Recommendation:** **Keep the existing conventions. Do not adopt OKF wholesale.** Optionally borrow one idea (stable `resource` id) only if cross-tool portability becomes a real need.

## What each is

**OKF** (GoogleCloudPlatform/knowledge-catalog) — a generic, vendor-neutral format: markdown + YAML frontmatter, graph-linked, git-versionable. Core required keys: `type`, `resource` (stable id, == filename stem), `tags`, `timestamp`. Designed for *portable knowledge bundles* consumed by arbitrary tools.

**Existing llm-wiki** — a purpose-built system already in use:
- `briefs/_pr-brief-template.md` frontmatter: `type`, `created`, `status`, `owner`, `target_repo`, `sources`, `tags` + a rich 10-section body and a paste-ready agent-handoff block.
- `wiki/schema/config.md` two-track model: Track A knowledge (`Raw/` → Karpathy plugin ingests → `entities/`/`concepts/`/`sources/`) vs Track B hand-authored docs (`wiki/schema/`).
- `pr-brief-workflow.md` retrieval-first pipeline (cherry-mcp `search_knowledge` → curate → ingest → draft).

## Head-to-head

| Dimension | OKF (generic) | Existing template | Winner |
|---|---|---|---|
| Frontmatter richness | 4 generic keys | domain keys (`status`, `owner`, `target_repo`, `sources`) | **Existing** |
| Body structure | freeform | 10 prescribed sections + handoff | **Existing** |
| Date key | `timestamp` | `created` | cosmetic |
| Stable id | `resource` (== stem) | filename only | OKF (minor) |
| Wiki/plugin integration | none | Karpathy ingest, `[[wiki/...]]` graph, Track A/B | **Existing** |
| Tooling cost | new validator + migrate all briefs | zero (already in use) | **Existing** |
| Cross-tool portability | strong (its whole point) | vault-specific | OKF |

## Why keep existing

1. **It's strictly richer for the actual job.** PR briefs need `status`/`owner`/`target_repo`/`sources` and the prescribed sections; OKF's 4 keys are a subset that would *lose* information.
2. **It's wired into the pipeline.** The Karpathy plugin, `[[wiki/...]]` linking, and Track A/B rules assume the current shape. OKF has no equivalent and adopting it means rebuilding that integration.
3. **Migration cost with no payoff.** Adopting OKF means rewriting every existing brief, changing the validator, and updating `pr-brief-workflow.md` — for a format that does *less*. Portability (OKF's one real edge) isn't a need here: these briefs are consumed by Claude/Codex reading this vault, not shipped to third-party tools.

## The one borrowable idea

OKF's `resource` (an explicit, stable id decoupled from the filename) is mildly useful if a brief ever gets renamed but must keep a durable identity (e.g. external references). Cost to adopt: add an optional `resource:` key to `_pr-brief-template.md`. **Verdict: not worth it now** — filenames are already `lowercase-with-hyphens` and stable, and finished briefs archive to `briefs/done/` rather than being renamed in place.

## Disposition of the OKF artifacts built during the doc-writer work

`clients/vault-writer/OKF-CONVENTIONS.md` and `okf-validate.py` were scaffolding for the engine A/B. They are **not wired into the LLM vault** (Goose there reads `~/Vault/LLM/.goosehints`, which points at the real template). Options:
- **Keep** as a generic scratch-note format for `~/Vault/Scratch/` (harmless), or
- **Remove** to reduce clutter, per the "delete over annotate" docs policy.

Recommend removing them in a follow-up cleanup unless a generic OKF surface is wanted for non-brief notes — they serve no purpose in the production path.
