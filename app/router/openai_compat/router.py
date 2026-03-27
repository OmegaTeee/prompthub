"""OpenAI-compatible API router.

Provides /v1/chat/completions and /v1/models endpoints that desktop apps
(Cursor, Raycast, Obsidian) can use as a drop-in OpenAI replacement.
Requests are authenticated via bearer tokens, optionally enhanced,
and forwarded to the LLM server with circuit breaker protection.
"""

import logging
import uuid
from collections.abc import Callable
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from router.audit import audit_event
from router.enhancement.llm_client import (
    LLMClient,
    LLMConfig,
    LLMConnectionError,
    LLMError,
)
from router.openai_compat.auth import ApiKeyManager
from router.openai_compat.models import (
    ApiKeyConfig,
    ChatCompletionRequest,
    ResponsesRequest,
)

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


def create_openai_compat_router(
    enhancement_service: Callable[[], Any],
    circuit_breakers: Callable[[], Any],
    api_key_manager: ApiKeyManager,
    llm_base_url: str = "http://localhost:1234/v1",
    llm_timeout: float = 120.0,
) -> APIRouter:
    """Create the OpenAI-compatible API router with injected dependencies.

    Dependencies that are initialized lazily (during lifespan) are passed
    as getter callables, matching the dashboard router pattern.

    Args:
        enhancement_service: Callable returning EnhancementService (may return None before startup)
        circuit_breakers: Callable returning CircuitBreakerRegistry (may return None before startup)
        api_key_manager: Manages bearer token validation (loaded at module level)
        llm_base_url: LLM server's OpenAI-compat base URL
        llm_timeout: Timeout for LLM requests in seconds

    Returns:
        Configured APIRouter for /v1/ endpoints
    """
    router = APIRouter(prefix="/v1", tags=["openai-compat"])

    # Shared LLM client for non-streaming requests
    _llm_client = LLMClient(LLMConfig(base_url=llm_base_url, timeout=llm_timeout))

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
        Optionally enhances the last user message before forwarding to LLM server.
        """
        client_name = api_key.client_name

        audit_event(
            event_type="openai_proxy",
            action="chat_completion",
            resource_type="llm",
            resource_name=body.model,
            status="initiated",
            client_name=client_name,
            stream=body.stream,
        )

        # Guard: reject placeholder model names (e.g. OpenAPI default "string")
        if not body.model or body.model in ("string", "model", "") or " " in body.model:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid model name: '{body.model}'. Provide a valid model name (e.g. 'gemma3:4b').",
            )

        # Circuit breaker check
        cb_registry = circuit_breakers()
        breaker = cb_registry.get("llm-proxy") if cb_registry else None
        if breaker:
            try:
                breaker.check()
            except Exception:
                audit_event(
                    event_type="openai_proxy",
                    action="chat_completion",
                    resource_type="llm",
                    resource_name=body.model,
                    status="failed",
                    error="Circuit breaker open",
                )
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": {
                            "message": "Service temporarily unavailable — LLM circuit breaker open",
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
                        "Invalid X-Privacy-Level: %s",
                        raw_privacy,
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

        # Build payload for LLM server
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
                _stream_with_breaker(payload, breaker, _llm_client, body.model),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        # --- Non-streaming response ---
        try:
            response = await _llm_client.chat_completion(
                model=body.model,
                messages=messages,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
            )
            if breaker:
                breaker.record_success()
            audit_event(
                event_type="openai_proxy",
                action="chat_completion",
                resource_type="llm",
                resource_name=body.model,
                status="success",
                stream=False,
            )
            return response.model_dump()

        except LLMConnectionError as e:
            if breaker:
                breaker.record_failure(e)
            audit_event(
                event_type="openai_proxy",
                action="chat_completion",
                resource_type="llm",
                resource_name=body.model,
                status="failed",
                error=str(e),
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": f"Cannot reach LLM server: {e}",
                        "type": "server_error",
                    }
                },
            )
        except (LLMError, httpx.HTTPError) as e:
            if breaker:
                breaker.record_failure(e)
            audit_event(
                event_type="openai_proxy",
                action="chat_completion",
                resource_type="llm",
                resource_name=body.model,
                status="failed",
                error=str(e),
            )
            raise HTTPException(
                status_code=502,
                detail={"error": {"message": str(e), "type": "server_error"}},
            )

    @router.get("/models")
    async def list_models():
        """List available models in OpenAI format.

        Unauthenticated — model listing is non-sensitive and clients
        like Raycast call this without a bearer token during provider
        discovery.
        """
        try:
            models = await _llm_client.list_models()
            return {"object": "list", "data": models}
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": f"Cannot reach LLM server: {e}",
                        "type": "server_error",
                    }
                },
            )

    @router.get("/api/version")
    async def api_version():
        """Version endpoint for client discovery.

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

    @router.post("/responses")
    async def responses(
        body: ResponsesRequest,
        request: Request,
        api_key: ApiKeyConfig = Depends(authenticate),
    ):
        """OpenAI Responses API endpoint (non-streaming).

        Translates Responses API format to Chat Completions, proxies to
        LLM server, and wraps the result back into Responses API shape.
        """
        client_name = api_key.client_name

        audit_event(
            event_type="openai_proxy",
            action="responses",
            resource_type="llm",
            resource_name=body.model,
            status="initiated",
            client_name=client_name,
        )

        # Reject streaming — not supported
        if body.stream:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": "Streaming not supported for /v1/responses. Disable streaming in your client.",
                        "type": "invalid_request_error",
                    }
                },
            )

        # Guard: reject placeholder model names
        if not body.model or body.model in ("string", "model", "") or " " in body.model:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid model name: '{body.model}'. Provide a valid model name (e.g. 'gemma-3-4b').",
            )

        # Circuit breaker check
        cb_registry = circuit_breakers()
        breaker = cb_registry.get("llm-proxy") if cb_registry else None
        if breaker:
            try:
                breaker.check()
            except Exception:
                audit_event(
                    event_type="openai_proxy",
                    action="responses",
                    resource_type="llm",
                    resource_name=body.model,
                    status="failed",
                    error="Circuit breaker open",
                )
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": {
                            "message": "Service temporarily unavailable — LLM circuit breaker open",
                            "type": "server_error",
                        }
                    },
                )

        # Translate Responses API input → Chat Completions messages
        messages = _translate_responses_to_messages(body.input, body.instructions)

        # Enhancement: optionally enhance the last user message
        svc = enhancement_service() if api_key.enhance else None
        if svc:
            privacy_override = None
            raw_privacy = request.headers.get("X-Privacy-Level")
            if raw_privacy:
                try:
                    from router.enhancement import PrivacyLevel

                    privacy_override = PrivacyLevel(raw_privacy)
                except ValueError:
                    logger.warning("Invalid X-Privacy-Level: %s", raw_privacy)

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
                    logger.warning("Enhancement failed for %s: %s", client_name, e)

        # Forward to LLM server
        try:
            response = await _llm_client.chat_completion(
                model=body.model,
                messages=messages,
                temperature=body.temperature,
                max_tokens=body.max_output_tokens,
            )
            if breaker:
                breaker.record_success()

            audit_event(
                event_type="openai_proxy",
                action="responses",
                resource_type="llm",
                resource_name=body.model,
                status="success",
            )

            return _build_responses_response(response.model_dump())

        except LLMConnectionError as e:
            if breaker:
                breaker.record_failure(e)
            audit_event(
                event_type="openai_proxy",
                action="responses",
                resource_type="llm",
                resource_name=body.model,
                status="failed",
                error=str(e),
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": f"Cannot reach LLM server: {e}",
                        "type": "server_error",
                    }
                },
            )
        except (LLMError, httpx.HTTPError) as e:
            if breaker:
                breaker.record_failure(e)
            audit_event(
                event_type="openai_proxy",
                action="responses",
                resource_type="llm",
                resource_name=body.model,
                status="failed",
                error=str(e),
            )
            raise HTTPException(
                status_code=502,
                detail={"error": {"message": str(e), "type": "server_error"}},
            )

    return router


