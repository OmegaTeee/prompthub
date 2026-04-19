Here’s a concrete set of “fast / general / thinking / code” profiles built around the Qwen3 models you already have. You can map these directly into PromptHub/OpenAI-style model names.

I’ll assume you’re using an OpenAI-compatible schema (temperature, top_p, presence_penalty, frequency_penalty, max_tokens).

> FLAGGED: This model profiles document was flagged by the rewrite verification
> pass for historical model tokens (e.g., `qwen2.5-coder`). These are kept for
> historical context. Consult `docs/architecture/ADR-008-task-specific-models.md`
> for the canonical current model assignments before making automated
> replacements.

Quick mapping (editor reference): enhancement → `qwen3-4b-instruct-2507`,
orchestrator → `qwen3-4b-thinking-2507`. If you update specific model names in
this document, prefer adding parenthetical mappings such as
`qwen2.5-coder (now qwen3-4b-instruct-2507)`.

***

## 1) `fast` – Qwen3‑1.7B (chat, routing, low-stakes)

**Intended use**

- Quick chat, routing decisions, small transforms.
- Low latency, small context, low GPU load.

**Model**

- Backend: `qwen3-1.7b` (LM Studio) or `qwen3-1.7b-instruct` if you wrap in LLM later.[1][2]

**Profile**

```jsonc
{
  "name": "qwen3-fast",
  "backend_model": "qwen3-1.7b",
  "temperature": 0.6,
  "top_p": 0.9,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0,
  "max_tokens": 1024,
  "stop": [],
  "notes": "Fast default for low-stakes chat, routing, and small edits."
}
```

- Slightly warm `temperature` to keep it conversational.
- `max_tokens` small so it returns quickly and doesn’t ramble.

[2][3][1]

***

## 2) `general` – Qwen3‑4B‑Instruct‑2507 (main assistant)

**Intended use**

- Default assistant for PromptHub, Clara, and most OpenAI-like calls.
- Good balance of speed, quality, and reasoning.

**Model**

- Backend: `qwen3-4b-instruct-2507` via LM Studio GGUF imported into LLM (as you’ve set up).[3][4][5]

**Profile**

```jsonc
{
  "name": "qwen3-general",
  "backend_model": "qwen3-4b-instruct-2507",
  "temperature": 0.5,
  "top_p": 0.9,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.2,
  "max_tokens": 2048,
  "stop": [],
  "notes": "Main general-purpose assistant; use for most chat, RAG, and tool-calling."
}
```

- Slightly cooler `temperature` for stability and determinism.
- `frequency_penalty` 0.2 to reduce repetition but not over-penalize.[4][6][3]

***

## 3) `thinking` – Qwen3‑4B‑Thinking‑2507 (deep reasoning)

**Intended use**

- Hard prompts, planning, multi-step reasoning, agent decisions.
- You expect or explicitly want “chain of thought” behavior.

**Model**

- Backend: `qwen3-4b-thinking-2507` (thinking variant).[5][1][3]

**Profile (router-visible)**

```jsonc
{
  "name": "qwen3-thinking",
  "backend_model": "qwen3-4b-thinking-2507",
  "temperature": 0.7,
  "top_p": 0.95,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0,
  "max_tokens": 4096,
  "stop": [],
  "notes": "Use only when explicitly asked for deep reasoning / analysis."
}
```

- Warmer and higher `top_p` so it explores more.[1][3][5]
- Large `max_tokens` to let it finish long thoughts.

**If you want to keep `<think>` hidden from end-users**

You can do this at the router layer:

- Send a system message like: “Think step by step inside `<think>...</think>` then answer concisely. Do not expose the `<think>` content to the user.”
- Strip `<think>...</think>` from the final assistant message before returning to the client. (Qwen3 thinking docs describe this pattern.)[3][5][1]

***

## 4) `code` – Qwen2.5‑Coder‑7B (coding assistant)

**Intended use**

- IDE-style coding, debugging, refactoring, docstrings.
- More deterministic output, less “creative writing.”

**Model**

- Backend: `qwen2.5-coder-7b-instruct` GGUF (your `Qwen2.5-Coder-7B-Instruct-GGUF`).[7][8]

**Profile**

