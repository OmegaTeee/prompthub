"""Pydantic models for OpenAI-compatible API proxy."""

from typing import Any

from pydantic import BaseModel, Field


class ChatCompletionRequest(BaseModel):
    """OpenAI chat completion request body.

    Accepts the standard OpenAI fields. Extra fields are ignored by Pydantic.
    Response models are reused from router.enhancement.llm_client.
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


class ResponsesRequest(BaseModel):
    """OpenAI Responses API request body.

    Translates to Chat Completions internally. Accepts string or
    message-array input, with optional system instructions.
    """

    model_config = {"extra": "ignore"}

    model: str
    input: str | list[dict[str, Any]]
    instructions: str | None = None
    temperature: float | None = 0.7
    max_output_tokens: int | None = None
    top_p: float | None = None
    stream: bool = False


class ResponsesContentBlock(BaseModel):
    """Content block in a Responses API output message."""

    type: str  # "output_text" or "thinking"
    text: str | None = None
    thinking: str | None = None


class ResponsesOutputMessage(BaseModel):
    """Output message in Responses API format."""

    type: str = "message"
    role: str = "assistant"
    content: list[ResponsesContentBlock]


class ResponsesResponse(BaseModel):
    """OpenAI Responses API response body."""

    id: str
    object: str = "response"
    created_at: int
    model: str
    output: list[ResponsesOutputMessage]
    output_text: str
    usage: dict[str, int] | None = None
