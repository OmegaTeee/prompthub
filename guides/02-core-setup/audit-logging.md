# Audit Logging and Security Monitoring

> **What you'll learn:** How AgentHub tracks activity, detects anomalies, and maintains security audit trails

---

## Overview

### What This Guide Covers
- Structured audit logging with JSON format
- Activity log persistence (SQLite)
- Security alert system
- Log file locations and rotation
- Querying activity history
- Compliance considerations

### Prerequisites
- ✅ AgentHub running
- ✅ Basic understanding of audit concepts
- ✅ Familiarity with dashboard at `http://localhost:9090/dashboard`

### Estimated Time
- Reading: 15 minutes
- Configuration: 5 minutes

---

## What is Audit Logging?

### Purpose

AgentHub tracks **every significant action** to provide:
1. **Security** - Detect unauthorized access or suspicious behavior
2. **Debugging** - Understand what happened when things go wrong
3. **Compliance** - Meet regulatory requirements (HIPAA, SOC 2, GDPR)
4. **Analytics** - Understand usage patterns

---

### What Gets Logged?

**Tracked events:**
- ✅ HTTP requests (method, path, client, status, duration)
- ✅ MCP server starts/stops/restarts
- ✅ Credential access from Keychain
- ✅ Dashboard configuration changes
- ✅ Circuit breaker state transitions
- ✅ Enhancement requests and failures
- ✅ Security alerts

**Not logged:**
- ❌ Prompt content (privacy)
- ❌ Response data (privacy)
- ❌ API keys or credentials (security)

---

## Audit Log Structure

### JSON Format

All logs are structured JSON via `structlog`:

```json
{
  "timestamp": "2026-02-06T10:30:45.123456Z",
  "level": "info",
  "event": "http_request",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "claude-desktop",
  "client_ip": "127.0.0.1",
  "method": "POST",
  "path": "/mcp/context7/query",
  "status_code": 200,
  "duration_ms": 234.5
}
```

---

### Key Fields

| Field | Description | Example |
|-------|-------------|---------|
| `timestamp` | ISO 8601 timestamp | `"2026-02-06T10:30:45Z"` |
| `level` | Log level | `"info"`, `"warning"`, `"error"` |
| `event` | Event type | `"http_request"`, `"credential_access"` |
| `request_id` | UUID for correlation | `"550e8400..."` |
| `client_id` | From X-Client-ID header | `"claude-desktop"` |
| `client_ip` | Remote IP (respects X-Forwarded-For) | `"127.0.0.1"` |
| `session_id` | From X-Session-ID header | `"abc123"` |

---

## Log Files

### Locations

| Log Type | Path | Purpose |
|----------|------|---------|
| **Router logs** | `~/Library/Logs/agenthub-router.log` | Main application logs |
| **Error logs** | `~/Library/Logs/agenthub-router-error.log` | Error-only logs |
| **Activity DB** | `~/.local/share/agenthub/activity.db` | Persistent SQLite store |
| **Audit trail** | `/var/log/agenthub/audit.log` | Compliance-focused audit trail |

---

### Viewing Logs

**Tail live logs:**
```bash
tail -f ~/Library/Logs/agenthub-router.log
```

**Filter for errors:**
```bash
grep '"level":"error"' ~/Library/Logs/agenthub-router.log | jq .
```

**Search by client:**
```bash
grep '"client_id":"vscode"' ~/Library/Logs/agenthub-router.log | jq .
```

---

### Log Rotation

**Automatic rotation via logrotate:**

Config: `~/.local/share/agenthub/configs/logrotate-macos.conf`

```
/Users/username/Library/Logs/agenthub-router.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 username staff
}
```

**Effect:** Logs rotated daily, kept for 7 days, compressed after 1 day.

---

## Activity Logging

### SQLite Persistent Store

AgentHub stores activity in SQLite database for queryable history:

**Location:** `~/.local/share/agenthub/activity.db`

**Schema:**
```sql
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    request_id TEXT NOT NULL,
    client_id TEXT,
    client_ip TEXT,
    session_id TEXT,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    duration_ms REAL NOT NULL,
    error_message TEXT
);
```

---

### Querying Activity

**API endpoint:**
```bash
curl http://localhost:9090/audit/activity?limit=50
```

**Filter by client:**
```bash
curl "http://localhost:9090/audit/activity?client_id=vscode&limit=20"
```

**Filter by date range:**
```bash
curl "http://localhost:9090/audit/activity?start_date=2026-02-01&end_date=2026-02-06"
```

**Filter by status code:**
```bash
curl "http://localhost:9090/audit/activity?status_code=500"
```

---

### Example Queries

