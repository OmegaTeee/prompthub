"""OpenAI-compatible API proxy for desktop app integration."""

from router.openai_compat.router import create_openai_compat_router

__all__ = [
    "create_openai_compat_router",
]
