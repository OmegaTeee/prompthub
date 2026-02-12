# Async Audit Code Review - Action Items

## Executive Summary

AgentHub's current audit implementation has **critical security and compliance gaps**. While basic logging exists for dashboard actions, the system lacks structured logging, audit context, proper persistence, and comprehensive coverage of security-sensitive operations.

**Security Score:** 4/10
**Compliance Readiness:** 2/10
**Operational Maturity:** 5/10

---

## Current Architecture

### Logging Components

1. **Python logging** (`router/main.py:44-48`)
   - Basic stdout/stderr logging
   - Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
   - No structured output

2. **Activity Log** (`router/middleware/activity.py`)
   - In-memory deque (max 100 entries)
   - Tracks HTTP requests only
   - Lost on restart

3. **Dashboard Action Logging** (`router/main.py:175-195`)
   - Manual `logger.info()` calls
   - Before/after each action
   - No context enrichment

4. **Keyring Logging** (`router/servers/process.py:86-94`)
   - Logs credential resolution count
   - Missing failed attempts

---

## Critical Issues

### 🔴 Issue 1: No Structured Audit Logging

**Location:** `router/main.py:175-195`

**Current Code:**
```python
async def _start_server(name: str):
    if not supervisor:
        raise ValueError("Supervisor not initialized")
    logger.info(f"Dashboard action: Starting server '{name}'")
    await supervisor.start_server(name)
    logger.info(f"Dashboard action: Server '{name}' started successfully")
```

**Problems:**
- String interpolation makes parsing difficult
- No standardized fields
- Cannot query by action type, server name, status
- Fails SOC 2, ISO 27001 audit requirements

**Impact:**
- Security incidents hard to detect
- Compliance failures
- No automated alerting possible

**Recommended Solution:**
```python
import structlog

# Structured audit logger
audit_logger = structlog.get_logger("audit")

async def _start_server(name: str):
    if not supervisor:
        raise ValueError("Supervisor not initialized")

    audit_logger.info(
        "server_lifecycle_event",
        action="start",
        server_name=name,
        status="initiated",
        event_type="admin_action",
        resource_type="mcp_server"
    )

    try:
        await supervisor.start_server(name)

        audit_logger.info(
            "server_lifecycle_event",
            action="start",
            server_name=name,
            status="success",
            event_type="admin_action",
            resource_type="mcp_server"
        )
    except Exception as e:
        audit_logger.error(
            "server_lifecycle_event",
            action="start",
            server_name=name,
            status="failed",
            error=str(e),
            event_type="admin_action",
            resource_type="mcp_server"
        )
        raise
```

**Benefits:**
- Queryable JSON logs
- Automated alerting on patterns
- Compliance-ready
- Integration with SIEM tools

---

### 🔴 Issue 2: Missing Audit Context

**Location:** All audit logging calls

**Current Problems:**
- No user/client identification
- No source IP tracking
- No request correlation IDs
- No session tracking

**Example Current Log:**
```
2026-01-28 18:52:05 - router.main - INFO - Dashboard action: Starting server 'obsidian'
```

**Cannot Answer:**
- WHO started the server?
- FROM WHERE (IP address)?
- WHICH SESSION/request?
- PART OF what larger operation?

**Recommended Solution:**

Create audit context middleware:

```python
# router/middleware/audit_context.py
import contextvars
from typing import Optional
from uuid import uuid4

# Context variables for async propagation
request_id_ctx = contextvars.ContextVar("request_id", default=None)
client_id_ctx = contextvars.ContextVar("client_id", default=None)
client_ip_ctx = contextvars.ContextVar("client_ip", default=None)

class AuditContextMiddleware(BaseHTTPMiddleware):
    """Captures and propagates audit context through async calls."""

    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID
        request_id = str(uuid4())
        request_id_ctx.set(request_id)

        # Extract client info
        client_ip = request.client.host if request.client else "unknown"
        client_ip_ctx.set(client_ip)

        # Get client ID from header or auth
        client_id = request.headers.get("X-Client-ID", "anonymous")
        client_id_ctx.set(client_id)

        # Add correlation ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response

def get_audit_context() -> dict:
    """Get current audit context for logging."""
    return {
        "request_id": request_id_ctx.get(),
        "client_id": client_id_ctx.get(),
        "client_ip": client_ip_ctx.get(),
    }
```

