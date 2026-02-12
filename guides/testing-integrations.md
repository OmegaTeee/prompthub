# Testing Client Integrations

> **Comprehensive test procedures for verifying Claude Desktop, VS Code, and Raycast integrations with PromptHub**

---

## Overview

This guide provides **step-by-step testing procedures** to verify that each client is properly integrated with PromptHub and can access all MCP servers.

### Test Coverage

- ✅ **Connection Tests** - Verify client can reach PromptHub
- ✅ **MCP Server Access** - Test each of the 7 MCP servers
- ✅ **Enhancement Tests** - Verify client-specific prompt enhancement
- ✅ **Performance Tests** - Check response times and caching
- ✅ **Error Handling** - Test failure scenarios

---

## Prerequisites

Before running tests, ensure:

```bash
# 1. PromptHub is running
curl http://localhost:9090/health
# Expected: {"status": "healthy", ...}

# 2. All MCP servers are running
curl http://localhost:9090/servers | jq '.[] | {name, status}'
# Expected: All show "running"

# 3. Ollama is running with required models
ollama list | grep -E "(deepseek-r1|qwen3-coder)"
# Expected: Both models listed

# 4. Clients are configured
# See example configs in clients/{claude,vscode,raycast}/
# - Claude Desktop: Check ~/Library/Application Support/Claude/claude_desktop_config.json
# - VS Code: Check ~/.vscode/settings.json or .vscode/settings.json
# - Raycast: Check ~/Library/Application Support/com.raycast.macos/mcp-servers.json
```

**Quick reference for example configs:**
- Claude Desktop: `~/.local/share/prompthub/clients/claude/`
- VS Code: `~/.local/share/prompthub/clients/vscode/`
- Raycast: `~/.local/share/prompthub/clients/raycast/`

---

## Test Suite 1: Claude Desktop

### T1.1: Connection Test

**Objective:** Verify Claude Desktop can connect to PromptHub

**Steps:**
1. Open Claude Desktop
2. Look for MCP badge at bottom of chat window
3. Should show: `🔌 PromptHub` or `🔌 prompthub-router`

**Expected Result:**
✅ MCP badge visible
✅ No connection errors in UI

**If Failed:**
- Check config: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json`
- Verify PromptHub running: `curl http://localhost:9090/health`
- Restart Claude Desktop

---

### T1.2: List MCP Tools

**Objective:** Verify Claude Desktop can enumerate MCP tools

**Steps:**
1. In Claude Desktop chat, type:
   ```
   What MCP tools are available?
   ```
2. Wait for response

**Expected Result:**
```
Available MCP Tools:

1. context7 - Documentation fetching
2. desktop-commander - File operations
3. sequential-thinking - Reasoning
4. memory - Context persistence
5. deepseek-reasoner - Local AI
6. fetch - Web requests
7. obsidian - Note management
```

**If Failed:**
- Check MCP servers: `curl http://localhost:9090/servers`
- Restart stopped servers: `curl -X POST http://localhost:9090/servers/{name}/start`

---

### T1.3: Test Context7 (Documentation)

**Objective:** Verify context7 MCP server integration

**Test Query:**
```
Use context7: Show me React useEffect hook documentation
```

**Expected Response:**
- ✅ Returns React useEffect documentation
- ✅ Includes code examples
- ✅ Formatted in Markdown
- ✅ Response time < 3 seconds (first request)
- ✅ Response time < 1 second (cached, second request)

**Validation:**
```bash
# Check PromptHub logs
curl http://localhost:9090/dashboard/activity-partial | grep "context7"
```

**If Failed:**
- Check context7 status: `curl http://localhost:9090/servers/context7`
- Restart context7: `curl -X POST http://localhost:9090/servers/context7/restart`

---

### T1.4: Test Desktop Commander (File Operations)

**Objective:** Verify desktop-commander MCP server integration

**Test Query:**
```
Use desktop-commander: List files in my Downloads folder
```

