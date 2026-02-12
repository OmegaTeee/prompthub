"""SSE streaming support for OpenAI-compatible API proxy.

Ollama's /v1/chat/completions with stream=true already produces
OpenAI-compatible SSE chunks. This module relays those chunks
from Ollama to the desktop app client.
"""

import logging
from collections.abc import AsyncIterator

import httpx

logger = logging.getLogger(__name__)


async def stream_ollama_response(
    ollama_base_url: str,
    payload: dict,
    timeout: float = 120.0,
) -> AsyncIterator[str]:
    """Stream chat completion from Ollama and yield SSE lines.

    Args:
        ollama_base_url: Ollama's OpenAI-compat base URL (e.g., "http://localhost:11434/v1")
        payload: Request payload (must have stream=true set)
        timeout: Request timeout in seconds

    Yields:
        SSE-formatted lines (e.g., "data: {...}\\n\\n")
    """
    url = f"{ollama_base_url}/chat/completions"

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    yield f"{line}\n\n"

    # Ensure [DONE] sentinel is sent for clients that expect it
    yield "data: [DONE]\n\n"
