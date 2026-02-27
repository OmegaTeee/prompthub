"""
Memory and context management for PromptHub sessions.

Provides:
- SQLite-backed session storage
- Fact and memory block management
- Optional Memory MCP sync layer
- REST API endpoints (/sessions/*)
"""

from .mcp_client import MemoryMCPClient
from .models import (
    FactCreate,
    FactResponse,
    MemoryBlockResponse,
    MemoryBlockUpsert,
    SessionContextResponse,
    SessionCreate,
    SessionListResponse,
    SessionResponse,
)
from .router import create_memory_router
from .storage import SessionStorage, get_session_storage

__all__ = [
    "SessionStorage",
    "get_session_storage",
    "MemoryMCPClient",
    "create_memory_router",
    "SessionCreate",
    "SessionResponse",
    "SessionListResponse",
    "SessionContextResponse",
    "FactCreate",
    "FactResponse",
    "MemoryBlockUpsert",
    "MemoryBlockResponse",
]
