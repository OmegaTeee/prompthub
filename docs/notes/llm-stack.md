---
title: "Local LLM Stack — Installed Models & PromptHub Roles"
status: review
created: 2026-03-10
updated: 2026-03-23
tags: [llm, stack, ollama, configuration, per-client, openclaw]
---

# Local LLM Stack

Inventory of every Ollama model installed on this machine, how PromptHub uses each one, and which clients connect through them.

## Installed Models

As of 2026-03-23, `ollama list` shows:

| Model | Size | Params | Context | Architecture | Pulled |
|---|---|---|---|---|---|
| `qwen3:14b` | 9.3 GB | 14.8B | 40K | Qwen3 dense | 2026-03-09 |
| `gemma3:27b` | 17 GB | 27.4B | 128K | Gemma3 dense | 2026-03-09 |
| `gemma3:4b` | 3.3 GB | 4.3B | 128K | Gemma3 dense | 2026-03-09 |
| `qwen3-coder:30b` | 18 GB | 30.5B (MoE, ~3.3B active) | 256K | Qwen3-Coder MoE | 2026-03-02 |
| `bge-m3` | 1.2 GB | 568M | 8K | BERT (embeddings only) | 2026-03-02 |

**Total disk**: ~49 GB across 5 models.

## PromptHub Roles

Each model serves a specific function in the PromptHub request pipeline. The three layers — orchestration, enhancement, and proxy — are independent and can fail without affecting each other.

### Layer 1: Orchestrator — `qwen3:14b`

**What it does**: Pre-enhancement intent classifier. Analyzes every incoming prompt and produces a structured JSON result: intent category, suggested MCP servers, context hints, and an annotated prompt.

**Where it runs**: `router/orchestrator/agent.py` — hardcoded as `MODEL = "qwen3:14b"`.

**Why this model**: Qwen3 has native tool-calling tokens and a `/think` mode for chain-of-thought reasoning. At 14B it's small enough to stay warm alongside enhancement models, but large enough for reliable structured output.

**Config**:
- Timeout: 2.5s hard ceiling (fail-safe: returns original prompt on timeout)
- Max tokens: 300 (only needs JSON output)
- Temperature: 0.1 (deterministic classification)
- Circuit breaker: independent (3 failures → 30s recovery)
- LRU cache: 256 entries (skip classification for repeated prompts)

**Intent categories**: `code`, `documentation`, `search`, `memory`, `workflow`, `reasoning`, `general` — mapped to MCP server suggestions via `INTENT_SERVER_MAP` in [intent.py](../../app/router/orchestrator/intent.py).

### Layer 2: Enhancement — per-client models

**What it does**: Rewrites the user's prompt to be clearer, more specific, and better structured for the downstream AI. Each client gets a tailored system prompt and model.

**Where it runs**: `router/enhancement/service.py`, configured via [enhancement-rules.json](../../app/configs/enhancement-rules.json).

**Current assignments** (from `enhancement-rules.json`):

| Client | Model | Temperature | Max Tokens | Privacy | System Prompt Focus |
|---|---|---|---|---|---|
| **default** | `gemma3:4b` | 0.3 | 500 | `local_only` | General prompt clarity |
| **claude-desktop** | `gemma3:27b` | 0.3 | 600 | `local_only` | Structured for reasoning AI, Markdown |
| **claude-code** | `qwen3-coder:30b` | 0.2 | 600 | `local_only` | Code-precise, file-path aware |
| **vscode** | `gemma3:4b` | 0.2 | 500 | `local_only` | Concise code prompts |
| **raycast** | `gemma3:4b` | 0.3 | 300 | `free_ok` | Action-oriented, CLI-style, <150 words |
| **perplexity** | `gemma3:4b` | 0.3 | 400 | `free_ok` | Research questions, Markdown, wikilinks |
| **cursor** | `gemma3:4b` | 0.2 | 500 | `local_only` | File-path-aware code prompts |
| **comfyui** | `gemma3:4b` | 0.5 | 400 | `local_only` | Image generation prompt expansion |
| **open-webui** | `gemma3:4b` | 0.3 | 500 | `local_only` | Conversational clarity |

**Important**: Enhancement is currently **disabled** on all API keys (`"enhance": false` in `api-keys.json`). The rules above define *how* enhancement works when enabled — toggle individual keys to `"enhance": true` to activate.

**Fallback chain**: `gemma3:4b → gemma3:27b → null` (pass-through if both fail).

### Layer 3: OpenAI-Compatible Proxy — `/v1/`

**What it does**: Clients that speak the OpenAI API format (Open WebUI, VS Code Chat, Raycast) connect to `localhost:9090/v1/chat/completions`. PromptHub authenticates via bearer token, optionally enhances the prompt (if `enhance: true`), then forwards to Ollama.

**The model is chosen by the client**, not PromptHub — the request's `model` field is passed through to Ollama as-is. PromptHub doesn't route chat models.

### Embeddings — `bge-m3`

**What it does**: BAAI General Embedding model for semantic similarity. F16 precision, 568M params.

**Current use**: Available for future RAG pipeline (see [plan-rag-improvement.md](plan-rag-improvement.md)). Not yet wired into PromptHub's request pipeline.

## OpenClaw Experimentation (2026-03-23)

Tested OpenClaw with two new models via the PromptHub stdio bridge. Results were mixed.

