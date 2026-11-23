"""Unit tests for SecurityAlertManager credential-access patterns."""

from router.security_alerts import SecurityAlertManager


def _cred(mgr, key, status, client="client-a", action="get"):
    return mgr.check_event(
        event_type="credential_access",
        action=action,
        status=status,
        resource_name=key,
        client_id=client,
        client_ip="10.0.0.1",
    )


def test_failed_get_of_never_seen_credential_is_probing():
    mgr = SecurityAlertManager()
    alert = _cred(mgr, "unknown_secret_key", "failed")
    assert alert is not None
    assert alert.alert_type == "credential_probing"
    assert alert.client_id == "client-a"
    assert alert.details["credential"] == "unknown_secret_key"


def test_failed_get_of_known_credential_is_not_probing():
    mgr = SecurityAlertManager()
    assert _cred(mgr, "openrouter_api_key", "success") is None
    assert _cred(mgr, "openrouter_api_key", "failed") is None


def test_credential_known_from_another_client_is_not_probing():
    mgr = SecurityAlertManager()
    _cred(mgr, "openrouter_api_key", "success", client="client-a")
    assert _cred(mgr, "openrouter_api_key", "failed", client="client-b") is None


def test_failed_attempt_does_not_make_credential_known():
    mgr = SecurityAlertManager()
    first = _cred(mgr, "guess_1", "failed")
    second = _cred(mgr, "guess_1", "failed")
    assert first is not None and first.alert_type == "credential_probing"
    assert second is not None and second.alert_type == "credential_probing"


def test_failed_non_get_action_is_not_probing():
    mgr = SecurityAlertManager()
    assert _cred(mgr, "new_key", "failed", action="set") is None


def test_keys_containing_colons_are_handled():
    mgr = SecurityAlertManager()
    _cred(mgr, "ns:openrouter_api_key", "success", client="host:1")
    assert _cred(mgr, "ns:openrouter_api_key", "failed", client="host:1") is None
    probe = _cred(mgr, "ns:other", "failed", client="host:1")
    assert probe is not None and probe.alert_type == "credential_probing"


def test_rapid_access_still_alerts():
    mgr = SecurityAlertManager()
    alerts = [_cred(mgr, "prod_key", "success") for _ in range(5)]
    assert alerts[:4] == [None] * 4
    assert alerts[4] is not None
    assert alerts[4].alert_type == "excessive_credential_access"
