"""Tests for OpenAI-compatible API proxy.

Tests cover:
- API key loading and validation
- Request model parsing
- Enhancement integration (only last user message enhanced)
- Router endpoint behavior (auth, circuit breaker, forwarding)
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from router.enhancement.llm_client import LLMConnectionError, LLMError
from router.openai_compat.auth import ApiKeyManager
from router.openai_compat.models import (
    ChatCompletionRequest,
    ResponsesRequest,
)
from router.openai_compat import router as router_module
from router.openai_compat.router import (
    _build_responses_response,
    _find_last_user_message,
    _flatten_content,
    _handle_llm_error,
    _responses_tool_choice_to_chat,
    _responses_tools_to_chat,
    _translate_responses_to_messages,
    create_openai_compat_router,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_api_keys():
    """Sample API keys config data."""
    return {
        "keys": {
            "sk-prompthub-test-abc123": {
                "client_name": "test-client",
                "enhance": True,
                "description": "Test client",
            },
            "sk-prompthub-passthrough-def456": {
                "client_name": "passthrough",
                "enhance": False,
                "description": "No enhancement",
            },
        }
    }


@pytest.fixture
def api_keys_file(tmp_path, sample_api_keys):
    """Write sample API keys to a temp file and return its path."""
    path = tmp_path / "api-keys.json"
    path.write_text(json.dumps(sample_api_keys))
    return path


@pytest.fixture
def api_key_manager(api_keys_file):
    """Configured ApiKeyManager loaded from temp file."""
    mgr = ApiKeyManager(config_path=api_keys_file)
    mgr.load()
    return mgr


@pytest.fixture
def mock_enhancement_service():
    """Mock EnhancementService that returns an enhanced prompt."""
    svc = AsyncMock()
    result = MagicMock()
    result.was_enhanced = True
    result.enhanced = "Enhanced: Hello world"
    result.cached = False
    svc.enhance.return_value = result
    return svc


@pytest.fixture
def mock_circuit_breakers():
    """Mock CircuitBreakerRegistry with a no-op breaker."""
    breaker = MagicMock()
    breaker.check.return_value = None
    breaker.record_success.return_value = None
    breaker.record_failure.return_value = None

    registry = MagicMock()
    registry.get.return_value = breaker
    return registry


@pytest.fixture
def test_app(api_key_manager, mock_enhancement_service, mock_circuit_breakers):
    """FastAPI test app with the OpenAI-compat router registered."""
    app = FastAPI()
    router = create_openai_compat_router(
        enhancement_service=lambda: mock_enhancement_service,
        circuit_breakers=lambda: mock_circuit_breakers,
        api_key_manager=api_key_manager,
        llm_base_url="http://localhost:1234/v1",
        llm_timeout=30.0,
    )
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app):
    """TestClient for the test app."""
    return TestClient(test_app)


# =============================================================================
# ApiKeyManager Tests
# =============================================================================


class TestApiKeyManager:
    """Test API key loading and validation."""

    def test_load_valid_config(self, api_key_manager):
        """Loaded config has the expected number of keys."""
        assert api_key_manager.key_count == 2

    def test_validate_known_token(self, api_key_manager):
        """Known token returns correct ApiKeyConfig."""
        config = api_key_manager.validate_token("sk-prompthub-test-abc123")
        assert config is not None
        assert config.client_name == "test-client"
        assert config.enhance is True

    def test_validate_unknown_token(self, api_key_manager):
        """Unknown token returns None."""
        assert api_key_manager.validate_token("sk-invalid-token") is None

    def test_reload_picks_up_changes(self, api_keys_file, api_key_manager):
        """Reloading config picks up new keys."""
        new_data = {
            "keys": {
                "sk-new-key": {
                    "client_name": "new",
                    "enhance": False,
                    "description": "Added",
                }
            }
        }
        api_keys_file.write_text(json.dumps(new_data))
        api_key_manager.reload()

        assert api_key_manager.key_count == 1
        assert api_key_manager.validate_token("sk-new-key") is not None
        assert api_key_manager.validate_token("sk-prompthub-test-abc123") is None

    def test_missing_config_file(self, tmp_path):
        """Missing config file logs warning, zero keys loaded."""
        mgr = ApiKeyManager(config_path=tmp_path / "nonexistent.json")
        mgr.load()
        assert mgr.key_count == 0

    def test_no_config_path(self):
        """None config path results in zero keys."""
        mgr = ApiKeyManager(config_path=None)
        mgr.load()
        assert mgr.key_count == 0


# =============================================================================
# Shipped Config Artifact Tests
# =============================================================================

# Resolve app/configs/ relative to this test file (app/tests/).
_CONFIGS_DIR = Path(__file__).resolve().parents[1] / "configs"


class TestShippedConfigArtifacts:
    """Guard the real config files against drifting from the loader.

    The loader (ApiKeyManager.load) is fail-closed: a malformed config logs an
    error and leaves zero keys, silently rejecting all /v1/ requests. Unit tests
    that build their own temp config never catch a broken *shipped* file, so
    these tests load the actual artifacts through the production code path and
    assert they yield a non-empty, well-formed registry.

    Both files must use the map shape {"keys": {<token>: {...}}} — NOT a bare
    array. An array loads as zero keys, which is the exact regression these
    tests exist to prevent.
    """

    def test_shipped_api_keys_loads(self):
        """app/configs/api-keys.json loads into a non-empty registry."""
        path = _CONFIGS_DIR / "api-keys.json"
        if not path.exists():
            pytest.skip("api-keys.json not present in this checkout")
        mgr = ApiKeyManager(config_path=path)
        mgr.load()
        assert mgr.key_count > 0, (
            "api-keys.json loaded zero keys — likely wrong shape "
            "(must be {'keys': {<token>: {...}}}, not a bare array)"
        )

    def test_example_api_keys_loads(self):
        """api-keys.json.example must match the loader's expected shape.

        A .example is copy-paste onboarding material; if it drifts from the
        model, users reproduce the fail-closed bug by following it.
        """
        path = _CONFIGS_DIR / "api-keys.json.example"
        if not path.exists():
            pytest.skip("api-keys.json.example not present in this checkout")
        mgr = ApiKeyManager(config_path=path)
        mgr.load()
        assert mgr.key_count > 0, (
            "api-keys.json.example loaded zero keys — it has drifted from "
            "ApiKeysRegistry; regenerate it as a token-keyed map"
        )
        # Enumerate tokens from the file, then verify each resolves through the
        # public validate_token() API (rather than reaching into the registry).
        tokens = json.loads(path.read_text())["keys"]
        for token in tokens:
            assert token.startswith("sk-"), f"example token {token!r} lacks sk- prefix"
            cfg = mgr.validate_token(token)
            assert cfg is not None, f"example token {token!r} did not load"
            assert cfg.client_name, f"example entry {token!r} missing client_name"


# =============================================================================
# Model Tests
# =============================================================================


class TestChatCompletionRequest:
    """Test OpenAI request model parsing."""

    def test_minimal_request(self):
        """Minimal valid request with defaults."""
        req = ChatCompletionRequest(
            model="llama3.2",
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert req.stream is False
        assert req.temperature == 0.7
        assert req.max_tokens is None

    def test_streaming_request(self):
        """stream=True parses correctly."""
        req = ChatCompletionRequest(
            model="llama3.2",
            messages=[{"role": "user", "content": "Hi"}],
            stream=True,
        )
        assert req.stream is True

    def test_full_request(self):
        """All fields parse correctly."""
        req = ChatCompletionRequest(
            model="deepseek-r1:latest",
            messages=[
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hello"},
            ],
            temperature=0.5,
            max_tokens=100,
            top_p=0.9,
            stop=["\n"],
        )
        assert req.model == "deepseek-r1:latest"
        assert len(req.messages) == 2
        assert req.temperature == 0.5


# =============================================================================
# Function-Calling / Tool Forwarding Tests
# =============================================================================


class TestToolForwarding:
    """Function-calling params must survive the /v1/chat/completions proxy.

    Regression: the proxy dropped `tools`/`tool_choice` on both the streaming
    and non-streaming paths, so the upstream model never saw tool definitions
    and narrated instead of emitting `tool_calls`. It also typed `messages`
    too narrowly to accept multi-turn tool conversations.
    """

    AUTH = {"Authorization": "Bearer sk-prompthub-passthrough-def456"}

    SAMPLE_TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the weather",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
    ]

    @patch("router.openai_compat.router._stream_with_breaker")
    def test_streaming_forwards_tools(self, mock_stream, client):
        """A streaming request forwards tools + tool_choice in the payload."""

        async def _fake_stream(*args, **kwargs):
            yield "data: [DONE]\n\n"

        mock_stream.side_effect = _fake_stream

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3-4b-instruct-2507",
                "messages": [{"role": "user", "content": "weather in Paris?"}],
                "stream": True,
                "tools": self.SAMPLE_TOOLS,
                "tool_choice": "auto",
            },
            headers=self.AUTH,
        )
        assert response.status_code == 200, response.text

        # First positional arg to _stream_with_breaker is the payload dict.
        payload = mock_stream.call_args.args[0]
        assert payload["tools"] == self.SAMPLE_TOOLS
        assert payload["tool_choice"] == "auto"

    @patch("router.openai_compat.router.LLMClient.chat_completion")
    def test_non_streaming_forwards_tools_and_relays_tool_calls(
        self, mock_chat, client
    ):
        """Non-streaming path passes tools upstream and relays tool_calls back."""
        from router.enhancement.llm_client import (
            ChatCompletionChoice,
            ChatCompletionResponse,
            ChatMessage,
        )

        tool_calls = [
            {
                "id": "call_abc",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"city": "Paris"}',
                },
            }
        ]
        mock_chat.return_value = ChatCompletionResponse(
            id="chatcmpl-test",
            object="chat.completion",
            created=1700000000,
            model="qwen3-4b-instruct-2507",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant", content=None, tool_calls=tool_calls
                    ),
                    finish_reason="tool_calls",
                )
            ],
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3-4b-instruct-2507",
                "messages": [{"role": "user", "content": "weather in Paris?"}],
                "tools": self.SAMPLE_TOOLS,
                "tool_choice": "auto",
            },
            headers=self.AUTH,
        )
        assert response.status_code == 200, response.text

        # Upstream client received the tools.
        kwargs = mock_chat.call_args.kwargs
        assert kwargs["tools"] == self.SAMPLE_TOOLS
        assert kwargs["tool_choice"] == "auto"

        # Response relays tool_calls and does not choke on null content.
        body = response.json()
        msg = body["choices"][0]["message"]
        assert msg["content"] is None
        assert msg["tool_calls"] == tool_calls

    def test_multi_turn_tool_messages_accepted(self):
        """Assistant tool_calls + tool-role messages validate (no 422)."""
        req = ChatCompletionRequest(
            model="qwen3-4b-instruct-2507",
            messages=[
                {"role": "user", "content": "weather in Paris?"},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_abc",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"city": "Paris"}',
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": "call_abc",
                    "content": "sunny, 20C",
                },
            ],
            tools=self.SAMPLE_TOOLS,
            tool_choice="auto",
        )
        assert len(req.messages) == 3
        assert req.messages[1]["tool_calls"][0]["id"] == "call_abc"
        assert req.tools == self.SAMPLE_TOOLS


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestFindLastUserMessage:
    """Test the helper that locates the last user message."""

    def test_single_user_message(self):
        messages = [{"role": "user", "content": "Hello"}]
        assert _find_last_user_message(messages) == 0

    def test_multiple_messages(self):
        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": "Second"},
        ]
        assert _find_last_user_message(messages) == 3

    def test_no_user_message(self):
        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "assistant", "content": "Hello"},
        ]
        assert _find_last_user_message(messages) is None

    def test_empty_messages(self):
        assert _find_last_user_message([]) is None

    def test_system_messages_not_matched(self):
        """System messages should never be treated as user messages."""
        messages = [{"role": "system", "content": "You are helpful."}]
        assert _find_last_user_message(messages) is None


# =============================================================================
# Endpoint Tests
# =============================================================================


class TestAuthEndpoints:
    """Test authentication behavior of /v1/ endpoints."""

    def test_missing_auth_returns_401(self, client):
        """Request without Authorization header returns 401."""
        response = client.post(
            "/v1/chat/completions",
            json={"model": "llama3.2", "messages": [{"role": "user", "content": "Hi"}]},
        )
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Request with invalid bearer token returns 401."""
        response = client.post(
            "/v1/chat/completions",
            json={"model": "llama3.2", "messages": [{"role": "user", "content": "Hi"}]},
            headers={"Authorization": "Bearer sk-invalid-garbage"},
        )
        assert response.status_code == 401
        body = response.json()
        assert "error" in body["detail"]

    def test_models_no_auth_required(self, client):
        """GET /v1/models is unauthenticated (model listing is non-sensitive)."""
        response = client.get("/v1/models")
        # Returns 200 with models list or 502 if LLM server unreachable in tests
        assert response.status_code in [200, 502]

    def test_api_keys_reload_no_auth_required(self, client):
        """POST /v1/api-keys/reload works without auth (admin endpoint)."""
        response = client.post("/v1/api-keys/reload")
        assert response.status_code == 200
        assert "count" in response.json()


