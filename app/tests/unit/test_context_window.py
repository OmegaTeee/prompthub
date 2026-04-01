"""
Unit tests for router.enhancement.context_window

Tests cover:
- TokenBudget.available_for_input (formula correctness)
- TokenBudget.fits() (True/False boundary)
- TokenBudget.truncate() (no-op, word boundary snap, notice appended)
- TokenBudget.summary() (all keys present, correct types)
- register_model() (runtime registry mutation)
- All active models have entries in MODEL_CONTEXT_TOKENS
"""

import pytest
from router.enhancement.context_window import (
    CHARS_PER_TOKEN,
    ENHANCEMENT_INPUT_CAP,
    MODEL_CONTEXT_TOKENS,
    OVERHEAD_TOKENS,
    TokenBudget,
    register_model,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_SYSTEM = (
    "Rewrite the following prompt to be clearer and more specific. "
    "Return only the rewritten prompt — no explanation, no preamble."
)

# All models used by enhancement-rules.json
ACTIVE_MODELS = ["qwen/qwen3-4b-2507", "qwen/qwen3-4b-thinking-2507"]


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


class TestModelRegistry:
    def test_all_active_models_registered(self):
        """Every model in enhancement-rules.json must have a context entry."""
        for model in ACTIVE_MODELS:
            assert model in MODEL_CONTEXT_TOKENS, (
                f"{model} missing from MODEL_CONTEXT_TOKENS — "
                "add it to context_window.py after pulling the model"
            )

    def test_context_windows_are_positive(self):
        for model, ctx in MODEL_CONTEXT_TOKENS.items():
            assert ctx > 0, f"{model} has non-positive context window: {ctx}"

    def test_register_model_adds_entry(self):
        register_model("test-model:1b", 4096)
        assert MODEL_CONTEXT_TOKENS["test-model:1b"] == 4096

    def test_register_model_overwrites_existing(self):
        original = MODEL_CONTEXT_TOKENS.get("qwen/qwen3-4b-2507")
        register_model("qwen/qwen3-4b-2507", 999)
        assert MODEL_CONTEXT_TOKENS["qwen/qwen3-4b-2507"] == 999
        # Restore
        MODEL_CONTEXT_TOKENS["qwen/qwen3-4b-2507"] = original

    def test_unknown_model_falls_back_to_default(self):
        b = TokenBudget(model="unknown-model:??b", max_response_tokens=500)
        assert b.context_limit == MODEL_CONTEXT_TOKENS["_default"]


# ---------------------------------------------------------------------------
# Budget formula tests
# ---------------------------------------------------------------------------


class TestTokenBudgetFormula:
    def test_available_capped_at_enhancement_input_cap(self):
        """Even with a giant context window, input is capped."""
        b = TokenBudget(model="qwen/qwen3-4b-2507", max_response_tokens=100, system_prompt="")
        assert b.available_for_input <= ENHANCEMENT_INPUT_CAP

    def test_available_never_negative(self):
        """Pathological config: max_response_tokens > context_limit."""
        b = TokenBudget(
            model="_default",          # 8192 tokens
            max_response_tokens=9000,  # exceeds context
            system_prompt="",
        )
        assert b.available_for_input == 0

    def test_system_prompt_reduces_budget(self):
        short_system = "Improve."
        long_system = "Improve. " * 200  # ~1800 chars ≈ 514 tokens
        b_short = TokenBudget(model="qwen/qwen3-4b-2507", max_response_tokens=500, system_prompt=short_system)
        b_long = TokenBudget(model="qwen/qwen3-4b-2507", max_response_tokens=500, system_prompt=long_system)
        # Long system prompt should not increase available tokens
        assert b_long.available_for_input <= b_short.available_for_input

    def test_available_chars_matches_tokens(self):
        b = TokenBudget(model="qwen/qwen3-4b-2507", max_response_tokens=500, system_prompt="")
        assert b.available_chars == int(b.available_for_input * CHARS_PER_TOKEN)

    @pytest.mark.parametrize("model", ACTIVE_MODELS)
    def test_all_models_have_positive_budget(self, model):
        b = TokenBudget(model=model, max_response_tokens=600, system_prompt=SAMPLE_SYSTEM)
        assert b.available_for_input > 0, (
            f"{model} has zero available tokens — "
            "system prompt + max_tokens may exceed context limit"
        )


# ---------------------------------------------------------------------------
# fits() tests
# ---------------------------------------------------------------------------


class TestFits:
    def setup_method(self):
        self.b = TokenBudget(
            model="qwen/qwen3-4b-2507",
            max_response_tokens=500,
            system_prompt=SAMPLE_SYSTEM,
        )

    def test_short_prompt_fits(self):
        assert self.b.fits("explain backpropagation") is True

    def test_empty_string_fits(self):
        assert self.b.fits("") is True

    def test_prompt_at_exactly_budget_fits(self):
        prompt = "a" * self.b.available_chars
        assert self.b.fits(prompt) is True

    def test_prompt_one_over_budget_does_not_fit(self):
        prompt = "a" * (self.b.available_chars + 1)
        assert self.b.fits(prompt) is False


# ---------------------------------------------------------------------------
# truncate() tests
# ---------------------------------------------------------------------------


class TestTruncate:
    def setup_method(self):
        self.b = TokenBudget(
            model="qwen/qwen3-4b-2507",
            max_response_tokens=500,
            system_prompt=SAMPLE_SYSTEM,
        )

    def test_short_prompt_not_truncated(self):
        prompt = "explain backpropagation to a high school student"
        out, was_truncated = self.b.truncate(prompt)
        assert was_truncated is False
        assert out == prompt

    def test_empty_prompt_not_truncated(self):
        out, was_truncated = self.b.truncate("")
        assert was_truncated is False
        assert out == ""

    def test_giant_prompt_is_truncated(self):
        prompt = "word " * 20_000  # ~100K chars
        out, was_truncated = self.b.truncate(prompt)
        assert was_truncated is True

    def test_truncated_output_fits_budget(self):
        prompt = "word " * 20_000
        out, _ = self.b.truncate(prompt)
        # Output must fit (with some slack for the notice suffix)
        assert len(out) <= self.b.available_chars + 100

    def test_truncation_notice_appended(self):
        prompt = "word " * 20_000
        out, _ = self.b.truncate(prompt)
        assert "[... input truncated to fit context window ...]" in out

    def test_truncation_snaps_to_word_boundary(self):
        """Output must not end mid-word (before the notice suffix)."""
        # Build a prompt without the notice and split at the notice
        prompt = "alpha " * 10_000
        out, _ = self.b.truncate(prompt)
        notice = "\n[... input truncated to fit context window ...]"
        body = out[: out.index(notice)]
        # Body must end with a complete word — last char is a space or letter
        # The word boundary snap means it shouldn't end in the middle of "alpha"
        # i.e. the body split on spaces should have all 5-char words
        words = body.strip().split()
        assert all(w == "alpha" for w in words), (
            f"Word boundary snap failed — found partial word: {words[-1]!r}"
        )

    def test_already_at_boundary_not_truncated(self):
        prompt = "x" * self.b.available_chars
        out, was_truncated = self.b.truncate(prompt)
        assert was_truncated is False


# ---------------------------------------------------------------------------
# summary() tests
# ---------------------------------------------------------------------------


class TestSummary:
    def test_summary_contains_all_keys(self):
        b = TokenBudget(model="qwen/qwen3-4b-2507", max_response_tokens=500, system_prompt=SAMPLE_SYSTEM)
        s = b.summary()
        expected_keys = {
            "model",
            "context_limit_tokens",
            "system_prompt_tokens",
            "max_response_tokens",
            "overhead_tokens",
            "enhancement_input_cap",
            "available_for_input_tokens",
            "available_for_input_chars",
        }
        assert expected_keys == set(s.keys())

    def test_summary_values_are_consistent(self):
        b = TokenBudget(model="qwen/qwen3-4b-2507", max_response_tokens=500, system_prompt=SAMPLE_SYSTEM)
        s = b.summary()
        assert s["model"] == "qwen/qwen3-4b-2507"
        assert s["available_for_input_tokens"] == b.available_for_input
        assert s["available_for_input_chars"] == b.available_chars
        assert s["enhancement_input_cap"] == ENHANCEMENT_INPUT_CAP
        assert s["overhead_tokens"] == OVERHEAD_TOKENS
