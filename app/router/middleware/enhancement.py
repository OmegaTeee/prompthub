"""
Enhancement middleware.

Optionally enhances prompt-like fields on MCP proxy requests.

Behavior:
- If `X-Enhance` header is present and truthy OR `auto_enhance_mcp` setting is True,
  the middleware will attempt to locate a `prompt`-like field in the JSON-RPC
  `params` and call the global `enhancement_service.enhance()` to replace it.

This file provides a minimal, safe scaffold — it gracefully no-ops when the
enhancement service is not yet initialized.
"""

import json
import logging
import time
from collections.abc import Callable

from fastapi import Request
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

from router.config.settings import get_settings

logger = logging.getLogger(__name__)


def _make_receive_with_body(body_bytes: bytes) -> Callable[[], dict]:
    async def receive() -> dict:
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    return receive


async def _enhance_field(container: dict, key: str, enhancement_service, client_name: str) -> bool:
    """Enhance a string field in-place using the enhancement service.

    Returns True if the field was updated.
    """
    try:
        original = container.get(key)
        if not isinstance(original, str):
            return False
        # Time the enhancement call and log if it's slow
        start = time.perf_counter()
        result = None
        try:
            result = await enhancement_service.enhance(prompt=original, client_name=client_name)
        except Exception:
            # Let outer handler log the exception
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        try:
            settings = get_settings()
            threshold = getattr(settings, "enhancement_slow_ms_threshold", 100)
        except Exception:
            threshold = 100

        if duration_ms > threshold:
            logger.warning(
                "Slow enhancement: %.1fms for %d chars (client=%s)",
                duration_ms,
                len(original) if isinstance(original, str) else 0,
                client_name,
            )

        # Prometheus metrics: record duration and count
        try:
            enhancement_duration_seconds.observe(duration_ms / 1000.0)
            enhancement_calls.inc()
        except Exception:
            # Metrics should never break functionality
            logger.debug("Metrics publish failed")

        if result and result.enhanced and result.enhanced != original:
            container[key] = result.enhanced
            return True
    except Exception:
        logger.exception("Enhancement failed for field %s", key)
    return False


# Prometheus metrics (module-level so tests can import/reset if needed)
enhancement_calls = Counter(
    "agenthub_enhancement_calls_total", "Total enhancement calls attempted"
)
enhancement_failures = Counter(
    "agenthub_enhancement_failures_total", "Enhancement calls that raised an exception"
)
enhancement_duration_seconds = Histogram(
    "agenthub_enhancement_duration_seconds", "Enhancement call duration (seconds)"
)


class _InMemoryRateLimiter:
    """Simple token-bucket rate limiter per-client stored in-memory.

    Not distributed; suitable for single-instance deployments. Uses fractional
    tokens to allow smooth refill.
    """

    def __init__(self):
        # client_key -> (tokens, last_ts, rate_per_second)
        self._buckets: dict[str, tuple[float, float, float]] = {}

    def allows(self, client_key: str, max_per_minute: int) -> bool:
        now = time.time()
        rate_per_sec = max_per_minute / 60.0
        bucket = self._buckets.get(client_key)
        if bucket is None:
            self._buckets[client_key] = (rate_per_sec, now, rate_per_sec)
            return True

        tokens, last_ts, capacity = bucket
        # Refill tokens
        elapsed = now - last_ts
        tokens = min(capacity, tokens + elapsed * rate_per_sec)
        if tokens < 1.0:
            # not enough tokens
            self._buckets[client_key] = (tokens, now, capacity)
            return False

        # consume one token
        tokens -= 1.0
        self._buckets[client_key] = (tokens, now, capacity)
        return True


# Shared rate limiter instance
_rate_limiter = _InMemoryRateLimiter()


class EnhancementMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()

        try:
            should_enhance = False
            header = request.headers.get("X-Enhance")
            if header and header.lower() in ("1", "true", "yes", "on"):  # per-request opt-in
                should_enhance = True

            if not should_enhance and not getattr(settings, "auto_enhance_mcp", False):
                return await call_next(request)

            # Only enhance MCP proxy POST requests
            if request.method != "POST" or not request.url.path.startswith("/mcp/"):
                return await call_next(request)

            # Protect against excessively large payloads
            content_length = request.headers.get("content-length")
            if content_length:
                size = int(content_length)
                max_size = settings.max_enhancement_body_size
                if size > max_size:
                    logger.warning(
                        f"Request body too large for enhancement: {size} bytes "
                        f"(max: {max_size}). Skipping enhancement."
                    )
                    return await call_next(request)

            # Read body (now with size protection)
            body_bytes = await request.body()
            if not body_bytes:
                return await call_next(request)

            try:
                body = json.loads(body_bytes)
            except Exception:
                return await call_next(request)

            params = body.get("params") if isinstance(body, dict) else None
            if not isinstance(params, dict):
                return await call_next(request)

            # Identify common prompt keys
            prompt_keys = ["prompt", "input", "message", "text"]
            found_key = None
            for k in prompt_keys:
                if k in params and isinstance(params[k], str):
                    found_key = k
                    break

            if not found_key:
                # try nested shapes (e.g., arguments: { prompt: ... })
                if isinstance(params.get("arguments"), dict):
                    for k in prompt_keys:
                        if k in params["arguments"] and isinstance(params["arguments"][k], str):
                            found_key = ("arguments", k)
                            break

            if not found_key:
                return await call_next(request)

            # Resolve enhancement_service from app.state, falling back to module-level variable for tests
            enhancement_service = None
            app_obj = getattr(request, "app", None)
            if app_obj is not None:
                enhancement_service = getattr(getattr(app_obj, "state", None), "enhancement_service", None)

            if not enhancement_service:
                # Fall back to module-level variable (used by some tests and legacy code)
                try:
                    from router import main as router_main

                    enhancement_service = getattr(router_main, "enhancement_service", None)
                except Exception:
                    enhancement_service = None

            if not enhancement_service:
                logger.debug("Enhancement service not available; skipping enhancement")
                return await call_next(request)

            # Rate-limiting: check per-client allowance if enabled
            settings = get_settings()
            client_name = request.headers.get("X-Client-Name") or request.client.host if request.client else "unknown"
            if getattr(settings, "enable_enhancement_rate_limit", False):
                allowed = _rate_limiter.allows(client_name, getattr(settings, "enhancement_rate_limit_per_minute", 60))
                if not allowed:
                    logger.warning("Enhancement rate-limited for client=%s", client_name)
                    return await call_next(request)

            # Extract prompt and enhance in a single helper to avoid duplication
            if isinstance(found_key, tuple):
                await _enhance_field(params[found_key[0]], found_key[1], enhancement_service, client_name or "unknown")
            else:
                await _enhance_field(params, found_key, enhancement_service, client_name or "unknown")

            # Replace the request body for downstream handlers.
            # NOTE: Starlette/FastAPI do not provide a public API to replace the
            # request body once it has been consumed. Downstream handlers call
            # the ASGI `receive` callable to retrieve body chunks; to ensure
            # they see the enhanced payload we replace the cached body and the
            # `receive` callable. This uses private attributes (`_body` and
            # `_receive`) and is therefore brittle — pin `starlette` in
            # `requirements.txt` and add integration tests that exercise this
            # behavior. See: https://github.com/encode/starlette/issues/495
            new_body = json.dumps(body).encode("utf-8")
            try:
                # Starlette/FastAPI may cache the body on the Request object
                request._body = new_body  # type: ignore[attr-defined]
            except Exception:
                # Best-effort: if we can't set the cached body, replacing
                # the receive callable still ensures downstream handlers
                # see the modified content.
                pass
            request._receive = _make_receive_with_body(new_body)  # type: ignore[attr-defined]

            return await call_next(request)

        except Exception as e:
            logger.exception(f"Enhancement middleware failed: {e}")
            return await call_next(request)
