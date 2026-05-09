# Enhancement Tuning Playbook

How to write and tune per-client prompt enhancement rules for PromptHub's
local rewriter. Pairs with [docs/architecture/ADR-003-per-client-enhancement.md](../architecture/ADR-003-per-client-enhancement.md)
(*why* per-client enhancement) and [docs/notes/models/qwen3-role-map.md](../notes/models/qwen3-role-map.md)
(*which model plays which role*); this guide covers *how to phrase the rules*.

## The rule schema

Each entry in [`app/configs/enhancement-rules.json`](../../app/configs/enhancement-rules.json)
controls how a client's prompts get rewritten before being forwarded to the
chat model. The shape:

```jsonc
"<client-name>": {
  "model": "qwen3-4b-instruct-2507",   // which model rewrites
  "system_prompt": "...",              // instructions to the rewriter
  "temperature": 0.3,                  // 0.0 = deterministic, 1.0 = creative
  "max_tokens": 600,                   // upper bound on the rewrite length
  "privacy_level": "local_only"        // local_only | free_ok | any
}
```

The rewriter sees `system_prompt` as its instructions and the user's prompt
as the message to rewrite. It returns the rewritten text, which then gets
forwarded to the chat model in place of the original.

## Picking a rewriter model

Match the rewriter to the workload. The rewriter runs on every enhanced
request, so latency and quality both matter.

| Workload                                    | Recommended rewriter           | Why                                             |
| ------------------------------------------- | ------------------------------ | ----------------------------------------------- |
| Default for chat-style enhancement          | `qwen3-4b-instruct-2507`       | Reliable instruction-following, no `<think>` overhead, ~2-5s |
| Code-focused (file paths, language hints)   | `qwen3-4b-instruct-2507`       | Same. Parens around language names are safe with this size |
| Quick cleanup of a one-line query           | `qwen3-4b-instruct-2507`       | The model's overhead matters less than its output quality |
| Reasoning-required orchestration            | `qwen3-4b-thinking-2507`       | But this is `/llm/orchestrate`, not enhancement |

**Don't use `qwen3-0.6b` as a directly-prompted rewriter.** It's too small
to follow nuanced rewriting instructions and it's *thinking-capable*, which
means it emits `<think>...</think>` blocks that consume your `max_tokens`
budget and leave whitespace residue (`\n\n`) in the output. It's correctly
deployed as a **speculative decoding draft model** behind 4b-instruct, not
as a direct rewriter. See [qwen3-role-map.md](../notes/models/qwen3-role-map.md).

## Anti-patterns in system prompts

Small models pattern-match on the *shape* of your instructions. Avoid:

### Bracketed parentheticals as examples

❌ **Don't:** `"make the target explicit (URL, path, library name)"`

The rewriter reads `(URL, path, library name)` as a template-fill instruction
and emits something like:
> `your prompt (specify target: search for information on [URL], retrieve data from [path], or execute command on [library name])`

✅ **Do:** Phrase as prose, not as a parenthetical list.
> `"When the prompt implies web research, name the URL directly. When it implies file operations, name the file path directly."`

### Meta-instructions that look like content

❌ **Don't:** `"Format the rewrite like this: 'Question: <query>'"`

The rewriter may reproduce the literal `Question: <query>` shape rather
than rewriting *as* a question.

✅ **Do:** Describe the *property* you want the output to have, not the
literal format. `"Frame the rewrite as a complete-sentence question."`

### Tool-name leakage

❌ **Don't:** `"Use comet_ask for web research"` in the rewriter
prompt — the rewriter will mention `comet_ask` in the rewritten user
prompt, confusing the chat model.

✅ **Do:** `"Do not name specific tool names."` Keep the chat model's
tool decisions to the chat model.

### Bracketed `[REPLACE_ME]` placeholders

❌ **Don't:** `"Output format: [rewritten prompt]"`

The rewriter often echoes the brackets literally.

✅ **Do:** `"Return only the rewritten prompt — no explanation, no preamble, no quotes."`
This phrasing is well-tested and produces clean outputs.

## Sampling settings

| Setting       | Recommended    | When to deviate                                      |
| ------------- | -------------- | ---------------------------------------------------- |
| `temperature` | `0.2 – 0.3`    | Lower (0.1) for code-heavy clients; higher (0.5) for image-prompt expansion (`comfyui`) |
| `max_tokens`  | `500 – 600`    | Lower (300) only for tight quick-task clients (Raycast); higher (800) for elaborate rewrites |

