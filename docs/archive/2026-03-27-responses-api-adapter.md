# Responses API Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> **Historical implementation plan:** this file is kept as execution history for
> the Responses API work. Use current code and `docs/api/openapi.yaml` for the
> live endpoint behavior.

**Goal:** Add `POST /v1/responses` endpoint that translates OpenAI Responses API format to Chat Completions, enabling Cherry Studio and similar clients to connect to local models through the router.

**Architecture:** Thin adapter inline in the existing `openai_compat` module. New Pydantic models in `models.py`, new endpoint + two helper functions in `router.py`. Reuses all existing infrastructure (auth, circuit breaker, enhancement, LLM client, audit).

**Tech Stack:** FastAPI, Pydantic, httpx, pytest

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `app/router/openai_compat/models.py` | Modify | Add `ResponsesRequest` and `ResponsesResponse` models |
| `app/router/openai_compat/router.py` | Modify | Add `POST /responses` endpoint + helpers |
| `app/tests/test_openai_compat.py` | Modify | Add `TestResponsesApi` test class |

---

### Task 1: Add Responses API Pydantic models

**Files:**
- Modify: `app/router/openai_compat/models.py`
- Test: `app/tests/test_openai_compat.py`

- [ ] **Step 1: Write failing tests for the new models**

Add to `app/tests/test_openai_compat.py`, after the existing `TestChatCompletionRequest` class:

```python
from router.openai_compat.models import ResponsesRequest


class TestResponsesRequest:
    """Test Responses API request model parsing."""

    def test_string_input(self):
        """String input is accepted."""
        req = ResponsesRequest(model="gemma-3-4b", input="Hello world")
        assert req.input == "Hello world"
        assert req.instructions is None
        assert req.stream is False

    def test_array_input(self):
        """Array of message objects is accepted."""
        req = ResponsesRequest(
            model="gemma-3-4b",
            input=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ],
        )
        assert isinstance(req.input, list)
        assert len(req.input) == 2

    def test_with_instructions(self):
        """Instructions field maps to system prompt."""
        req = ResponsesRequest(
            model="gemma-3-4b",
            input="Hello",
            instructions="Be concise",
        )
        assert req.instructions == "Be concise"

    def test_max_output_tokens(self):
        """max_output_tokens is accepted (maps to max_tokens)."""
        req = ResponsesRequest(
            model="gemma-3-4b",
            input="Hello",
            max_output_tokens=500,
        )
        assert req.max_output_tokens == 500

    def test_defaults(self):
        """Default values are sensible."""
        req = ResponsesRequest(model="gemma-3-4b", input="Hi")
        assert req.temperature == 0.7
        assert req.top_p is None
        assert req.max_output_tokens is None
        assert req.stream is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd app && python -m pytest tests/test_openai_compat.py::TestResponsesRequest -v`
Expected: FAIL with `ImportError: cannot import name 'ResponsesRequest'`

- [ ] **Step 3: Implement the models**

Add to the end of `app/router/openai_compat/models.py`:

```python
class ResponsesRequest(BaseModel):
    """OpenAI Responses API request body.

    Translates to Chat Completions internally. Accepts string or
    message-array input, with optional system instructions.
    """

    model: str
    input: str | list[dict[str, str]]
    instructions: str | None = None
    temperature: float = 0.7
    max_output_tokens: int | None = None
    top_p: float | None = None
    stream: bool = False


class ResponsesContentBlock(BaseModel):
    """Content block in a Responses API output message."""

    type: str  # "output_text" or "thinking"
    text: str | None = None
    thinking: str | None = None


class ResponsesOutputMessage(BaseModel):
    """Output message in Responses API format."""

    type: str = "message"
    role: str = "assistant"
    content: list[ResponsesContentBlock]


class ResponsesResponse(BaseModel):
    """OpenAI Responses API response body."""

    id: str
    object: str = "response"
    created_at: int
    model: str
    output: list[ResponsesOutputMessage]
    output_text: str
    usage: dict[str, int] | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd app && python -m pytest tests/test_openai_compat.py::TestResponsesRequest -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/router/openai_compat/models.py app/tests/test_openai_compat.py
git commit -m "feat: add Pydantic models for Responses API adapter"
```

