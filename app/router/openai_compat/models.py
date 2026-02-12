"""Pydantic models for OpenAI-compatible API proxy."""

from pydantic import BaseModel, Field


class ChatCompletionRequest(BaseModel):
    """OpenAI chat completion request body.

    Accepts the standard OpenAI fields. Extra fields are ignored by Pydantic.
    Response models are reused from router.enhancement.ollama_openai.
    """

    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    stop: str | list[str] | None = None
    user: str | None = None


class ApiKeyConfig(BaseModel):
    """Configuration for a single API key."""

    client_name: str
    enhance: bool = True
    description: str = ""


class ApiKeysRegistry(BaseModel):
    """Registry of API keys loaded from config file."""

    keys: dict[str, ApiKeyConfig] = Field(default_factory=dict)
