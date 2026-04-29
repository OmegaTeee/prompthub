# Responses API Adapter — Design Spec

**Date**: 2026-03-27
**Status**: Approved
**Scope**: Add `POST /v1/responses` endpoint to PromptHub router

> Historical implementation spec: this document is preserved as design history
> for the Responses API adapter. Use current code and API docs for the live
> contract.

## Problem

Cherry Studio (and potentially other clients) use OpenAI's Responses API format (`/v1/responses`) instead of Chat Completions (`/v1/chat/completions`). The router currently only speaks Chat Completions, blocking these clients from connecting.

## Solution

A thin format adapter inside the existing `openai_compat` module. The endpoint translates Responses API requests into Chat Completions calls, then wraps the result back into Responses API shape. No new modules, no new dependencies.

## Approach

Inline in existing `openai_compat/router.py` and `models.py` (Approach A). Reuses all existing infrastructure: auth, circuit breaker, enhancement, LLM client, audit logging.

## Endpoint

`POST /v1/responses` — authenticated via bearer token (same as `/v1/chat/completions`).

## Request Translation

| Responses API field | Chat Completions equivalent |
|---|---|
| `input` (string) | Single `{"role": "user", "content": input}` message |
| `input` (array of `{role, content}`) | `messages` array directly |
| `instructions` (string) | Prepended as `{"role": "system", "content": instructions}` |
| `model` | `model` (passthrough) |
| `temperature` | `temperature` (passthrough) |
| `max_output_tokens` | `max_tokens` |
| `top_p` | `top_p` (passthrough) |
| `stream` (if true) | Reject with 400 — not supported |

### Input normalization

The `input` field accepts two forms:

1. **String**: Wrapped as a single user message.
2. **Array of message objects**: Each item has `role` ("user", "assistant", "system") and `content` (string). Mapped directly to Chat Completions messages.

If `instructions` is provided, it becomes the first message with `role: "system"`, followed by the input messages.

## Response Translation

Chat Completions response is wrapped into Responses API format:

```json
{
  "id": "resp_<uuid>",
  "object": "response",
  "created_at": 1234567890,
  "model": "google/gemma-3-4b",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        { "type": "output_text", "text": "The actual response text" }
      ]
    }
  ],
  "output_text": "The actual response text",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 50,
    "total_tokens": 60
  }
}
```

### Thinking tokens

If the LLM response contains reasoning/thinking content (e.g., qwen3 models), include it as a separate content block:

```json
"content": [
  { "type": "thinking", "thinking": "Internal reasoning..." },
  { "type": "output_text", "text": "The actual response text" }
]
```

Thinking content is detected from the Chat Completions response `choices[0].message` — if a `reasoning_content` field is present (LM Studio / OpenAI convention), it maps to a `thinking` block.

## Reused Infrastructure

All of these are called directly from the new endpoint handler — no duplication:

- **Auth**: `_verify_bearer()` validates bearer token, returns `ApiKeyConfig`
- **Circuit breaker**: Check before request, record success/failure after
- **Enhancement**: If `api_key.enhance == True`, enhance last user message
- **LLM client**: `_llm_client.chat_completion()` for the actual call
- **Audit**: `audit_event()` with `event_type="openai_proxy"`, `action="responses"`

## Not Supported (intentionally)

| Feature | Reason |
|---|---|
| Streaming | Different SSE event format; Cherry Studio can disable it |
| Tool use / function calling | Not needed for LM Studio local models |
| `previous_response_id` (multi-turn state) | Client manages conversation history |
| Background mode | Not applicable to local proxy |
| `developer` role messages | Cherry Studio has this toggle off |
| `service_tier` | Cherry Studio has this toggle off |

## New Code

### `models.py` additions (~30 lines)

- `ResponsesRequest` — input (str | list), instructions, model, temperature, max_output_tokens, top_p
- `ResponsesContentBlock` — type + text/thinking fields
- `ResponsesOutputMessage` — type, role, content list
- `ResponsesResponse` — id, object, created_at, model, output, output_text, usage

### `router.py` additions (~80 lines)

- `POST /responses` endpoint handler
- `_translate_responses_to_messages()` helper — converts input + instructions to messages list
- `_build_responses_response()` helper — wraps Chat Completions result into Responses API shape

## Error Handling

Follows existing OpenAI-compatible error format:

| Condition | Status | Message |
|---|---|---|
| `stream: true` | 400 | "Streaming not supported for /v1/responses. Disable streaming in your client." |
| Invalid bearer token | 401 | (existing auth handler) |
| Invalid model name | 422 | (existing validation) |
| LLM unreachable | 502 | (existing error handler) |
| Circuit breaker open | 503 | (existing breaker check) |

## Testing

Unit tests in existing `test_openai_compat.py` or new `test_responses_api.py`:

- String input translation
- Array input translation
- Instructions prepended as system message
- Response wrapping (with and without thinking tokens)
- Stream rejection (400)
- Auth required
- Usage passthrough
