# llmpm + vLLM daemon — direction for the model layer

> **Status (2026-06-01):** Vision-stage idea. Captures the architectural shift the model layer wants to make over time, without committing to it now. Lives alongside `idea-clients-folder-sunset.md` as a "thing we'd do when the cost is low and the value is real."

## Two ideas, one motion

### 1. Replace the bespoke download script with [llmpm](https://www.llmpm.co)

`scripts/models/download-qwen-distilled.sh` is ~200 lines of `huggingface-cli` orchestration with a profile system, `.env`-style config, and dry-run safety. It works, and PR #45 made it format-agnostic (GGUF + safetensors both supported). But the *manifest model* of a real package manager — `llmpm.json` checked into the repo, a `registry.json` tracking what's installed, a `--path` flag for "I downloaded this manually, just register it" — replaces a chunk of the bespoke code with a smaller, declarative surface.

What llmpm gives us that the script doesn't:
- **One tool for both formats.** llmpm uses `llama.cpp` for GGUF and Transformers for safetensors. The current script can technically download both (per the PR that added the `instruct` profile), but the import workflow is still per-format — LM Studio for GGUF, something-else for safetensors. llmpm handles both natively.
- **A real manifest.** `llmpm.json` checked into the repo describes "what models this deployment needs" in a way the bash script's `.env` defaults *almost* do but never quite formalize.
- **`--path` coexistence.** Existing manual installs in LM Studio's model directory keep working; llmpm just registers them by path. No big-bang migration.

What llmpm doesn't give us, contrary to my initial read:
- **Local usage tracking.** llmpm's "stats" feature is `llmpm trending` — HF popularity (likes, downloads). Not "which of my installed models did the router hit this week." If we want that, it lives in the router (we already have audit infra; a model-usage panel is a small query problem).

### 2. Move the daemon to [vLLM](https://docs.vllm.ai)

Today the daemon runs in LM Studio (via OpenAI-compatible API). LM Studio is excellent for the dev loop — easy model swaps, GGUF-first, GUI metrics — but it's not built for serving concurrent enhancement requests with shared KV cache, batching, or systematic eviction. vLLM is.

The daemon is the always-on model. It serves the enhancement layer (`POST /llm/enhance`) on every client request that opts into enhancement, often dozens per minute when multiple clients are active. That's exactly the workload vLLM is designed for.

What changes when the daemon moves to vLLM:
- **Repo format flips.** vLLM needs safetensors (full precision or AWQ/GPTQ quantized), not GGUF. PR #45 already added the safetensors `instruct` profile to the download script for this exact reason — `Qwen/Qwen3-4B-Instruct-2507` works for both LM Studio (today, as fallback) and vLLM (tomorrow, as daemon).
- **Inference server topology changes.** Today: one LM Studio process serving all roles. Tomorrow: vLLM serving the daemon on one port, LM Studio serving everything else (coder, claude_feel, fallback) on another. `LLM_HOST` / `LLM_PORT` becomes more nuanced — maybe `LLM_DAEMON_HOST` / `LLM_DAEMON_PORT` split out.
- **Settings get a backend toggle.** Probably a per-profile `backend: lmstudio|vllm` field in `enhancement-rules.json`, with the LLMClient picking which base URL to call.

## What we should do before committing to either

| Question | Why it matters |
|---|---|
| What's the actual concurrent load on the daemon today? | If we're rarely above 1 in-flight request, vLLM's batching wins are theoretical. Audit log query against `/llm/enhance` request volume answers this in five minutes. |
| Does llmpm handle our LM Studio import workflow cleanly? | LM Studio loads GGUFs from a specific directory layout. llmpm's `--local-dir`-equivalent output needs to match, or we need a post-install symlink step. |
| What's the LM Studio fallback strategy if vLLM crashes? | The whole point of "Instruct as fallback" presupposes a working fallback path. We need to know what happens during vLLM downtime — is the router smart enough to route around it, or do we manually flip env vars? |
| Is the existing `model_profile` resolution enough, or do we need a `backend_profile` too? | Currently `model_profile` selects which *model id* a client gets. It doesn't say *which inference server* serves that model. Adding vLLM means that gap matters. |

## Sketch of the order things would land

This is what a "yes, commit" timeline would look like. Not a plan, just a way to see the shape.

1. **vLLM smoke test.** Stand up vLLM with `Qwen/Qwen3-4B-Instruct-2507` on a side port. Confirm it can serve the existing `LLMClient` API shape. No router changes; pure proof-of-life.
2. **Backend abstraction in `LLMClient`.** Per-call base URL selection. Probably reuses the OpenAI-compatible client with a different default URL — small structural change.
3. **`enhancement-rules.json` gains a `backend` field per profile.** `daemon` → `vllm`, everything else → `lmstudio` (default). Resolves at rule-load time.
4. **llmpm migration of the download script.** `llmpm.json` checked in, the bash script becomes thin wrapper around `llmpm install`. Or deleted in favor of `make download-models`.
5. **Local usage stats panel** (separable). Router already logs `/llm/enhance` requests with `client_id` and `model`. A small SQL roll-up + dashboard partial gives the "which model did what this week" view that llmpm doesn't.

Steps 1–3 are the meaningful work. 4 is housekeeping. 5 is independent and could land first.

## Open question: when, not whether

The "whether" is settled — vLLM is the right serving layer for a daemon-class workload, and llmpm is the right tool when the model set grows past 3–4 profiles. The "when" is the harder question. Cheap signals that say "now":

- Daemon serving more than ~1 concurrent request on average (vLLM batching pays off).
- Model set grows past 5 profiles (the bash script's `case`-statement starts to creak).
- Wanting to test a new model without going through LM Studio's GUI (llmpm CLI shines here).

If none of those apply yet, the cost of waiting is near-zero — the `instruct` profile shipped in PR #46 is forward-compatible with both directions.

## See also

- The script that exists today: [`scripts/models/download-qwen-distilled.sh`](../../../scripts/models/download-qwen-distilled.sh).
- The model profiles that govern routing: `app/configs/enhancement-rules.json` (top-level `model_profiles` block).
- The enhancement service that drives the daemon: `app/router/enhancement/service.py`.
- llmpm's docs: https://www.llmpm.co/docs
- vLLM's docs: https://docs.vllm.ai
