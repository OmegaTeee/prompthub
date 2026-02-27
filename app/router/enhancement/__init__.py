"""Prompt enhancement via local Ollama models."""

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