`temperature = 0.3` is the project default — deterministic enough that the
same prompt produces consistent rewrites, creative enough to phrase the
rewrite naturally. Do not set `temperature = 0.0` for enhancement; it
sometimes makes the model echo the input verbatim instead of rewriting.

`max_tokens = 600` works for instruct-class 4B models. Smaller models that
emit thinking tokens need *more* headroom (~1000) which is exactly why we
recommend instruct-class models — same quality, half the budget.

## Debugging checklist

When a rewrite comes back wrong, work through these in order:

| Symptom                                              | Likely cause                                      | Fix                                                 |
| ---------------------------------------------------- | ------------------------------------------------- | --------------------------------------------------- |
| Leading `\n\n` in the output                         | Thinking-tag residue from a thinking-capable model | Use a non-thinking model (instruct variant)         |
| Output truncated mid-word                            | `max_tokens` exhausted                             | Bump `max_tokens` *or* switch to a model that doesn't think |
| Output identical or nearly-identical to input        | Rewriter model too small to follow instructions    | Use a larger rewriter (4b-instruct vs 0.6b)         |
| Output contains literal `[URL]` / `[path]` / `<query>` | System prompt has bracketed examples              | Rephrase system prompt without brackets             |
| Output mentions `comet_ask` / `memory_create_entities` / etc. | Tool names leaked from the system prompt or rules  | Add `"Do not name specific tool names"` to system prompt |
| Output is a hallucinated *different* prompt           | Input was a placeholder ("test prompt here") that the rewriter substituted | Test with a real input — placeholders are an LLM trap, not a rule failure |
| `provider: openrouter` when expected `llm`            | Local LLM is down; cloud fallback engaged          | Check `/health` for `llm: up`, restart LM Studio if needed |
| `enhanced_by_llm: false` and `enhanced == original`   | Privacy level forbids leaving localhost AND local LLM is down | Either start the local LLM or change `privacy_level` to `free_ok` |

## Live-test recipes

Verifying a rule produces good rewrites is a one-shot curl:

```bash
# Test any client's rule with a real prompt
curl -s -X POST http://localhost:9090/llm/enhance \
  -H 'Content-Type: application/json' \
  -H 'X-Client-Name: <client>' \
  -H 'X-Privacy-Level: local_only' \
  -d '{"prompt": "<realistic prompt>"}' \
  | python3 -m json.tool
```

The response includes `original`, `enhanced`, `model`, `provider`, and
`privacy_level`. Read the `enhanced` field as if you were the chat model
receiving it — does it carry forward the user's intent? Are URLs/paths/
library names baked in instead of left as placeholders? Is it free of
trailing `[brackets]` or hallucinated metadata?

**Test prompts to use** (avoid placeholders like "your test prompt here" —
the rewriter often substitutes a fictional one):

- Code-leaning: `"look up the FastAPI lifespan docs and tell me how to add startup logic"`
- Research-leaning: `"find the parameters for qwen3 thinking on lmstudio.ai"`
- File-ops-leaning: `"summarize what's in app/router/main.py"`
- Tool-routing-leaning: `"what does my dashboard show for circuit breakers right now"`

A good rule produces rewrites where each of these gets *more concrete*
without losing meaning.

## Per-client tuning patterns

Common shapes seen in production rules in `enhancement-rules.json`:

- **Code clients** (`claude-code`, `cursor`, `opencode`, `vscode`): low
  temperature (0.2), instructions to preserve file paths and language hints,
  ~500-600 token ceiling
- **Conversational clients** (`claude-desktop`, `open-webui`,
  `lm-studio`): mid temperature (0.3), preserve conversational tone,
  ~500-600 token ceiling
- **Research clients** (`perplexity`, `raycast`): mid temperature (0.3),
  optimize for the destination's UI/parser quirks, shorter ceiling for
  Raycast (~300 since it shows previews), longer for Perplexity (~600
  since Comet handles full prose)
- **Image-gen clients** (`comfyui`): higher temperature (0.5),
  expand keywords into stylistic detail, ~400 token ceiling

When in doubt, copy the closest-match existing rule and tune from there.

## Stay in scope

The enhancement layer rewrites *the user's most recent prompt only*. It
doesn't see conversation history, tool results, or the chat model's
intermediate state. So the rewriter cannot "improve" multi-turn coherence
or fix tool-routing decisions made elsewhere — those are the chat model's
job, not the rewriter's. Keep system prompts focused on what the rewriter
*can* do: clarity, specificity, target-explicitness, format conformance.
