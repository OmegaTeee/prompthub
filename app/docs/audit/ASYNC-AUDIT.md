# Async/HTTP Audit Report

**Date**: January 26, 2026  
**Scope**: `router/servers/`, `router/routing/`, `router/main.py`, `router/enhancement/`

---

## Summary

Overall the codebase demonstrates good async patterns with several strengths:
- ✅ Consistent use of `httpx.AsyncClient` in enhancement/ollama.py
- ✅ Proper timeouts on critical paths (stdio bridge, ollama, process shutdown)
- ✅ No blocking HTTP libraries (`requests`, `urllib`)
- ✅ Proper async/await usage in subprocess management

**Critical Issues Found**: 2  
**Major Issues Found**: 3  
**Minor Issues Found**: 4

---

## Critical Issues

### 🔴 C1: Missing HTTP timeout in MCP proxy endpoint
**Location**: `router/main.py:527` (mcp_proxy function)  
**Issue**: The stdio bridge call has a default 30s timeout, but this is not explicitly shown in the proxy endpoint.  
**Risk**: Callers may hang indefinitely if bridge doesn't respond.  
**Fix**: Make timeout configurable and expose in API response metadata.

### 🔴 C2: No circuit breaker on ollama calls in enhancement service
**Location**: `router/enhancement/service.py` + ollama.py  
**Issue**: While httpx has timeouts, there's no circuit breaker wrapping Ollama calls.  
**Risk**: If Ollama becomes slow or unresponsive, requests will accumulate and timeout individually rather than failing fast.  
**Fix**: Wrap Ollama client in circuit breaker, similar to MCP servers.

---

## Major Issues

### 🟠 M1: Blocking file I/O in synchronous contexts
**Locations**:
- `router/servers/registry.py:57` - `open()` for loading config
- `router/servers/registry.py:95` - `open()` for saving config  
- `router/enhancement/service.py:142` - `open()` for loading rules
- `router/clients/generators.py:59,96,181,190,279` - Multiple `open()` calls

**Issue**: Using synchronous `open()`/`read()`/`write()` in async contexts will block the event loop.  
**Risk**: Under load, file I/O will cause latency spikes for all concurrent requests.  
**Fix**: Use `aiofiles` library for async file operations:
```python
import aiofiles
async with aiofiles.open(path) as f:
    content = await f.read()
```

### 🟠 M2: MCP proxy doesn't enforce timeout at FastAPI level
**Location**: `router/main.py:472-560`  
**Issue**: While bridge.send() has a timeout, the FastAPI endpoint doesn't have request-level timeout middleware.  
**Risk**: Slow clients or network issues could tie up workers indefinitely.  
**Fix**: Add timeout middleware or use `asyncio.wait_for()` wrapper around bridge calls.

### 🟠 M3: No validation that circuit breaker is called before operations
**Locations**: Enhancement service, dashboard operations  
**Issue**: Only MCP proxy explicitly checks circuit breaker; enhancement service calls Ollama without CB.  
**Risk**: Inconsistent resilience patterns across the codebase.  
**Fix**: Add circuit breaker middleware or decorator pattern for consistency.

---

## Minor Issues

### 🟡 m1: Subprocess stderr read uses small timeout
**Location**: `router/servers/process.py:243`  
**Issue**: `timeout=0.1` for reading stderr is very short and may miss error output.  
**Impact**: Minor - only affects error reporting quality.  
**Fix**: Increase to 1.0 second or make configurable.

### 🟡 m2: No timeout on supervisor health check HTTP calls
**Location**: `router/servers/supervisor.py`  
**Issue**: Supervisor doesn't make HTTP calls currently, but if HTTP transport servers are added, health checks will need timeouts.  
**Impact**: Minor - future proofing needed.  
**Fix**: Add timeout parameter when HTTP transport support is added.

### 🟡 m3: Dashboard router helpers not all async
**Location**: `router/main.py:119-157`  
**Issue**: `_get_health()` and `_get_servers()` are synchronous, while `_get_stats()` and actions are async.  
**Impact**: Minor - currently these just read in-memory state, but mixing patterns is confusing.  
**Fix**: Make all dashboard helpers consistently async for clarity.

### 🟡 m4: No connection pooling in httpx client
**Location**: `router/enhancement/ollama.py:100`  
**Issue**: Using default connection limits; under high load might need tuning.  
**Impact**: Minor - unlikely to be an issue at current scale.  
**Fix**: Add explicit limits if needed: `httpx.Limits(max_keepalive_connections=20, max_connections=100)`

---

## Detailed Findings by Module

### router/servers/