---

### Task 2: Add input translation helper

**Files:**
- Modify: `app/router/openai_compat/router.py`
- Test: `app/tests/test_openai_compat.py`

- [ ] **Step 1: Write failing tests for the translation helper**

Add to `app/tests/test_openai_compat.py`:

```python
from router.openai_compat.router import _translate_responses_to_messages


class TestTranslateResponsesToMessages:
    """Test Responses API input → Chat Completions messages translation."""

    def test_string_input(self):
        """String input becomes a single user message."""
        messages = _translate_responses_to_messages("Hello world", instructions=None)
        assert messages == [{"role": "user", "content": "Hello world"}]

    def test_string_input_with_instructions(self):
        """Instructions prepended as system message."""
        messages = _translate_responses_to_messages(
            "Hello", instructions="Be concise"
        )
        assert messages == [
            {"role": "system", "content": "Be concise"},
            {"role": "user", "content": "Hello"},
        ]

    def test_array_input(self):
        """Array input passed through as messages."""
        input_msgs = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": "Second"},
        ]
        messages = _translate_responses_to_messages(input_msgs, instructions=None)
        assert messages == input_msgs

    def test_array_input_with_instructions(self):
        """Instructions prepended before array messages."""
        input_msgs = [{"role": "user", "content": "Hello"}]
        messages = _translate_responses_to_messages(
            input_msgs, instructions="You are helpful"
        )
        assert len(messages) == 2
        assert messages[0] == {"role": "system", "content": "You are helpful"}
        assert messages[1] == {"role": "user", "content": "Hello"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd app && python -m pytest tests/test_openai_compat.py::TestTranslateResponsesToMessages -v`
Expected: FAIL with `ImportError: cannot import name '_translate_responses_to_messages'`

- [ ] **Step 3: Implement the helper**

Add to `app/router/openai_compat/router.py`, after the existing `_find_last_user_message` function:

```python
def _translate_responses_to_messages(
    input_data: str | list[dict[str, str]],
    instructions: str | None,
) -> list[dict[str, str]]:
    """Convert Responses API input + instructions to Chat Completions messages.

    Args:
        input_data: String (single user message) or array of message dicts.
        instructions: Optional system prompt to prepend.

    Returns:
        List of message dicts for Chat Completions API.
    """
    messages: list[dict[str, str]] = []

    if instructions:
        messages.append({"role": "system", "content": instructions})

    if isinstance(input_data, str):
        messages.append({"role": "user", "content": input_data})
    else:
        messages.extend(input_data)

    return messages
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd app && python -m pytest tests/test_openai_compat.py::TestTranslateResponsesToMessages -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/router/openai_compat/router.py app/tests/test_openai_compat.py
git commit -m "feat: add input translation helper for Responses API"
```

---

### Task 3: Add response builder helper

**Files:**
- Modify: `app/router/openai_compat/router.py`
- Test: `app/tests/test_openai_compat.py`

- [ ] **Step 1: Write failing tests for the response builder**

Add to `app/tests/test_openai_compat.py`:

