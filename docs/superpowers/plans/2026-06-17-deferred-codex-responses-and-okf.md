# Deferred Items Implementation Plan — codex /v1/responses streaming + OKF evaluation

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`).

**Goal:** Unblock codex by adding SSE streaming to the router's `/v1/responses` endpoint (with tool-calling), and produce a written recommendation on whether to adopt OKF.

**Architecture:** Buffered streaming — `/responses` runs the existing non-streaming completion (now with `tools` forwarded), then replays the result as a well-formed OpenAI Responses SSE event sequence including `function_call` items. Validated live against `codex exec`.

**Tech Stack:** FastAPI `StreamingResponse`, OpenAI Responses API event schema, codex-cli 0.137, local `qwen3-coder-30b` via PromptHub.

---

## Item A — codex `/v1/responses` streaming

### Task A1: Forward tools on the Responses path + extend the request model

**Files:**
- Modify: `app/router/openai_compat/models.py` (`ResponsesRequest`)
- Modify: `app/router/openai_compat/router.py` (`/responses` handler)
- Test: `app/tests/test_openai_compat.py`

- [ ] **Step 1 (TDD):** Write a failing test: a `ResponsesRequest` with `tools` set forwards `tools` into the upstream `chat_completion` call. Assert via mock.
- [ ] **Step 2:** Add to `ResponsesRequest`: `tools: list[dict[str, Any]] | None = None`, `tool_choice: str | dict[str, Any] | None = None`.
- [ ] **Step 3:** In the `/responses` handler, pass `tools=body.tools, tool_choice=body.tool_choice` into `_llm_client.chat_completion(...)`.
- [ ] **Step 4:** Run test → pass. Commit.

### Task A2: Emit a buffered Responses SSE stream

**Files:**
- Modify: `app/router/openai_compat/router.py` (`/responses` handler + new helper `_stream_responses`)
- Test: `app/tests/test_openai_compat.py`

- [ ] **Step 1 (TDD):** Write a failing test: POST `/responses` with `stream: true` returns `text/event-stream`, and the body contains, in order, the event types `response.created`, `response.output_item.added`, `response.output_text.delta` (with the model text), and `response.completed`. (Mock the upstream completion to return a fixed assistant message.)
- [ ] **Step 2:** Remove the hard 400 rejection of `body.stream`. When `stream` is true, return `StreamingResponse(_stream_responses(...), media_type="text/event-stream")`.
- [ ] **Step 3:** Implement `_stream_responses(completion, model)`: build the events from the *completed* chat response. For a text message emit:
  `response.created` → `response.output_item.added` (message item) → `response.content_part.added` → one `response.output_text.delta` carrying the full content → `response.output_text.done` → `response.content_part.done` → `response.output_item.done` → `response.completed` (full response object) → `data: [DONE]`.
  Each event as `event: <type>\ndata: <json>\n\n`.
- [ ] **Step 4:** Run test → pass. Commit.

### Task A3: function_call items in the stream (so codex can write files)

**Files:**
- Modify: `app/router/openai_compat/router.py` (`_stream_responses`, `_build_responses_response`)
- Test: `app/tests/test_openai_compat.py`

- [ ] **Step 1 (TDD):** Write a failing test: when the upstream completion's message has `tool_calls`, the streamed events include a `response.output_item.added` whose item `type` is `function_call` with `name`/`arguments`/`call_id`, followed by `response.function_call_arguments.delta`, `...done`, `response.output_item.done`, and `response.completed` whose `output` array contains the function_call item.
- [ ] **Step 2:** Extend `_stream_responses` and `_build_responses_response` to translate each `tool_calls[i]` into a Responses `function_call` output item (map `id`→`call_id`, `function.name`→`name`, `function.arguments`→`arguments`).
- [ ] **Step 3:** Run test → pass. Commit.

### Task A4: Live acceptance against codex

- [ ] **Step 1:** Restart router (`launchctl kickstart -k gui/$(id -u)/com.prompthub.router`), wait healthy.
- [ ] **Step 2:** Run `vault-codex` smoke: `cd ~/Vault/Scratch && PROMPTHUB_VAULT_KEY=sk-prompthub-vault-writer-001 codex --profile vault-writer exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox "Create codex-okf-test.md ... write the file"`.
- [ ] **Step 3:** Confirm `~/Vault/Scratch/codex-okf-test.md` exists. If codex's strict parser rejects an event, read its error, adjust the event schema in `_stream_responses`, restart, retry (cap: ~4 iterations). If still failing after the cap, report the exact codex parser error as the remaining blocker.
- [ ] **Step 4:** Commit any schema adjustments.

## Item B — OKF evaluation (decision doc)

### Task B1: Write the recommendation

**Files:**
- Create: `docs/notes/eval-okf-vs-pr-brief-template.md`

- [ ] **Step 1:** Compare OKF (generic: `type/resource/tags/timestamp`, `resource`==stem) against the live `~/Vault/LLM/briefs/_pr-brief-template.md` (`type/created/status/owner/target_repo/sources/tags` + rich body) and `wiki/schema/config.md` two-track rules.
- [ ] **Step 2:** Recommend keep-existing vs adopt-OKF vs hybrid, with concrete reasons (wiki integration, Karpathy-plugin ingestion, existing briefs, migration cost). Note that adopting OKF would require migrating existing briefs and updating the validator.
- [ ] **Step 3:** Commit.

---

## Notes
- codex is a *secondary* engine (Goose already works). Item A is the larger effort; if codex's Responses parser proves too strict to satisfy with buffered streaming within the iteration cap, that is an acceptable stopping point — Goose remains the working path.