> **NOTE:** Historical model token `qwen2.5-coder` appears in the following code block; prefer mapping: qwen2.5-coder (now qwen3-4b-instruct-2507). Do not change the code block without a manual review.

```jsonc
{
  "name": "qwen25-code",
  "backend_model": "qwen2.5-coder-7b-instruct",
  "temperature": 0.2,
  "top_p": 0.9,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0,
  "max_tokens": 2048,
  "stop": ["```"],
  "notes": "Deterministic coding assistant; keep temp low, bias toward concise code."
}
```

- Low `temperature` so it’s predictable for code. [][]
- Optional `stop: ["```"]` if you wrap code in fences from your prompt template.

***

## 5) `speculative` – Qwen3‑0.6B (draft model, internal only)

You’re already using Qwen3‑0.6B as a draft model in LM Studio, which matches how Qwen describes it for speculative decoding.[9][10][11]

In PromptHub, I’d treat this as an **internal** **profile**, not user-facing:

```jsonc
{
  "name": "qwen3-draft",
  "backend_model": "qwen3-0.6b",
  "temperature": 0.8,
  "top_p": 0.95,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0,
  "max_tokens": 64,
  "notes": "Internal draft model for speculative decoding; not exposed to end users."
}
```

Then wire your speculative decoding logic to:

- Use `qwen3-draft` to propose tokens.
- Verify/correct with `qwen3-general` or `qwen3-thinking`.[10][11][12]

***

## 6) Suggested OpenAI-style ids for PromptHub

So your OpenAI-compatible router could expose something like:

- `ph-qwen-fast` → `qwen3-fast`
- `ph-qwen-general` → `qwen3-general`
- `ph-qwen-thinking` → `qwen3-thinking`
- `ph-qwen-code` → `qwen25-code`

And keep:

- `ph-qwen-draft` → `qwen3-draft` (internal only)

You can then:

- Default `model` to `ph-qwen-general`.
- Offer `ph-qwen-thinking` for agents or a `?mode=deep` flag.
- Route `/v1/chat/completions` with `model` → matching backend profile.

[8][4][5][1][3]

***

If you share the exact JSON shape PromptHub expects for a “model profile,” I can rewrite these directly into your config format so you can paste them in and go.

Sources
[1] Qwen3: Think Deeper, Act Faster | Qwen https://qwenlm.github.io/blog/qwen3/
[2] unsloth/Qwen3-1.7B-bnb-4bit - Hugging Face https://huggingface.co/unsloth/Qwen3-1.7B-bnb-4bit
[3] Qwen3 Technical Report - arXiv https://arxiv.org/html/2505.09388v1
[4] Qwen3 4B 2507 Instruct Intelligence, Performance & Price Analysis https://artificialanalysis.ai/models/qwen3-4b-2507-instruct
[5] What's New with Qwen3-4B-Instruct-2507 and Qwen3-4B-Thinking ... https://apidog.com/blog/qwen3-4b-instruct-2507-and-qwen3-4b-thinking-2507/
[6] We Benchmarked 12 Small Language Models Across 8 Tasks to ... https://www.distillabs.ai/blog/we-benchmarked-12-small-language-models-across-8-tasks-to-find-the-best-base-model-for-fine-tuning/
[7] Qwen 3 Benchmarks, Comparisons, Model Specifications, and More https://dev.to/best_codes/qwen-3-benchmarks-comparisons-model-specifications-and-more-4hoa
[8] Qwen Models Guide: 600M to 1 Trillion Parameters - Digital Applied https://www.digitalapplied.com/blog/qwen-models-complete-guide
[9] Qwen3-0.6B: Compact Dense Transformer LLM - Emergent Mind https://www.emergentmind.com/topics/qwen3-0-6b
[10] Speculative Decoding - Artificial Intelligence in Plain English https://ai.plainenglish.io/speculative-decoding-93a689b9cc64
[11] Accelerating decode-heavy LLM inference with speculative ... - AWS https://aws.amazon.com/blogs/machine-learning/accelerating-decode-heavy-llm-inference-with-speculative-decoding-on-aws-trainium-and-vllm/
[12] Tutorial: Using Speculative Decoding (SD) to improve inference ... https://awsdocs-neuron.readthedocs-hosted.com/en/latest/libraries/nxd-inference/tutorials/sd-inference-tutorial.html