**Find slow requests (> 1s):**
```bash
sqlite3 ~/.local/share/agenthub/activity.db \
  "SELECT timestamp, client_id, path, duration_ms
   FROM activity_log
   WHERE duration_ms > 1000
   ORDER BY duration_ms DESC
   LIMIT 10;"
```

**Count requests by client:**
```bash
sqlite3 ~/.local/share/agenthub/activity.db \
  "SELECT client_id, COUNT(*) as request_count
   FROM activity_log
   GROUP BY client_id;"
```

**Find errors in last 24 hours:**
```bash
sqlite3 ~/.local/share/agenthub/activity.db \
  "SELECT timestamp, client_id, path, error_message
   FROM activity_log
   WHERE status_code >= 500
   AND timestamp > datetime('now', '-24 hours');"
```

---

## Security Alerts

### Real-Time Anomaly Detection

AgentHub automatically detects suspicious patterns:

**Alert types:**
| Alert | Trigger | Action |
|-------|---------|--------|
| **Repeated failures** | 3+ failures in 5 min | Log + Circuit breaker |
| **Credential probing** | 5+ credential attempts in 1 min | Log + Alert |
| **Excessive access** | 10+ requests/sec from single client | Log + Rate limit |
| **Configuration changes** | Dashboard admin actions | Log + Audit trail |

---

### Security Alert Format

```json
{
  "timestamp": "2026-02-06T10:30:45Z",
  "level": "warning",
  "event": "security_alert",
  "alert_type": "repeated_failures",
  "client_id": "unknown",
  "client_ip": "192.168.1.100",
  "details": "3 failed requests in 5 minutes",
  "action_taken": "circuit_breaker_opened"
}
```

---

### Viewing Security Alerts

**Dashboard:**
```
http://localhost:9090/dashboard → Security Alerts panel
```

**Logs:**
```bash
grep '"event":"security_alert"' ~/Library/Logs/agenthub-router.log | jq .
```

**API:**
```bash
curl http://localhost:9090/audit/security-alerts?limit=20
```

---

## Audit Events

### HTTP Requests

**Logged for every request:**
```json
{
  "event": "http_request",
  "method": "POST",
  "path": "/mcp/context7/query",
  "status_code": 200,
  "duration_ms": 234.5,
  "request_id": "550e8400-...",
  "client_id": "claude-desktop",
  "client_ip": "127.0.0.1"
}
```

---

### Credential Access

**Logged when AgentHub reads from Keychain:**
```json
{
  "event": "credential_access",
  "action": "get",
  "credential_key": "api_key",
  "status": "success",
  "client_id": "context7-server"
}
```

**Failed access:**
```json
{
  "event": "credential_access",
  "action": "get",
  "credential_key": "invalid_key",
  "status": "error",
  "error": "Item not found in keychain"
}
```

---

### Admin Actions

**Logged for dashboard operations:**
```json
{
  "event": "admin_action",
  "action": "start",
  "server_name": "context7",
  "status": "success",
  "initiated_by": "admin"
}
```

**Configuration changes:**
```json
{
  "event": "config_change",
  "file": "enhancement-rules.json",
  "change_type": "update",
  "initiated_by": "admin"
}
```

---

## Compliance Use Cases

### HIPAA Compliance

**Requirements:**
- ✅ Audit trail for all access to protected health information (PHI)
- ✅ Track who accessed what, when, and from where
- ✅ Retain logs for 6 years

**AgentHub provides:**
- Structured JSON logs with client_id, client_ip, timestamp
- SQLite persistence for long-term storage
- Queryable activity history

**Additional steps:**
1. **Backup activity.db regularly:**
   ```bash
   sqlite3 ~/.local/share/agenthub/activity.db ".backup /path/to/backups/activity-$(date +%Y%m%d).db"
   ```

2. **Archive rotated logs:**
   ```bash
   # Copy to long-term storage
   cp ~/Library/Logs/agenthub-router.log.*.gz /path/to/archive/
   ```

---

### SOC 2 Compliance

**Requirements:**
- ✅ Logging of security-relevant events
- ✅ Anomaly detection and alerting
- ✅ Tamper-evident audit trails

**AgentHub provides:**
- Security alert system
- Structured logging for SIEM integration
- Activity database with checksums

**Additional steps:**
1. **Enable audit integrity checks:**
   ```bash
   # In .env
   AUDIT_INTEGRITY_ENABLED=true
   ```

2. **Export logs to SIEM:**
   ```bash
   # Forward logs to Splunk, Datadog, etc.
   tail -f ~/Library/Logs/agenthub-router.log | your-siem-forwarder
   ```

---

### GDPR Compliance

**Requirements:**
- ✅ User consent for data processing
- ✅ Right to access personal data
- ✅ Right to erasure

