"""
Unit tests for the OrchestratorAgent.

These tests mock the LLMClient so they run offline — no LLM server needed.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from router.orchestrator.agent import (
    CHARS_PER_TOKEN,
    CONTEXT_TOKEN_BUDGET,
    OrchestratorAgent,
    _parse_json_response,
    _strip_think_blocks,
)
from router.orchestrator.intent import IntentCategory, OrchestratorResult
from router.resilience import CircuitBreakerError, CircuitState


# ── Helper ─────────────────────────────────────────────────────────────────────

def _mock_ollama_response(payload: dict) -> MagicMock:
    """Create a mock ChatCompletionResponse returning a JSON string."""
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = json.dumps(payload)
    return mock


# ── strip_think_blocks ─────────────────────────────────────────────────────────

def test_strip_think_blocks_removes_block():
    raw = "<think>some reasoning here</think>{\"intent\": \"code\"}"
    assert _strip_think_blocks(raw) == '{"intent": "code"}'


def test_strip_think_blocks_multiline():
    raw = "<think>\nline1\nline2\n</think>result"
    assert _strip_think_blocks(raw) == "result"


def test_strip_think_blocks_no_block():
    raw = '{"intent": "general"}'
    assert _strip_think_blocks(raw) == raw


# ── _parse_json_response ──────────────────────────────────────────────────────


def test_parse_json_valid():
    data = _parse_json_response('{"intent": "code", "confidence": 0.9}')
    assert data == {"intent": "code", "confidence": 0.9}


def test_parse_json_with_preamble():
    """Regex fallback extracts JSON from wrapped text."""
    raw = 'Here is my analysis:\n{"intent": "general"}\nDone.'
    data = _parse_json_response(raw)
    assert data is not None
    assert data["intent"] == "general"


def test_parse_json_with_think_tags_stripped():
    """Works with raw output after think blocks are stripped."""
    raw = '{"intent": "search", "suggested_tools": ["duckduckgo"]}'
    data = _parse_json_response(raw)
    assert data["suggested_tools"] == ["duckduckgo"]


def test_parse_json_empty_string():
    assert _parse_json_response("") is None


def test_parse_json_plain_text():
    assert _parse_json_response("I don't know how to respond as JSON") is None


def test_parse_json_malformed_json():
    """Partial JSON that looks like a dict but isn't parseable."""
    assert _parse_json_response("{intent: code}") is None


def test_parse_json_nested_braces():
    """Regex greedily matches outermost braces."""
    raw = '{"intent": "code", "context_hints": ["use {curly} brackets"]}'
    data = _parse_json_response(raw)
    assert data is not None
    assert data["intent"] == "code"


# ── pass_through factory ──────────────────────────────────────────────────────

def test_pass_through_sets_skipped():
    r = OrchestratorResult.pass_through("hello", "timeout")
    assert r.skipped is True
    assert r.annotated_prompt == "hello"
    assert r.error == "timeout"


# ── OrchestratorAgent.process ─────────────────────────────────────────────────

@pytest.fixture
def agent():
    a = OrchestratorAgent()
    a._healthy = True   # skip real health check
    return a


@pytest.mark.asyncio
async def test_process_classifies_code_intent(agent):
    payload = {
        "intent": "code",
        "suggested_tools": ["desktop-commander"],
        "context_hints": ["python"],
        "annotated_prompt": "[INTENT:code] write a function",
        "reasoning": "User asked for code.",
        "confidence": 0.95,
    }
    with patch.object(agent._client, "chat_completion", new=AsyncMock(return_value=_mock_ollama_response(payload))):
        result = await agent.process("write a function", client_name="vscode")

    assert result.intent == IntentCategory.CODE
    assert result.skipped is False
    assert "desktop-commander" in result.suggested_tools
    # Intent map should also append context7 for code
    assert "context7" in result.suggested_tools


@pytest.mark.asyncio
async def test_process_returns_passthrough_on_timeout(agent):
    async def _slow(*args, **kwargs):
        import asyncio
        await asyncio.sleep(10)

    with patch("router.orchestrator.agent.TIMEOUT_SECONDS", 0.01), \
         patch.object(agent._client, "chat_completion", new=AsyncMock(side_effect=_slow)):
        result = await agent.process("hello")

    assert result.skipped is True
    assert result.error == "timeout"
    assert result.annotated_prompt == "hello"


@pytest.mark.asyncio
async def test_process_cache_hit(agent):
    payload = {
        "intent": "general",
        "suggested_tools": [],
        "context_hints": [],
        "annotated_prompt": "hi",
        "reasoning": "Simple greeting.",
        "confidence": 1.0,
    }
    call_count = 0

    async def _generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return _mock_ollama_response(payload)

    with patch.object(agent._client, "chat_completion", new=AsyncMock(side_effect=_generate)):
        await agent.process("hi")
        await agent.process("hi")   # should hit cache

    assert call_count == 1


@pytest.mark.asyncio
async def test_process_handles_non_json_response(agent):
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "I cannot classify this."
    with patch.object(agent._client, "chat_completion", new=AsyncMock(return_value=mock_resp)):
        result = await agent.process("weird prompt")

    assert result.skipped is True
    assert result.error == "parse_error"


@pytest.mark.asyncio
async def test_process_passthrough_when_unhealthy():
    agent = OrchestratorAgent()
    agent._healthy = False
    with patch.object(agent._client, "is_healthy", new=AsyncMock(return_value=False)):
        result = await agent.process("hello")
    assert result.skipped is True


