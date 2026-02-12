# Circuit Breaker Pattern in AgentHub

> **What you'll learn:** How AgentHub's circuit breaker protects against failing MCP servers and maintains system stability

---

## Overview

### What This Guide Covers
- Circuit breaker pattern fundamentals
- State transitions (CLOSED → OPEN → HALF_OPEN)
- User-facing behavior during failures
- Configuration tuning for your use case
- Dashboard monitoring

### Prerequisites
- ✅ AgentHub running with MCP servers configured
- ✅ Basic understanding of MCP server operations
- ✅ Familiarity with dashboard at `http://localhost:9090/dashboard`

### Estimated Time
- Reading: 10 minutes
- Configuration: 5 minutes

---

## What is a Circuit Breaker?

### Analogy: Electrical Circuit Breaker

Think of your home's electrical circuit breaker. When something goes wrong (short circuit, overload), the breaker **automatically opens** to prevent damage. You don't need to manually shut off power — it protects itself.

AgentHub's circuit breaker works the same way:
- **Normal operation**: Circuit is CLOSED, requests flow through
- **Failures detected**: Circuit OPENS, requests rejected immediately
- **Recovery attempt**: Circuit goes HALF_OPEN to test if service recovered
- **Success**: Circuit CLOSES, back to normal

### Why Circuit Breakers Matter

**Without circuit breaker:**
```
User request → AgentHub → Slow/crashed MCP server (30s timeout) → Failure
User request → AgentHub → Slow/crashed MCP server (30s timeout) → Failure
User request → AgentHub → Slow/crashed MCP server (30s timeout) → Failure
[Each request waits full timeout, system becomes unresponsive]
```

**With circuit breaker:**
```
User request → AgentHub → Failed server → Circuit OPENS
User request → AgentHub → Circuit OPEN → Fast failure (no wait)
User request → AgentHub → Circuit OPEN → Fast failure (no wait)
[After 30s] → Circuit tries HALF_OPEN → Test request → Success? → Circuit CLOSES
```

