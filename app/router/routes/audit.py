"""Audit, activity log, integrity, and security alert endpoints."""

import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)


def create_audit_router(
    get_activity_log: Callable[[], Any],
) -> APIRouter:
    router = APIRouter(tags=["audit"])

    # --- Activity log endpoints ---

    @router.get("/audit/activity")
    async def query_activity(
        method: str | None = None,
        status_min: int | None = None,
        status_max: int | None = None,
        client_id: str | None = None,
        request_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        """Query activity log with filters."""
        log = get_activity_log()
        if not log:
            raise HTTPException(503, "Activity log not initialized")

        limit = min(limit, 1000)

        total = await log.count(
            method=method,
            status_min=status_min,
            status_max=status_max,
            client_id=client_id,
        )

        entries = await log.query(
            method=method,
            status_min=status_min,
            status_max=status_max,
            client_id=client_id,
            request_id=request_id,
            limit=limit,
            offset=offset,
        )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "entries": entries,
        }

    @router.get("/audit/activity/stats")
    async def activity_stats():
        """Get activity log statistics."""
        log = get_activity_log()
        if not log:
            raise HTTPException(503, "Activity log not initialized")

        import aiosqlite

        stats = {
            "total_entries": await log.count(),
            "by_method": {},
            "by_status": {},
        }

        async with aiosqlite.connect(str(log.db_path)) as db:
            cursor = await db.execute(
                "SELECT method, COUNT(*) as count FROM activity GROUP BY method ORDER BY count DESC"
            )
            rows = await cursor.fetchall()
            stats["by_method"] = {row[0]: row[1] for row in rows}

            cursor = await db.execute(
                "SELECT status, COUNT(*) as count FROM activity GROUP BY status ORDER BY status"
            )
            rows = await cursor.fetchall()
            stats["by_status"] = {row[0]: row[1] for row in rows}

        return stats

    @router.delete("/audit/activity")
    async def clear_activity_log():
        """Clear all activity log entries."""
        log = get_activity_log()
        if not log:
            raise HTTPException(503, "Activity log not initialized")

        await log.clear()

        from router.audit import audit_event
        audit_event(
            event_type="admin_action",
            action="clear",
            resource_type="activity_log",
            resource_name="persistent_activity",
            status="success",
        )

        return {"message": "Activity log cleared"}

    @router.post("/audit/activity/cleanup")
    async def cleanup_old_activity(days: int = 30):
        """Delete activity entries older than specified days."""
        log = get_activity_log()
        if not log:
            raise HTTPException(503, "Activity log not initialized")

        if days < 1:
            raise HTTPException(400, "Days must be >= 1")

        deleted = await log.cleanup_old_entries(days)

        from router.audit import audit_event
        audit_event(
            event_type="admin_action",
            action="cleanup",
            resource_type="activity_log",
            resource_name="persistent_activity",
            status="success",
            days=days,
            deleted_count=deleted,
        )

        return {"deleted": deleted}

    # --- Audit integrity endpoints ---

    @router.get("/audit/integrity/verify")
    async def verify_audit_integrity():
        """Verify audit log integrity using checksums."""
        from router.audit_integrity import get_integrity_manager

        integrity_mgr = get_integrity_manager()

        try:
            is_valid, error_msg = integrity_mgr.verify_integrity()

            history = integrity_mgr.get_checksum_history(limit=2)
            current_checksum = history[0].model_dump() if history else None
            previous_checksum = history[1].model_dump() if len(history) > 1 else None

            return {
                "valid": is_valid,
                "message": error_msg or "Integrity verified successfully",
                "current_checksum": current_checksum,
                "previous_checksum": previous_checksum,
            }
        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            raise HTTPException(500, f"Integrity verification error: {e}")

    @router.get("/audit/integrity/history")
    async def get_integrity_history(limit: int = 10):
        """Get checksum history for audit log."""
        from router.audit_integrity import get_integrity_manager

        integrity_mgr = get_integrity_manager()
        history = integrity_mgr.get_checksum_history(limit=limit)

        return {
            "total": len(history),
            "checksums": [c.model_dump() for c in history],
        }

    # --- Security alert endpoints ---

    @router.get("/security/alerts")
    async def get_security_alerts(
        limit: int = 50,
        severity: str | None = None,
    ):
        """Get recent security alerts."""
        from router.security_alerts import AlertSeverity, get_alert_manager

        alert_mgr = get_alert_manager()

        severity_filter = None
        if severity:
            try:
                severity_filter = AlertSeverity(severity.lower())
            except ValueError:
                raise HTTPException(400, f"Invalid severity: {severity}")

        alerts = alert_mgr.get_recent_alerts(limit=limit, severity=severity_filter)

        return {
            "total": len(alerts),
            "alerts": [a.model_dump() for a in alerts],
        }

    @router.get("/security/alerts/stats")
    async def get_alert_stats():
        """Get security alert statistics."""
        from router.security_alerts import get_alert_manager

        alert_mgr = get_alert_manager()
        return alert_mgr.get_alert_stats()

    return router
