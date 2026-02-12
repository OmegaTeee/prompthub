"""
Ollama client for local LLM inference.

This module provides async communication with a local Ollama instance
for prompt enhancement. It handles connection management, retries,
and graceful degradation when Ollama is unavailable.
"""

import asyncio
import logging
from typing import Any

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OllamaConfig(BaseModel):
    """Configuration for Ollama client."""

    base_url: str = "http://localhost:11434"
    timeout: float = 30.0  # Request timeout in seconds
    max_retries: int = 2
    retry_delay: float = 1.0


class OllamaResponse(BaseModel):
    """Response from Ollama generate endpoint."""

    model: str
    response: str
    done: bool = True
    total_duration: int | None = None  # nanoseconds
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None

    @property
    def tokens_per_second(self) -> float | None:
        """Calculate tokens per second if duration available."""
        if self.eval_count and self.eval_duration:
            # eval_duration is in nanoseconds
            return self.eval_count / (self.eval_duration / 1e9)
        return None


class OllamaError(Exception):
    """Base exception for Ollama errors."""

    pass


class OllamaConnectionError(OllamaError):
    """Raised when unable to connect to Ollama."""

    pass


class OllamaModelError(OllamaError):
    """Raised when model is not available."""

    pass


class OllamaClient:
    """
    Async client for Ollama API.

    Provides methods for:
    - Text generation (prompt enhancement)
    - Model listing
    - Health checking

    Example:
        client = OllamaClient()
        if await client.is_healthy():
            response = await client.generate(
                model="llama3.2:3b",
                prompt="Hello, world!",
                system="You are a helpful assistant."
            )
            print(response.response)
    """

    def __init__(self, config: OllamaConfig | None = None):
        """
        Initialize the Ollama client.

        Args:
            config: Configuration options
        """
        self.config = config or OllamaConfig()
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
            response = await client.get("/api/tags")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    async def list_models(self) -> list[dict[str, Any]]:
        """
        List available models.

        Returns:
            List of model information dicts

        Raises:
            OllamaConnectionError: If unable to connect
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except httpx.ConnectError as e:
            raise OllamaConnectionError(f"Cannot connect to Ollama: {e}") from e
        except httpx.RequestError as e:
            raise OllamaError(f"Request failed: {e}") from e

    async def has_model(self, model: str) -> bool:
        """
        Check if a specific model is available.

        Args:
            model: Model name (e.g., "llama3.2:3b")

        Returns:
            True if model is available
        """
        try:
            models = await self.list_models()
            model_names = [m.get("name", "") for m in models]
            return model in model_names
        except OllamaError:
            return False

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> OllamaResponse:
        """
        Generate text using Ollama.

        Args:
            model: Model name (e.g., "llama3.2:3b")
            prompt: The prompt to complete
            system: System prompt for context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response (not implemented)

        Returns:
            OllamaResponse with generated text

        Raises:
            OllamaConnectionError: If unable to connect
            OllamaModelError: If model not found
            OllamaError: For other errors
        """
        if stream:
            raise NotImplementedError("Streaming not yet implemented")

        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if system:
            payload["system"] = system

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        last_error: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                client = await self._get_client()
                response = await client.post("/api/generate", json=payload)

                if response.status_code == 404:
                    raise OllamaModelError(f"Model '{model}' not found")

                response.raise_for_status()
                data = response.json()

                return OllamaResponse(
                    model=data.get("model", model),
                    response=data.get("response", ""),
                    done=data.get("done", True),
                    total_duration=data.get("total_duration"),
                    load_duration=data.get("load_duration"),
                    prompt_eval_count=data.get("prompt_eval_count"),
                    eval_count=data.get("eval_count"),
                    eval_duration=data.get("eval_duration"),
                )

            except httpx.ConnectError as e:
                last_error = OllamaConnectionError(f"Cannot connect to Ollama: {e}")
                logger.warning(f"Ollama connection failed (attempt {attempt + 1})")

            except OllamaModelError:
                raise  # Don't retry model errors

            except httpx.TimeoutException as e:
                last_error = OllamaError(f"Request timed out: {e}")
                logger.warning(f"Ollama request timed out (attempt {attempt + 1})")

            except httpx.RequestError as e:
                last_error = OllamaError(f"Request failed: {e}")
                logger.warning(f"Ollama request failed (attempt {attempt + 1})")

            # Wait before retry
            if attempt < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay)

        # All retries exhausted
        if last_error:
            raise last_error
        raise OllamaError("Unknown error occurred")

    async def __aenter__(self) -> "OllamaClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