**Expected Response:**
- ✅ Returns list of files in ~/Downloads
- ✅ Shows file sizes
- ✅ No permission errors
- ✅ Response time < 2 seconds

**If Failed:**
- Grant Full Disk Access to Claude Desktop (System Settings → Privacy & Security)
- Check desktop-commander: `curl http://localhost:9090/servers/desktop-commander`

---

### T1.5: Test Sequential Thinking (Reasoning)

**Objective:** Verify sequential-thinking MCP server integration

**Test Query:**
```
Use sequential-thinking: Plan a 5-day workout routine
```

**Expected Response:**
- ✅ Returns step-by-step plan
- ✅ Numbered steps (Day 1, Day 2, etc.)
- ✅ Structured reasoning
- ✅ Response time < 5 seconds

---

### T1.6: Test Memory (Context Persistence)

**Objective:** Verify memory MCP server stores and retrieves context

**Test Query 1 (Store):**
```
Use memory: Remember that my favorite programming language is TypeScript
```

**Expected Response:**
```
✅ Stored: favorite programming language = TypeScript
```

**Test Query 2 (Retrieve):**
```
Use memory: What's my favorite programming language?
```

**Expected Response:**
```
Your favorite programming language is TypeScript
```

**Validation:**
```bash
# Check memory server has stored data
curl http://localhost:9090/servers/memory | jq '.stored_items'
```

---

### T1.7: Test Prompt Enhancement

**Objective:** Verify Claude Desktop prompts are enhanced with DeepSeek-R1

**Test Query (Vague):**
```
context7 react
```

**Expected Behavior:**
1. Prompt enhanced by DeepSeek-R1 before sending to context7
2. Enhanced prompt requests structured, comprehensive React docs
3. Response includes clear sections and Markdown formatting

**Validation:**
```bash
# Check enhancement was applied
curl http://localhost:9090/audit/activity?client_id=claude-desktop&limit=1 | jq '.enhanced'
```

**Expected:** `"enhanced": true`

---

### T1.8: Test Caching

**Objective:** Verify responses are cached for faster subsequent requests

**Steps:**
1. First request:
   ```
   Use context7: Python list comprehensions
   ```
   Note response time (should be ~2-3 seconds)

2. Second request (same query):
   ```
   Use context7: Python list comprehensions
   ```
   Note response time (should be <500ms)

**Expected:**
- ✅ Second request significantly faster
- ✅ Identical response content

**Validation:**
```bash
# Check cache stats
curl http://localhost:9090/dashboard/stats-partial | grep "cache_hits"
```

---

## Test Suite 2: VS Code (Claude Code / Cline)

### T2.1: Connection Test

**Objective:** Verify VS Code extension connects to PromptHub

**Steps:**
1. Open VS Code
2. Open Command Palette (`Cmd+Shift+P`)
3. Type: "Claude: Show MCP Status"
4. Check status

**Expected Result:**
✅ Shows: "Connected to PromptHub (7 tools)"

**Alternative Check:**
```bash
# Check VS Code settings
code ~/.vscode/settings.json | grep prompthub
```

**If Failed:**
- Reload VS Code: `Cmd+Shift+P` → "Developer: Reload Window"
- Check settings.json syntax

---

### T2.2: Test Code Documentation (Context7)

**Objective:** Verify code-optimized documentation lookup

**Test Query:**
```
Use context7: TypeScript type guards examples
```

**Expected Response:**
- ✅ Returns TypeScript code examples
- ✅ Code-first formatting (code before explanation)
- ✅ Includes file paths (e.g., `src/utils/typeGuards.ts`)
- ✅ Minimal prose
- ✅ Syntax highlighting

**Expected Format:**
```typescript
// src/utils/typeGuards.ts

interface User {
  name: string;
  email: string;
}

function isUser(obj: any): obj is User {
  return typeof obj.name === 'string' && typeof obj.email === 'string';
}

// Usage
const data: unknown = fetchData();
if (isUser(data)) {
  console.log(data.email);  // TypeScript knows data is User
}
```

