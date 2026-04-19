---
title: "LM Studio Enhancement Orchestration Sketch"
status: review
created: 2026-03-23
updated: 2026-04-09
tags: [research, lm-studio, enhancement, orchestration]
---

# LM Studio sketch for PromptHub enhancement orchestration

> **Research artifact:** This sketch captures an intermediate design exploration.
> Some lane names and config examples differ from the current implementation.
> Use it for background context, not as the current source of truth.

> FLAGGED: This research sketch contains historical model tokens (e.g.,
> `gemma3`, `qwen3:14b`). These are preserved for context. Consult
> `docs/architecture/ADR-008-task-specific-models.md` for current model
> assignments before applying automated replacements.

Editor quick-reference: enhancement → `qwen3-4b-instruct-2507`; orchestrator
→ `qwen3-4b-thinking-2507`. Prefer annotating historical model mentions with
the modern mapping (e.g., `qwen3:14b (now qwen3-4b-thinking-2507)`) to keep
historical accuracy while making user-facing docs clearer.

Here’s a concrete, LM‑Studio‑only sketch you can adapt. It assumes:

- Small model: Qwen3‑4B‑Instruct‑2507 (fast, no thinking).[^1]
- Reasoning lane: Qwen3‑4B‑Thinking‑2507 (opt‑in thinking).[^2]
- Big local agent (later): some Qwen3.5‑9B/14B you add via LM Studio.[^3]

***

## 1. Example “enhancement‑rules.json” (LM Studio endpoints)

Imagine you expose LM Studio via HTTP (or `lmstudio://` in your bridge). Rough sketch:

[enhancement-rules-sketch.json](../../../app/configs/enhancement-rules-sketch.json)

Key ideas:

- All default / high‑frequency stuff goes to **4B‑Instruct**, no thinking.[^1]
- A separate `reasoning_lane` is defined for **4B‑Thinking**, only used when the orchestrator opts in.[^4][^2]
- Claude clients skip enhancement entirely and just get your raw prompt.

***

## 2. Orchestrator sketch (Python‑style pseudo‑code)

You can drop something like this into your router’s agent module and adapt names:

```python
REASONING_TRIGGERS = [
    "step by step",
    "show your reasoning",
    "explain your reasoning",
    "think out loud",
    "detailed reasoning"
]

def wants_reasoning(prompt: str) -> bool:
    lower = prompt.lower()
    return any(t in lower for t in REASONING_TRIGGERS)


def choose_enhancement_model(client_id: str, intent: str, prompt: str):
    # 1. Claude clients: no enhancement
    if client_id in {"claude-desktop", "claude-code"}:
        return None  # pass-through

    # 2. Pure enhancement tasks (rewrite, clarify, small edit)
    if intent in {"enhancement", "text_rewrite", "small_change"}:
        if wants_reasoning(prompt):
            # Opt-in reasoning lane (Qwen3-4B-Thinking-2507)
            return {
                "model": "qwen3-4b-thinking-2507",
                "thinking": True,
                "temperature": 0.4,
                "max_tokens": 768
            }
        else:
            # Default small enhancer (Qwen3-4B-Instruct-2507)
            return {
                "model": "qwen3-4b-instruct-2507",
                "thinking": False,
                "temperature": 0.3,
                "max_tokens": 512
            }

    # 3. Code / workflow prompts (local agent path)
    if intent in {"code", "workflow"}:
        # For now, you can still use 4B-Instruct as a light agent
        # Later, swap this to your Qwen3.5-9B/14B model from LM Studio
        return {
            "model": "qwen3-4b-instruct-2507",
            "thinking": False,
            "temperature": 0.2,
            "max_tokens": 1024
        }

    # 4. Everything else: small model, no thinking
    return {
        "model": "qwen3-4b-instruct-2507",
        "thinking": False,
        "temperature": 0.3,
        "max_tokens": 512
    }
```

You’d then:

- Use `choose_enhancement_model(...)` before calling LM Studio’s `/v1/chat/completions`.
- Inject a **simple system prompt** for the small models, e.g.:

```python
system_prompt = (
    "You are a concise rewriting assistant. "
    "Rewrite or lightly edit the user's text as requested. "
    "Do not show intermediate reasoning or chain-of-thought."
)
```

- For the `thinking=True` case, you can optionally set a different system prompt to encourage structured explanations, but you still don’t need special tokens—Qwen3‑4B‑Thinking‑2507 already has the reasoning head.[^2][^4]

***

## 3. Testing inside LM Studio chat

Within LM Studio itself (no router):

- Create two models in the sidebar:
    - “Qwen3‑4B‑Instruct‑Enhancer” (temperature 0.2–0.3).[^5][^1]
    - “Qwen3‑4B‑Thinking‑Reasoner” (temperature 0.4, higher max tokens).[^6][^2]
- Manual testing pattern:
    - Use **Enhancer** for your usual “rewrite this prompt / clean this diff / format this doc” tasks.
    - Swap to **Reasoner** only when you explicitly want step‑by‑step explanation and to see how its thinking feels before wiring that lane into PromptHub.

Once you’re happy with how both behave, you can plug the exact model IDs and temps into the JSON/Python sketches above.

If you share the current shape of your [`enhancement-rules.json`](../../../app/configs/enhancement-rules-sketch.json) and orchestrator file later, I can map this directly onto your real filenames and keys so it’s a near drop‑in.
- This keeps your existing per‑client behavior and just swaps Gemma‑3‑4B for Qwen3‑4B‑Instruct‑2507.
- No “thinking” flags here, so the small model never runs in a special thinking mode by accident.

If you later decide to use Qwen3‑4B‑Thinking‑2507 as a reasoning lane, add a separate section like:

```json
  "lanes": {
    "reasoning": {
      "model": "qwen3-4b-thinking-2507",
      "temperature": 0.4,
      "max_tokens": 800,
      "privacy_level": "local_only"
    }
  }

```
and let your Python orchestrator opt into it explicitly based on trigger phrases.

<span style="display:none">[^10][^11][^12][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507

[^2]: https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507

[^3]: https://unsloth.ai/docs/models/qwen3.5

[^4]: https://dev.to/lukehinds/qwen3-4b-thinking-2507-just-shipped-4e0n

[^5]: https://lmstudio.ai/qwen3-4b-thinking-2507

[^6]: https://huggingface.co/lmstudio-community/Qwen3-4B-Thinking-2507-MLX-4bit

[^7]: llm-bge-m3-model-card.md

[^8]: llm-gemma3 (now qwen3-4b-instruct-2507)-4b-model-card.md

[^9]: llm-gemma3 (now qwen3-4b-instruct-2507)-27b-model-card.md

[^10]: llm-qwen3-14b-model-card.md

[^11]: llm-qwen3-coder-30b-model-card.md

[^12]: llm-qwen35-2b-model-card.md