**Updated Audit Logging:**
```python
async def _start_server(name: str):
    context = get_audit_context()

    audit_logger.info(
        "server_lifecycle_event",
        action="start",
        server_name=name,
        status="initiated",
        **context  # Includes request_id, client_id, client_ip
    )
```

**Result:**
```json
{
  "timestamp": "2026-01-28T18:52:05.123Z",
  "level": "info",
  "event": "server_lifecycle_event",
  "action": "start",
  "server_name": "obsidian",
  "status": "initiated",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "client_id": "dashboard_user_1",
  "client_ip": "127.0.0.1"
}
```

---

### 🔴 Issue 3: Incomplete Keyring Audit Trail

**Location:** `router/keyring_manager.py`

**Current Coverage:**
- ✅ Successful credential retrieval (line 49)
- ❌ Failed credential access attempts
- ❌ Credential creation/modification
- ❌ Credential deletion
- ❌ Authorization failures

**Security Risk:**
- Attacker probing for credentials goes undetected
- Unauthorized credential changes not logged
- Compliance violation (GDPR, SOC 2 require access logs)

**Recommended Changes:**

```python
# router/keyring_manager.py

def get_credential(self, key: str) -> Optional[str]:
    """Retrieve a credential from the keyring."""
    context = get_audit_context()

    if not self.enabled:
        audit_logger.error(
            "credential_access_denied",
            reason="keyring_unavailable",
            credential_key=key,
            **context
        )
        return None

    try:
        value = keyring.get_password(self.service_name, key)

        if value:
            audit_logger.info(
                "credential_accessed",
                credential_key=key,
                status="success",
                **context
            )
        else:
            audit_logger.warning(
                "credential_not_found",
                credential_key=key,
                service=self.service_name,
                **context
            )

        return value

    except Exception as e:
        audit_logger.error(
            "credential_access_error",
            credential_key=key,
            error=str(e),
            **context
        )
        return None

def set_credential(self, key: str, value: str) -> bool:
    """Store a credential in the keyring."""
    context = get_audit_context()

    audit_logger.warning(
        "credential_modified",
        credential_key=key,
        action="set",
        **context
    )

    # ... implementation

def delete_credential(self, key: str) -> bool:
    """Delete a credential from the keyring."""
    context = get_audit_context()

    audit_logger.warning(
        "credential_deleted",
        credential_key=key,
        **context
    )

    # ... implementation
```

---

### 🟡 Issue 4: No Dedicated Audit Log File

**Location:** `router/main.py:44-48`

**Current:**
- All logs (audit, debug, application) go to stderr
- No separation of concerns
- Cannot apply different retention policies
- Audit logs mixed with noise

**Compliance Problem:**
- SOC 2 requires **tamper-evident** audit logs
- HIPAA requires **separate** audit trail storage
- PCI DSS requires **immutable** audit logs

**Recommended Solution:**

```python
# router/config/logging.py
import logging
import logging.handlers
from pathlib import Path

def setup_logging(log_dir: Path = Path("/var/log/agenthub")):
    """
    Configure dual logging:
    1. Application logs -> /var/log/agenthub/app.log
    2. Audit logs -> /var/log/agenthub/audit.log
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    # Application logger
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=100_000_000,  # 100MB
        backupCount=10,
    )
    app_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )

    # Audit logger (JSON format, longer retention)
    audit_handler = logging.handlers.RotatingFileHandler(
        log_dir / "audit.log",
        maxBytes=100_000_000,  # 100MB
        backupCount=90,  # Keep 90 days
    )

    # Configure structlog for audit
    import structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Setup loggers
    audit_logger = logging.getLogger("audit")
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)

    app_logger = logging.getLogger()
    app_logger.addHandler(app_handler)
    app_logger.setLevel(logging.INFO)
```

**Audit Log Output (`/var/log/agenthub/audit.log`):**
```json
{"timestamp": "2026-01-28T18:52:05.123Z", "level": "info", "event": "server_lifecycle_event", "action": "start", "server_name": "obsidian", "status": "success", "request_id": "...", "client_id": "dashboard", "client_ip": "127.0.0.1"}
{"timestamp": "2026-01-28T18:52:10.456Z", "level": "warning", "event": "credential_accessed", "credential_key": "obsidian_api_key", "status": "success", "request_id": "...", "client_id": "dashboard", "client_ip": "127.0.0.1"}
```