---

### T2.3: Test Code Enhancement (Qwen3-Coder)

**Objective:** Verify VS Code prompts use Qwen3-Coder for code-first responses

**Test Query (Minimal):**
```
array sort typescript
```

**Expected Response:**
- ✅ Code-first (no introductory text)
- ✅ TypeScript examples
- ✅ Multiple sorting scenarios
- ✅ File path included
- ✅ Under 100 words of prose

**Validation:**
```bash
# Verify Qwen3-Coder was used
curl http://localhost:9090/audit/activity?client_id=vscode&limit=1 | jq '.model_used'
```

**Expected:** `"model_used": "qwen3-coder:latest"`

---

### T2.4: Test Desktop Commander Integration

**Objective:** Verify file operations from VS Code

**Test Query:**
```
Use desktop-commander: Find all package.json files in current workspace
```

**Expected Response:**
- ✅ Lists all package.json files
- ✅ Shows file paths relative to workspace root
- ✅ No permission errors
- ✅ Response time < 2 seconds

---

### T2.5: Test Workspace-Specific Configuration

**Objective:** Verify per-project MCP settings work

**Steps:**
1. Create `.vscode/settings.json` in a project:
   ```json
   {
     "claude.mcp.servers": {
       "prompthub": {
         "headers": {
           "X-Client-Name": "vscode-test-project"
         }
       }
     }
   }
   ```

2. Update `~/.local/share/prompthub/configs/enhancement-rules.json`:
   ```json
   {
     "clients": {
       "vscode-test-project": {
         "model": "qwen3-coder:latest",
         "system_prompt": "Test project: Always include TODO comments"
       }
     }
   }
   ```

3. Test query:
   ```
   array filter javascript
   ```

**Expected Response:**
- ✅ Includes TODO comments in code examples
- ✅ Uses custom system prompt

**Validation:**
```bash
curl http://localhost:9090/audit/activity?client_id=vscode-test-project&limit=1
```

---

### T2.6: Test Response Caching in VS Code

**Objective:** Verify caching works across VS Code sessions

**Steps:**
1. First query: `Use context7: Node.js fs module` (note time)
2. Close and reopen VS Code
3. Second query: `Use context7: Node.js fs module` (note time)

**Expected:**
- ✅ Second query faster even after restart
- ✅ Cache persists across sessions

---

## Test Suite 3: Raycast

### T3.1: Connection Test

**Objective:** Verify Raycast AI connects to PromptHub

**Steps:**
1. Open Raycast (`Cmd+Space`)
2. Type: "AI Settings"
3. Navigate to: MCP Servers
4. Check PromptHub status

**Expected Result:**
✅ PromptHub listed with green checkmark
✅ Shows: "Connected (7 tools)"

**If Failed:**
- Check config: `cat ~/Library/Application\ Support/com.raycast.macos/mcp-servers.json`
- Restart Raycast: `killall Raycast && open -a Raycast`

---

### T3.2: Test Quick CLI Commands

**Objective:** Verify Raycast returns action-oriented CLI commands

**Test Query:**
```
How do I check disk usage on macOS?
```

**Expected Response:**
- ✅ CLI command first
- ✅ Under 200 words
- ✅ Copy-paste ready
- ✅ No lengthy explanations

**Expected Format:**
```bash
# Check disk usage
df -h

# Or for specific directory
du -sh ~/Documents

# Human-readable, sorted
du -h -d 1 ~ | sort -hr | head -10
```

---

### T3.3: Test Context7 Quick Docs

**Objective:** Verify quick documentation lookup in Raycast

**Test Query:**
```
context7: curl POST request example
```

**Expected Response:**
- ✅ Returns concise curl examples
- ✅ Under 200 words
- ✅ Code-first
- ✅ Response time < 2 seconds

---

### T3.4: Test Action-Oriented Enhancement

**Objective:** Verify Raycast prompts use action-oriented system prompt

**Test Query (Vague):**
```
docker containers
```