class TestApiKeysReload:
    """Test the API keys reload endpoint."""

    def test_reload_returns_count(self, client):
        response = client.post("/v1/api-keys/reload")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["message"] == "API keys reloaded"


class TestChatCompletionsModelValidation:
    """Validate the /v1/chat/completions model-name guard.

    The guard rejects OpenAPI swagger placeholders (`"string"`, `"model"`, empty),
    but accepts any other string — including names with spaces, which Qwen Code's
    VS Code Companion sends as provider display labels. An earlier version of
    this guard rejected any model name containing a space, which broke valid
    provider configurations.
    """

    AUTH = {"Authorization": "Bearer sk-prompthub-passthrough-def456"}

    def test_placeholder_string_returns_422(self, client):
        """OpenAPI swagger default `"string"` is rejected."""
        response = client.post(
            "/v1/chat/completions",
            json={"model": "string", "messages": [{"role": "user", "content": "hi"}]},
            headers=self.AUTH,
        )
        assert response.status_code == 422

    def test_placeholder_model_returns_422(self, client):
        """OpenAPI default `"model"` placeholder is rejected."""
        response = client.post(
            "/v1/chat/completions",
            json={"model": "model", "messages": [{"role": "user", "content": "hi"}]},
            headers=self.AUTH,
        )
        assert response.status_code == 422

    def test_empty_model_returns_422(self, client):
        """Empty/whitespace-only model is rejected."""
        response = client.post(
            "/v1/chat/completions",
            json={"model": "   ", "messages": [{"role": "user", "content": "hi"}]},
            headers=self.AUTH,
        )
        assert response.status_code == 422

    def test_invalid_model_error_uses_openai_shape(self, client):
        """The 422 body matches OpenAI's error envelope so SDK clients parse it."""
        response = client.post(
            "/v1/chat/completions",
            json={"model": "string", "messages": [{"role": "user", "content": "hi"}]},
            headers=self.AUTH,
        )
        assert response.status_code == 422
        body = response.json()
        # FastAPI wraps HTTPException.detail in `{"detail": ...}`; the detail
        # itself is the OpenAI-style `{"error": {...}}` envelope.
        assert "error" in body["detail"]
        err = body["detail"]["error"]
        assert err["type"] == "invalid_request_error"
        assert err["param"] == "model"
        assert err["code"] == "invalid_model_name"
        assert "Invalid model name" in err["message"]

    @patch("router.openai_compat.router.LLMClient.chat_completion")
    def test_model_name_with_spaces_accepted(self, mock_chat, client):
        """Display names with spaces (e.g. 'GPT-4 Turbo') must not 422.

        Regression test: an earlier guard rejected any model name with a space,
        which broke Qwen Code Companion and similar clients that send the
        provider display label.
        """
        from router.enhancement.llm_client import (
            ChatCompletionChoice,
            ChatCompletionResponse,
            ChatMessage,
        )

        mock_chat.return_value = ChatCompletionResponse(
            id="chatcmpl-test",
            object="chat.completion",
            created=1700000000,
            model="PromptHub Router · Qwen3 4B Instruct 2507",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content="hi"),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "PromptHub Router · Qwen3 4B Instruct 2507",
                "messages": [{"role": "user", "content": "hi"}],
            },
            headers=self.AUTH,
        )
        assert response.status_code != 422, response.json()


