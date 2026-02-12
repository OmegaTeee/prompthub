#!/usr/bin/env python3
"""
Test script to trigger security alerts.

Simulates suspicious patterns to verify alert system.
"""

import sys
import time
from pathlib import Path

# Add router to path
sys.path.insert(0, str(Path(__file__).parent))

from router.middleware.audit_context import (
    request_id_ctx,
    client_id_ctx,
    client_ip_ctx,
)
from router.audit import audit_admin_action, audit_credential_access
from router.security_alerts import get_alert_manager


def test_repeated_failures():
    """Test Pattern 1: Repeated failed operations (should trigger after 3 failures)."""
    print("=" * 60)
    print("TEST 1: Repeated Failed Server Start Attempts")
    print("=" * 60)

    # Set audit context to simulate a client
    client_id_ctx.set("attacker-001")
    client_ip_ctx.set("10.0.0.42")
    request_id_ctx.set("test-req-001")

    # Simulate 3 failed attempts within 5 minutes
    for i in range(1, 4):
        print(f"\n[Attempt {i}] Simulating failed server start...")
        audit_admin_action(
            action="start",
            server_name="restricted-server",
            status="failed",
            error="Permission denied"
        )
        time.sleep(0.5)

    # Check alerts
    alert_mgr = get_alert_manager()
    alerts = alert_mgr.get_recent_alerts(limit=10)

    print(f"\n✓ Generated {len(alerts)} alert(s)")
    for alert in alerts:
        print(f"  - [{alert.severity}] {alert.alert_type}: {alert.description}")

    return len(alerts) > 0


def test_excessive_credential_access():
    """Test Pattern 2: Excessive credential access (should trigger after 5 accesses in 1 min)."""
    print("\n" + "=" * 60)
    print("TEST 2: Excessive Credential Access")
    print("=" * 60)

    # Set audit context
    client_id_ctx.set("suspicious-client")
    client_ip_ctx.set("192.168.1.100")
    request_id_ctx.set("test-req-002")

    # Simulate rapid credential access (5+ times in 1 minute)
    for i in range(1, 6):
        print(f"\n[Access {i}] Accessing API key...")
        audit_credential_access(
            action="get",
            credential_key="production_api_key",
            status="success"
        )
        time.sleep(0.2)

    # Check alerts
    alert_mgr = get_alert_manager()
    alerts = alert_mgr.get_recent_alerts(limit=10)

    print(f"\n✓ Total alerts: {len(alerts)}")
    for alert in alerts:
        if alert.alert_type == "excessive_credential_access":
            print(f"  - [{alert.severity}] {alert.alert_type}: {alert.description}")

    return any(a.alert_type == "excessive_credential_access" for a in alerts)


def test_credential_probing():
    """Test Pattern 3: Credential probing (unknown credential access)."""
    print("\n" + "=" * 60)
    print("TEST 3: Credential Probing")
    print("=" * 60)

    # Set audit context
    client_id_ctx.set("probe-bot")
    client_ip_ctx.set("203.0.113.10")
    request_id_ctx.set("test-req-003")

    # Try to access non-existent credential
    print("\n[Probe] Attempting to access unknown credential...")
    audit_credential_access(
        action="get",
        credential_key="unknown_secret_key",
        status="failed",
        error="Credential not found"
    )

    # Check alerts
    alert_mgr = get_alert_manager()
    alerts = alert_mgr.get_recent_alerts(limit=10)

    print(f"\n✓ Total alerts: {len(alerts)}")
    for alert in alerts:
        if alert.alert_type == "credential_probing":
            print(f"  - [{alert.severity}] {alert.alert_type}: {alert.description}")

    return any(a.alert_type == "credential_probing" for a in alerts)


def main():
    """Run all alert tests."""
    print("\n" + "=" * 60)
    print("SECURITY ALERT SYSTEM TEST SUITE")
    print("=" * 60)

    results = {
        "repeated_failures": test_repeated_failures(),
        "excessive_credential_access": test_excessive_credential_access(),
        "credential_probing": test_credential_probing(),
    }

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")

    # Print alert stats
    alert_mgr = get_alert_manager()
    stats = alert_mgr.get_alert_stats()

    print("\n" + "=" * 60)
    print("ALERT STATISTICS")
    print("=" * 60)
    print(f"Total Alerts: {stats['total_alerts']}")
    print(f"By Severity:")
    for severity, count in stats['by_severity'].items():
        print(f"  - {severity}: {count}")
    print(f"By Type:")
    for alert_type, count in stats['by_type'].items():
        print(f"  - {alert_type}: {count}")

    print("\n" + "=" * 60)

    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