**Expected Response:**
- ✅ CLI commands for listing containers
- ✅ Action verbs ("Run:", "Try:", "Check:")
- ✅ Multiple command options
- ✅ Under 200 words total

**Validation:**
```bash
# Check enhancement used "raycast" client rules
curl http://localhost:9090/audit/activity?client_id=raycast&limit=1 | jq '.enhancement_rules'
```

---

### T3.5: Test Fast Response Times

**Objective:** Verify Raycast optimized for speed

**Test Query:**
```
git status command
```

**Expected Response Time:**
- ✅ First request: <3 seconds
- ✅ Cached request: <500ms

**Validation:**
```bash
# Check response time metrics
curl http://localhost:9090/dashboard/stats-partial | grep "avg_response_time"
```

---

## Test Suite 4: Cross-Client Tests

### T4.1: Shared Cache Test

**Objective:** Verify cache is shared across all clients

**Steps:**
1. **In Claude Desktop**, query:
   ```
   Use context7: React useState hook
   ```
   Note response time (e.g., 2.5s)

2. **In VS Code**, query:
   ```
   Use context7: React useState hook
   ```
   Note response time (should be <500ms)

3. **In Raycast**, query:
   ```
   context7: React useState hook
   ```
   Note response time (should be <500ms)

**Expected:**
- ✅ First query caches the result
- ✅ Subsequent queries in other clients use cache
- ✅ Significant speed improvement

**Validation:**
```bash
curl http://localhost:9090/dashboard/stats-partial | jq '.cache_hits'
# Should show 2 cache hits
```

---

### T4.2: Client-Specific Enhancement Test

**Objective:** Verify each client gets appropriate enhancement

**Steps:**
1. **Claude Desktop** - Ask: `explain async/await`
   Expected: Structured response with clear reasoning

2. **VS Code** - Ask: `explain async/await`
   Expected: Code-first with TypeScript examples

3. **Raycast** - Ask: `explain async/await`
   Expected: CLI-ready code snippets, under 200 words

**Validation:**
```bash
# Check different models/prompts were used
curl http://localhost:9090/audit/activity | jq -r '.[] | "\\(.client_id): \\(.model_used)"'
```

**Expected Output:**
```
claude-desktop: deepseek-r1:latest
vscode: qwen3-coder:latest
raycast: deepseek-r1:latest
```

---

### T4.3: Concurrent Request Test

**Objective:** Verify PromptHub handles concurrent requests from multiple clients

**Steps:**
1. Open all three clients (Claude Desktop, VS Code, Raycast)
2. Simultaneously send requests:
   - **Claude Desktop**: `Use context7: Python pandas`
   - **VS Code**: `Use context7: JavaScript promises`
   - **Raycast**: `context7: Bash loops`

**Expected:**
- ✅ All requests complete successfully
- ✅ No timeouts or errors
- ✅ Responses arrive within 5 seconds

**Validation:**
```bash
# Check concurrent request handling
curl http://localhost:9090/audit/activity?limit=3 | jq -r '.[] | .timestamp'
# Timestamps should be within seconds of each other
```

---

## Test Suite 5: Error Handling

### T5.1: Test PromptHub Down

**Objective:** Verify graceful handling when PromptHub is unreachable

**Steps:**
1. Stop PromptHub:
   ```bash
   launchctl stop com.prompthub.router
   ```

2. Try query in any client:
   ```
   Use context7: test
   ```

**Expected:**
- ✅ Client shows clear error: "Cannot connect to PromptHub"
- ✅ No crash or hang
- ✅ Suggested action: "Check if PromptHub is running"

3. Restart PromptHub:
   ```bash
   launchctl start com.prompthub.router
   ```

---

### T5.2: Test MCP Server Crash

**Objective:** Verify auto-restart of crashed MCP servers

**Steps:**
1. Kill a server process:
   ```bash
   # Find PID
   curl http://localhost:9090/servers/context7 | jq '.pid'

   # Kill it
   kill -9 <PID>
   ```

