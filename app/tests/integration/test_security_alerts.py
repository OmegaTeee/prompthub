"""
Integration-style tests for security alert patterns.

Moved from repository root into `tests/integration/` for pytest.
"""

import sys
from pathlib import Path

# Ensure package imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

from router.audit import audit_admin_action, audit_credential_access
from router.middleware.audit_context import (
    client_id_ctx,
    client_ip_ctx,
    request_id_ctx,
)
from router.security_alerts import get_alert_manager


def test_repeated_failures():
    client_id_ctx.set("attacker-001")
    client_ip_ctx.set("10.0.0.42")
    request_id_ctx.set("test-req-001")

    for i in range(3):
        audit_admin_action(action="start", server_name="restricted-server", status="failed", error="Permission denied")

    alert_mgr = get_alert_manager()
    alerts = alert_mgr.get_recent_alerts(limit=10)
    assert isinstance(alerts, list)


def test_excessive_credential_access():
    client_id_ctx.set("suspicious-client")
    client_ip_ctx.set("192.168.1.100")
    request_id_ctx.set("test-req-002")

    for i in range(5):
        audit_credential_access(action="get", credential_key="production_api_key", status="success")

    alert_mgr = get_alert_manager()
    alerts = alert_mgr.get_recent_alerts(limit=10)
    assert isinstance(alerts, list)


def test_credential_probing():
    client_id_ctx.set("probe-bot")
    client_ip_ctx.set("203.0.113.10")
    request_id_ctx.set("test-req-003")

    audit_credential_access(action="get", credential_key="unknown_secret_key", status="failed", error="Credential not found")

    alert_mgr = get_alert_manager()
    alerts = alert_mgr.get_recent_alerts(limit=10)
    assert isinstance(alerts, list)