```python
from router.openai_compat.router import _build_responses_response


class TestBuildResponsesResponse:
    """Test Chat Completions result → Responses API response wrapping."""

    def test_basic_response(self):
        """Wraps a simple completion into Responses format."""
        chat_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1700000000,
            "model": "gemma-3-4b",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello there!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }
        result = _build_responses_response(chat_response)

        assert result["object"] == "response"
        assert result["id"].startswith("resp_")
        assert result["model"] == "gemma-3-4b"
        assert result["output_text"] == "Hello there!"
        assert len(result["output"]) == 1
        assert result["output"][0]["type"] == "message"
        assert result["output"][0]["content"][0]["type"] == "output_text"
        assert result["output"][0]["content"][0]["text"] == "Hello there!"
        assert result["usage"]["input_tokens"] == 10
        assert result["usage"]["output_tokens"] == 5
        assert result["usage"]["total_tokens"] == 15

    def test_response_with_reasoning(self):
        """Includes thinking block when reasoning_content is present."""
        chat_response = {
            "id": "chatcmpl-456",
            "object": "chat.completion",
            "created": 1700000000,
            "model": "qwen3-coder:30b",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "The answer is 42.",
                        "reasoning_content": "Let me think step by step...",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 30,
                "total_tokens": 50,
            },
        }
        result = _build_responses_response(chat_response)

        assert len(result["output"][0]["content"]) == 2
        assert result["output"][0]["content"][0]["type"] == "thinking"
        assert result["output"][0]["content"][0]["thinking"] == "Let me think step by step..."
        assert result["output"][0]["content"][1]["type"] == "output_text"
        assert result["output"][0]["content"][1]["text"] == "The answer is 42."
        assert result["output_text"] == "The answer is 42."

    def test_response_without_usage(self):
        """Handles missing usage gracefully."""
        chat_response = {
            "id": "chatcmpl-789",
            "object": "chat.completion",
            "created": 1700000000,
            "model": "gemma-3-4b",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hi"},
                    "finish_reason": "stop",
                }
            ],
        }
        result = _build_responses_response(chat_response)

        assert result["output_text"] == "Hi"
        assert result["usage"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd app && python -m pytest tests/test_openai_compat.py::TestBuildResponsesResponse -v`
Expected: FAIL with `ImportError: cannot import name '_build_responses_response'`

- [ ] **Step 3: Implement the response builder**

Add to `app/router/openai_compat/router.py`, after `_translate_responses_to_messages`:

```python
import uuid


def _build_responses_response(chat_response: dict) -> dict:
    """Wrap a Chat Completions response dict into Responses API format.

    Args:
        chat_response: Raw dict from LLMClient.chat_completion().model_dump()

    Returns:
        Dict matching the OpenAI Responses API shape.
    """
    message = chat_response["choices"][0]["message"]
    text = message.get("content", "")
    reasoning = message.get("reasoning_content")

    content_blocks = []
    if reasoning:
        content_blocks.append({"type": "thinking", "thinking": reasoning})
    content_blocks.append({"type": "output_text", "text": text})

    # Map usage field names: prompt_tokens → input_tokens
    raw_usage = chat_response.get("usage")
    usage = None
    if raw_usage:
        usage = {
            "input_tokens": raw_usage.get("prompt_tokens", 0),
            "output_tokens": raw_usage.get("completion_tokens", 0),
            "total_tokens": raw_usage.get("total_tokens", 0),
        }

    return {
        "id": f"resp_{uuid.uuid4().hex[:24]}",
        "object": "response",
        "created_at": chat_response.get("created", 0),
        "model": chat_response.get("model", ""),
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": content_blocks,
            }
        ],
        "output_text": text,
        "usage": usage,
    }
```

Note: add `import uuid` to the imports at the top of `router.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd app && python -m pytest tests/test_openai_compat.py::TestBuildResponsesResponse -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/router/openai_compat/router.py app/tests/test_openai_compat.py
git commit -m "feat: add response builder helper for Responses API"
```

---

### Task 4: Add POST /v1/responses endpoint

**Files:**
- Modify: `app/router/openai_compat/router.py` (inside `create_openai_compat_router`)
- Test: `app/tests/test_openai_compat.py`

- [ ] **Step 1: Write failing tests for the endpoint**

Add to `app/tests/test_openai_compat.py`:

