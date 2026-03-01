"""
Unit tests for the OrchestratorAgent.

These tests mock the OllamaClient so they run offline — no Ollama needed.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from router.orchestrator.agent import OrchestratorAgent, _strip_think_blocks
from router.orchestrator.intent import IntentCategory, OrchestratorResult


# ── Helper ─────────────────────────────────────────────────────────────────────

def _mock_ollama_response(payload: dict) -> MagicMock:
    """Create a mock OllamaResponse returning a JSON string."""
    mock = MagicMock()
    mock.response = json.dumps(payload)
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
    with patch.object(agent._client, "generate", new=AsyncMock(return_value=_mock_ollama_response(payload))):
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

    with patch.object(agent._client, "generate", new=AsyncMock(side_effect=_slow)):
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

    with patch.object(agent._client, "generate", new=AsyncMock(side_effect=_generate)):
        await agent.process("hi")
        await agent.process("hi")   # should hit cache

    assert call_count == 1


@pytest.mark.asyncio
async def test_process_handles_non_json_response(agent):
    mock_resp = MagicMock()
    mock_resp.response = "I cannot classify this."
    with patch.object(agent._client, "generate", new=AsyncMock(return_value=mock_resp)):
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