2. Wait 5-10 seconds

3. Check server status:
   ```bash
   curl http://localhost:9090/servers/context7 | jq '.status'
   ```

**Expected:**
- ✅ Server status shows: "restarting" then "running"
- ✅ Auto-restart happens within 10 seconds
- ✅ New PID assigned

---

### T5.3: Test Ollama Down

**Objective:** Verify graceful degradation when Ollama unavailable

**Steps:**
1. Stop Ollama:
   ```bash
   pkill -9 ollama
   ```

2. Send a query requiring enhancement:
   ```
   react hooks
   ```

**Expected:**
- ✅ Request still completes
- ✅ Uses original (unenhanced) prompt
- ✅ Warning logged but not shown to user

3. Restart Ollama:
   ```bash
   ollama serve
   ```

---

## Test Suite 6: Performance Tests

### T6.1: Cache Hit Ratio

**Objective:** Measure cache effectiveness

**Steps:**
1. Clear cache:
   ```bash
   curl -X POST http://localhost:9090/dashboard/actions/clear-cache
   ```

2. Run 10 queries (5 unique, 5 duplicates)

3. Check cache stats:
   ```bash
   curl http://localhost:9090/dashboard/stats-partial | jq '.cache_stats'
   ```

**Expected:**
- ✅ Cache hit ratio > 50%
- ✅ Average response time for cache hits < 100ms

---

### T6.2: Response Time Benchmarks

**Objective:** Establish baseline performance metrics

**Benchmark Queries:**

| Query Type | Expected Time (First) | Expected Time (Cached) |
|------------|---------------------|---------------------|
| Context7 doc lookup | < 3s | < 500ms |
| Desktop Commander file list | < 2s | < 100ms |
| Sequential thinking | < 5s | < 1s |
| Memory recall | < 1s | < 50ms |

**Measurement:**
```bash
# Time a request
time curl -X POST http://localhost:9090/mcp/context7/tools/call \
  -H "Content-Type: application/json" \
  -d '{"method": "query", "params": {"library": "react"}}'
```

---

## Test Report Template

After running all tests, generate a report:

```markdown
# PromptHub Integration Test Report

**Date:** YYYY-MM-DD
**PromptHub Version:** 1.0.0
**Tester:** [Your Name]

## Summary

- Total Tests: 30
- Passed: 28
- Failed: 2
- Skipped: 0

## Claude Desktop
- [x] T1.1: Connection Test
- [x] T1.2: List MCP Tools
- [x] T1.3: Context7 Test
- [x] T1.4: Desktop Commander
- [x] T1.5: Sequential Thinking
- [x] T1.6: Memory Test
- [x] T1.7: Prompt Enhancement
- [ ] T1.8: Caching (FAILED - cache miss rate too high)

## VS Code
- [x] T2.1: Connection Test
- [x] T2.2: Code Documentation
- [x] T2.3: Code Enhancement
- ...

## Raycast
- ...

## Failures

### T1.8: Caching Test (Claude Desktop)
**Issue:** Cache hit rate only 30%, expected >50%
**Root Cause:** Cache key not accounting for client-specific enhancements
**Fix:** Update cache key generation to include client name

## Performance Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Context7 first request | < 3s | 2.4s | ✅ PASS |
| Cache hit response | < 500ms | 89ms | ✅ PASS |
| Concurrent requests (3 clients) | < 5s | 6.2s | ⚠️ WARN |

## Recommendations

1. Optimize concurrent request handling
2. Investigate cache key collision issues
3. Add request queueing for better concurrency
```

---

## Automated Testing Script

Save this script to automate tests:

