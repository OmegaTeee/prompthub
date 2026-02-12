"""
AgentHub Middleware.

Request logging and activity tracking for the dashboard.
"""

from router.middleware.activity import (
    ActivityLog,
    ActivityLoggingMiddleware,
    activity_log,
)
from router.middleware.audit_context import (
    AuditContextMiddleware,
    get_audit_context,
    set_client_id,
    set_client_ip,
    set_request_id,
    set_session_id,
)

__all__ = [
    "ActivityLog",
    "ActivityLoggingMiddleware",
    "activity_log",
    "AuditContextMiddleware",
    "get_audit_context",
    "set_client_id",
    "set_client_ip",
    "set_request_id",
    "set_session_id",
]