### OpenClaw Client Config

OpenClaw connects to PromptHub via the stdio bridge with its own API key (`sk-prompthub-openclaw-001`), accessing a filtered set of MCP servers:

```
SERVERS: duckduckgo, sequential-thinking, desktop-commander, browsermcp, context7
```

Enhancement is **disabled** for OpenClaw (`"enhance": false`). It also has no entry in `enhancement-rules.json`, so if enabled it would fall back to the default (`gemma3:4b`).

### `qwen3:8b` — removed

- **Size**: 5.2 GB, 8.2B params, 128K context
- **Result**: Answered general questions but **failed to invoke MCP tools**. The model produces text responses instead of structured tool calls.
- **Root cause**: The bridge's schema minification strips `description`, `title`, and `examples` from tool schemas. Larger models (14B+) can infer tool purpose from structural schema alone (`type`, `properties`, `required`), but 8B struggles without the semantic hints that descriptions provide. The prefixed tool names (`duckduckgo_search`, `desktop-commander_list_directory`) add further ambiguity without descriptions to clarify them.

### `glm-4.7-flash` — removed

- **Size**: 19 GB, ~9B params — poor size-to-param ratio (compare: `qwen3:14b` is 9.3 GB with 14.8B params)
- **Result**: Did not work effectively with OpenClaw. Removed from Ollama.
- **Lesson**: GLM-4 family may have tool-calling support in theory, but the Ollama quantization and bridge integration didn't produce usable results.

### Lessons on Model-Client Pairing

Pairing local models with MCP clients is harder than it looks. The key variables:

| Factor | Impact | Where to tune |
|---|---|---|
| **Model size** | <14B models struggle with tool calling through minified schemas | Choose model ≥14B for tool-using clients |
| **Schema minification** | Saves ~67% context but removes semantic hints smaller models need | `MINIFY_SCHEMAS` env var in bridge |
| **Tool count** | More tools = more confusion for smaller models | `SERVERS` filter per client in bridge config |
| **Server filter** | Reducing exposed servers helps smaller models focus | `SERVERS` (stdio bridge) or `GATEWAY_SERVERS` (HTTP gateway) |
| **Enhancement overhead** | Extra Ollama round-trip adds latency | `"enhance": false` in `api-keys.json` |

**Practical tiers:**

| Model Tier | Tool Calling | Enhancement | Chat | Examples |
|---|---|---|---|---|
| **≥27B** | Reliable | High quality | Excellent | `gemma3:27b`, `qwen3-coder:30b` |
| **14B** | Good (native tokens) | Good | Good | `qwen3:14b` |
| **4B** | Unreliable | Fast but basic | Adequate | `gemma3:4b` |

**Recommendation**: For tool-calling clients (OpenClaw, Open WebUI with MCP), use `qwen3:14b` minimum. For chat-only or enhancement, `gemma3:4b` is fine. The `GATEWAY_SERVERS` filter for Open WebUI and `SERVERS` filter for stdio clients should limit tool count to ≤15 tools for models under 14B.

## Cloud Fallback

When Ollama is unavailable, clients with `free_ok` privacy level (currently: raycast, perplexity) can fall back to OpenRouter free-tier models. Controlled by `OPENROUTER_ENABLED` in `.env`.

**Default cloud model**: `qwen/qwen3-next-80b-a3b-instruct:free` (per `.env.example`).

**Free-tier models available** (from [cloud-models.json](../../app/configs/cloud-models.json)):
- `qwen/qwen3-coder:free` — coding
- `deepseek/deepseek-r1-0528:free` — reasoning (full 671B, massive upgrade over any local model)
- `meta-llama/llama-3.3-70b-instruct:free` — general
- `mistralai/devstral-2512:free` — coding
- `mistralai/mistral-small-3.1-24b-instruct:free` — general

**Privacy boundary**: `local_only` clients (the default) **never** use cloud fallback, regardless of Ollama status.

## VRAM Notes

On Apple Silicon with unified memory, Ollama keeps recently-used models warm. Practical considerations:

- `gemma3:4b` (3.3 GB) loads in seconds — good default for high-frequency enhancement
- The orchestrator (`qwen3:14b`, 9.3 GB) and default enhancement model (`gemma3:4b`, 3.3 GB) fit comfortably together (~13 GB)
- Loading `qwen3-coder:30b` (18 GB) or `gemma3:27b` (17 GB) will likely evict smaller models
- `bge-m3` (1.2 GB) is tiny and can coexist with anything
- Set `"enhance": false` on latency-sensitive API keys to skip the Ollama round-trip entirely

## Configuration Quick Reference

| Config File | What It Controls |
|---|---|
| [enhancement-rules.json](../../app/configs/enhancement-rules.json) | Per-client model, system prompt, temperature, privacy level |
| [api-keys.json](../../app/configs/api-keys.json) | Bearer tokens, client names, `enhance` on/off toggle |
| [cloud-models.json](../../app/configs/cloud-models.json) | Local → cloud model mapping, free-tier list |
| [.env](../../app/.env.example) | `OPENROUTER_*` settings, `OLLAMA_*` defaults, `GATEWAY_SERVERS` filter |
| [orchestrator/agent.py](../../app/router/orchestrator/agent.py) | Hardcoded `MODEL = "qwen3:14b"`, timeout, temperature |