```bash
#!/bin/bash
# File: test-integrations.sh

echo "🧪 PromptHub Integration Test Suite"
echo "=================================="

# Check prerequisites
echo "Checking prerequisites..."

if ! curl -s http://localhost:9090/health > /dev/null; then
  echo "❌ PromptHub not running"
  exit 1
fi

if ! ollama list | grep -q deepseek-r1; then
  echo "❌ DeepSeek-R1 model not installed"
  exit 1
fi

echo "✅ Prerequisites met"
echo ""

# Run tests
PASSED=0
FAILED=0

test_context7() {
  echo "Testing Context7..."
  RESPONSE=$(curl -s -X POST http://localhost:9090/mcp/context7/tools/call \
    -H "Content-Type: application/json" \
    -d '{"method": "query", "params": {"library": "react"}}')

  if echo "$RESPONSE" | grep -q "useState"; then
    echo "✅ Context7 test passed"
    PASSED=$((PASSED + 1))
  else
    echo "❌ Context7 test failed"
    FAILED=$((FAILED + 1))
  fi
}

test_cache() {
  echo "Testing cache..."
  # Clear cache
  curl -s -X POST http://localhost:9090/dashboard/actions/clear-cache > /dev/null

  # First request
  START=$(date +%s%N)
  curl -s -X POST http://localhost:9090/mcp/context7/tools/call \
    -H "Content-Type: application/json" \
    -d '{"method": "query", "params": {"library": "react"}}' > /dev/null
  END=$(date +%s%N)
  FIRST_TIME=$(((END - START) / 1000000))

  # Second request (cached)
  START=$(date +%s%N)
  curl -s -X POST http://localhost:9090/mcp/context7/tools/call \
    -H "Content-Type: application/json" \
    -d '{"method": "query", "params": {"library": "react"}}' > /dev/null
  END=$(date +%s%N)
  CACHE_TIME=$(((END - START) / 1000000))

  echo "First request: ${FIRST_TIME}ms"
  echo "Cached request: ${CACHE_TIME}ms"

  if [ "$CACHE_TIME" -lt 500 ]; then
    echo "✅ Cache test passed"
    PASSED=$((PASSED + 1))
  else
    echo "❌ Cache test failed (too slow)"
    FAILED=$((FAILED + 1))
  fi
}

# Run all tests
test_context7
test_cache

echo ""
echo "Test Results: $PASSED passed, $FAILED failed"
```

Make executable and run:
```bash
chmod +x test-integrations.sh
./test-integrations.sh
```

---

## Automated Integration Tests

In addition to manual testing, PromptHub includes a comprehensive automated integration test suite using pytest.

### Running Automated Tests

```bash
# Quick start - Run all integration tests
./scripts/run-tests.sh integration

# Or with pytest directly
source .venv/bin/activate
pytest tests/integration/ -v
```

### Test Suite Overview

**36 automated integration tests** covering:

```
tests/integration/
├── test_client_integrations.py      (19 tests)
│   ├── Claude Desktop integration (6 tests)
│   ├── VS Code integration (3 tests)
│   ├── Raycast integration (3 tests)
│   ├── Cross-client features (3 tests)
│   └── Configuration validation (4 tests)
│
├── test_mcp_proxy.py                (11 tests)
│   ├── MCP proxy routing (6 tests)
│   ├── Performance (2 tests)
│   └── Audit logging (2 tests)
│
└── test_enhancement_and_caching.py  (11 tests)
    ├── Prompt enhancement (5 tests, some require Ollama)
    └── Caching (6 tests)

Status: ✅ 31 passed, 5 skipped (Ollama required)
```

### What the Automated Tests Validate

**Client Integrations:**
- ✅ curl-based stdio bridge for Claude Desktop
- ✅ HTTP endpoints for VS Code and Raycast
- ✅ Example configuration files are valid JSON
- ✅ All clients can access all 7 MCP servers
- ✅ Cache is shared across all clients
- ✅ Client-specific enhancement routing works

**MCP Proxy:**
- ✅ JSON-RPC requests properly forwarded to MCP servers
- ✅ All 7 servers (context7, desktop-commander, sequential-thinking, memory, deepseek-reasoner, fetch, obsidian) accessible
- ✅ Invalid servers return 404
- ✅ JSON-RPC error handling
- ✅ X-Client-Name header preserved
- ✅ Concurrent request handling (10+ simultaneous)
- ✅ Timeout handling
- ✅ Audit logging captures all requests

