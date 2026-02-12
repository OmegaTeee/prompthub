"""
AgentHub Dashboard.

HTMX-powered dashboard for monitoring router health, activity, and stats.
"""

from router.dashboard.router import create_dashboard_router

__all__ = [
    "create_dashboard_router",
]