# =============================================================================
# Responses API Model Tests
# =============================================================================


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


# =============================================================================
# Translation Helper Tests
# =============================================================================


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


# =============================================================================
# Responses → Chat Completions Tool/Input Translation Tests
# =============================================================================


class TestResponsesToolTranslation:
    """codex sends Responses-format (flat) tools and function_call input items.

    Forwarding them unchanged to LM Studio's /v1/chat/completions produces a
    400. These tests cover the translation helpers and their wire-up on
    /v1/responses.
    """

    AUTH = {"Authorization": "Bearer sk-prompthub-passthrough-def456"}

    FLAT_TOOL = {
        "type": "function",
        "name": "get_weather",
        "description": "Get the weather",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
        "strict": False,
    }

    @patch("router.openai_compat.router.LLMClient.chat_completion")
    def test_responses_translates_flat_tools_to_nested(self, mock_chat, client):
        """A FLAT Responses tool is forwarded in NESTED Chat-Completions shape."""
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
                    message=ChatMessage(role="assistant", content="ok"),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )

        response = client.post(
            "/v1/responses",
            json={
                "model": "gemma-3-4b",
                "input": "weather in Paris?",
                "tools": [self.FLAT_TOOL],
            },
            headers=self.AUTH,
        )
        assert response.status_code == 200, response.text

        tools = mock_chat.call_args.kwargs["tools"]
        assert tools[0]["type"] == "function"
        assert "name" not in tools[0]  # no top-level name in nested shape
        assert tools[0]["function"]["name"] == "get_weather"
        assert tools[0]["function"]["description"] == "Get the weather"
        assert tools[0]["function"]["parameters"] == self.FLAT_TOOL["parameters"]

    def test_responses_tools_to_chat_passthrough_and_none(self):
        """Nested tools pass through unchanged; None returns None."""
        assert _responses_tools_to_chat(None) is None

        nested = [
            {
                "type": "function",
                "function": {"name": "x", "parameters": {"type": "object"}},
            }
        ]
        assert _responses_tools_to_chat(nested) == nested

        out = _responses_tools_to_chat([self.FLAT_TOOL])
        assert out[0]["function"]["name"] == "get_weather"
        assert "name" not in out[0]

    def test_responses_translates_flat_tool_choice(self):
        """Flat tool_choice nests; strings pass through."""
        assert _responses_tool_choice_to_chat("auto") == "auto"
        assert _responses_tool_choice_to_chat("none") == "none"
        assert _responses_tool_choice_to_chat("required") == "required"
        assert _responses_tool_choice_to_chat(None) is None

        flat = {"type": "function", "name": "x"}
        assert _responses_tool_choice_to_chat(flat) == {
            "type": "function",
            "function": {"name": "x"},
        }

        # Already-nested tool_choice passes through.
        nested = {"type": "function", "function": {"name": "x"}}
        assert _responses_tool_choice_to_chat(nested) == nested

    def test_responses_input_function_call_and_output_translation(self):
        """function_call / function_call_output input items become tool messages."""
        input_data = [
            {"role": "user", "content": "write a file"},
            {
                "type": "function_call",
                "call_id": "c1",
                "name": "write_file",
                "arguments": '{"path": "a.txt"}',
            },
            {
                "type": "function_call_output",
                "call_id": "c1",
                "output": "wrote a.txt",
            },
        ]
        messages = _translate_responses_to_messages(input_data, instructions=None)

        assert messages[0] == {"role": "user", "content": "write a file"}

        assistant = messages[1]
        assert assistant["role"] == "assistant"
        assert assistant["content"] is None
        tc = assistant["tool_calls"][0]
        assert tc["id"] == "c1"
        assert tc["type"] == "function"
        assert tc["function"]["name"] == "write_file"
        assert tc["function"]["arguments"] == '{"path": "a.txt"}'

        tool_msg = messages[2]
        assert tool_msg["role"] == "tool"
        assert tool_msg["tool_call_id"] == "c1"
        assert tool_msg["content"] == "wrote a.txt"


