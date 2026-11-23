"""
OpenAI-compatible client for local LLM servers.

This module provides async communication with LLM servers using OpenAI's API format.
LM Studio and similar servers expose OpenAI-compatible endpoints at
/v1/chat/completions and /v1/completions.

This allows drop-in replacement of OpenAI with local LLM models.
"""

import asyncio
import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Payload keys chat_completion() builds from its own arguments; extra_params
# may not override them (e.g. a client-supplied "model" or "stream").
_CORE_PAYLOAD_KEYS = frozenset(
    {"model", "messages", "temperature", "stream", "max_tokens", "tools", "tool_choice"}
)


class LLMConfig(BaseModel):
    """Configuration for OpenAI-compatible LLM client."""

    base_url: str = "http://localhost:11434/v1"
    timeout: float = 30.0
    max_retries: int = 2
    retry_delay: float = 1.0
    extra_headers: dict[str, str] = {}


class ChatMessage(BaseModel):
    """Chat message in OpenAI format."""

    role: str  # "system", "user", or "assistant"
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


class ChatCompletionChoice(BaseModel):
    """Choice in chat completion response."""

    index: int
    message: ChatMessage
    finish_reason: str | None = None


class ChatCompletionResponse(BaseModel):
    """Response from /v1/chat/completions endpoint."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: dict[str, Any] | None = None


class LLMError(Exception):
    """Base exception for LLM server API errors."""

    pass


class LLMConnectionError(LLMError):
    """Raised when unable to connect to LLM server."""

    pass


class LLMModelError(LLMError):
    """Raised when model is not available."""

    pass


class LLMUpstreamError(LLMError):
    """The LLM server answered with an HTTP error status.

    ``message`` is the server's own explanation (e.g. LM Studio's
    ``'response_format.type' must be 'json_schema' or 'text'``), so callers can
    relay it instead of a generic transport error.
    """

    def __init__(self, status_code: int, message: str):
        super().__init__(f"LLM server returned {status_code}: {message}")
        self.status_code = status_code
        self.message = message


def upstream_error_message(response: httpx.Response) -> str:
    """Extract the error text from an LLM server's error response.

    Handles LM Studio (``{"error": "..."}``) and OpenAI
    (``{"error": {"message": "..."}}``) shapes; otherwise returns the raw body.
    """
    try:
        error = response.json().get("error")
    except (json.JSONDecodeError, AttributeError):
        error = None
    if isinstance(error, str) and error:
        return error
    if isinstance(error, dict) and error.get("message"):
        return str(error["message"])
    return response.text[:500] or response.reason_phrase


class LLMClient:
    """
    OpenAI-compatible async client for local LLM servers.

    Uses OpenAI-compatible endpoints:
    - /v1/chat/completions (Chat Completions API)
    - /v1/completions (Completions API)
    - /v1/models (Models API)

    Example:
        client = LLMClient()
        if await client.is_healthy():
            response = await client.chat_completion(
                model="deepseek-r1:latest",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"}
                ]
            )
            print(response.choices[0].message.content)
    """

    def __init__(self, config: LLMConfig | None = None):
        """
        Initialize the OpenAI-compatible LLM client.

        Args:
            config: Configuration options
        """
        self.config = config or LLMConfig()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout),
                headers=self.config.extra_headers or {},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def is_healthy(self) -> bool:
        """
        Check if LLM server is running and accessible.

        Returns:
            True if LLM server is healthy
        """
        try:
            client = await self._get_client()
            response = await client.get("/models")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    async def list_models(self) -> list[dict[str, Any]]:
        """
        List available models using OpenAI-compatible endpoint.

        Returns:
            List of model information dicts

        Raises:
            LLMConnectionError: If unable to connect
        """
        try:
            client = await self._get_client()
            response = await client.get("/models")
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except httpx.ConnectError as e:
            raise LLMConnectionError(
                f"Cannot connect to LLM server: {e}"
            ) from e
        except httpx.RequestError as e:
            raise LLMError(f"Request failed: {e}") from e

    async def has_model(self, model: str) -> bool:
        """
        Check if a specific model is available.

        Args:
            model: Model name (e.g., "deepseek-r1:latest")

        Returns:
            True if model is available
        """
        try:
            models = await self.list_models()
            model_ids = [m.get("id", "") for m in models]
            return model in model_ids
        except LLMError:
            return False

    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        stream: bool = False,
        extra_params: dict[str, Any] | None = None,
    ) -> ChatCompletionResponse:
        """
        Generate chat completion using OpenAI-compatible API.

        Args:
            model: Model name (e.g., "deepseek-r1:latest")
            messages: List of message dicts with "role" and "content"
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response (not implemented)
            extra_params: Further OpenAI fields to send as-is (e.g.
                ``response_format``, ``top_p``, ``stop``). Keys this method
                sets itself (model, messages, stream, ...) are ignored.

        Returns:
            ChatCompletionResponse with generated text

        Raises:
            LLMConnectionError: If unable to connect
            LLMModelError: If model not found
            LLMError: For other errors
        """
        if stream:
            raise NotImplementedError("Streaming not yet implemented")

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice

        for key, value in (extra_params or {}).items():
            if key in _CORE_PAYLOAD_KEYS:
                logger.debug(f"Ignoring extra_params key {key!r}; set by caller")
                continue
            payload[key] = value

        last_error: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                client = await self._get_client()
                response = await client.post("/chat/completions", json=payload)

                if response.status_code == 404:
                    raise LLMModelError(f"Model '{model}' not found")
                if response.is_error:
                    raise LLMUpstreamError(
                        response.status_code, upstream_error_message(response)
                    )

                try:
                    data = response.json()
                except json.JSONDecodeError:
                    body_preview = response.text[:200] if response.text else "(empty)"
                    raise LLMError(
                        f"LLM server returned non-JSON response "
                        f"(status {response.status_code}): {body_preview}"
                    )

                return ChatCompletionResponse(
                    id=data.get("id", ""),
                    object=data.get("object", "chat.completion"),
                    created=data.get("created", 0),
                    model=data.get("model", model),
                    choices=[
                        ChatCompletionChoice(
                            index=choice.get("index", 0),
                            message=ChatMessage(
                                role=choice.get("message", {}).get("role", "assistant"),
                                content=choice.get("message", {}).get("content"),
                                tool_calls=choice.get("message", {}).get("tool_calls"),
                            ),
                            finish_reason=choice.get("finish_reason"),
                        )
                        for choice in data.get("choices", [])
                    ],
                    usage=data.get("usage"),
                )

            except httpx.ConnectError as e:
                last_error = LLMConnectionError(
                    f"Cannot connect to LLM server: {e}"
                )
                logger.warning(f"LLM server connection failed (attempt {attempt + 1})")

            except (LLMModelError, LLMUpstreamError):
                raise  # The server answered; retrying won't change it

            except httpx.TimeoutException as e:
                last_error = LLMError(f"Request timed out: {e}")
                logger.warning(f"LLM server request timed out (attempt {attempt + 1})")

            except httpx.RequestError as e:
                last_error = LLMError(f"Request failed: {e}")
                logger.warning(f"LLM server request failed (attempt {attempt + 1})")

            # Wait before retry
            if attempt < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay)

        # All retries exhausted
        if last_error:
            raise last_error
        raise LLMError("Unknown error occurred")

    async def generate_from_prompt(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """
        Helper method to generate text from a simple prompt.

        Converts prompt to chat format and extracts response text.

        Args:
            model: Model name
            prompt: User prompt
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.chat_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if response.choices:
            return response.choices[0].message.content or ""
        return ""

    async def __aenter__(self) -> "LLMClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
