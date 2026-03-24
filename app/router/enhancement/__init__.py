"""Prompt enhancement via local LLM models."""

from router.enhancement.context_window import (
    ENHANCEMENT_INPUT_CAP,
    MODEL_CONTEXT_TOKENS,
    TokenBudget,
    register_model,
)
from router.enhancement.llm_client import (
    LLMClient,
    LLMConfig,
    LLMConnectionError,
    LLMError,
    LLMModelError,
)
from router.enhancement.service import (
    EnhancementResult,
    EnhancementRule,
    EnhancementService,
    PrivacyLevel,
    resolve_privacy_level,
)

__all__ = [
    "ENHANCEMENT_INPUT_CAP",
    "MODEL_CONTEXT_TOKENS",
    "TokenBudget",
    "register_model",
    "EnhancementResult",
    "EnhancementRule",
    "EnhancementService",
    "LLMClient",
    "LLMConfig",
    "LLMConnectionError",
    "LLMError",
    "LLMModelError",
    "PrivacyLevel",
    "resolve_privacy_level",
]