# =============================================================================
# Response Builder Tests
# =============================================================================


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


# =============================================================================
# Responses Endpoint Tests
# =============================================================================


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

    @patch("router.openai_compat.router.LLMClient.chat_completion")
    def test_stream_true_emits_text_event_sequence(self, mock_chat, client):
        """stream=True returns SSE with an ordered text event sequence."""
        from router.enhancement.llm_client import (
            ChatCompletionChoice,
            ChatCompletionResponse,
            ChatMessage,
        )

        mock_chat.return_value = ChatCompletionResponse(
            id="chatcmpl-stream",
            object="chat.completion",
            created=1700000000,
            model="gemma-3-4b",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content="Hello there!"),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        )

        response = client.post(
            "/v1/responses",
            json={"model": "gemma-3-4b", "input": "Hi", "stream": True},
            headers={"Authorization": "Bearer sk-prompthub-passthrough-def456"},
        )
        assert response.status_code == 200, response.text
        assert response.headers["content-type"].startswith("text/event-stream")

        body = response.text
        # Event types appear in the expected order.
        types_in_order = [
            "response.created",
            "response.output_item.added",
            "response.output_text.delta",
            "response.completed",
        ]
        last = -1
        for t in types_in_order:
            idx = body.find(f"event: {t}\n")
            assert idx != -1, f"missing event {t}\n{body}"
            assert idx > last, f"event {t} out of order\n{body}"
            last = idx

        # The text delta carries the full assistant content.
        delta_events = [
            json.loads(line[len("data: "):])
            for line in body.splitlines()
            if line.startswith("data: ") and line != "data: [DONE]"
        ]
        deltas = [
            e for e in delta_events if e.get("type") == "response.output_text.delta"
        ]
        assert deltas, "no output_text.delta event"
        assert deltas[0]["delta"] == "Hello there!"

        assert body.rstrip().endswith("data: [DONE]")

    def test_invalid_model_returns_422(self, client):
        """Placeholder model name returns 422 with OpenAI-shaped error body."""
        response = client.post(
            "/v1/responses",
            json={"model": "string", "input": "Hello"},
            headers={"Authorization": "Bearer sk-prompthub-passthrough-def456"},
        )
        assert response.status_code == 422
        err = response.json()["detail"]["error"]
        assert err["type"] == "invalid_request_error"
        assert err["param"] == "model"
        assert err["code"] == "invalid_model_name"

    @patch("router.openai_compat.router.LLMClient.chat_completion")
    def test_model_name_with_spaces_accepted_on_responses(self, mock_chat, client):
        """Regression: model names with spaces must not 422 on /v1/responses either."""
        from router.enhancement.llm_client import (
            ChatCompletionChoice,
            ChatCompletionResponse,
            ChatMessage,
        )

        mock_chat.return_value = ChatCompletionResponse(
            id="chatcmpl-test",
            object="chat.completion",
            created=1700000000,
            model="GPT-4 Turbo (via OpenRouter)",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content="hi"),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )

        response = client.post(
            "/v1/responses",
            json={"model": "GPT-4 Turbo (via OpenRouter)", "input": "Hello"},
            headers={"Authorization": "Bearer sk-prompthub-passthrough-def456"},
        )
        assert response.status_code != 422, response.json()

    @patch("router.openai_compat.router.LLMClient.chat_completion")
    def test_stream_emits_function_call_items(self, mock_chat, client):
        """stream=True with tool_calls emits function_call item events."""
        from router.enhancement.llm_client import (
            ChatCompletionChoice,
            ChatCompletionResponse,
            ChatMessage,
        )

        tool_calls = [
            {
                "id": "call_abc",
                "type": "function",
                "function": {
                    "name": "write_file",
                    "arguments": '{"path": "a.txt", "content": "hi"}',
                },
            }
        ]
        mock_chat.return_value = ChatCompletionResponse(
            id="chatcmpl-fc",
            object="chat.completion",
            created=1700000000,
            model="gemma-3-4b",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant", content=None, tool_calls=tool_calls
                    ),
                    finish_reason="tool_calls",
                )
            ],
            usage={"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        )

        response = client.post(
            "/v1/responses",
            json={"model": "gemma-3-4b", "input": "write a file", "stream": True},
            headers={"Authorization": "Bearer sk-prompthub-passthrough-def456"},
        )
        assert response.status_code == 200, response.text

        body = response.text
        events = [
            json.loads(line[len("data: "):])
            for line in body.splitlines()
            if line.startswith("data: ") and line != "data: [DONE]"
        ]
        by_type = {}
        for e in events:
            by_type.setdefault(e.get("type"), []).append(e)

        # function_call item added
        added = [
            e
            for e in by_type.get("response.output_item.added", [])
            if e["item"].get("type") == "function_call"
        ]
        assert added, "no function_call output_item.added"
        item = added[0]["item"]
        assert item["call_id"] == "call_abc"
        assert item["name"] == "write_file"
        assert item["arguments"] == '{"path": "a.txt", "content": "hi"}'

        # arguments delta + done
        delta = by_type.get("response.function_call_arguments.delta", [])
        assert delta and delta[0]["delta"] == '{"path": "a.txt", "content": "hi"}'
        assert by_type.get("response.function_call_arguments.done")

        # output_item.done for the function_call
        done_fc = [
            e
            for e in by_type.get("response.output_item.done", [])
            if e["item"].get("type") == "function_call"
        ]
        assert done_fc, "no function_call output_item.done"

        # response.completed includes the function_call item in output
        completed = by_type["response.completed"][0]
        outputs = completed["response"]["output"]
        fc_outputs = [o for o in outputs if o.get("type") == "function_call"]
        assert fc_outputs, "function_call missing from completed output"
        assert fc_outputs[0]["call_id"] == "call_abc"
        assert fc_outputs[0]["name"] == "write_file"

    def test_responses_stream_emits_created_before_model_awaited(self, client):
        """The first SSE chunk (response.created) is emitted BEFORE the model
        completion is awaited.

        This is the latency-bug regression test. Previously the handler awaited
        the full completion before the streaming generator emitted any byte, so
        time-to-first-byte == total time and slow backends timed out clients.

        Asserts via call-order instrumentation: a shared `order` list records
        when `response.created` is built (`sse:response.created`) and when the
        upstream `chat_completion` is awaited (`chat_completion`). The created
        event must be recorded first.
        """
        from router.enhancement.llm_client import (
            ChatCompletionChoice,
            ChatCompletionResponse,
            ChatMessage,
        )

        order: list[str] = []

        async def _record_chat(*args, **kwargs):
            order.append("chat_completion")
            return ChatCompletionResponse(
                id="chatcmpl-order",
                object="chat.completion",
                created=1700000000,
                model="gemma-3-4b",
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content="hi"),
                        finish_reason="stop",
                    )
                ],
                usage={
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 2,
                },
            )

        real_sse_event = router_module._sse_event

        def _record_sse(event_type, data):
            order.append(f"sse:{event_type}")
            return real_sse_event(event_type, data)

        with (
            patch(
                "router.openai_compat.router.LLMClient.chat_completion",
                new=_record_chat,
            ),
            patch(
                "router.openai_compat.router._sse_event",
                new=_record_sse,
            ),
        ):
            response = client.post(
                "/v1/responses",
                json={"model": "gemma-3-4b", "input": "Hi", "stream": True},
                headers={
                    "Authorization": "Bearer sk-prompthub-passthrough-def456"
                },
            )

        assert response.status_code == 200, response.text

        # response.created must be recorded BEFORE the model is awaited.
        assert "sse:response.created" in order, order
        assert "chat_completion" in order, order
        created_idx = order.index("sse:response.created")
        awaited_idx = order.index("chat_completion")
        assert created_idx < awaited_idx, (
            f"response.created (idx {created_idx}) was not emitted before "
            f"chat_completion was awaited (idx {awaited_idx}): {order}"
        )

        # And the stream is well-formed: exactly one response.created event,
        # ending with [DONE].
        body = response.text
        assert body.count("event: response.created\n") == 1, body
        assert body.rstrip().endswith("data: [DONE]")

    @patch("router.openai_compat.router.LLMClient.chat_completion")
    def test_responses_forwards_tools(self, mock_chat, client):
        """A non-stream /responses request forwards tools into chat_completion."""
        from router.enhancement.llm_client import (
            ChatCompletionChoice,
            ChatCompletionResponse,
            ChatMessage,
        )

        sample_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the weather",
                    "parameters": {
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                        "required": ["city"],
                    },
                },
            }
        ]

        mock_chat.return_value = ChatCompletionResponse(
            id="chatcmpl-test",
            object="chat.completion",
            created=1700000000,
            model="gemma-3-4b",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content="ok"),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )

        response = client.post(
            "/v1/responses",
            json={
                "model": "gemma-3-4b",
                "input": "weather in Paris?",
                "tools": sample_tools,
                "tool_choice": "auto",
            },
            headers={"Authorization": "Bearer sk-prompthub-passthrough-def456"},
        )
        assert response.status_code == 200, response.text

        kwargs = mock_chat.call_args.kwargs
        assert kwargs["tools"] == sample_tools
        assert kwargs["tool_choice"] == "auto"

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