**Caching:**
- ✅ Cache improves response time (2-10x faster on hits)
- ✅ Cache shared across all clients
- ✅ Cache statistics tracked correctly
- ✅ Cache clear functionality works
- ✅ LRU eviction policy

**Prompt Enhancement** (when Ollama available):
- ⏭️ Client-specific models (DeepSeek-R1 for Claude Desktop, Qwen3-Coder for VS Code)
- ⏭️ VS Code gets code-first responses
- ⏭️ Raycast gets action-oriented CLI responses
- ✅ Enhancement endpoint accessible
- ⏭️ Graceful fallback when Ollama unavailable

### Test Output Example

```bash
$ pytest tests/integration/ -v

============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/visualval/.local/share/prompthub
configfile: pyproject.toml

tests/integration/test_client_integrations.py::TestClaudeDesktopIntegration::test_curl_based_stdio_bridge PASSED [  2%]
tests/integration/test_client_integrations.py::TestClaudeDesktopIntegration::test_claude_desktop_config_example_valid PASSED [  5%]
tests/integration/test_client_integrations.py::TestClaudeDesktopIntegration::test_client_name_header_routes_to_correct_enhancement PASSED [  8%]
tests/integration/test_client_integrations.py::TestVSCodeIntegration::test_vscode_http_endpoint PASSED [ 11%]
tests/integration/test_client_integrations.py::TestVSCodeIntegration::test_vscode_config_example_valid PASSED [ 13%]
tests/integration/test_client_integrations.py::TestRaycastIntegration::test_raycast_http_endpoint PASSED [ 16%]
tests/integration/test_client_integrations.py::TestRaycastIntegration::test_raycast_config_example_valid PASSED [ 19%]
tests/integration/test_client_integrations.py::TestCrossClientFeatures::test_shared_cache_across_clients PASSED [ 22%]
tests/integration/test_client_integrations.py::TestCrossClientFeatures::test_all_mcp_servers_accessible_from_all_clients PASSED [ 25%]
...

======================== 31 passed, 5 skipped in 6.27s =========================
```

### Running Specific Test Suites

```bash
# Only client integration tests
pytest tests/integration/test_client_integrations.py -v

# Only caching tests
pytest tests/integration/test_enhancement_and_caching.py::TestCaching -v

# Only tests that don't require Ollama
pytest tests/integration/ -v -m "not requires_ollama"

# Run individual test
pytest tests/integration/test_mcp_proxy.py::TestMCPProxyRouting::test_proxy_to_context7 -v
```

### Continuous Integration

Tests run automatically on:
- Every push to `main`
- Every pull request
- Release tags

CI Status: [![Tests](https://github.com/your-org/prompthub/workflows/Tests/badge.svg)](https://github.com/your-org/prompthub/actions)

### Key Differences: Manual vs Automated Tests

| Aspect | Manual Tests | Automated Tests |
|--------|-------------|-----------------|
| **Coverage** | Full user workflows | API/HTTP endpoints |
| **Speed** | Slow (hours) | Fast (seconds) |
| **Client UI** | Tests actual client UX | Tests integration layer only |
| **Enhancement** | Sees enhanced prompts | Tests enhancement routing |
| **Debugging** | User-facing errors | Low-level assertions |
| **When to Use** | Pre-release validation | Development & CI/CD |

**Recommendation:** Use both! Automated tests catch regressions quickly during development. Manual tests validate the complete user experience before major releases.

## See Also

- [claude-desktop-integration.md](claude-desktop-integration.md) - Claude Desktop setup
- [vscode-integration.md](vscode-integration.md) - VS Code setup
- [raycast-integration.md](raycast-integration.md) - Raycast setup
- [getting-started.md](getting-started.md) - PromptHub installation
- `tests/integration/` - Automated test suite source code
- `scripts/run-tests.sh` - Test runner script
