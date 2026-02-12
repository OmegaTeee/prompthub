"""OpenAI-compatible API router.

Provides /v1/chat/completions and /v1/models endpoints that desktop apps
(Cursor, Raycast, Obsidian) can use as a drop-in OpenAI replacement.
Requests are authenticated via bearer tokens, optionally enhanced,
and forwarded to Ollama with circuit breaker protection.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from router.audit import audit_event
from router.enhancement.ollama_openai import (
    OllamaOpenAIClient,
    OllamaOpenAIConnectionError,
    OllamaOpenAIError,
    OpenAICompatConfig,
)
from router.openai_compat.auth import ApiKeyManager
from router.openai_compat.models import ApiKeyConfig, ChatCompletionRequest
from collections.abc import Callable

from router.openai_compat.streaming import stream_ollama_response

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


def create_openai_compat_router(
    enhancement_service: Callable[[], Any],
    circuit_breakers: Callable[[], Any],
    api_key_manager: ApiKeyManager,
    ollama_base_url: str = "http://localhost:11434/v1",
    ollama_timeout: float = 120.0,
) -> APIRouter:
    """Create the OpenAI-compatible API router with injected dependencies.

    Dependencies that are initialized lazily (during lifespan) are passed
    as getter callables, matching the dashboard router pattern.

    Args:
        enhancement_service: Callable returning EnhancementService (may return None before startup)
        circuit_breakers: Callable returning CircuitBreakerRegistry (may return None before startup)
        api_key_manager: Manages bearer token validation (loaded at module level)
        ollama_base_url: Ollama's OpenAI-compat base URL
        ollama_timeout: Timeout for Ollama requests in seconds

    Returns:
        Configured APIRouter for /v1/ endpoints
    """
    router = APIRouter(prefix="/v1", tags=["openai-compat"])

    # Shared Ollama client for non-streaming requests
    _ollama_client = OllamaOpenAIClient(
        OpenAICompatConfig(base_url=ollama_base_url, timeout=ollama_timeout)
    )

    # --- Auth dependency (closure over api_key_manager) ---

    async def authenticate(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> ApiKeyConfig:
        """Validate bearer token and return the associated API key config."""
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "message": "Missing bearer token",
                        "type": "invalid_request_error",
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        config = api_key_manager.validate_token(credentials.credentials)
        if not config:
            audit_event(
                event_type="auth_failure",
                action="validate",
                resource_type="api_key",
                resource_name="openai_compat",
                status="failed",
                error="Invalid bearer token",
            )
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "message": "Invalid API key",
                        "type": "invalid_request_error",
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        return config

    # --- Endpoints ---

    @router.post("/chat/completions")
    async def chat_completions(
        body: ChatCompletionRequest,
        api_key: ApiKeyConfig = Depends(authenticate),
    ):
        """OpenAI-compatible chat completion endpoint.

        Supports both streaming (SSE) and non-streaming modes.
        Optionally enhances the last user message before forwarding to Ollama.
        """
        client_name = api_key.client_name

        audit_event(
            event_type="openai_proxy",
            action="chat_completion",
            resource_type="ollama",
            resource_name=body.model,
            status="initiated",
            client_name=client_name,
            stream=body.stream,
        )

        # Circuit breaker check
        cb_registry = circuit_breakers()
        breaker = cb_registry.get("ollama-proxy") if cb_registry else None
        if breaker:
            try:
                breaker.check()
            except Exception:
                audit_event(
                    event_type="openai_proxy",
                    action="chat_completion",
                    resource_type="ollama",
                    resource_name=body.model,
                    status="failed",
                    error="Circuit breaker open",
                )
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": {
                            "message": "Service temporarily unavailable — Ollama circuit breaker open",
                            "type": "server_error",
                        }
                    },
                )

        # Enhancement: optionally enhance the last user message
        messages = [msg.copy() for msg in body.messages]

        svc = enhancement_service() if api_key.enhance else None
        if svc:
            last_user_idx = _find_last_user_message(messages)
            if last_user_idx is not None:
                original = messages[last_user_idx]["content"]
                try:
                    result = await svc.enhance(
                        prompt=original,
                        client_name=client_name,
                    )
                    if result.was_enhanced:
                        messages[last_user_idx] = {
                            **messages[last_user_idx],
                            "content": result.enhanced,
                        }
                        logger.info(
                            "Enhanced last user message for client=%s cached=%s",
                            client_name,
                            result.cached,
                        )
                except Exception as e:
                    # Enhancement failure is non-fatal — proceed with original
                    logger.warning("Enhancement failed for %s: %s", client_name, e)

        # Build Ollama payload
        payload: dict[str, Any] = {
            "model": body.model,
            "messages": messages,
            "temperature": body.temperature,
            "stream": body.stream,
        }
        if body.max_tokens is not None:
            payload["max_tokens"] = body.max_tokens
        if body.top_p is not None:
            payload["top_p"] = body.top_p
        if body.stop is not None:
            payload["stop"] = body.stop

        # --- Streaming response ---
        if body.stream:
            return StreamingResponse(
                _stream_with_breaker(
                    ollama_base_url, payload, ollama_timeout, breaker, body.model
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        # --- Non-streaming response ---
        try:
            response = await _ollama_client.chat_completion(
                model=body.model,
                messages=messages,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                stream=False,
            )
            if breaker:
                breaker.record_success()
            audit_event(
                event_type="openai_proxy",
                action="chat_completion",
                resource_type="ollama",
                resource_name=body.model,
                status="success",
                stream=False,
            )
            return response.model_dump()

        except (OllamaOpenAIConnectionError, OllamaOpenAIError) as e:
            if breaker:
                breaker.record_failure(e)
            audit_event(
                event_type="openai_proxy",
                action="chat_completion",
                resource_type="ollama",
                resource_name=body.model,
                status="failed",
                error=str(e),
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {"message": str(e), "type": "server_error"}
                },
            )

    @router.get("/models")
    async def list_models(
        api_key: ApiKeyConfig = Depends(authenticate),
    ):
        """List available Ollama models in OpenAI format."""
        try:
            models = await _ollama_client.list_models()
            return {"object": "list", "data": models}
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": f"Cannot reach Ollama: {e}",
                        "type": "server_error",
                    }
                },
            )

    @router.post("/api-keys/reload")
    async def reload_api_keys():
        """Reload API keys from config file (admin endpoint, no auth)."""
        api_key_manager.reload()
        audit_event(
            event_type="admin_action",
            action="reload",
            resource_type="config",
            resource_name="api_keys",
            status="success",
        )
        return {"message": "API keys reloaded", "count": api_key_manager.key_count}

    return router


# --- Helper functions ---


def _find_last_user_message(messages: list[dict[str, str]]) -> int | None:
    """Find the index of the last user message in the conversation."""
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            return i
    return None


async def _stream_with_breaker(
    ollama_base_url: str,
    payload: dict,
    timeout: float,
    breaker: Any,
    model: str,
):
    """Wrap the SSE stream with circuit breaker recording and audit logging."""
    try:
        async for chunk in stream_ollama_response(
            ollama_base_url=ollama_base_url,
            payload=payload,
            timeout=timeout,
        ):
            yield chunk
        breaker.record_success()
        audit_event(
            event_type="openai_proxy",
            action="chat_completion",
            resource_type="ollama",
            resource_name=model,
            status="success",
            stream=True,
        )
    except Exception as e:
        breaker.record_failure(e)
        logger.error("Streaming error for model=%s: %s", model, e)
        audit_event(
            event_type="openai_proxy",
            action="chat_completion",
            resource_type="ollama",
            resource_name=model,
            status="failed",
            error=str(e),
        )
        error_msg = str(e).replace('"', '\\"')
        yield f'data: {{"error": {{"message": "{error_msg}"}}}}\n\n'
        yield "data: [DONE]\n\n"
