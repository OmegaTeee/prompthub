"""SSE streaming support for OpenAI-compatible API proxy.

Routes streaming requests through Ollama's native ``/api/chat``
endpoint (which respects ``think: false``) and translates responses
to OpenAI-compatible SSE chunks.  This avoids Ollama's ``/v1/``
limitation where hybrid-thinking models always emit reasoning tokens
that confuse non-Ollama clients like Raycast.
"""

import json
import logging
import time
from collections.abc import AsyncIterator

import httpx

logger = logging.getLogger(__name__)

# Counter for generating unique chunk IDs
_chunk_counter = 0


def _ollama_base_from_v1(v1_url: str) -> str:
    """Derive Ollama's base URL from the /v1 URL.

    ``http://localhost:11434/v1`` → ``http://localhost:11434``
    """
    return v1_url.rstrip("/").removesuffix("/v1")


def _to_openai_chunk(
    ollama_obj: dict, model: str, chunk_id: str, is_first: bool,
) -> str:
    """Convert an Ollama native streaming object to an OpenAI SSE chunk."""
    msg = ollama_obj.get("message", {})
    content = msg.get("content", "")
    done = ollama_obj.get("done", False)

    delta: dict = {}
    if is_first:
        delta["role"] = "assistant"
    if content:
        delta["content"] = content

    finish_reason = None
    if done:
        reason = ollama_obj.get("done_reason", "stop")
        finish_reason = "length" if reason == "length" else "stop"

    chunk = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason,
            }
        ],
    }
    return f"data: {json.dumps(chunk, separators=(',', ':'))}"


async def stream_ollama_response(
    ollama_base_url: str,
    payload: dict,
    timeout: float = 120.0,
) -> AsyncIterator[str]:
    """Stream chat completion from Ollama and yield OpenAI-compatible SSE lines.

    Uses Ollama's native ``/api/chat`` with ``think: false`` to avoid
    reasoning tokens, then translates each chunk to the OpenAI SSE format.

    Args:
        ollama_base_url: Ollama's OpenAI-compat base URL (e.g., "http://localhost:11434/v1")
        payload: Request payload (OpenAI format — translated to Ollama native format)
        timeout: Request timeout in seconds

    Yields:
        SSE-formatted lines (e.g., "data: {...}\\n\\n")
    """
    base = _ollama_base_from_v1(ollama_base_url)
    url = f"{base}/api/chat"

    model = payload.get("model", "")

    # Translate OpenAI payload → Ollama native format
    native_payload: dict = {
        "model": model,
        "messages": payload.get("messages", []),
        "stream": True,
        "think": False,
    }
    # Map OpenAI options → Ollama options
    options: dict = {}
    if payload.get("temperature") is not None:
        options["temperature"] = payload["temperature"]
    if payload.get("top_p") is not None:
        options["top_p"] = payload["top_p"]
    if payload.get("max_tokens") is not None:
        options["num_predict"] = payload["max_tokens"]
    if payload.get("stop") is not None:
        options["stop"] = payload["stop"]
    if options:
        native_payload["options"] = options

    global _chunk_counter
    _chunk_counter += 1
    chunk_id = f"chatcmpl-{_chunk_counter}"

    is_first = True

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        async with client.stream("POST", url, json=native_payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                sse_line = _to_openai_chunk(obj, model, chunk_id, is_first)
                is_first = False
                yield f"{sse_line}\n\n"

    yield "data: [DONE]\n\n"