```python
from unittest.mock import patch


class TestResponsesEndpoint:
    """Test POST /v1/responses endpoint behavior."""

    def test_missing_auth_returns_401(self, client):
        """Request without Authorization header returns 401."""
        response = client.post(
            "/v1/responses",
            json={"model": "gemma-3-4b", "input": "Hello"},
        )
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Request with invalid bearer token returns 401."""
        response = client.post(
            "/v1/responses",
            json={"model": "gemma-3-4b", "input": "Hello"},
            headers={"Authorization": "Bearer sk-invalid-garbage"},
        )
        assert response.status_code == 401

    def test_stream_true_returns_400(self, client):
        """Streaming is not supported — returns 400."""
        response = client.post(
            "/v1/responses",
            json={"model": "gemma-3-4b", "input": "Hello", "stream": True},
            headers={"Authorization": "Bearer sk-prompthub-passthrough-def456"},
        )
        assert response.status_code == 400
        assert "streaming" in response.json()["detail"]["error"]["message"].lower()

    def test_invalid_model_returns_422(self, client):
        """Placeholder model name returns 422."""
        response = client.post(
            "/v1/responses",
            json={"model": "string", "input": "Hello"},
            headers={"Authorization": "Bearer sk-prompthub-passthrough-def456"},
        )
        assert response.status_code == 422

    @patch("router.openai_compat.router.LLMClient.chat_completion")
    def test_string_input_success(self, mock_chat, client):
        """String input returns valid Responses API format."""
        from router.enhancement.llm_client import (
            ChatCompletionChoice,
            ChatCompletionResponse,
            ChatMessage,
        )

        mock_chat.return_value = ChatCompletionResponse(
            id="chatcmpl-test",
            object="chat.completion",
            created=1700000000,
            model="gemma-3-4b",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content="Hello!"),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        )

        response = client.post(
            "/v1/responses",
            json={"model": "gemma-3-4b", "input": "Hi there"},
            headers={"Authorization": "Bearer sk-prompthub-passthrough-def456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "response"
        assert data["id"].startswith("resp_")
        assert data["output_text"] == "Hello!"
        assert data["output"][0]["type"] == "message"
        assert data["usage"]["input_tokens"] == 5

    @patch("router.openai_compat.router.LLMClient.chat_completion")
    def test_array_input_with_instructions(self, mock_chat, client):
        """Array input with instructions translates correctly."""
        from router.enhancement.llm_client import (
            ChatCompletionChoice,
            ChatCompletionResponse,
            ChatMessage,
        )

        mock_chat.return_value = ChatCompletionResponse(
            id="chatcmpl-test2",
            object="chat.completion",
            created=1700000000,
            model="gemma-3-4b",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content="Sure!"),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
        )

        response = client.post(
            "/v1/responses",
            json={
                "model": "gemma-3-4b",
                "input": [{"role": "user", "content": "Help me"}],
                "instructions": "Be concise",
            },
            headers={"Authorization": "Bearer sk-prompthub-passthrough-def456"},
        )
        assert response.status_code == 200

        # Verify instructions were prepended as system message
        call_kwargs = mock_chat.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        assert messages[0] == {"role": "system", "content": "Be concise"}
        assert messages[1] == {"role": "user", "content": "Help me"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd app && python -m pytest tests/test_openai_compat.py::TestResponsesEndpoint -v`