**Benefits:**
- Separate retention policies (audit: 90 days, app: 10 days)
- Tamper detection (file checksums)
- Automated compliance reports
- Integration with SIEM (Splunk, ELK, Datadog)

---

### 🟡 Issue 5: Activity Log Lost on Restart

**Location:** `router/middleware/activity.py:96`

**Current:**
```python
activity_log = ActivityLog(max_entries=100)  # In-memory deque
```

**Problems:**
- Lost on router restart
- Only keeps last 100 entries
- Cannot reconstruct historical activity
- No forensics capability

**Recommended Solution:**

Option 1: **SQLite Persistence**
```python
# router/middleware/activity.py
import sqlite3
from contextlib import asynccontextmanager

class PersistentActivityLog:
    """Activity log with SQLite persistence."""

    def __init__(self, db_path: Path = Path("/var/lib/agenthub/activity.db")):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite schema."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                status INTEGER NOT NULL,
                duration REAL NOT NULL,
                client_id TEXT,
                client_ip TEXT,
                request_id TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON activity(timestamp)")
        conn.commit()
        conn.close()

    async def add(self, method: str, path: str, status: int, duration: float):
        """Add activity entry (async)."""
        context = get_audit_context()

        # Use asyncio thread pool for DB I/O
        await asyncio.to_thread(
            self._insert,
            method, path, status, duration,
            context.get("client_id"),
            context.get("client_ip"),
            context.get("request_id")
        )

    def _insert(self, method, path, status, duration, client_id, client_ip, request_id):
        """Synchronous insert."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO activity (timestamp, method, path, status, duration, client_id, client_ip, request_id) "
            "VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?)",
            (method, path, status, duration, client_id, client_ip, request_id)
        )
        conn.commit()
        conn.close()

    async def get_recent(self, limit: int = 50) -> list[dict]:
        """Get recent entries."""
        return await asyncio.to_thread(self._query, limit)

    def _query(self, limit: int):
        """Synchronous query."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM activity ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        results = [dict(row) for row in cursor]
        conn.close()
        return results
```

Option 2: **Redis for High Performance**
```python
import aioredis
import json

class RedisActivityLog:
    """Activity log backed by Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = None
        self.redis_url = redis_url

    async def initialize(self):
        """Connect to Redis."""
        self.redis = await aioredis.from_url(self.redis_url)

    async def add(self, method: str, path: str, status: int, duration: float):
        """Add activity entry."""
        context = get_audit_context()

        entry = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "path": path,
            "status": status,
            "duration": duration,
            **context
        }

        # Store in Redis list (LPUSH + LTRIM for bounded size)
        await self.redis.lpush("activity_log", json.dumps(entry))
        await self.redis.ltrim("activity_log", 0, 999)  # Keep last 1000

    async def get_recent(self, limit: int = 50) -> list[dict]:
        """Get recent entries."""
        entries = await self.redis.lrange("activity_log", 0, limit - 1)
        return [json.loads(e) for e in entries]
```

---

### 🟢 Issue 6: No Async Context Propagation

**Location:** All async functions

**Problem:**
When multiple async operations run concurrently, logs are interleaved without correlation.

**Example Problem:**
```python
# Two concurrent operations
await asyncio.gather(
    _start_server("server1"),
    _start_server("server2")
)

# Log output is mixed:
# 2026-01-28 18:52:05 - Starting server 'server1'
# 2026-01-28 18:52:05 - Starting server 'server2'
# 2026-01-28 18:52:06 - Server started successfully  # Which one?
# 2026-01-28 18:52:07 - Server started successfully  # Which one?
```

**Solution: Python contextvars**

Already shown in Issue 2 - using `contextvars` for request ID propagation.

**Example:**
```python
# Each request gets unique ID
# server1 operations all tagged with request_id=abc123
# server2 operations all tagged with request_id=def456

# Logs now clearly separated:
# {"request_id": "abc123", "msg": "Starting server 'server1'"}
# {"request_id": "def456", "msg": "Starting server 'server2'"}
# {"request_id": "abc123", "msg": "Server 'server1' started"}
# {"request_id": "def456", "msg": "Server 'server2' started"}
```

---

### 🟢 Issue 7: No Log Rotation

**Solution:** Already covered in Issue 4 with `RotatingFileHandler`.

---

## Implementation Action Items

### Phase 1: Critical Security Fixes (Week 1)

**Priority: CRITICAL**

