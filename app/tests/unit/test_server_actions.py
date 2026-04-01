"""
Unit tests for _server_action() in router.main.

Tests the parameterized server action helper that consolidates
restart/start/stop into a single audited function.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── _server_action ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_server_action_calls_supervisor_method():
    """_server_action dispatches to the correct supervisor method."""
    mock_supervisor = MagicMock()
    mock_supervisor.restart_server = AsyncMock()

    with patch("router.main.supervisor", mock_supervisor), \
         patch("router.main.audit_admin_action"):
        from router.main import _server_action

        await _server_action("restart", "context7")

    mock_supervisor.restart_server.assert_awaited_once_with("context7")


@pytest.mark.asyncio
async def test_server_action_audits_initiated_and_success():
    """Successful action emits 'initiated' then 'success' audit events."""
    mock_supervisor = MagicMock()
    mock_supervisor.start_server = AsyncMock()

    with patch("router.main.supervisor", mock_supervisor), \
         patch("router.main.audit_admin_action") as mock_audit:
        from router.main import _server_action

        await _server_action("start", "memory")

    calls = mock_audit.call_args_list
    assert len(calls) == 2
    assert calls[0].kwargs["status"] == "initiated"
    assert calls[0].kwargs["action"] == "start"
    assert calls[0].kwargs["server_name"] == "memory"
    assert calls[1].kwargs["status"] == "success"


@pytest.mark.asyncio
async def test_server_action_audits_failure_on_error():
    """Failed action emits 'initiated' then 'failed' audit events and re-raises."""
    mock_supervisor = MagicMock()
    mock_supervisor.stop_server = AsyncMock(side_effect=RuntimeError("process not running"))

    with patch("router.main.supervisor", mock_supervisor), \
         patch("router.main.audit_admin_action") as mock_audit:
        from router.main import _server_action

        with pytest.raises(RuntimeError, match="process not running"):
            await _server_action("stop", "duckduckgo")

    calls = mock_audit.call_args_list
    assert len(calls) == 2
    assert calls[0].kwargs["status"] == "initiated"
    assert calls[1].kwargs["status"] == "failed"
    assert "process not running" in calls[1].kwargs["error"]


@pytest.mark.asyncio
async def test_server_action_raises_without_supervisor():
    """Raises ValueError when supervisor is not initialized."""
    with patch("router.main.supervisor", None):
        from router.main import _server_action

        with pytest.raises(ValueError, match="Supervisor not initialized"):
            await _server_action("restart", "context7")


# ── Thin wrappers ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_restart_server_delegates():
    """_restart_server delegates to _server_action('restart', ...)."""
    with patch("router.main._server_action", new_callable=AsyncMock) as mock:
        from router.main import _restart_server

        await _restart_server("context7")
        mock.assert_awaited_once_with("restart", "context7")


@pytest.mark.asyncio
async def test_start_server_delegates():
    with patch("router.main._server_action", new_callable=AsyncMock) as mock:
        from router.main import _start_server

        await _start_server("memory")
        mock.assert_awaited_once_with("start", "memory")


@pytest.mark.asyncio
async def test_stop_server_delegates():
    with patch("router.main._server_action", new_callable=AsyncMock) as mock:
        from router.main import _stop_server

        await _stop_server("duckduckgo")
        mock.assert_awaited_once_with("stop", "duckduckgo")
