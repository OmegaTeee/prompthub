"""OpenAI-compatible API router.

Provides /v1/chat/completions and /v1/models endpoints that desktop apps
(Cursor, Raycast, Obsidian) can use as a drop-in OpenAI replacement.
Requests are authenticated via bearer tokens, optionally enhanced,
and forwarded to Ollama with circuit breaker protection.
"""

import logging
import time
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
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
        request: Request,
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

        # Guard: reject placeholder model names (e.g. OpenAPI default "string")
        if not body.model or body.model in ("string", "model", "") or " " in body.model:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid model name: '{body.model}'. Provide a valid Ollama model (e.g. 'gemma3:4b').",
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
            # Parse privacy header override
            privacy_override = None
            raw_privacy = request.headers.get("X-Privacy-Level")
            if raw_privacy:
                try:
                    from router.enhancement import PrivacyLevel
                    privacy_override = PrivacyLevel(raw_privacy)
                except ValueError:
                    logger.warning(
                        "Invalid X-Privacy-Level: %s", raw_privacy,
                    )

            last_user_idx = _find_last_user_message(messages)
            if last_user_idx is not None:
                original = messages[last_user_idx]["content"]
                try:
                    result = await svc.enhance(
                        prompt=original,
                        client_name=client_name,
                        privacy_override=privacy_override,
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

        # Build Ollama payload (think:false is applied downstream in
        # streaming.py and _chat_via_native_api via Ollama's native API)
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
        # Route through Ollama's native /api/chat with think:false
        # (Ollama's /v1/ ignores think:false, wasting tokens on reasoning)
        try:
            result = await _chat_via_native_api(
                ollama_base_url, payload, ollama_timeout,
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
            return result

        except (OllamaOpenAIConnectionError, OllamaOpenAIError, httpx.HTTPError) as e:
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
    async def list_models():
        """List available Ollama models in OpenAI format.

        Unauthenticated — model listing is non-sensitive and clients
        like Raycast call this without a bearer token during provider
        discovery.
        """
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

    @router.get("/api/version")
    async def api_version():
        """Ollama-compatible version endpoint.

        Raycast probes this to verify the provider is alive.
        Returns a minimal version response to prevent 404 errors.
        """
        return {"version": "0.1.0"}

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


async def _chat_via_native_api(
    ollama_v1_url: str,
    payload: dict,
    timeout: float,
) -> dict:
    """Non-streaming chat via Ollama's native /api/chat (supports think:false).

    Translates the OpenAI-format payload to Ollama native format,
    calls /api/chat, and returns an OpenAI-compatible response dict.
    """
    from router.openai_compat.streaming import _ollama_base_from_v1

    base = _ollama_base_from_v1(ollama_v1_url)
    url = f"{base}/api/chat"

    native_payload: dict = {
        "model": payload.get("model", ""),
        "messages": payload.get("messages", []),
        "stream": False,
        "think": False,
    }
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

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        resp = await client.post(url, json=native_payload)
        resp.raise_for_status()
        data = resp.json()

    msg = data.get("message", {})
    model = data.get("model", payload.get("model", ""))
    prompt_tokens = data.get("prompt_eval_count", 0)
    completion_tokens = data.get("eval_count", 0)
    reason = data.get("done_reason", "stop")

    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": msg.get("role", "assistant"),
                    "content": msg.get("content", ""),
                },
                "finish_reason": "length" if reason == "length" else "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