#### bridge.py ✅
- Uses `asyncio.wait_for()` with configurable timeout (default 30s)
- Proper async patterns for stdin/stdout communication
- Timeout handling raises appropriate exceptions
- No blocking calls detected

#### process.py ✅
- Uses `asyncio.create_subprocess_exec()` correctly
- Shutdown timeout properly configured (5s)
- Stderr reading has timeout (0.1s - see minor issue m1)
- No blocking subprocess usage

#### supervisor.py ✅
- Proper async patterns throughout
- Health check loop uses `asyncio.sleep()`
- Process checks use async methods
- No HTTP calls currently (see minor issue m2 for future)

#### registry.py ⚠️
- **Issue**: Uses blocking `open()` for file I/O (see M1)
- Otherwise proper state management
- No async file operations

### router/routing/

- **Empty module** - no code to audit
- Appears MCP routing logic is in main.py instead

### router/main.py

#### Async patterns ✅
- Proper lifespan management
- All endpoints correctly marked `async def`
- Uses `await` for all I/O operations

#### Issues ⚠️
- MCP proxy missing explicit timeout documentation (C1)
- No request-level timeout middleware (M2)
- Dashboard helpers mixed sync/async (m3)
- Circuit breaker only checked in MCP proxy, not enhancement

### router/enhancement/

#### ollama.py ✅
- Excellent httpx usage with explicit timeout: `httpx.Timeout(self.config.timeout)`
- Proper connection reuse pattern
- Exception handling for `ConnectError`, `TimeoutException`, `RequestError`
- No blocking HTTP libraries

#### service.py ⚠️
- **Issue**: No circuit breaker wrapping Ollama calls (C2)
- **Issue**: Blocking file I/O for loading rules (M1)
- Cache operations are async-friendly (in-memory dict)
- Otherwise good async patterns

---

## Recommendations

### Immediate (Critical)

1. **Add circuit breaker for Ollama**:
   ```python
   # In enhancement/service.py
   self._circuit_breaker = CircuitBreaker("ollama", failure_threshold=3, recovery_timeout=30)
   
   async def enhance(self, ...):
       self._circuit_breaker.check()  # Raises if open
       try:
           result = await self.ollama_client.generate(...)
           self._circuit_breaker.record_success()
       except Exception as e:
           self._circuit_breaker.record_failure(e)
           raise
   ```

2. **Document/expose timeouts in API responses**:
   ```python
   # In main.py mcp_proxy
   response["metadata"] = {
       "timeout_used": 30.0,
       "elapsed_ms": elapsed_time
   }
   ```

### High Priority (Major)

3. **Convert file I/O to async**:
   ```bash
   pip install aiofiles
   ```
   ```python
   import aiofiles
   async with aiofiles.open(self.config_path) as f:
       content = await f.read()
       data = json.loads(content)
   ```

4. **Add request timeout middleware**:
   ```python
   from starlette.middleware.base import BaseHTTPMiddleware
   
   class TimeoutMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request, call_next):
           try:
               return await asyncio.wait_for(call_next(request), timeout=60.0)
           except asyncio.TimeoutError:
               return JSONResponse({"error": "Request timeout"}, status_code=504)
   
   app.add_middleware(TimeoutMiddleware)
   ```

### Medium Priority (Minor)

5. Increase stderr read timeout to 1.0s
6. Make dashboard helpers consistently async
7. Add connection pool limits to httpx client if scaling issues arise
8. Add HTTP health check timeout when HTTP transport servers are supported

---

## Compliance Summary

| Requirement | Status | Notes |
|-------------|--------|-------|
| Use httpx (not requests) | ✅ Pass | All HTTP via httpx.AsyncClient |
| Async/await for I/O | ⚠️ Partial | Needs aiofiles for file I/O |
| Timeouts on external calls | ⚠️ Partial | Ollama yes, file I/O no |
| Circuit breaker coverage | ⚠️ Partial | MCP yes, Ollama no |
| No blocking calls in async | ⚠️ Partial | File I/O blocks event loop |
| Type hints | ✅ Pass | Comprehensive throughout |

---

## Testing Recommendations

1. **Load test file I/O paths** to measure block duration
2. **Simulate Ollama failure** to verify circuit breaker needs
3. **Test timeout behavior** under network latency
4. **Verify process cleanup** on supervisor shutdown
5. **Test concurrent MCP requests** to ensure bridge thread-safety

---

## Next Steps

1. Create GitHub issues for critical/major findings
2. Prioritize circuit breaker for Ollama (C2)
3. Schedule aiofiles migration sprint (M1)
4. Add integration tests for timeout/CB scenarios
5. Document timeout values in API specs (OpenAPI)
