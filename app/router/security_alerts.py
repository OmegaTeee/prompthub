"""
Security Alert System for PromptHub.

Detects suspicious patterns in audit logs and generates alerts.
Integrates with audit logging to provide real-time security monitoring.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AlertSeverity(StrEnum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class SecurityAlert(BaseModel):
    """A security alert event."""

    id: str
    timestamp: str
    severity: AlertSeverity
    alert_type: str
    description: str
    details: dict[str, Any]
    client_id: str | None = None
    client_ip: str | None = None


class SecurityAlertManager:
    """
    Manages security alerts and anomaly detection.

    Detects patterns such as:
    - Repeated failed operations (credential access, server actions)
    - Unusual credential access patterns
    - Rapid-fire requests from same client
    - Privilege escalation attempts
    - Configuration changes
    """

    def __init__(self):
        """Initialize alert manager."""
        self.alerts: list[SecurityAlert] = []
        self.max_alerts = 1000  # Keep last 1000 alerts

        # Tracking for anomaly detection
        self._failed_attempts: defaultdict[str, list[datetime]] = defaultdict(list)
        self._credential_access: defaultdict[str, list[datetime]] = defaultdict(list)
        self._config_changes: list[datetime] = []

    def check_event(
        self,
        event_type: str,
        action: str,
        status: str,
        resource_name: str,
        client_id: str | None = None,
        client_ip: str | None = None,
        error: str | None = None,
    ) -> SecurityAlert | None:
        """
        Check an audit event for suspicious patterns.

        Args:
            event_type: Type of event (admin_action, credential_access, etc.)
            action: Action performed
            status: Operation status (initiated, success, failed)
            resource_name: Resource being accessed
            client_id: Client identifier
            client_ip: Client IP address
            error: Error message if failed

        Returns:
            SecurityAlert if suspicious pattern detected, None otherwise
        """
        now = datetime.now()
        alert = None

        # Check for failed operations
        if status == "failed":
            alert = self._check_failed_operation(
                event_type, action, resource_name, client_id, client_ip, error, now
            )

        # Check for credential access patterns
        if event_type == "credential_access":
            cred_alert = self._check_credential_access(
                action, resource_name, status, client_id, client_ip, now
            )
            if cred_alert and not alert:  # Don't override existing alert
                alert = cred_alert

        # Check for config changes
        if event_type == "config_change":
            config_alert = self._check_config_change(
                action, resource_name, client_id, client_ip, now
            )
            if config_alert and not alert:
                alert = config_alert

        # Save alert if generated
        if alert:
            self.alerts.append(alert)
            # Keep only recent alerts
            self.alerts = self.alerts[-self.max_alerts :]
            logger.warning(f"Security alert: {alert.alert_type} - {alert.description}")

        return alert

    def _check_failed_operation(
        self,
        event_type: str,
        action: str,
        resource_name: str,
        client_id: str | None,
        client_ip: str | None,
        error: str | None,
        now: datetime,
    ) -> SecurityAlert | None:
        """Check for repeated failed operations."""
        if not client_id:
            return None

        # Track failed attempts
        key = f"{client_id}:{event_type}:{action}"
        self._failed_attempts[key].append(now)

        # Clean old attempts (>5 minutes)
        cutoff = now - timedelta(minutes=5)
        self._failed_attempts[key] = [
            t for t in self._failed_attempts[key] if t > cutoff
        ]

        # Alert on 3+ failures in 5 minutes
        if len(self._failed_attempts[key]) >= 3:
            return SecurityAlert(
                id=f"failed-{now.timestamp()}",
                timestamp=now.isoformat(),
                severity=AlertSeverity.WARNING,
                alert_type="repeated_failures",
                description=f"Multiple failed {action} attempts on {resource_name}",
                details={
                    "event_type": event_type,
                    "action": action,
                    "resource": resource_name,
                    "failure_count": len(self._failed_attempts[key]),
                    "time_window": "5 minutes",
                    "error": error,
                },
                client_id=client_id,
                client_ip=client_ip,
            )

        return None

    def _check_credential_access(
        self,
        action: str,
        credential_key: str,
        status: str,
        client_id: str | None,
        client_ip: str | None,
        now: datetime,
    ) -> SecurityAlert | None:
        """Check for unusual credential access patterns."""
        if not client_id:
            return None

        key = f"{client_id}:{credential_key}"
        self._credential_access[key].append(now)

        # Clean old accesses (>1 minute)
        cutoff = now - timedelta(minutes=1)
        self._credential_access[key] = [
            t for t in self._credential_access[key] if t > cutoff
        ]

        # Alert on rapid credential access (5+ times in 1 minute)
        if len(self._credential_access[key]) >= 5:
            return SecurityAlert(
                id=f"cred-{now.timestamp()}",
                timestamp=now.isoformat(),
                severity=AlertSeverity.WARNING,
                alert_type="excessive_credential_access",
                description=f"Rapid credential access: {credential_key}",
                details={
                    "credential": credential_key,
                    "access_count": len(self._credential_access[key]),
                    "time_window": "1 minute",
                    "status": status,
                },
                client_id=client_id,
                client_ip=client_ip,
            )

        # Alert on failed credential access
        if status == "failed" and action == "get":
            # Check if this is a new credential being probed
            if credential_key not in [
                k.split(":")[1] for k in self._credential_access.keys()
            ]:
                return SecurityAlert(
                    id=f"cred-probe-{now.timestamp()}",
                    timestamp=now.isoformat(),
                    severity=AlertSeverity.WARNING,
                    alert_type="credential_probing",
                    description=f"Attempted access to unknown credential: {credential_key}",
                    details={
                        "credential": credential_key,
                        "action": action,
                        "status": status,
                    },
                    client_id=client_id,
                    client_ip=client_ip,
                )

        return None

    def _check_config_change(
        self,
        action: str,
        config_name: str,
        client_id: str | None,
        client_ip: str | None,
        now: datetime,
    ) -> SecurityAlert | None:
        """Check for config changes (always alert - high importance)."""
        self._config_changes.append(now)

        # Clean old changes (>1 hour)
        cutoff = now - timedelta(hours=1)
        self._config_changes = [t for t in self._config_changes if t > cutoff]

        # Always create INFO alert for config changes
        severity = AlertSeverity.INFO

        # Escalate to WARNING if multiple changes in short time
        if len(self._config_changes) >= 3:
            severity = AlertSeverity.WARNING

        return SecurityAlert(
            id=f"config-{now.timestamp()}",
            timestamp=now.isoformat(),
            severity=severity,
            alert_type="configuration_change",
            description=f"Configuration changed: {config_name}",
            details={
                "config": config_name,
                "action": action,
                "recent_changes": len(self._config_changes),
            },
            client_id=client_id,
            client_ip=client_ip,
        )

    def get_recent_alerts(
        self, limit: int = 50, severity: AlertSeverity | None = None
    ) -> list[SecurityAlert]:
        """
        Get recent security alerts.

        Args:
            limit: Maximum alerts to return
            severity: Filter by severity (optional)

        Returns:
            List of recent alerts (newest first)
        """
        alerts = self.alerts

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return list(reversed(alerts[-limit:]))

    def get_alert_stats(self) -> dict[str, Any]:
        """Get alert statistics."""
        total = len(self.alerts)
        by_severity = {
            "info": 0,
            "warning": 0,
            "critical": 0,
        }
        by_type = defaultdict(int)

        for alert in self.alerts:
            by_severity[alert.severity] += 1
            by_type[alert.alert_type] += 1

        return {
            "total_alerts": total,
            "by_severity": by_severity,
            "by_type": dict(by_type),
        }


# Global alert manager
alert_manager: SecurityAlertManager | None = None


def get_alert_manager() -> SecurityAlertManager:
    """Get or create global alert manager."""
    global alert_manager
    if alert_manager is None:
        alert_manager = SecurityAlertManager()
    return alert_manager
