"""
OpenAI-compatible client for Ollama.

This module provides async communication with Ollama using OpenAI's API format.
Ollama exposes OpenAI-compatible endpoints at /v1/chat/completions and /v1/completions.

This allows drop-in replacement of OpenAI with local Ollama models.
"""

import asyncio
import logging
from typing import Any

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OpenAICompatConfig(BaseModel):
    """Configuration for OpenAI-compatible Ollama client."""

    base_url: str = "http://localhost:11434/v1"
    timeout: float = 30.0
    max_retries: int = 2
    retry_delay: float = 1.0


class ChatMessage(BaseModel):
    """Chat message in OpenAI format."""

    role: str  # "system", "user", or "assistant"
    content: str


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
    usage: dict[str, int] | None = None


class OllamaOpenAIError(Exception):
    """Base exception for Ollama OpenAI-compatible API errors."""

    pass


class OllamaOpenAIConnectionError(OllamaOpenAIError):
    """Raised when unable to connect to Ollama."""

    pass


class OllamaOpenAIModelError(OllamaOpenAIError):
    """Raised when model is not available."""

    pass


class OllamaOpenAIClient:
    """
    OpenAI-compatible async client for Ollama.

    Uses Ollama's OpenAI-compatible endpoints:
    - /v1/chat/completions (Chat Completions API)
    - /v1/completions (Completions API)
    - /v1/models (Models API)

    Example:
        client = OllamaOpenAIClient()
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

    def __init__(self, config: OpenAICompatConfig | None = None):
        """
        Initialize the OpenAI-compatible Ollama client.

        Args:
            config: Configuration options
        """
        self.config = config or OpenAICompatConfig()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def is_healthy(self) -> bool:
        """
        Check if Ollama is running and accessible.

        Returns:
            True if Ollama is healthy
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
            OllamaOpenAIConnectionError: If unable to connect
        """
        try:
            client = await self._get_client()
            response = await client.get("/models")
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except httpx.ConnectError as e:
            raise OllamaOpenAIConnectionError(
                f"Cannot connect to Ollama: {e}"
            ) from e
        except httpx.RequestError as e:
            raise OllamaOpenAIError(f"Request failed: {e}") from e

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
        except OllamaOpenAIError:
            return False

    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> ChatCompletionResponse:
        """
        Generate chat completion using OpenAI-compatible API.

        Args:
            model: Model name (e.g., "deepseek-r1:latest")
            messages: List of message dicts with "role" and "content"
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response (not implemented)

        Returns:
            ChatCompletionResponse with generated text

        Raises:
            OllamaOpenAIConnectionError: If unable to connect
            OllamaOpenAIModelError: If model not found
            OllamaOpenAIError: For other errors
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

        last_error: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                client = await self._get_client()
                response = await client.post("/chat/completions", json=payload)

                if response.status_code == 404:
                    raise OllamaOpenAIModelError(f"Model '{model}' not found")

                response.raise_for_status()
                data = response.json()

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
                                content=choice.get("message", {}).get("content", ""),
                            ),
                            finish_reason=choice.get("finish_reason"),
                        )
                        for choice in data.get("choices", [])
                    ],
                    usage=data.get("usage"),
                )

            except httpx.ConnectError as e:
                last_error = OllamaOpenAIConnectionError(
                    f"Cannot connect to Ollama: {e}"
                )
                logger.warning(f"Ollama connection failed (attempt {attempt + 1})")

            except OllamaOpenAIModelError:
                raise  # Don't retry model errors

            except httpx.TimeoutException as e:
                last_error = OllamaOpenAIError(f"Request timed out: {e}")
                logger.warning(f"Ollama request timed out (attempt {attempt + 1})")

            except httpx.RequestError as e:
                last_error = OllamaOpenAIError(f"Request failed: {e}")
                logger.warning(f"Ollama request failed (attempt {attempt + 1})")

            # Wait before retry
            if attempt < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay)

        # All retries exhausted
        if last_error:
            raise last_error
        raise OllamaOpenAIError("Unknown error occurred")

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
            return response.choices[0].message.content
        return ""

    async def __aenter__(self) -> "OllamaOpenAIClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