**AgentHub privacy:**
- ❌ Does NOT log prompt content
- ❌ Does NOT log response data
- ✅ Only logs metadata (client_id, path, duration)

**For user data requests:**
```bash
# Export all activity for a user's client_id
sqlite3 ~/.local/share/agenthub/activity.db \
  "SELECT * FROM activity_log WHERE client_id = 'user-client-id';" > user_data.json
```

**For erasure requests:**
```bash
# Delete all activity for a user's client_id
sqlite3 ~/.local/share/agenthub/activity.db \
  "DELETE FROM activity_log WHERE client_id = 'user-client-id';"
```

---

## Dashboard Monitoring

### Activity Log Panel

**View recent activity:**
```
http://localhost:9090/dashboard → Activity Log panel
```

**Shows:**
- Last 50 requests
- Client ID
- Method and path
- Status code
- Duration
- Timestamp

**Auto-refreshes** every 5 seconds.

---

### Security Alerts Panel

**View recent alerts:**
```
http://localhost:9090/dashboard → Security Alerts panel
```

**Shows:**
- Alert type
- Client ID and IP
- Details
- Action taken
- Timestamp

---

## Audit Context Propagation

### How Context Works

AgentHub uses `contextvars` (not thread-local) to propagate audit context across async boundaries:

```python
from router.audit import get_audit_context

# Anywhere in async code:
context = get_audit_context()
# Returns: {
#   "request_id": "550e8400-...",
#   "client_id": "claude-desktop",
#   "client_ip": "127.0.0.1",
#   "session_id": "abc123"
# }
```

**Effect:** Every log entry automatically includes request_id, client_id, etc.

---

### Middleware Stack

Three middleware classes populate audit context:

1. **AuditContextMiddleware** - Sets request_id, client_id, client_ip, session_id
2. **ActivityLoggingMiddleware** - Records to in-memory deque + SQLite
3. **EnhancementMiddleware** - Logs enhancement requests

---

## Performance Considerations

### Log Volume

**Typical volume:**
- 10 requests/sec = ~864,000 logs/day
- Each log entry: ~500 bytes
- Daily log file: ~400 MB

**Mitigation:**
- Log rotation (compress after 1 day)
- Configurable retention (default: 7 days)
- SQLite for efficient querying

---

### SQLite Performance

**Activity database grows over time:**
- 1 million entries = ~200 MB
- Indexed queries remain fast (< 100ms)

**Pruning old data:**
```bash
sqlite3 ~/.local/share/agenthub/activity.db \
  "DELETE FROM activity_log WHERE timestamp < datetime('now', '-30 days');"
```

---

## Troubleshooting

### No Logs Appearing

**Check log file exists:**
```bash
ls -lah ~/Library/Logs/agenthub-router.log
```

**Check LaunchAgent output:**
```bash
launchctl list | grep com.agenthub.router
```

**Check log level:**
```bash
# In .env
LOG_LEVEL=INFO  # Not DEBUG (too verbose) or ERROR (too minimal)
```

---

### Activity DB Locked

**Symptom:** "database is locked" error

**Solution:**
```bash
# Check for open connections
lsof ~/.local/share/agenthub/activity.db

# Restart AgentHub
launchctl restart com.agenthub.router
```

---

### Logs Too Large

**Symptom:** Log files filling disk

**Solution:**
1. **Reduce log retention:**
   ```
   # In logrotate config
   rotate 3  # Instead of 7
   ```

2. **Increase rotation frequency:**
   ```
   hourly  # Instead of daily
   ```

3. **Prune activity database:**
   ```bash
   sqlite3 ~/.local/share/agenthub/activity.db \
     "DELETE FROM activity_log WHERE timestamp < datetime('now', '-7 days');"
   ```

---

## Key Takeaways

- ✅ Structured JSON logging for all security-relevant events
- ✅ SQLite persistence for queryable activity history
- ✅ Real-time security alerts for anomaly detection
- ✅ HIPAA/SOC 2/GDPR compliance-ready audit trails
- ✅ Dashboard monitoring with auto-refresh
- ✅ Log rotation and retention configuration
- ✅ Audit context propagation across async boundaries

---

## Next Steps

**Related Guides:**
- [Circuit Breaker](circuit-breaker.md) - Audit circuit breaker events
- [Enhancement Rules](enhancement-rules.md) - Track enhancement usage
- [LaunchAgent Setup](launchagent.md) - Configure log paths

**Advanced Topics:**
- SIEM integration (Splunk, Datadog, ELK)
- Custom security alert rules
- Audit log encryption
- Tamper-evident logging with checksums

---

**Last Updated:** 2026-02-06
**Audience:** Security-conscious users, compliance teams
**Time:** 15-20 minutes
**Difficulty:** Advanced
