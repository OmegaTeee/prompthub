"""
Audit Context Middleware for AgentHub.

Captures and propagates audit context (request ID, client ID, client IP)
through async calls using Python contextvars.
"""

import contextvars
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variables for async propagation
request_id_ctx = contextvars.ContextVar("request_id", default=None)
client_id_ctx = contextvars.ContextVar("client_id", default=None)
client_ip_ctx = contextvars.ContextVar("client_ip", default=None)
session_id_ctx = contextvars.ContextVar("session_id", default=None)


def get_audit_context() -> dict:
    """
    Get current audit context for logging.

    Returns:
        Dictionary with request_id, client_id, client_ip, session_id.
        Values are None if not set.
    """
    return {
        "request_id": request_id_ctx.get(),
        "client_id": client_id_ctx.get(),
        "client_ip": client_ip_ctx.get(),
        "session_id": session_id_ctx.get(),
    }


def set_request_id(request_id: str) -> None:
    """Set request ID in context."""
    request_id_ctx.set(request_id)


def set_client_id(client_id: str) -> None:
    """Set client ID in context."""
    client_id_ctx.set(client_id)


def set_client_ip(client_ip: str) -> None:
    """Set client IP in context."""
    client_ip_ctx.set(client_ip)


def set_session_id(session_id: str) -> None:
    """Set session ID in context."""
    session_id_ctx.set(session_id)


class AuditContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that captures and propagates audit context through async calls.

    For each request:
    1. Generates a unique correlation ID (request_id)
    2. Extracts client information (client_id, client_ip, session_id)
    3. Stores in contextvars for async propagation
    4. Adds correlation ID to response headers for client-side tracing
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and set audit context.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response with X-Request-ID header
        """
        # Generate unique correlation ID for this request
        request_id = str(uuid4())
        request_id_ctx.set(request_id)

        # Extract client IP address
        client_ip = "unknown"
        if request.client:
            client_ip = request.client.host

        # Check X-Forwarded-For for proxy scenarios
        if forwarded_for := request.headers.get("X-Forwarded-For"):
            # Take first IP (client's original IP)
            client_ip = forwarded_for.split(",")[0].strip()

        client_ip_ctx.set(client_ip)

        # Get client ID from header (for authenticated requests)
        # Default to 'anonymous' for unauthenticated requests
        client_id = request.headers.get("X-Client-ID", "anonymous")
        client_id_ctx.set(client_id)

        # Get session ID from header or cookie
        session_id = request.headers.get("X-Session-ID")
        if not session_id and "session_id" in request.cookies:
            session_id = request.cookies["session_id"]
        if session_id:
            session_id_ctx.set(session_id)

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers for client-side tracing
        response.headers["X-Request-ID"] = request_id

        return response