Expected: FAIL — 404 (endpoint doesn't exist yet)

- [ ] **Step 3: Implement the endpoint**

Add inside `create_openai_compat_router()` in `app/router/openai_compat/router.py`, after the `reload_api_keys` endpoint and before `return router`:

```python
    @router.post("/responses")
    async def responses(
        body: ResponsesRequest,
        request: Request,
        api_key: ApiKeyConfig = Depends(authenticate),
    ):
        """OpenAI Responses API endpoint (non-streaming).

        Translates Responses API format to Chat Completions, proxies to
        LLM server, and wraps the result back into Responses API shape.
        """
        client_name = api_key.client_name

        audit_event(
            event_type="openai_proxy",
            action="responses",
            resource_type="llm",
            resource_name=body.model,
            status="initiated",
            client_name=client_name,
        )

        # Reject streaming — not supported
        if body.stream:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": "Streaming not supported for /v1/responses. Disable streaming in your client.",
                        "type": "invalid_request_error",
                    }
                },
            )

        # Guard: reject placeholder model names
        if not body.model or body.model in ("string", "model", "") or " " in body.model:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid model name: '{body.model}'. Provide a valid model name (e.g. 'gemma-3-4b').",
            )

        # Circuit breaker check
        cb_registry = circuit_breakers()
        breaker = cb_registry.get("llm-proxy") if cb_registry else None
        if breaker:
            try:
                breaker.check()
            except Exception:
                audit_event(
                    event_type="openai_proxy",
                    action="responses",
                    resource_type="llm",
                    resource_name=body.model,
                    status="failed",
                    error="Circuit breaker open",
                )
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": {
                            "message": "Service temporarily unavailable — LLM circuit breaker open",
                            "type": "server_error",
                        }
                    },
                )

        # Translate Responses API input → Chat Completions messages
        messages = _translate_responses_to_messages(body.input, body.instructions)

        # Enhancement: optionally enhance the last user message
        svc = enhancement_service() if api_key.enhance else None
        if svc:
            privacy_override = None
            raw_privacy = request.headers.get("X-Privacy-Level")
            if raw_privacy:
                try:
                    from router.enhancement import PrivacyLevel
                    privacy_override = PrivacyLevel(raw_privacy)
                except ValueError:
                    logger.warning("Invalid X-Privacy-Level: %s", raw_privacy)

            last_user_idx = _find_last_user_message(messages)
            if last_user_idx is not None:
                original = messages[last_user_idx]["content"]
                try:
                    result = await svc.enhance(
                        prompt=original,
                        client_name=client_name,
                        privacy_override=privacy_override,
                    )
                    if result.was_enhanced:
                        messages[last_user_idx] = {
                            **messages[last_user_idx],
                            "content": result.enhanced,
                        }
                except Exception as e:
                    logger.warning("Enhancement failed for %s: %s", client_name, e)

        # Forward to LLM server
        try:
            response = await _llm_client.chat_completion(
                model=body.model,
                messages=messages,
                temperature=body.temperature,
                max_tokens=body.max_output_tokens,
            )
            if breaker:
                breaker.record_success()

            audit_event(
                event_type="openai_proxy",
                action="responses",
                resource_type="llm",
                resource_name=body.model,
                status="success",
            )

            return _build_responses_response(response.model_dump())

        except LLMConnectionError as e:
            if breaker:
                breaker.record_failure(e)
            audit_event(
                event_type="openai_proxy",
                action="responses",
                resource_type="llm",
                resource_name=body.model,
                status="failed",
                error=str(e),
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {"message": f"Cannot reach LLM server: {e}", "type": "server_error"}
                },
            )
        except (LLMError, httpx.HTTPError) as e:
            if breaker:
                breaker.record_failure(e)
            audit_event(
                event_type="openai_proxy",
                action="responses",
                resource_type="llm",
                resource_name=body.model,
                status="failed",
                error=str(e),
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {"message": str(e), "type": "server_error"}
                },
            )
```

Also add the import of `ResponsesRequest` to the imports at the top of `router.py`:

```python
from router.openai_compat.models import ApiKeyConfig, ChatCompletionRequest, ResponsesRequest
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd app && python -m pytest tests/test_openai_compat.py::TestResponsesEndpoint -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Run the full test file to check for regressions**

Run: `cd app && python -m pytest tests/test_openai_compat.py -v`
Expected: All tests PASS (existing + new)

- [ ] **Step 6: Commit**

```bash
git add app/router/openai_compat/router.py app/router/openai_compat/models.py app/tests/test_openai_compat.py
git commit -m "feat: add POST /v1/responses endpoint for Responses API clients"
```

---

### Task 5: Verify full stack and run linting

**Files:**
- No new files — verification only

- [ ] **Step 1: Run the full test suite**

Run: `cd app && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Run ruff linting**

Run: `cd app && ruff check router/openai_compat/`
Expected: No errors

- [ ] **Step 3: Run ruff formatting**

Run: `cd app && ruff format router/openai_compat/`
Expected: Files already formatted (or reformatted)

- [ ] **Step 4: Verify endpoint is registered by checking imports**

Run: `cd app && python -c "from router.openai_compat.router import create_openai_compat_router; print('Import OK')"`
Expected: `Import OK`

- [ ] **Step 5: Commit any formatting fixes**

```bash
git add -u && git diff --cached --quiet || git commit -m "style: format Responses API code"
```