- [ ] **A1.1** Install structlog
  ```bash
  pip install structlog
  ```

- [ ] **A1.2** Create audit context middleware
  - File: `router/middleware/audit_context.py`
  - Implement `AuditContextMiddleware`
  - Implement `get_audit_context()`
  - Add to FastAPI app

- [ ] **A1.3** Setup structured audit logger
  - File: `router/config/logging.py`
  - Configure structlog with JSON output
  - Setup `/var/log/agenthub/audit.log`
  - 90-day retention, 100MB rotation

- [ ] **A1.4** Update dashboard action logging
  - File: `router/main.py`
  - Replace string logs with structured audit logs
  - Add try/except for failure logging
  - Include audit context

- [ ] **A1.5** Enhance keyring audit trail
  - File: `router/keyring_manager.py`
  - Log all access attempts (success/failure)
  - Log credential modifications
  - Log deletions

**Testing:**
```bash
# Verify structured logs
tail -f /var/log/agenthub/audit.log | jq .

# Verify context propagation
curl -H "X-Client-ID: test-user" http://localhost:9090/dashboard/actions/start/memory
# Check log contains client_id: test-user
```

---

### Phase 2: Operational Improvements (Week 2)

**Priority: HIGH**

- [ ] **A2.1** Implement persistent activity log
  - Choose: SQLite or Redis
  - File: `router/middleware/activity.py`
  - Add async persistence
  - Migrate existing in-memory log

- [ ] **A2.2** Add log rotation monitoring
  - Create `/var/log/agenthub/` directory
  - Setup logrotate config
  - Add disk space monitoring

- [ ] **A2.3** Create audit query API
  - Endpoint: `GET /audit/events?start=<timestamp>&end=<timestamp>&action=<type>`
  - Support filtering by action, server, client
  - Pagination support

**Testing:**
```bash
# Query audit logs
curl "http://localhost:9090/audit/events?action=server_lifecycle_event&server_name=obsidian&limit=10"
```

---

### Phase 3: Compliance & Monitoring (Week 3)

**Priority: MEDIUM**

- [ ] **A3.1** Implement audit log integrity
  - File checksums for tamper detection
  - Periodic verification
  - Alert on modifications

- [ ] **A3.2** Create audit dashboard
  - Real-time audit event stream
  - Security event alerts
  - Anomaly detection (e.g., unusual credential access patterns)

- [ ] **A3.3** Setup SIEM integration
  - Forward audit logs to SIEM
  - Configure alerting rules
  - Document incident response procedures

- [ ] **A3.4** Add audit retention policy
  - Automated cleanup of old logs
  - Archive to cold storage
  - Compliance documentation

---

## Compliance Checklist

### SOC 2 Requirements

- [ ] Audit logs capture WHO, WHAT, WHEN, WHERE
- [ ] Audit logs are tamper-evident (checksums)
- [ ] Audit logs have separate storage from app logs
- [ ] Audit log access is restricted
- [ ] Audit logs retained for minimum 1 year
- [ ] Failed authentication attempts logged
- [ ] Privilege changes logged

### GDPR Requirements

- [ ] Access to personal data logged
- [ ] Data exports logged
- [ ] Data deletions logged
- [ ] Consent changes logged
- [ ] Logs retained for 3 years minimum

### HIPAA Requirements

- [ ] PHI access logged
- [ ] Audit logs encrypted at rest
- [ ] Audit logs encrypted in transit
- [ ] Audit trail immutable
- [ ] Access to audit logs restricted

---

## Code Examples

### Complete Audit Logger Implementation

```python
# router/audit/__init__.py
"""
AgentHub Audit System.

Provides structured audit logging for compliance and security.
"""
import contextvars
import structlog
from typing import Optional
from pathlib import Path

# Context variables
request_id_ctx = contextvars.ContextVar("request_id", default=None)
client_id_ctx = contextvars.ContextVar("client_id", default=None)
client_ip_ctx = contextvars.ContextVar("client_ip", default=None)

# Audit logger
audit_logger = structlog.get_logger("audit")

def get_audit_context() -> dict:
    """Get current audit context."""
    return {
        "request_id": request_id_ctx.get(),
        "client_id": client_id_ctx.get(),
        "client_ip": client_ip_ctx.get(),
    }

def audit_event(
    event_type: str,
    action: str,
    resource_type: str,
    resource_name: str,
    status: str,
    error: Optional[str] = None,
    **kwargs
):
    """
    Log an audit event.

    Args:
        event_type: Type of event (admin_action, credential_access, etc.)
        action: Action performed (start, stop, get, set, delete)
        resource_type: Type of resource (mcp_server, credential, config)
        resource_name: Name of resource
        status: Status (initiated, success, failed)
        error: Error message if failed
        **kwargs: Additional context
    """
    context = get_audit_context()

    log_method = audit_logger.info
    if status == "failed":
        log_method = audit_logger.error
    elif event_type == "credential_access":
        log_method = audit_logger.warning

    log_method(
        event_type,
        action=action,
        resource_type=resource_type,
        resource_name=resource_name,
        status=status,
        error=error,
        **context,
        **kwargs
    )
```