# --- Helper functions ---


def _find_last_user_message(messages: list[dict[str, str]]) -> int | None:
    """Find the index of the last user message in the conversation."""
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            return i
    return None


def _translate_responses_to_messages(
    input_data: str | list[dict[str, str]],
    instructions: str | None,
) -> list[dict[str, str]]:
    """Convert Responses API input + instructions to Chat Completions messages.

    Args:
        input_data: String (single user message) or array of message dicts.
        instructions: Optional system prompt to prepend.

    Returns:
        List of message dicts for Chat Completions API.
    """
    messages: list[dict[str, str]] = []

    if instructions:
        messages.append({"role": "system", "content": instructions})

    if isinstance(input_data, str):
        messages.append({"role": "user", "content": input_data})
    else:
        messages.extend(input_data)

    return messages


def _build_responses_response(chat_response: dict) -> dict:
    """Wrap a Chat Completions response dict into Responses API format.

    Args:
        chat_response: Raw dict from LLMClient.chat_completion().model_dump()

    Returns:
        Dict matching the OpenAI Responses API shape.
    """
    message = chat_response["choices"][0]["message"]
    text = message.get("content", "")
    reasoning = message.get("reasoning_content")

    content_blocks = []
    if reasoning:
        content_blocks.append({"type": "thinking", "thinking": reasoning})
    content_blocks.append({"type": "output_text", "text": text})

    # Map usage field names: prompt_tokens → input_tokens
    raw_usage = chat_response.get("usage")
    usage = None
    if raw_usage:
        usage = {
            "input_tokens": raw_usage.get("prompt_tokens", 0),
            "output_tokens": raw_usage.get("completion_tokens", 0),
            "total_tokens": raw_usage.get("total_tokens", 0),
        }

    return {
        "id": f"resp_{uuid.uuid4().hex[:24]}",
        "object": "response",
        "created_at": chat_response.get("created", 0),
        "model": chat_response.get("model", ""),
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": content_blocks,
            }
        ],
        "output_text": text,
        "usage": usage,
    }


async def _stream_with_breaker(
    payload: dict,
    breaker: Any,
    llm_client: LLMClient,
    model: str,
):
    """Stream chat completion via OpenAI-compat /v1/chat/completions."""
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(llm_client.config.timeout)
        ) as client:
            async with client.stream(
                "POST",
                f"{llm_client.config.base_url}/chat/completions",
                json=payload,
                headers=llm_client.config.extra_headers or {},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        yield f"{line}\n\n"
        if breaker:
            breaker.record_success()
        audit_event(
            event_type="openai_proxy",
            action="chat_completion",
            resource_type="llm",
            resource_name=model,
            status="success",
            stream=True,
        )
    except Exception as e:
        if breaker:
            breaker.record_failure(e)
        logger.error("Streaming error for model=%s: %s", model, e)
        audit_event(
            event_type="openai_proxy",
            action="chat_completion",
            resource_type="llm",
            resource_name=model,
            status="failed",
            error=str(e),
        )
        error_msg = str(e).replace('"', '\\"')
        yield f'data: {{"error": {{"message": "{error_msg}"}}}}\n\n'
        yield "data: [DONE]\n\n"
