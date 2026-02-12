"""
Structured Audit Logging for AgentHub.

Provides structured audit logging with JSON format for compliance
and security monitoring. Audit events are logged separately from
application logs with longer retention.

Audit events follow a standardized schema:
- event_type: Category of event (admin_action, credential_access, etc.)
- action: Specific action (start, stop, get, set, delete)
- resource_type: Type of resource (mcp_server, credential, config)
- resource_name: Name of resource
- status: Status (initiated, success, failed)
- error: Error message if failed
- request_id: Correlation ID for tracing
- client_id: User or client identifier
- client_ip: Source IP address
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

import structlog

from router.middleware.audit_context import get_audit_context

# Get logger instance
logger = logging.getLogger(__name__)

# Configure structlog processors
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


def setup_audit_logging(
    log_dir: Path | None = None,
    console_output: bool = True,
) -> None:
    """
    Configure dual logging system.

    Sets up:
    1. Audit logs -> JSON format, /var/log/agenthub/audit.log or stderr
    2. Application logs -> human-readable, existing handlers

    Args:
        log_dir: Directory for log files. If None, logs to stderr only.
        console_output: If True, also log audit to console (for dev)
    """
    # Get audit logger
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False  # Don't propagate to root logger

    # Clear existing handlers
    audit_logger.handlers.clear()

    # File handler (if log_dir provided)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        audit_file = log_dir / "audit.log"

        # Rotating file handler for audit logs
        # Keep 90 days worth (assuming ~100MB per file)
        file_handler = logging.handlers.RotatingFileHandler(
            audit_file,
            maxBytes=100_000_000,  # 100MB
            backupCount=90,  # Keep 90 rotations
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        audit_logger.addHandler(file_handler)

    # Console handler (for development)
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)
        audit_logger.addHandler(console_handler)

    # If no handlers were added, add stderr as fallback
    if not audit_logger.handlers:
        fallback_handler = logging.StreamHandler(sys.stderr)
        fallback_handler.setLevel(logging.INFO)
        audit_logger.addHandler(fallback_handler)


# Get structured audit logger
audit_logger = structlog.get_logger("audit")


def audit_event(
    event_type: str,
    action: str,
    resource_type: str,
    resource_name: str,
    status: str,
    error: str | None = None,
    **kwargs: Any,
) -> None:
    """
    Log a structured audit event.

    Args:
        event_type: Type of event (admin_action, credential_access, config_change, etc.)
        action: Action performed (start, stop, restart, get, set, delete, update)
        resource_type: Type of resource (mcp_server, credential, config, cache)
        resource_name: Name of the resource being operated on
        status: Operation status (initiated, success, failed)
        error: Error message if status is 'failed'
        **kwargs: Additional event-specific fields

    Examples:
        >>> audit_event(
        ...     event_type="admin_action",
        ...     action="start",
        ...     resource_type="mcp_server",
        ...     resource_name="obsidian",
        ...     status="success"
        ... )

        >>> audit_event(
        ...     event_type="credential_access",
        ...     action="get",
        ...     resource_type="credential",
        ...     resource_name="obsidian_api_key",
        ...     status="success"
        ... )

        >>> audit_event(
        ...     event_type="admin_action",
        ...     action="stop",
        ...     resource_type="mcp_server",
        ...     resource_name="memory",
        ...     status="failed",
        ...     error="Server not running"
        ... )
    """
    # Get audit context (request_id, client_id, client_ip)
    context = get_audit_context()

    # Choose log level based on event type and status
    log_method = audit_logger.info

    if status == "failed":
        log_method = audit_logger.error
    elif event_type == "credential_access":
        # Credential access is always logged at warning level for security
        log_method = audit_logger.warning
    elif event_type == "config_change":
        # Config changes are important, log at warning
        log_method = audit_logger.warning

    # Log the event
    log_method(
        event_type,
        action=action,
        resource_type=resource_type,
        resource_name=resource_name,
        status=status,
        error=error,
        **context,
        **kwargs,
    )

    # Check for security alerts (only if status is final: success or failed)
    if status in ("success", "failed"):
        try:
            from router.security_alerts import get_alert_manager

            alert_mgr = get_alert_manager()
            alert_mgr.check_event(
                event_type=event_type,
                action=action,
                status=status,
                resource_name=resource_name,
                client_id=context.get("client_id"),
                client_ip=context.get("client_ip"),
                error=error,
            )
        except Exception as e:
            # Don't fail audit logging if alert check fails
            logger.warning(f"Security alert check failed: {e}")


def audit_admin_action(
    action: str,
    server_name: str,
    status: str,
    error: str | None = None,
    **kwargs: Any,
) -> None:
    """
    Log an admin action on an MCP server.

    Convenience wrapper for server lifecycle events.

    Args:
        action: Action performed (start, stop, restart)
        server_name: Name of the server
        status: Operation status (initiated, success, failed)
        error: Error message if failed
        **kwargs: Additional fields
    """
    audit_event(
        event_type="admin_action",
        action=action,
        resource_type="mcp_server",
        resource_name=server_name,
        status=status,
        error=error,
        **kwargs,
    )


def audit_credential_access(
    action: str,
    credential_key: str,
    status: str,
    error: str | None = None,
    **kwargs: Any,
) -> None:
    """
    Log credential access (get, set, delete).

    Convenience wrapper for credential operations.

    Args:
        action: Action performed (get, set, delete)
        credential_key: Name of the credential
        status: Operation status (success, failed)
        error: Error message if failed
        **kwargs: Additional fields
    """
    audit_event(
        event_type="credential_access",
        action=action,
        resource_type="credential",
        resource_name=credential_key,
        status=status,
        error=error,
        **kwargs,
    )


def audit_config_change(
    action: str,
    config_name: str,
    status: str,
    old_value: str | None = None,
    new_value: str | None = None,
    error: str | None = None,
    **kwargs: Any,
) -> None:
    """
    Log configuration changes.

    Convenience wrapper for config operations.

    Args:
        action: Action performed (update, create, delete)
        config_name: Name of config being changed
        status: Operation status (success, failed)
        old_value: Previous value (for updates)
        new_value: New value (for updates/creates)
        error: Error message if failed
        **kwargs: Additional fields
    """
    audit_event(
        event_type="config_change",
        action=action,
        resource_type="config",
        resource_name=config_name,
        status=status,
        old_value=old_value,
        new_value=new_value,
        error=error,
        **kwargs,
    )