### Usage in Dashboard Actions

```python
# router/main.py
from router.audit import audit_event

async def _start_server(name: str):
    """Start a server for dashboard."""
    if not supervisor:
        raise ValueError("Supervisor not initialized")

    audit_event(
        event_type="admin_action",
        action="start",
        resource_type="mcp_server",
        resource_name=name,
        status="initiated"
    )

    try:
        await supervisor.start_server(name)

        audit_event(
            event_type="admin_action",
            action="start",
            resource_type="mcp_server",
            resource_name=name,
            status="success"
        )

    except Exception as e:
        audit_event(
            event_type="admin_action",
            action="start",
            resource_type="mcp_server",
            resource_name=name,
            status="failed",
            error=str(e)
        )
        raise
```

---

## Metrics

### Before Implementation

| Metric | Score |
|--------|-------|
| Security | 4/10 |
| Compliance | 2/10 |
| Observability | 5/10 |
| Forensics Capability | 2/10 |
| Incident Response Readiness | 3/10 |
| **Overall** | **3.2/10** |

### After Phase 1

| Metric | Expected Score |
|--------|----------------|
| Security | 7/10 |
| Compliance | 6/10 |
| Observability | 8/10 |
| Forensics Capability | 7/10 |
| Incident Response Readiness | 7/10 |
| **Overall** | **7.0/10** |

### After All Phases

| Metric | Expected Score |
|--------|----------------|
| Security | 9/10 |
| Compliance | 9/10 |
| Observability | 9/10 |
| Forensics Capability | 9/10 |
| Incident Response Readiness | 9/10 |
| **Overall** | **9.0/10** |

---

## Async Best Practices Review

### ✅ What's Done Right

1. **Proper async/await usage**
   - All I/O operations properly awaited
   - No blocking calls in async functions

2. **AsyncIO subprocess management**
   - Uses `asyncio.create_subprocess_exec`
   - Proper stdin/stdout pipe handling

3. **Async context manager**
   - FastAPI lifespan properly implemented
   - Cleanup on shutdown

4. **Concurrent operations**
   - `asyncio.gather` used for parallel starts
   - Task cancellation handled

### ⚠️ Async Anti-Patterns to Avoid

1. **Don't use sync file I/O in async functions**
   ```python
   # ❌ Bad
   async def log_audit():
       with open("audit.log", "a") as f:  # Blocks event loop!
           f.write("...")

   # ✅ Good
   async def log_audit():
       await asyncio.to_thread(write_log, "...")
   ```

2. **Don't forget to propagate context**
   ```python
   # ❌ Bad - context lost
   async def parent():
       request_id_ctx.set("123")
       asyncio.create_task(child())  # Child won't see request_id!

   # ✅ Good - context preserved
   async def parent():
       request_id_ctx.set("123")
       await child()  # Context inherited
   ```

3. **Use structured concurrency**
   ```python
   # ✅ Good - tasks cleaned up properly
   async with asyncio.TaskGroup() as tg:
       tg.create_task(operation1())
       tg.create_task(operation2())
   # If either fails, all are cancelled
   ```

---

## Next Steps

1. **Review and approve** this action plan
2. **Prioritize** phases based on compliance deadlines
3. **Assign** developers to action items
4. **Set up** test environment for validation
5. **Schedule** code review after Phase 1

**Estimated Effort:**
- Phase 1: 3-4 days (1 developer)
- Phase 2: 2-3 days (1 developer)
- Phase 3: 3-5 days (1 developer)
- **Total: 8-12 days**

**Risk Level:** Low (additive changes, no breaking modifications)
