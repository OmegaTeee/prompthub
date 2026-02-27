"""
Request Timeout Middleware

Protects against slow clients and network delays by enforcing request-level timeouts.
This prevents workers from being tied up indefinitely by unresponsive clients.

Timeout is applied at the FastAPI request processing level, separate from individual
I/O operation timeouts (httpx, subprocess, etc.).
"""

import asyncio
import logging
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Default request timeout in seconds
DEFAULT_REQUEST_TIMEOUT = 60.0

# Paths that should have extended timeout
EXTENDED_TIMEOUT_PATHS = {
    "/pipelines/documentation": 300.0,  # 5 minutes for long-running documentation processing
    "/v1/chat/completions": 180.0,  # 3 minutes for slow Ollama models (deepseek-r1, etc.)
    "/ollama/enhance": 180.0,  # 3 minutes for cold model loads + enhancement
    "/sessions/": 120.0,  # 2 minutes for session memory operations (DB queries + MCP sync)
}

# Paths that should have no timeout
NO_TIMEOUT_PATHS = set()


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces request-level timeouts.

    Prevents slow clients and network delays from indefinitely consuming server resources.

    Example:
        app.add_middleware(RequestTimeoutMiddleware, timeout=60.0)

        # Custom timeouts per path:
        EXTENDED_TIMEOUT_PATHS = {
            "/long-running-task": 300.0,
        }
    """

    def __init__(self, app, timeout: float = DEFAULT_REQUEST_TIMEOUT):
        """
        Initialize the timeout middleware.

        Args:
            app: FastAPI application
            timeout: Default request timeout in seconds
        """
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """
        Process request with timeout enforcement.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint handler

        Returns:
            HTTP response or 504 Gateway Timeout error
        """
        # Determine timeout for this path
        timeout = self._get_timeout_for_path(request.url.path)

        if timeout is None:
            # No timeout enforcement for this path
            return await call_next(request)

        try:
            # Wrap the next middleware/endpoint call with asyncio timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=timeout,
            )
            return response

        except asyncio.TimeoutError:
            logger.warning(
                f"Request timeout: {request.method} {request.url.path} "
                f"exceeded {timeout}s timeout"
            )

            # Return JSON-RPC error if this is an MCP endpoint
            if "/mcp/" in request.url.path:
                return JSONResponse(
                    {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"Request timed out after {timeout:.0f}s",
                        },
                        "id": None,
                    },
                    status_code=504,
                )

            # Return standard HTTP 504 for other endpoints
            return JSONResponse(
                {
                    "error": "Request Timeout",
                    "message": f"Request processing exceeded {timeout:.0f}s timeout",
                    "timeout": timeout,
                },
                status_code=504,
            )

        except Exception as e:
            logger.exception(f"Unexpected error in timeout middleware: {e}")
            return JSONResponse(
                {"error": "Internal Server Error"},
                status_code=500,
            )

    @staticmethod
    def _get_timeout_for_path(path: str) -> float | None:
        """
        Determine the timeout for a given request path.

        Args:
            path: Request path (e.g., "/mcp/server/endpoint")

        Returns:
            Timeout in seconds, or None for no timeout
        """
        # Check for no-timeout paths first
        for no_timeout_path in NO_TIMEOUT_PATHS:
            if path.startswith(no_timeout_path):
                return None

        # Check for extended timeout paths
        for extended_path, extended_timeout in EXTENDED_TIMEOUT_PATHS.items():
            if path.startswith(extended_path):
                return extended_timeout

        # Use default timeout
        return DEFAULT_REQUEST_TIMEOUT