**Benefits:**
- ✅ Fast failures (milliseconds instead of 30-second timeouts)
- ✅ Prevents cascade failures (one bad server doesn't bring down AgentHub)
- ✅ Automatic recovery (circuit tests and reopens when server recovers)
- ✅ Better user experience (immediate error messages, not hanging requests)

---

## Circuit Breaker States

### State Machine

```
        [CLOSED] ──────────────┐
           │                    │
           │ 3+ failures        │ Success
           ↓                    │
        [OPEN] ────────→ [HALF_OPEN]
           ↑                    │
           │    Failure         │
           └────────────────────┘
```

### 1. CLOSED State (Normal Operation)

**Behavior:**
- All requests pass through to MCP server
- Failures are tracked but don't block requests
- This is the default healthy state

**Example:**
```bash
curl -X POST http://localhost:9090/mcp/filesystem/read_file \
  -H "Content-Type: application/json" \
  -d '{"path": "/tmp/test.txt"}'

# Response: File contents returned normally
```

**Failure counter:**
- Each failure increments counter
- Each success resets counter to 0
- If counter reaches threshold (default: 3), circuit OPENS

---

### 2. OPEN State (Protective Mode)

**Behavior:**
- **All requests rejected immediately** (no attempt to contact server)
- Fast failure response (< 10ms)
- State automatically transitions to HALF_OPEN after timeout (default: 30s)

**User-facing error:**
```json
{
  "error": "Circuit breaker is OPEN for server 'filesystem'",
  "retry_after": 25,
  "details": "Server has failed too many times. Waiting for recovery."
}
```

**Why this helps:**
- User knows immediately something is wrong (not waiting 30s)
- AgentHub continues serving other servers
- Gives failing server time to recover without constant hammering

---

### 3. HALF_OPEN State (Testing Recovery)

**Behavior:**
- **One test request** is allowed through
- All other requests wait for test result
- If test succeeds → Circuit CLOSES
- If test fails → Circuit OPENS again

**Example flow:**
```bash
# At t=0s: Server fails 3 times → Circuit OPENS

# At t=30s: Circuit automatically goes HALF_OPEN

# Next request becomes the test:
curl -X POST http://localhost:9090/mcp/filesystem/read_file

# If succeeds: Circuit CLOSES (back to normal)
# If fails: Circuit OPENS (wait another 30s)
```

**What users see:**
```json
{
  "status": "testing_recovery",
  "message": "Circuit breaker is testing if server recovered"
}
```

---

## Configuration

### Default Settings

Default configuration in `.env`:

```bash
# Circuit breaker thresholds
CB_FAILURE_THRESHOLD=3       # Failures before OPEN
CB_RECOVERY_TIMEOUT=30       # Seconds in OPEN before HALF_OPEN
```

### Tuning for Your Use Case

#### High-Reliability Services (e.g., Production API)

**Goal:** Quickly stop calling failing services

```bash
CB_FAILURE_THRESHOLD=2       # Open after 2 failures
CB_RECOVERY_TIMEOUT=60       # Wait 60s before retry
```

**Effect:** More aggressive protection, longer recovery time

---

#### Development Environment

**Goal:** More tolerance for flaky servers

```bash
CB_FAILURE_THRESHOLD=5       # Open after 5 failures
CB_RECOVERY_TIMEOUT=10       # Wait only 10s before retry
```

**Effect:** More lenient, faster recovery attempts

---

#### Slow External APIs (e.g., Web scraping)

**Goal:** Balance protection with slow response times

```bash
CB_FAILURE_THRESHOLD=3
CB_RECOVERY_TIMEOUT=120      # Wait 2 minutes before retry
```

**Effect:** Standard protection, longer cooldown for slow recovery

---

### Per-Server Configuration

You can configure circuit breaker behavior per MCP server in `configs/mcp-servers.json`:

```json
{
  "servers": [
    {
      "name": "context7",
      "command": "node",
      "args": ["mcps/context7/index.js"],
      "auto_start": true,
      "restart_on_failure": true,
      "circuit_breaker": {
        "failure_threshold": 5,
        "recovery_timeout": 60
      }
    }
  ]
}
```

**Note:** Per-server settings override global defaults.

---

## Dashboard Monitoring

### Viewing Circuit Breaker Status

**Open dashboard:**
```
http://localhost:9090/dashboard
```

**Circuit breaker panel shows:**
- Server name
- Current state (CLOSED / OPEN / HALF_OPEN)
- Failure count
- Last failure time
- Time until next recovery attempt (if OPEN)

**Example:**
```
Server: context7
State: OPEN
Failures: 3 / 3
Last Failure: 12 seconds ago
Recovery In: 18 seconds
```

---

### Real-Time Updates

Dashboard auto-refreshes every 5 seconds using HTMX. You'll see:
- State changes in real-time
- Countdown timers for recovery
- Success/failure history

---

## Common Scenarios

### Scenario 1: Temporary Network Glitch

**What happens:**
```
1. Network drops for 10 seconds
2. 3 requests fail → Circuit OPENS
3. User sees "Circuit breaker is OPEN" error
4. After 30 seconds → Circuit goes HALF_OPEN
5. Network is back → Test request succeeds
6. Circuit CLOSES → Back to normal
```

**User experience:** Brief outage, automatic recovery

---

### Scenario 2: MCP Server Crash

**What happens:**
```
1. MCP server crashes
2. 3 requests fail → Circuit OPENS
3. User sees "Circuit breaker is OPEN" error
4. After 30 seconds → Circuit goes HALF_OPEN
5. Server still crashed → Test fails → Circuit OPENS
6. Repeat until server recovers or admin restarts it
```

**User experience:** Immediate error, no 30s hangs

---

### Scenario 3: Slow Server

**What happens:**
```
1. Server becomes slow (> 30s response time)
2. Requests timeout and count as failures
3. Circuit OPENS after 3 timeouts
4. User sees "Circuit breaker is OPEN"
5. Admin investigates and fixes performance
6. Circuit recovers automatically once server responds
```

**User experience:** Protected from slow server

---

## Manual Interventions

### Force Circuit Reset

If you know a server has recovered and don't want to wait:

```bash
# Restart the server (also resets circuit)
curl -X POST http://localhost:9090/servers/context7/restart
```

**Effect:** Resets failure counter and closes circuit immediately.

---

### Check Circuit State

```bash
curl http://localhost:9090/servers | jq '.[] | {name, circuit_state, failure_count}'
```

**Output:**
```json
{
  "name": "filesystem",
  "circuit_state": "CLOSED",
  "failure_count": 0
}
```

---

## Troubleshooting

### Circuit Opens Too Easily

**Symptom:** Circuit opens even for occasional failures

**Solution:** Increase failure threshold
```bash
CB_FAILURE_THRESHOLD=5  # Instead of 3
```

---

### Circuit Stays Open Too Long

**Symptom:** Server recovers but circuit takes forever to close

**Solution:** Reduce recovery timeout
```bash
CB_RECOVERY_TIMEOUT=15  # Instead of 30
```

---

### Circuit Never Opens

**Symptom:** Server keeps failing but circuit stays CLOSED

**Check:**
```bash
# Verify circuit breaker is enabled
cat ~/.local/share/agenthub/.env | grep CB_

# Check server logs for actual failures
curl http://localhost:9090/dashboard/activity-partial | grep -A5 "error"
```

**Solution:** Failures might not be counted correctly. Check logs.

---

## Best Practices

### 1. Monitor Dashboard During Issues

When troubleshooting MCP server problems:
- Open dashboard first
- Watch circuit breaker state changes
- Use state transitions to diagnose issues

### 2. Tune Thresholds Per Environment

- **Production:** Lower threshold (2-3), longer timeout (60s)
- **Development:** Higher threshold (5+), shorter timeout (10s)

### 3. Combine with `restart_on_failure`

In `mcp-servers.json`:
```json
{
  "restart_on_failure": true,
  "circuit_breaker": {
    "failure_threshold": 3,
    "recovery_timeout": 30
  }
}
```

**Effect:** Circuit opens to protect system, `restart_on_failure` attempts to fix underlying issue.

### 4. Alert on OPEN States

For production, consider monitoring circuit states:
```bash
# Check for OPEN circuits
curl http://localhost:9090/servers | jq '.[] | select(.circuit_state=="OPEN")'
```

Set up alerts if any circuit stays OPEN > 5 minutes.

---

## Understanding Failure Types

### What Counts as a Failure?

✅ **Counted:**
- Connection refused (server not running)
- Timeout (> 30s response)
- 5xx HTTP errors
- Process crash
- Invalid JSON-RPC response

❌ **Not counted:**
- 4xx client errors (bad request, not server fault)
- Successful empty responses
- Cached responses

---

## Key Takeaways

- ✅ Circuit breaker prevents cascade failures
- ✅ Three states: CLOSED → OPEN → HALF_OPEN
- ✅ Automatic recovery every 30 seconds (configurable)
- ✅ Fast failures instead of long timeouts
- ✅ Monitor via dashboard in real-time
- ✅ Tune thresholds per environment
- ✅ Combine with `restart_on_failure` for resilience

---

## Next Steps

**Related Guides:**
- [Enhancement Rules](enhancement-rules.md) - Configure model selection per client
- [Audit Logging](audit-logging.md) - Track circuit breaker events
- [LaunchAgent Setup](launchagent.md) - Auto-start with resilience

**Advanced Topics:**
- Custom circuit breaker strategies
- Prometheus metrics for circuit state
- Alerting on prolonged OPEN states

---

**Last Updated:** 2026-02-06
**Audience:** All users
**Time:** 10-15 minutes
**Difficulty:** Intermediate
