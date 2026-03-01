"""Prompt enhancement via local Ollama models."""

from router.enhancement.context_window import (
    ENHANCEMENT_INPUT_CAP,
    MODEL_CONTEXT_TOKENS,
    TokenBudget,
    register_model,
)
from router.enhancement.ollama import (
    OllamaClient,
    OllamaConfig,
    OllamaConnectionError,
    OllamaError,
    OllamaModelError,
    OllamaResponse,
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
    "OllamaClient",
    "OllamaConfig",
    "OllamaConnectionError",
    "OllamaError",
    "OllamaModelError",
    "OllamaResponse",
    "PrivacyLevel",
    "resolve_privacy_level",
]
