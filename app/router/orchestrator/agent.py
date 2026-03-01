"""
Orchestrator Agent — local reasoning layer using qwen3:14b.

Sits upstream of EnhancementService. Classifies intent, injects
session context within a token budget, and annotates prompts with
routing hints before they reach the enhancement layer.

Flow:
    incoming prompt
        → OrchestratorAgent.process()  (qwen3:14b, 2s timeout)
        → OrchestratorResult (intent + annotated_prompt)
        → EnhancementService.enhance() (gemma3:4b, fast rewrite)
        → downstream client

Fail-safe: any error or timeout returns the original prompt unchanged.
"""

import asyncio
import json
import logging
import re
from hashlib import sha256
from pathlib import Path
from typing import Any

from router.enhancement.ollama import OllamaClient, OllamaConfig, OllamaError
from router.orchestrator.intent import (
    INTENT_SERVER_MAP,
    IntentCategory,
    OrchestratorResult,
)
from router.resilience import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerError

logger = logging.getLogger(__name__)

# ── Model config ──────────────────────────────────────────────────────────────
MODEL = "qwen3:14b"
TIMEOUT_SECONDS = 2.5          # Hard ceiling — must not block enhancement
MAX_TOKENS = 300               # Keep responses tight; we only need JSON
TEMPERATURE = 0.1              # Low randomness for reliable structured output

# ── Token budget for context injection ───────────────────────────────────────
CHARS_PER_TOKEN = 4            # ~4 chars per token heuristic (no tokenizer needed)
CONTEXT_TOKEN_BUDGET = 800     # Max tokens of session context to prepend


SYSTEM_PROMPT = """You are an intent classifier for a local AI router. Analyze the user's prompt and respond ONLY with a JSON object — no markdown, no preamble.

Required fields:
- intent: one of [code, documentation, search, memory, workflow, reasoning, general]
- suggested_tools: list of relevant MCP server names (may be empty)
- context_hints: list of short strings the enhancement layer should be aware of
- annotated_prompt: the original prompt, optionally prepended with a one-line hint like [INTENT:code] or [CTX:...]
- reasoning: one sentence explaining your classification
- confidence: float 0.0–1.0

Rules:
- Keep annotated_prompt close to the original — do NOT rewrite it
- Only add a [HINT:...] prefix if it genuinely helps routing
- Strip any <think>...</think> blocks before outputting
- Output valid JSON only"""


