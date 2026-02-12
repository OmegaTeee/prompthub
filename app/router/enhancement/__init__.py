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
]