# ── LLM output validation ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_process_handles_invalid_suggested_tools_type(agent):
    """LLM returns suggested_tools as a string instead of a list."""
    payload = {
        "intent": "code",
        "suggested_tools": "desktop-commander",  # string, not list
        "context_hints": [],
        "annotated_prompt": "write code",
        "reasoning": "Code task.",
        "confidence": 0.9,
    }
    with patch.object(agent._client, "chat_completion", new=AsyncMock(return_value=_mock_ollama_response(payload))):
        result = await agent.process("write code")

    assert result.skipped is False
    # Invalid type should be dropped; intent map tools should still appear
    assert "desktop-commander" in result.suggested_tools  # from INTENT_SERVER_MAP
    assert "context7" in result.suggested_tools


@pytest.mark.asyncio
async def test_process_handles_non_numeric_confidence(agent):
    """LLM returns confidence as a string like 'high'."""
    payload = {
        "intent": "general",
        "suggested_tools": [],
        "context_hints": [],
        "annotated_prompt": "hello",
        "reasoning": "Simple greeting.",
        "confidence": "high",  # non-numeric
    }
    with patch.object(agent._client, "chat_completion", new=AsyncMock(return_value=_mock_ollama_response(payload))):
        result = await agent.process("hello")

    assert result.skipped is False
    assert result.confidence == 1.0  # falls back to default


@pytest.mark.asyncio
async def test_process_clamps_out_of_range_confidence(agent):
    """LLM returns confidence > 1.0."""
    payload = {
        "intent": "general",
        "suggested_tools": [],
        "context_hints": [],
        "annotated_prompt": "hello",
        "reasoning": "Greeting.",
        "confidence": 50.0,
    }
    with patch.object(agent._client, "chat_completion", new=AsyncMock(return_value=_mock_ollama_response(payload))):
        result = await agent.process("hello")

    assert result.confidence == 1.0  # clamped to max


@pytest.mark.asyncio
async def test_process_handles_regex_extracted_invalid_json(agent):
    """Regex finds braces but content isn't valid JSON."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "Here is the result: {not valid json} done"
    with patch.object(agent._client, "chat_completion", new=AsyncMock(return_value=mock_resp)):
        result = await agent.process("test")

    assert result.skipped is True
    assert result.error == "parse_error"


@pytest.mark.asyncio
async def test_process_bypass_cache(agent):
    """bypass_cache=True skips cache and calls the model again."""
    payload = {
        "intent": "general",
        "suggested_tools": [],
        "context_hints": [],
        "annotated_prompt": "hi",
        "reasoning": "Greeting.",
        "confidence": 1.0,
    }
    call_count = 0

    async def _generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return _mock_ollama_response(payload)

    with patch.object(agent._client, "chat_completion", new=AsyncMock(side_effect=_generate)):
        await agent.process("hi")
        await agent.process("hi", bypass_cache=True)  # should NOT hit cache

    assert call_count == 2


@pytest.mark.asyncio
async def test_cache_eviction(agent):
    """Cache evicts oldest entry when full."""
    agent._cache_max = 2
    payload_template = {
        "suggested_tools": [],
        "context_hints": [],
        "reasoning": "Test.",
        "confidence": 1.0,
    }

    def _make_response(**kwargs):
        messages = kwargs.get("messages", [])
        user_content = messages[-1]["content"] if messages else ""
        return _mock_ollama_response({
            **payload_template,
            "intent": "general",
            "annotated_prompt": user_content,
        })

    with patch.object(agent._client, "chat_completion", new=AsyncMock(side_effect=_make_response)):
        await agent.process("first")
        await agent.process("second")
        await agent.process("third")  # should evict "first"

    assert len(agent._cache) == 2


# ── Circuit breaker ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_process_passthrough_when_circuit_open(agent):
    """Circuit breaker in OPEN state returns pass-through without calling model."""
    import time as _time

    agent._breaker._stats.state = CircuitState.OPEN
    agent._breaker._stats.last_failure_time = _time.time()  # recently opened

    result = await agent.process("hello")

    assert result.skipped is True
    assert result.error == "circuit_open"


# ── Session context truncation ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_session_context_truncated_to_budget(agent):
    """Session context exceeding the token budget is truncated."""
    budget_chars = CONTEXT_TOKEN_BUDGET * CHARS_PER_TOKEN
    long_context = "x" * (budget_chars + 500)

    payload = {
        "intent": "general",
        "suggested_tools": [],
        "context_hints": [],
        "annotated_prompt": "hi",
        "reasoning": "Greeting.",
        "confidence": 1.0,
    }
    captured_prompt = None

    async def _capture(**kwargs):
        nonlocal captured_prompt
        messages = kwargs.get("messages", [])
        # User message is the last message in the list
        captured_prompt = messages[-1]["content"] if messages else ""
        return _mock_ollama_response(payload)

    with patch.object(agent._client, "chat_completion", new=AsyncMock(side_effect=_capture)):
        await agent.process("hi", session_context=long_context)

    # The context block should be present but truncated to budget
    assert "[SESSION_CONTEXT]" in captured_prompt
    ctx_start = captured_prompt.index("[SESSION_CONTEXT]\n") + len("[SESSION_CONTEXT]\n")
    ctx_end = captured_prompt.index("\n[/SESSION_CONTEXT]")
    injected_context = captured_prompt[ctx_start:ctx_end]
    assert len(injected_context) == budget_chars