# =============================================================================
# _handle_llm_error Tests
# =============================================================================


class TestHandleLlmError:
    """Test the shared LLM error handler extracted from both endpoints."""

    def test_connection_error_raises_502_with_prefix(self):
        """LLMConnectionError produces 'Cannot reach LLM server' message."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _handle_llm_error(
                LLMConnectionError("Connection refused"),
                breaker=None,
                action="chat_completion",
                model="test-model",
            )
        assert exc_info.value.status_code == 502
        assert "Cannot reach LLM server" in exc_info.value.detail["error"]["message"]

    def test_generic_llm_error_raises_502(self):
        """LLMError produces a plain error message."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _handle_llm_error(
                LLMError("Model overloaded"),
                breaker=None,
                action="responses",
                model="test-model",
            )
        assert exc_info.value.status_code == 502
        assert exc_info.value.detail["error"]["message"] == "Model overloaded"

    def test_records_breaker_failure(self):
        """Circuit breaker records failure when provided."""
        from fastapi import HTTPException

        breaker = MagicMock()
        err = LLMError("timeout")

        with pytest.raises(HTTPException):
            _handle_llm_error(err, breaker, "chat_completion", "test-model")

        breaker.record_failure.assert_called_once_with(err)

    def test_no_breaker_does_not_crash(self):
        """None breaker is handled gracefully."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            _handle_llm_error(
                LLMError("err"), breaker=None, action="responses", model="m"
            )


# =============================================================================
# _flatten_content Tests
# =============================================================================


class TestFlattenContent:
    """Test Responses API content flattening."""

    def test_string_passthrough(self):
        assert _flatten_content("hello world") == "hello world"

    def test_empty_string(self):
        assert _flatten_content("") == ""

    def test_single_text_block(self):
        blocks = [{"type": "input_text", "text": "hello"}]
        assert _flatten_content(blocks) == "hello"

    def test_multiple_text_blocks(self):
        blocks = [
            {"type": "input_text", "text": "hello "},
            {"type": "input_text", "text": "world"},
        ]
        assert _flatten_content(blocks) == "hello world"

    def test_block_without_text_key(self):
        """Blocks missing 'text' field produce empty string."""
        blocks = [{"type": "image", "url": "https://example.com/img.png"}]
        assert _flatten_content(blocks) == ""

    def test_mixed_blocks(self):
        """Text blocks extracted, non-text blocks silently skipped."""
        blocks = [
            {"type": "input_text", "text": "describe "},
            {"type": "image", "url": "https://example.com/img.png"},
            {"type": "input_text", "text": "this image"},
        ]
        assert _flatten_content(blocks) == "describe this image"

    def test_empty_list(self):
        assert _flatten_content([]) == ""


# =============================================================================
# _build_responses_response Tests (edge cases)
# =============================================================================


class TestBuildResponsesEdgeCases:
    """Test edge cases in the Responses API response builder."""

    def test_empty_choices_returns_empty_response(self):
        """Empty choices array returns valid empty response structure."""
        result = _build_responses_response({"choices": [], "created": 0, "model": "m"})
        assert result["output_text"] == ""
        assert result["object"] == "response"
        assert result["id"].startswith("resp_")

    def test_reasoning_field_lm_studio(self):
        """LM Studio 'reasoning' field is captured."""
        result = _build_responses_response({
            "choices": [{"message": {"content": "answer", "reasoning": "I thought about it"}}],
            "created": 0,
            "model": "m",
        })
        blocks = result["output"][0]["content"]
        assert blocks[0] == {"type": "thinking", "thinking": "I thought about it"}
        assert blocks[1] == {"type": "output_text", "text": "answer"}

    def test_reasoning_content_field_openrouter(self):
        """OpenRouter 'reasoning_content' field is captured as fallback."""
        result = _build_responses_response({
            "choices": [{"message": {"content": "answer", "reasoning_content": "deep thought"}}],
            "created": 0,
            "model": "m",
        })
        blocks = result["output"][0]["content"]
        assert blocks[0] == {"type": "thinking", "thinking": "deep thought"}

    def test_no_reasoning_omits_thinking_block(self):
        """No reasoning field produces only output_text block."""
        result = _build_responses_response({
            "choices": [{"message": {"content": "just text"}}],
            "created": 0,
            "model": "m",
        })
        blocks = result["output"][0]["content"]
        assert len(blocks) == 1
        assert blocks[0] == {"type": "output_text", "text": "just text"}

    def test_usage_mapping(self):
        """prompt_tokens maps to input_tokens."""
        result = _build_responses_response({
            "choices": [{"message": {"content": "ok"}}],
            "created": 0,
            "model": "m",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        })
        assert result["usage"] == {
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        }

    def test_missing_usage_is_none(self):
        result = _build_responses_response({
            "choices": [{"message": {"content": "ok"}}],
            "created": 0,
            "model": "m",
        })
        assert result["usage"] is None


# =============================================================================
# Per-Model Circuit Breaker Isolation Tests
# =============================================================================


class TestPerModelCircuitBreakerIsolation:
    """The OpenAI-compat proxy must isolate the circuit breaker per model.

    Regression: a single shared "llm-proxy" breaker meant that repeated
    upstream failures for one (e.g. nonexistent) model would OPEN the breaker
    and 503 every other client/model. Each model must get its own breaker keyed
    as "llm-proxy:<model>" so one bad model can't DoS the others.
    """

    AUTH = {"Authorization": "Bearer sk-prompthub-passthrough-def456"}

    def _real_breaker_app(self, api_key_manager, mock_enhancement_service):
        """Build a test app backed by a REAL CircuitBreakerRegistry."""
        from router.resilience.circuit_breaker import CircuitBreakerRegistry

        registry = CircuitBreakerRegistry()
        app = FastAPI()
        router = create_openai_compat_router(
            enhancement_service=lambda: mock_enhancement_service,
            circuit_breakers=lambda: registry,
            api_key_manager=api_key_manager,
            llm_base_url="http://localhost:1234/v1",
            llm_timeout=30.0,
        )
        app.include_router(router)
        return app, registry

    @patch("router.openai_compat.router.LLMClient.chat_completion")
    def test_bad_model_does_not_open_breaker_for_good_model(
        self, mock_chat, api_key_manager, mock_enhancement_service
    ):
        """Failures on model A must not trip the breaker for model B."""
        from router.enhancement.llm_client import (
            ChatCompletionChoice,
            ChatCompletionResponse,
            ChatMessage,
            LLMError,
        )

        app, registry = self._real_breaker_app(
            api_key_manager, mock_enhancement_service
        )
        test_client = TestClient(app)

        # Drive enough upstream failures for model A to OPEN its breaker.
        # Each upstream failure yields 502; once the failure threshold is
        # crossed the breaker opens and subsequent requests fail fast with 503.
        mock_chat.side_effect = LLMError("upstream 400: no such model")
        for _ in range(5):
            resp = test_client.post(
                "/v1/chat/completions",
                json={
                    "model": "gpt-5.4-mini",
                    "messages": [{"role": "user", "content": "hi"}],
                },
                headers=self.AUTH,
            )
            assert resp.status_code in (502, 503), resp.text

        # Model A's breaker is now OPEN; a further request fails fast with 503.
        resp_a = test_client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-5.4-mini",
                "messages": [{"role": "user", "content": "hi"}],
            },
            headers=self.AUTH,
        )
        assert resp_a.status_code == 503, resp_a.text

        # Model B must be unaffected — it reaches the mocked client (200), not 503.
        mock_chat.side_effect = None
        mock_chat.return_value = ChatCompletionResponse(
            id="chatcmpl-ok",
            object="chat.completion",
            created=1700000000,
            model="qwen3-4b-instruct-2507",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content="hi"),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )
        resp_b = test_client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen3-4b-instruct-2507",
                "messages": [{"role": "user", "content": "hi"}],
            },
            headers=self.AUTH,
        )
        assert resp_b.status_code == 200, resp_b.text

    def test_breaker_name_is_model_scoped_on_chat(
        self, api_key_manager, mock_enhancement_service
    ):
        """The breaker name requested is 'llm-proxy:<model>' on /chat/completions."""
        registry = MagicMock()
        breaker = MagicMock()
        breaker.check.return_value = None
        registry.get.return_value = breaker

        app = FastAPI()
        router = create_openai_compat_router(
            enhancement_service=lambda: mock_enhancement_service,
            circuit_breakers=lambda: registry,
            api_key_manager=api_key_manager,
            llm_base_url="http://localhost:1234/v1",
            llm_timeout=30.0,
        )
        app.include_router(router)
        test_client = TestClient(app)

        with patch("router.openai_compat.router.LLMClient.chat_completion") as mc:
            from router.enhancement.llm_client import (
                ChatCompletionChoice,
                ChatCompletionResponse,
                ChatMessage,
            )

            mc.return_value = ChatCompletionResponse(
                id="x",
                object="chat.completion",
                created=1,
                model="model-a",
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content="hi"),
                        finish_reason="stop",
                    )
                ],
                usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            )
            test_client.post(
                "/v1/chat/completions",
                json={
                    "model": "model-a",
                    "messages": [{"role": "user", "content": "hi"}],
                },
                headers=self.AUTH,
            )
            test_client.post(
                "/v1/chat/completions",
                json={
                    "model": "model-b",
                    "messages": [{"role": "user", "content": "hi"}],
                },
                headers=self.AUTH,
            )

        names = [c.args[0] for c in registry.get.call_args_list]
        assert "llm-proxy:model-a" in names
        assert "llm-proxy:model-b" in names

    def test_breaker_name_is_model_scoped_on_responses(
        self, api_key_manager, mock_enhancement_service
    ):
        """The breaker name requested is 'llm-proxy:<model>' on /responses."""
        registry = MagicMock()
        breaker = MagicMock()
        breaker.check.return_value = None
        registry.get.return_value = breaker

        app = FastAPI()
        router = create_openai_compat_router(
            enhancement_service=lambda: mock_enhancement_service,
            circuit_breakers=lambda: registry,
            api_key_manager=api_key_manager,
            llm_base_url="http://localhost:1234/v1",
            llm_timeout=30.0,
        )
        app.include_router(router)
        test_client = TestClient(app)

        with patch("router.openai_compat.router.LLMClient.chat_completion") as mc:
            from router.enhancement.llm_client import (
                ChatCompletionChoice,
                ChatCompletionResponse,
                ChatMessage,
            )

            mc.return_value = ChatCompletionResponse(
                id="x",
                object="chat.completion",
                created=1,
                model="resp-model",
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content="hi"),
                        finish_reason="stop",
                    )
                ],
                usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            )
            test_client.post(
                "/v1/responses",
                json={"model": "resp-model", "input": "Hello"},
                headers=self.AUTH,
            )

        names = [c.args[0] for c in registry.get.call_args_list]
        assert "llm-proxy:resp-model" in names


# =============================================================================
# /v1/models Response Shape Tests
# =============================================================================


class TestListModelsResponseShape:
    """GET /v1/models must expose both `data` and `models` keys.

    Regression: codex-cli's model manager fails to decode the response with
    "missing field `models`". We add a top-level `models` field mirroring
    `data` (keeping `data` for backward compatibility).
    """

    @patch("router.openai_compat.router.LLMClient.list_models")
    def test_models_response_has_both_data_and_models(self, mock_list, client):
        """Response contains `data` and `models`, both equal to the model list."""
        known = [
            {"id": "qwen3-4b-instruct-2507", "object": "model"},
            {"id": "gemma-3-4b", "object": "model"},
        ]
        mock_list.return_value = known

        response = client.get("/v1/models")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["object"] == "list"
        assert body["data"] == known
        assert body["models"] == known
