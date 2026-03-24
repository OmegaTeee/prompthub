"""
Token budget management for prompt enhancement.

Problem this solves
-------------------
Enhancement rewrites a prompt — it produces 300-600 output tokens.
Sending a 50,000-token prompt for a 500-token rewrite is:
  - Slow    (model processes all input before generating)
  - Wasteful (most of the input context is ignored)
  - Fragile  (large inputs can confuse smaller models)

This module caps enhancement input at ENHANCEMENT_INPUT_CAP tokens
and truncates cleanly at a word boundary when exceeded.

Usage (in service.py)
---------------------
    budget = TokenBudget(
        model=rule.model,
        max_response_tokens=rule.max_tokens or 500,
        system_prompt=rule.system_prompt,
    )
    prompt, truncated = budget.truncate(prompt)
    if truncated:
        logger.debug("Prompt truncated to %d tokens for %s",
                     budget.available_for_input, rule.model)
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model context window registry (tokens)
# Source: model metadata (context_length from model manifest)
# ---------------------------------------------------------------------------
MODEL_CONTEXT_TOKENS: dict[str, int] = {
    "gemma3:4b":       131_072,
    "gemma3:27b":      131_072,
    "qwen3-coder:30b": 262_144,
    "qwen3:14b":        40_960,
    "bge-m3:latest":     8_192,
    "llama3.2:3b":       8_192,
    "llama3.2:latest":   8_192,
    "_default":          8_192,
}

# ---------------------------------------------------------------------------
# Practical cap on enhancement input
# Enhancement rewrites prompts — it does not need the model's full context.
# 4,096 tokens covers normal and long prompts without any truncation.
# Only truly giant inputs (pastes, docs) will be clipped.
# ---------------------------------------------------------------------------
ENHANCEMENT_INPUT_CAP = 4_096  # tokens

# Conservative chars-per-token (English prose + code + unicode)
CHARS_PER_TOKEN: float = 3.5

# Overhead for message roles, special tokens, formatting
OVERHEAD_TOKENS = 64


class TokenBudget:
    """
    Compute the token headroom available for a user prompt.

    Subtracts system prompt tokens, response reservation, and overhead
    from the model's context limit, then caps at ENHANCEMENT_INPUT_CAP.

    Example
    -------
        budget = TokenBudget(
            model="gemma3:4b",
            max_response_tokens=500,
            system_prompt="Rewrite the following prompt...",
        )
        prompt, was_truncated = budget.truncate(long_prompt)
    """

    def __init__(
        self,
        model: str,
        max_response_tokens: int = 500,
        system_prompt: str = "",
    ) -> None:
        self.model = model
        self.context_limit = MODEL_CONTEXT_TOKENS.get(
            model, MODEL_CONTEXT_TOKENS["_default"]
        )
        self.system_tokens = int(len(system_prompt) / CHARS_PER_TOKEN)
        self.max_response_tokens = max_response_tokens
        self.overhead_tokens = OVERHEAD_TOKENS

    @property
    def available_for_input(self) -> int:
        """Max tokens the user prompt may consume."""
        reserved = self.system_tokens + self.max_response_tokens + self.overhead_tokens
        headroom = max(0, self.context_limit - reserved)
        return min(headroom, ENHANCEMENT_INPUT_CAP)

    @property
    def available_chars(self) -> int:
        """Character equivalent of available_for_input."""
        return int(self.available_for_input * CHARS_PER_TOKEN)

    def fits(self, prompt: str) -> bool:
        """Return True if prompt fits within the token budget."""
        return len(prompt) <= self.available_chars

    def truncate(self, prompt: str) -> tuple[str, bool]:
        """
        Truncate prompt to fit within the token budget.

        Truncates at a word boundary (last space within the allowed range)
        so the model never sees a cut mid-word. Appends a truncation notice
        so the model knows the input was intentionally shortened.

        Returns:
            (prompt, was_truncated)
        """
        if self.fits(prompt):
            return prompt, False

        cap = self.available_chars
        truncated = prompt[:cap]

        # Snap to last word boundary (must be in last 10% of cap)
        last_space = truncated.rfind(" ")
        if last_space > int(cap * 0.9):
            truncated = truncated[:last_space]

        result = truncated + "\n[... input truncated to fit context window ...]"
        logger.debug(
            "Truncated prompt from %d to ~%d chars for model=%s (budget=%d tokens)",
            len(prompt), len(result), self.model, self.available_for_input,
        )
        return result, True

    def summary(self) -> dict[str, int | str]:
        """Budget breakdown — useful for debugging and the dashboard."""
        return {
            "model": self.model,
            "context_limit_tokens": self.context_limit,
            "system_prompt_tokens": self.system_tokens,
            "max_response_tokens": self.max_response_tokens,
            "overhead_tokens": self.overhead_tokens,
            "enhancement_input_cap": ENHANCEMENT_INPUT_CAP,
            "available_for_input_tokens": self.available_for_input,
            "available_for_input_chars": self.available_chars,
        }


def register_model(model: str, context_tokens: int) -> None:
    """
    Register a model's context window at runtime.

    Call this after pulling a new model to get accurate budgeting
    without editing context_window.py.

    Example:
        register_model("llama4-scout:17b", 10_485_760)
    """
    MODEL_CONTEXT_TOKENS[model] = context_tokens
    logger.info("Registered context window: %s = %d tokens", model, context_tokens)