def _strip_think_blocks(text: str) -> str:
    """Remove qwen3 <think>...</think> reasoning blocks from output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _cache_key(prompt: str, client_name: str | None) -> str:
    payload = f"{client_name or ''}:{prompt}"
    return sha256(payload.encode()).hexdigest()[:16]


class OrchestratorAgent:
    """
    Wraps qwen3:14b to classify intent and annotate prompts.

    Usage:
        agent = OrchestratorAgent()
        await agent.initialize()
        result = await agent.process(prompt, client_name="vscode")
    """

    def __init__(self, ollama_config: OllamaConfig | None = None):
        self._config = ollama_config or OllamaConfig()
        self._client = OllamaClient(self._config)
        self._breaker = CircuitBreaker(
            name="orchestrator",
            config=CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30.0,
                half_open_max_calls=1,
            ),
        )
        # Simple in-process LRU cache (prompt hash → result)
        self._cache: dict[str, OrchestratorResult] = {}
        self._cache_max = 256
        self._healthy: bool | None = None   # None = not yet checked

    async def initialize(self) -> None:
        """Check model availability. Logs warning if model not found."""
        self._healthy = await self._client.is_healthy()
        if self._healthy:
            has_model = await self._client.has_model(MODEL)
            if not has_model:
                logger.warning(
                    f"Orchestrator model '{MODEL}' not found in Ollama. "
                    f"Pull with: ollama pull {MODEL}. "
                    f"Orchestrator will pass-through until model is available."
                )
                self._healthy = False
        else:
            logger.warning("Ollama unavailable — orchestrator disabled until Ollama starts.")

    async def close(self) -> None:
        await self._client.close()


    async def process(
        self,
        prompt: str,
        client_name: str | None = None,
        session_context: str | None = None,
        bypass_cache: bool = False,
    ) -> OrchestratorResult:
        """
        Classify intent and annotate prompt within a strict timeout.

        Args:
            prompt: Raw user prompt
            client_name: Client identifier for context (e.g. "vscode")
            session_context: Recent session facts to inject (token-budgeted)
            bypass_cache: Skip cache lookup

        Returns:
            OrchestratorResult — falls back to pass-through on any failure
        """
        if not self._healthy:
            # Re-probe once per N calls to recover after Ollama starts
            self._healthy = await self._client.is_healthy()
            if not self._healthy:
                return OrchestratorResult.pass_through(prompt, "Ollama unavailable")

        # Cache check
        key = _cache_key(prompt, client_name)
        if not bypass_cache and key in self._cache:
            logger.debug(f"Orchestrator cache hit: {key}")
            return self._cache[key]

        # Build the user message — inject session context within budget
        user_msg = self._build_user_message(prompt, client_name, session_context)

        try:
            result = await asyncio.wait_for(
                self._call_model(user_msg, prompt),
                timeout=TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Orchestrator timed out after {TIMEOUT_SECONDS}s — passing through")
            return OrchestratorResult.pass_through(prompt, "timeout")
        except CircuitBreakerError:
            logger.warning("Orchestrator circuit breaker open — passing through")
            return OrchestratorResult.pass_through(prompt, "circuit_open")
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            return OrchestratorResult.pass_through(prompt, str(e))

        # Store in cache, evict oldest if full
        if len(self._cache) >= self._cache_max:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = result
        return result

    def _build_user_message(
        self,
        prompt: str,
        client_name: str | None,
        session_context: str | None,
    ) -> str:
        budget_chars = CONTEXT_TOKEN_BUDGET * CHARS_PER_TOKEN
        parts: list[str] = []

        if client_name:
            parts.append(f"[CLIENT:{client_name}]")

        if session_context:
            truncated = session_context[:budget_chars]
            parts.append(f"[SESSION_CONTEXT]\n{truncated}\n[/SESSION_CONTEXT]")

        parts.append(f"[PROMPT]\n{prompt}\n[/PROMPT]")
        return "\n".join(parts)

    async def _call_model(self, user_msg: str, original_prompt: str) -> OrchestratorResult:
        """Call qwen3:14b via circuit breaker and parse JSON response."""
        try:
            self._breaker.check()
        except CircuitBreakerError:
            raise

        try:
            response = await self._client.generate(
                model=MODEL,
                prompt=user_msg,
                system=SYSTEM_PROMPT,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            self._breaker.record_success()
        except Exception as e:
            self._breaker.record_failure(e)
            raise
        raw = _strip_think_blocks(response.response)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from a partially wrapped response
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                logger.warning(f"Orchestrator returned non-JSON: {raw[:120]}")
                return OrchestratorResult.pass_through(original_prompt, "parse_error")

        # Validate intent field
        try:
            intent = IntentCategory(data.get("intent", "general"))
        except ValueError:
            intent = IntentCategory.GENERAL

        # Merge server suggestions: model hints + intent map
        model_tools: list[str] = data.get("suggested_tools", [])
        intent_tools: list[str] = INTENT_SERVER_MAP.get(intent, [])
        merged_tools = list(dict.fromkeys(model_tools + intent_tools))  # dedup, preserve order

        annotated = data.get("annotated_prompt", original_prompt) or original_prompt

        return OrchestratorResult(
            intent=intent,
            suggested_tools=merged_tools,
            context_hints=data.get("context_hints", []),
            annotated_prompt=annotated,
            reasoning=data.get("reasoning", ""),
            confidence=float(data.get("confidence", 1.0)),
        )


# ── Module-level singleton ────────────────────────────────────────────────────

_agent: OrchestratorAgent | None = None


def get_orchestrator_agent(ollama_config: OllamaConfig | None = None) -> OrchestratorAgent:
    """Get or create the global OrchestratorAgent instance."""
    global _agent
    if _agent is None:
        _agent = OrchestratorAgent(ollama_config)
    return _agent
