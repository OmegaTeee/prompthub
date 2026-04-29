# Qwen3 Role Map for PromptHub

Which Qwen3 model plays which role in PromptHub's request lifecycle. Lives
alongside [model-profiles-settings.md](model-profiles-settings.md) — that
file is about **per-model sampling settings**; this file is about
**per-role model assignments**. When they disagree, this file wins for
role decisions, the profiles file wins for sampling knobs.

See also [ADR-008](../../architecture/ADR-008-task-specific-models.md) for
the canonical current model assignments that both files should stay in
sync with.

---

## Roles

| Role                  | Model                        | Loaded in LM Studio | Triggered by                                 |
| --------------------- | ---------------------------- | ------------------- | -------------------------------------------- |
| **Chat / tools**      | `qwen3-4b-thinking-2507`     | Yes                 | User chat in LM Studio, Claude clients, etc. |
| **Prompt enhancement**| `qwen3-4b-instruct-2507`     | Yes                 | `POST /llm/enhance`, `/v1/chat/completions` when `enhance: true` |
| **Orchestrator**      | `qwen3-4b-thinking-2507`     | Yes *(shared)*      | `POST /llm/orchestrate` intent classification |
| **Text rewrite**      | `qwen3-0.6b`                 | Yes                 | Short-form text-editor prompt templates       |
| **Speculative draft** | `qwen3-0.6b`                 | Yes *(shared)*      | LM Studio's speculative decoding for `-4b-*`  |

**Settings env**: `LLM_MODEL=qwen3-4b-instruct-2507`, `LLM_ORCHESTRATOR_MODEL=qwen3-4b-thinking-2507` (see [app/.env](../../../app/.env) and [CLAUDE.md § Configuration](../../../CLAUDE.md#configuration-files)).

---

## Why split the 4B weights by reasoning mode

Qwen3-4B ships as two checkpoints from the same family:

- **`-thinking-2507`** — trained to emit `<think>...</think>` tags and
  internalize chain-of-thought. Better at multi-step reasoning, intent
  classification, and tool-call arbitration. Slower per-token because it
  thinks before answering.
- **`-instruct-2507`** — trained for direct instruction following.
  Faster, cleaner output, no `<think>` tags. Better at one-shot rewrites
  and templated transforms.

Enhancement is a **one-shot rewrite** task — thinking tokens would be
wasted overhead and could bleed into the rewritten output. Intent
classification and tool routing are **multi-step** decisions where the
thinking model's scratchpad earns its cost.

---

## Why `qwen3-0.6b` does two jobs

The 0.6B model is small enough to load once and serve two purposes with
no contention:

1. **Text rewrite prompt templates** (e.g.
   [clients/lm-studio/prompt_templates/qwick-text-editor.txt](../../../clients/lm-studio/prompt_templates/qwick-text-editor.txt))
   — grammar/clarity edits that don't need reasoning.
2. **Speculative decoding draft** for the 4B models. LM Studio's
   speculative decoding accepts a small draft model that proposes tokens
   the big model either accepts (fast path) or rejects (re-roll). 0.6B
   is the standard pairing for 4B Qwen3 checkpoints.

Keep it loaded alongside whichever 4B is active.

---

## LM Studio concurrent-load guidance

On a 36 GB Apple Silicon box with 28 GB Metal VRAM:

| Concurrent slots | Works | Notes                                                |
| ---------------- | ----- | ---------------------------------------------------- |
| `-thinking-2507` + `0.6b`  | Yes   | Thinking as chat model, 0.6B as draft + rewrite      |
| `-instruct-2507` + `0.6b`  | Yes   | Same, with instruct in place of thinking             |
| Both 4B + `0.6b`           | Tight | Only if context windows are capped (~8k each). Monitor VRAM |
| Both 4B + `0.6b` + embed   | No    | Drop one 4B; embeddings get their own slot elsewhere |

For PromptHub specifically, **load both 4Bs + 0.6B when you need
enhancement and orchestration simultaneously** — they're called on
distinct code paths and don't conflict.

---

## When to upgrade

Replace 4B with 7B/8B checkpoints only if:

- Tool-routing accuracy on `qwen3-4b-thinking-2507` drops below ~85% on a
  fixed eval set (currently no such eval — see TODO below).
- Enhancement output shows clear quality regressions on code-heavy or
  long-context prompts.

Don't upgrade proactively. The 4B+0.6B combo is deliberately chosen to
keep both loaded with headroom for MCP tool memory.

---

## TODO

- Fixed tool-routing eval set (`docs/notes/evals/tool-routing.md`) so
  model upgrades have an objective signal.
- Benchmark enhancement latency p50/p95 on `-instruct-2507` vs a potential
  `qwen3-1.7b` downgrade — smaller rewriter may be acceptable.
