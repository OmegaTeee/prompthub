"""
PromptHub Router - Main FastAPI Application

A centralized MCP router that provides:
- MCP server lifecycle management (install, start, stop, monitor)
- Unified MCP server access
- Prompt enhancement via Ollama
- Response caching (L1 memory, L2 semantic)
- Circuit breaker resilience
"""

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from router.audit import audit_admin_action, setup_audit_logging
from router.clients import (
    generate_claude_desktop_config,
    generate_raycast_script,
    generate_vscode_config,
    generate_vscode_tasks,
)
from router.config import get_settings
from router.dashboard import create_dashboard_router
from router.enhancement import EnhancementService
from router.openai_compat import create_openai_compat_router
from router.openai_compat.auth import ApiKeyManager
from router.middleware import (
    ActivityLoggingMiddleware,
    AuditContextMiddleware,
    RequestTimeoutMiddleware,
)
from router.pipelines import DocumentationPipeline
from router.resilience import CircuitBreakerError, CircuitBreakerRegistry
from router.servers import (
    ProcessManager,
    ServerConfig,
    ServerRegistry,
    ServerStatus,
    ServerTransport,
    Supervisor,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global service instances (initialized in lifespan)
registry: ServerRegistry | None = None
process_manager: ProcessManager | None = None
supervisor: Supervisor | None = None
enhancement_service: EnhancementService | None = None
circuit_breakers: CircuitBreakerRegistry | None = None
documentation_pipeline: DocumentationPipeline | None = None
persistent_activity_log = None  # Will be initialized in lifespan


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    global registry, process_manager, supervisor, enhancement_service, circuit_breakers, documentation_pipeline, persistent_activity_log

    # Startup
    settings = get_settings()

    # Setup audit logging (log to /tmp for development, can be changed in production)
    from pathlib import Path
    log_dir = Path("/tmp/prompthub")
    setup_audit_logging(log_dir=log_dir, console_output=True)

    # Initialize persistent activity log
    from router.middleware.persistent_activity import get_persistent_activity_log
    persistent_activity_log = get_persistent_activity_log(db_path=log_dir / "activity.db")
    await persistent_activity_log.initialize()
    logger.info("Initialized persistent activity log")

    logger.info(f"Starting PromptHub Router on {settings.host}:{settings.port}")

    # Initialize server management
    registry = ServerRegistry(settings.mcp_servers_config)
    await registry.load_async()  # Use async file I/O

    process_manager = ProcessManager(registry)
    supervisor = Supervisor(registry, process_manager)

    # Start supervisor (will auto-start configured servers)
    await supervisor.start()

    # Initialize circuit breaker registry
    circuit_breakers = CircuitBreakerRegistry()

    # Initialize enhancement service
    enhancement_service = EnhancementService(
        rules_path=settings.enhancement_rules_config,
        cache_max_size=500,
        cache_ttl=7200.0,
    )
    await enhancement_service.initialize()

    # Initialize documentation pipeline
    documentation_pipeline = DocumentationPipeline(
        enhancement_service=enhancement_service,
        supervisor=supervisor,
    )

    yield

    # Shutdown
    logger.info("Shutting down PromptHub Router")

    if enhancement_service:
        await enhancement_service.close()

    if supervisor:
        await supervisor.stop()


def normalize_tool_schema(schema: dict) -> dict:
    """
    Normalize tool input schemas to ensure they're valid JSON Schema.

    Some MCP servers return malformed schemas (e.g., missing 'properties' field).
    This function fixes common issues to prevent client validation warnings.

    Args:
        schema: Tool input schema (potentially malformed)

    Returns:
        Normalized schema that passes JSON Schema validation
    """
    if not isinstance(schema, dict):
        return schema

    # If schema has 'type': 'object' but no 'properties', add empty properties
    if schema.get("type") == "object" and "properties" not in schema:
        schema = schema.copy()  # Don't mutate original
        schema["properties"] = {}

    return schema


def normalize_mcp_response(response: dict, method: str) -> dict:
    """
    Normalize MCP JSON-RPC responses to fix common schema issues.

    Args:
        response: JSON-RPC response from MCP server
        method: The method that was called (e.g., "tools/list")

    Returns:
        Normalized response with fixed schemas
    """
    # Only normalize tools/list responses
    if method != "tools/list" and method != "tools.list":
        return response

    # Check if response has tools
    if not isinstance(response, dict):
        return response

    result = response.get("result")
    if not result or not isinstance(result, dict):
        return response

    tools = result.get("tools")
    if not tools or not isinstance(tools, list):
        return response

    # Normalize schema for each tool
    normalized_tools = []
    for tool in tools:
        if isinstance(tool, dict) and "inputSchema" in tool:
            tool = tool.copy()  # Don't mutate original
            tool["inputSchema"] = normalize_tool_schema(tool["inputSchema"])
        normalized_tools.append(tool)

    # Return response with normalized tools
    response = response.copy()
    result = result.copy()
    result["tools"] = normalized_tools
    response["result"] = result

    return response


app = FastAPI(
    title="PromptHub Router",
    description="Centralized MCP router with server management, prompt enhancement, and caching",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Activity logging middleware for dashboard (uses lazy init for persistent log)
# Must be added BEFORE AuditContext so that AuditContext runs FIRST (middleware is a stack)
app.add_middleware(ActivityLoggingMiddleware)

# Audit context middleware (sets request context for downstream middleware)
app.add_middleware(AuditContextMiddleware)

# Request timeout middleware (prevents slow clients from consuming workers indefinitely)
# Must be added AFTER other middlewares so it wraps them (middleware is a stack)
app.add_middleware(RequestTimeoutMiddleware, timeout=60.0)

# Mount static files for dashboard CSS
static_path = Path(__file__).parent.parent / "templates" / "css"
app.mount("/static/css", StaticFiles(directory=str(static_path)), name="static")


# =============================================================================
# Dashboard Helper Functions
# =============================================================================


async def _get_health():
    """Get health status for dashboard."""
    # Made async for consistency with other dashboard helpers
    return supervisor.get_status_summary() if supervisor else {}


async def _get_stats():
    """Get enhancement stats for dashboard."""
    if enhancement_service:
        return await enhancement_service.get_stats()
    return {}


async def _get_servers():
    """Get server statuses for dashboard."""
    # Made async for consistency with other dashboard helpers
    if not supervisor or not registry:
        return {"servers": {}}

    servers = {}
    for name in registry._servers.keys():
        info = registry.get_process_info(name)
        servers[name] = {
            "status": info.status.value if info else "unknown",
            "pid": info.pid if info else None,
            "restart_count": info.restart_count if info else 0,
        }
    return {"servers": servers}


async def _clear_cache():
    """Clear enhancement cache for dashboard."""
    from router.audit import audit_event

    if enhancement_service:
        audit_event(
            event_type="admin_action",
            action="clear",
            resource_type="cache",
            resource_name="enhancement_cache",
            status="initiated"
        )
        try:
            await enhancement_service.clear_cache()
            audit_event(
                event_type="admin_action",
                action="clear",
                resource_type="cache",
                resource_name="enhancement_cache",
                status="success"
            )
        except Exception as e:
            audit_event(
                event_type="admin_action",
                action="clear",
                resource_type="cache",
                resource_name="enhancement_cache",
                status="failed",
                error=str(e)
            )
            raise


async def _restart_server(name: str):
    """Restart a server for dashboard."""
    if not supervisor:
        raise ValueError("Supervisor not initialized")

    audit_admin_action(action="restart", server_name=name, status="initiated")

    try:
        await supervisor.restart_server(name)
        audit_admin_action(action="restart", server_name=name, status="success")
    except Exception as e:
        audit_admin_action(action="restart", server_name=name, status="failed", error=str(e))
        raise


async def _start_server(name: str):
    """Start a server for dashboard."""
    if not supervisor:
        raise ValueError("Supervisor not initialized")

    audit_admin_action(action="start", server_name=name, status="initiated")

    try:
        await supervisor.start_server(name)
        audit_admin_action(action="start", server_name=name, status="success")
    except Exception as e:
        audit_admin_action(action="start", server_name=name, status="failed", error=str(e))
        raise


async def _stop_server(name: str):
    """Stop a server for dashboard."""
    if not supervisor:
        raise ValueError("Supervisor not initialized")

    audit_admin_action(action="stop", server_name=name, status="initiated")

    try:
        await supervisor.stop_server(name)
        audit_admin_action(action="stop", server_name=name, status="success")
    except Exception as e:
        audit_admin_action(action="stop", server_name=name, status="failed", error=str(e))
        raise


def _get_circuit_breakers():
    """Get circuit breaker states for dashboard."""
    if circuit_breakers:
        return circuit_breakers.get_all_stats()
    return {}


# Register dashboard router
dashboard_router = create_dashboard_router(
    get_health=_get_health,
    get_stats=_get_stats,
    get_servers=_get_servers,
    clear_cache=_clear_cache,
    restart_server=_restart_server,
    start_server=_start_server,
    stop_server=_stop_server,
    get_circuit_breakers=_get_circuit_breakers,
)
app.include_router(dashboard_router)


# Register OpenAI-compatible proxy router (uses getter callables like dashboard)
_openai_settings = get_settings()
_openai_api_key_manager = ApiKeyManager(config_path=_openai_settings.api_keys_config)
_openai_api_key_manager.load()

openai_compat_router = create_openai_compat_router(
    enhancement_service=lambda: enhancement_service,
    circuit_breakers=lambda: circuit_breakers,
    api_key_manager=_openai_api_key_manager,
    ollama_base_url=f"http://{_openai_settings.ollama_host}:{_openai_settings.ollama_port}/v1",
    ollama_timeout=float(_openai_settings.ollama_timeout),
)
app.include_router(openai_compat_router)


# =============================================================================
# Health Endpoints
# =============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint - returns status of all services."""
    server_summary = supervisor.get_status_summary() if supervisor else {}

    # Check Ollama status
    ollama_status = "unknown"
    if enhancement_service:
        stats = await enhancement_service.get_stats()
        ollama_status = "up" if stats.get("ollama_healthy") else "down"

    # Get cache stats
    cache_stats = {}
    if enhancement_service:
        stats = await enhancement_service.get_stats()
        cache_stats = stats.get("cache", {})

    return {
        "status": "healthy",
        "services": {
            "router": "up",
            "ollama": ollama_status,
            "cache": {
                "status": "up",
                "hit_rate": cache_stats.get("hits", 0)
                / max(1, cache_stats.get("hits", 0) + cache_stats.get("misses", 0)),
                "size": cache_stats.get("size", 0),
            },
        },
        "servers": server_summary,
    }


@app.get("/health/{server}")
async def server_health(server: str):
    """Health check for a specific MCP server."""
    if not registry:
        raise HTTPException(503, "Server registry not initialized")

    state = registry.get_state(server)
    if not state:
        raise HTTPException(404, f"Server {server} not found")

    # Get circuit breaker stats for this server
    cb_stats = None
    if circuit_breakers:
        breaker = circuit_breakers.get(server)
        cb_stats = breaker.stats.model_dump()

    return {
        "server": server,
        "status": state.process.status.value,
        "pid": state.process.pid,
        "restart_count": state.process.restart_count,
        "last_error": state.process.last_error,
        "circuit_breaker": cb_stats,
        "config": {
            "package": state.config.package,
            "transport": state.config.transport.value,
            "auto_start": state.config.auto_start,
        },
    }


# =============================================================================
# Server Management Endpoints
# =============================================================================


@app.get("/servers")
async def list_servers():
    """List all configured MCP servers with their status."""
    if not registry:
        raise HTTPException(503, "Server registry not initialized")

    states = registry.list_all()
    return {
        "servers": [
            {
                "name": state.config.name,
                "package": state.config.package,
                "transport": state.config.transport.value,
                "status": state.process.status.value,
                "pid": state.process.pid,
                "auto_start": state.config.auto_start,
                "restart_count": state.process.restart_count,
                "description": state.config.description,
            }
            for state in states
        ]
    }


@app.get("/servers/{name}")
async def get_server(name: str):
    """Get detailed information about a specific server."""
    if not registry:
        raise HTTPException(503, "Server registry not initialized")

    state = registry.get_state(name)
    if not state:
        raise HTTPException(404, f"Server {name} not found")

    return {
        "name": state.config.name,
        "config": state.config.model_dump(),
        "process": state.process.model_dump(),
    }


@app.post("/servers/{name}/start")
async def start_server(name: str):
    """Start a stopped server."""
    if not supervisor:
        raise HTTPException(503, "Supervisor not initialized")

    config = registry.get(name) if registry else None
    if not config:
        raise HTTPException(404, f"Server {name} not found")

    info = registry.get_process_info(name) if registry else None
    if info and info.status == ServerStatus.RUNNING:
        raise HTTPException(400, f"Server {name} is already running")

    try:
        await supervisor.start_server(name)
        # Reset circuit breaker on manual start
        if circuit_breakers:
            circuit_breakers.reset(name)
        return {"message": f"Server {name} started", "status": "running"}
    except Exception as e:
        logger.error(f"Failed to start {name}: {e}")
        raise HTTPException(500, f"Failed to start server: {e}")


@app.post("/servers/{name}/stop")
async def stop_server(name: str):
    """Stop a running server."""
    if not supervisor:
        raise HTTPException(503, "Supervisor not initialized")

    config = registry.get(name) if registry else None
    if not config:
        raise HTTPException(404, f"Server {name} not found")

    info = registry.get_process_info(name) if registry else None
    if not info or info.status != ServerStatus.RUNNING:
        raise HTTPException(400, f"Server {name} is not running")

    try:
        await supervisor.stop_server(name)
        return {"message": f"Server {name} stopped", "status": "stopped"}
    except Exception as e:
        logger.error(f"Failed to stop {name}: {e}")
        raise HTTPException(500, f"Failed to stop server: {e}")


@app.post("/servers/{name}/restart")
async def restart_server(name: str):
    """Restart a server."""
    if not supervisor:
        raise HTTPException(503, "Supervisor not initialized")

    config = registry.get(name) if registry else None
    if not config:
        raise HTTPException(404, f"Server {name} not found")

    try:
        await supervisor.restart_server(name)
        # Reset circuit breaker on restart
        if circuit_breakers:
            circuit_breakers.reset(name)
        return {"message": f"Server {name} restarted", "status": "running"}
    except Exception as e:
        logger.error(f"Failed to restart {name}: {e}")
        raise HTTPException(500, f"Failed to restart server: {e}")


class InstallServerRequest(BaseModel):
    """Request body for installing a new MCP server."""

    package: str
    name: str | None = None
    auto_start: bool = False
    description: str = ""


@app.post("/servers/install")
async def install_server(request: InstallServerRequest):
    """Install and configure a new MCP server."""
    if not registry:
        raise HTTPException(503, "Server registry not initialized")

    # Generate name from package if not provided
    name = request.name or request.package.split("/")[-1].replace("@", "").replace(
        "-mcp", ""
    )

    # Check if already exists
    if registry.get(name):
        raise HTTPException(400, f"Server {name} already exists")

    # Create config
    config = ServerConfig(
        name=name,
        package=request.package,
        transport=ServerTransport.STDIO,
        command="npx",
        args=["-y", request.package],
        auto_start=request.auto_start,
        description=request.description,
    )

    try:
        registry.add(config)
        return {
            "message": f"Server {name} installed",
            "name": name,
            "package": request.package,
        }
    except Exception as e:
        logger.error(f"Failed to install {name}: {e}")
        raise HTTPException(500, f"Failed to install server: {e}")


@app.delete("/servers/{name}")
async def remove_server(name: str):
    """Remove a server configuration."""
    if not registry:
        raise HTTPException(503, "Server registry not initialized")

    config = registry.get(name)
    if not config:
        raise HTTPException(404, f"Server {name} not found")

    info = registry.get_process_info(name)
    if info and info.status == ServerStatus.RUNNING:
        raise HTTPException(400, f"Cannot remove running server {name}, stop it first")

    try:
        registry.remove(name)
        return {"message": f"Server {name} removed"}
    except Exception as e:
        logger.error(f"Failed to remove {name}: {e}")
        raise HTTPException(500, f"Failed to remove server: {e}")


# =============================================================================
# MCP Proxy Endpoints
# =============================================================================


@app.post("/mcp/{server}/{path:path}")
async def mcp_proxy(server: str, path: str, request: Request):
    """
    Proxy JSON-RPC requests to MCP servers.

    This endpoint forwards JSON-RPC calls to MCP servers via stdio bridges,
    with configurable timeouts and circuit breaker protection.

    Args:
        server: Target MCP server name (e.g., "context7")
        path: MCP endpoint path (e.g., "tools/call")

    Returns:
        JSON-RPC response with metadata including timeout and elapsed time.

    Timeout Behavior:
        - Request timeout: 60s (via RequestTimeoutMiddleware)
        - MCP bridge timeout: 30s (per request)
        - If bridge timeout exceeded: returns JSON-RPC error with code -32603

    Response Metadata:
        - timeout_used: Configured timeout in seconds (30.0)
        - elapsed_ms: Actual request processing time in milliseconds
    """
    if not supervisor or not registry or not circuit_breakers:
        raise HTTPException(503, "Services not initialized")

    # Configure bridge timeout (30 seconds is the standard MCP timeout)
    bridge_timeout = 30.0

    # Record request start time for elapsed time calculation
    start_time = time.time()

    # Get server config
    config = registry.get(server)
    if not config:
        raise HTTPException(404, f"Server {server} not found")

    # Check circuit breaker before attempting connection
    # This prevents cascading failures by failing fast when server is known unhealthy
    breaker = circuit_breakers.get(server)
    try:
        breaker.check()
    except CircuitBreakerError as e:
        # Circuit is OPEN - return JSON-RPC error immediately without hitting the server
        # Client can use retry_after to know when to try again
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Server {server} circuit breaker open",
                "data": {"retry_after": e.retry_after},
            },
            "id": None,
        }

    # Check server status - if not running, try auto-start if configured
    info = registry.get_process_info(server)
    if not info or info.status != ServerStatus.RUNNING:
        # Auto-start is a convenience feature for on-demand MCP servers
        # This allows clients to call servers without manually starting them first
        if config.auto_start:
            try:
                await supervisor.start_server(server)
            except Exception as e:
                # Record failure to prevent repeated auto-start attempts (circuit breaker)
                breaker.record_failure(e)
                raise HTTPException(503, f"Failed to auto-start server: {e}")
        else:
            # Server must be started manually via POST /servers/{name}/start
            raise HTTPException(503, f"Server {server} is not running")

    # Get the stdio bridge
    bridge = supervisor.get_bridge(server)
    if not bridge:
        raise HTTPException(503, f"No bridge available for server {server}")

    # Parse request body
    try:
        body = await request.json()
    except Exception:
        body = {}

    # Route the JSON-RPC request through the stdio bridge
    try:
        # Extract method from JSON-RPC body, fall back to path if not specified
        # This supports both: POST /mcp/server/tools/call with method in body
        # or POST /mcp/server/tools.call with method in path
        method = body.get("method", path.replace("/", "."))
        params = body.get("params", {})

        # Send request through stdio bridge (stdin/stdout communication)
        # with timeout protection
        response = await bridge.send(method, params, timeout=bridge_timeout)

        # Normalize the response to fix common schema issues from MCP servers
        # This prevents client validation warnings from malformed schemas
        response = normalize_mcp_response(response, method)

        # Record success to reset circuit breaker failure count
        # After success_threshold successes, circuit transitions HALF_OPEN → CLOSED
        breaker.record_success()

        # Add timeout metadata to response (for observability)
        # Clients can use this to understand performance characteristics
        if isinstance(response, dict):
            if "metadata" not in response:
                response["metadata"] = {}
            elapsed_ms = (time.time() - start_time) * 1000
            response["metadata"]["timeout_used"] = bridge_timeout
            response["metadata"]["elapsed_ms"] = round(elapsed_ms, 2)

        return response

    except Exception as e:
        # Record failure to potentially open circuit breaker after failure_threshold
        # This protects against cascading failures when MCP server is unhealthy
        breaker.record_failure(e)
        logger.error(f"MCP proxy error for {server}/{path}: {e}")

        # Return JSON-RPC error response (not HTTP error)
        # Clients expect JSON-RPC format even for failures
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e),
                "data": {
                    "timeout_used": bridge_timeout,
                    "elapsed_ms": round((time.time() - start_time) * 1000, 2),
                },
            },
            "id": body.get("id"),
        }


# =============================================================================
# Enhancement Endpoints
# =============================================================================


class EnhanceRequest(BaseModel):
    """Request body for prompt enhancement."""

    prompt: str
    bypass_cache: bool = False


@app.post("/ollama/enhance")
async def enhance_prompt(
    body: EnhanceRequest,
    x_client_name: str | None = Header(None, alias="X-Client-Name"),
):
    """
    Enhance a prompt via Ollama.

    Headers:
        X-Client-Name: Client identifier for rule selection

    Body:
        prompt: The prompt to enhance
        bypass_cache: Skip cache lookup (default: false)

    Returns:
        original: The original prompt
        enhanced: The enhanced prompt (or original if enhancement failed)
        model: The model used for enhancement
        cached: Whether the result came from cache
        error: Error message if enhancement failed
    """
    if not enhancement_service:
        raise HTTPException(503, "Enhancement service not initialized")

    result = await enhancement_service.enhance(
        prompt=body.prompt,
        client_name=x_client_name,
        bypass_cache=body.bypass_cache,
    )

    return {
        "original": result.original,
        "enhanced": result.enhanced,
        "model": result.model,
        "cached": result.cached,
        "was_enhanced": result.was_enhanced,
        "error": result.error,
    }


@app.get("/ollama/stats")
async def enhancement_stats():
    """Get enhancement service statistics."""
    if not enhancement_service:
        raise HTTPException(503, "Enhancement service not initialized")

    return await enhancement_service.get_stats()


@app.post("/ollama/reset")
async def reset_enhancement():
    """Reset enhancement service (clear cache and circuit breaker)."""
    if not enhancement_service:
        raise HTTPException(503, "Enhancement service not initialized")

    await enhancement_service.clear_cache()
    await enhancement_service.reset_circuit_breaker()

    return {"message": "Enhancement service reset"}


# =============================================================================
# Circuit Breaker Endpoints
# =============================================================================


@app.get("/circuit-breakers")
async def list_circuit_breakers():
    """Get all circuit breaker states."""
    if not circuit_breakers:
        raise HTTPException(503, "Circuit breakers not initialized")

    return circuit_breakers.get_all_stats()


@app.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(name: str):
    """Reset a specific circuit breaker."""
    if not circuit_breakers:
        raise HTTPException(503, "Circuit breakers not initialized")

    if circuit_breakers.reset(name):
        return {"message": f"Circuit breaker {name} reset"}
    raise HTTPException(404, f"Circuit breaker {name} not found")


# =============================================================================
# Audit & Activity Query Endpoints
# =============================================================================


@app.get("/audit/activity")
async def query_activity(
    method: str | None = None,
    status_min: int | None = None,
    status_max: int | None = None,
    client_id: str | None = None,
    request_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    Query activity log with filters.

    Query Parameters:
        method: Filter by HTTP method (GET, POST, etc.)
        status_min: Minimum status code
        status_max: Maximum status code
        client_id: Filter by client ID
        request_id: Filter by request ID
        limit: Maximum entries to return (default: 50, max: 1000)
        offset: Number of entries to skip for pagination (default: 0)

    Returns:
        {
            "total": <total count matching filters>,
            "limit": <limit used>,
            "offset": <offset used>,
            "entries": [<activity entries>]
        }
    """
    if not persistent_activity_log:
        raise HTTPException(503, "Activity log not initialized")

    # Limit cap
    limit = min(limit, 1000)

    # Get count and entries
    total = await persistent_activity_log.count(
        method=method,
        status_min=status_min,
        status_max=status_max,
        client_id=client_id,
    )

    entries = await persistent_activity_log.query(
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


@app.get("/audit/activity/stats")
async def activity_stats():
    """
    Get activity log statistics.

    Returns:
        {
            "total_entries": <total count>,
            "by_method": {<method>: <count>, ...},
            "by_status": {<status>: <count>, ...}
        }
    """
    if not persistent_activity_log:
        raise HTTPException(503, "Activity log not initialized")

    import aiosqlite

    stats = {
        "total_entries": await persistent_activity_log.count(),
        "by_method": {},
        "by_status": {},
    }

    # Get method distribution
    async with aiosqlite.connect(str(persistent_activity_log.db_path)) as db:
        cursor = await db.execute(
            "SELECT method, COUNT(*) as count FROM activity GROUP BY method ORDER BY count DESC"
        )
        rows = await cursor.fetchall()
        stats["by_method"] = {row[0]: row[1] for row in rows}

        # Get status distribution
        cursor = await db.execute(
            "SELECT status, COUNT(*) as count FROM activity GROUP BY status ORDER BY status"
        )
        rows = await cursor.fetchall()
        stats["by_status"] = {row[0]: row[1] for row in rows}

    return stats


@app.delete("/audit/activity")
async def clear_activity_log():
    """Clear all activity log entries."""
    if not persistent_activity_log:
        raise HTTPException(503, "Activity log not initialized")

    await persistent_activity_log.clear()

    from router.audit import audit_event
    audit_event(
        event_type="admin_action",
        action="clear",
        resource_type="activity_log",
        resource_name="persistent_activity",
        status="success",
    )

    return {"message": "Activity log cleared"}


@app.post("/audit/activity/cleanup")
async def cleanup_old_activity(days: int = 30):
    """
    Delete activity entries older than specified days.

    Query Parameters:
        days: Delete entries older than this many days (default: 30)

    Returns:
        {"deleted": <number of entries deleted>}
    """
    if not persistent_activity_log:
        raise HTTPException(503, "Activity log not initialized")

    if days < 1:
        raise HTTPException(400, "Days must be >= 1")

    deleted = await persistent_activity_log.cleanup_old_entries(days)

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


# =============================================================================
# Pipeline Endpoints
# =============================================================================


class DocumentationRequest(BaseModel):
    """Request body for documentation generation."""

    repo_path: str
    project_name: str
    vault_path: str | None = None
    include_structure: bool = True


@app.post("/pipelines/documentation")
async def run_documentation_pipeline(request: DocumentationRequest):
    """
    Generate documentation for a codebase.

    This pipeline:
    1. Creates a documentation prompt from the repo path
    2. Enhances it with Ollama (deepseek-r1)
    3. Optionally structures with Sequential Thinking
    4. Writes to Obsidian vault with Desktop Commander
    """
    if not documentation_pipeline:
        raise HTTPException(503, "Documentation pipeline not initialized")

    result = await documentation_pipeline.run(
        repo_path=request.repo_path,
        project_name=request.project_name,
        vault_path=request.vault_path,
        include_structure=request.include_structure,
    )

    return result.model_dump()


# =============================================================================
# Client Configuration Endpoints
# =============================================================================


@app.get("/configs/claude-desktop")
async def get_claude_desktop_config():
    """Generate Claude Desktop configuration for PromptHub."""
    settings = get_settings()
    return generate_claude_desktop_config(
        router_host="localhost",
        router_port=settings.port,
    )


@app.get("/configs/vscode")
async def get_vscode_config():
    """Generate VS Code MCP configuration for PromptHub."""
    settings = get_settings()
    return generate_vscode_config(
        router_host="localhost",
        router_port=settings.port,
    )


@app.get("/configs/vscode-tasks")
async def get_vscode_tasks():
    """Generate VS Code tasks.json for PromptHub pipelines."""
    settings = get_settings()
    return generate_vscode_tasks(
        router_host="localhost",
        router_port=settings.port,
    )


@app.get("/configs/raycast")
async def get_raycast_script():
    """Generate Raycast script for MCP queries."""
    from fastapi.responses import PlainTextResponse

    settings = get_settings()
    script = generate_raycast_script(
        router_host="localhost",
        router_port=settings.port,
    )
    return PlainTextResponse(content=script, media_type="text/plain")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "router.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


# =============================================================================
# Audit Integrity & Security Endpoints
# =============================================================================


@app.get("/audit/integrity/verify")
async def verify_audit_integrity():
    """
    Verify audit log integrity using checksums.

    Returns:
        {
            "valid": true/false,
            "message": "status message",
            "current_checksum": {...},
            "previous_checksum": {...}
        }
    """
    from router.audit_integrity import get_integrity_manager

    integrity_mgr = get_integrity_manager()

    try:
        is_valid, error_msg = integrity_mgr.verify_integrity()

        # Get current and previous checksums
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


@app.get("/audit/integrity/history")
async def get_integrity_history(limit: int = 10):
    """
    Get checksum history for audit log.

    Query Parameters:
        limit: Maximum number of records to return (default: 10)

    Returns:
        List of checksum records
    """
    from router.audit_integrity import get_integrity_manager

    integrity_mgr = get_integrity_manager()
    history = integrity_mgr.get_checksum_history(limit=limit)

    return {
        "total": len(history),
        "checksums": [c.model_dump() for c in history],
    }


@app.get("/security/alerts")
async def get_security_alerts(
    limit: int = 50,
    severity: str | None = None,
):
    """
    Get recent security alerts.

    Query Parameters:
        limit: Maximum alerts to return (default: 50)
        severity: Filter by severity (info, warning, critical)

    Returns:
        {
            "total": <total count>,
            "alerts": [<alert objects>]
        }
    """
    from router.security_alerts import AlertSeverity, get_alert_manager

    alert_mgr = get_alert_manager()

    # Parse severity
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


@app.get("/security/alerts/stats")
async def get_alert_stats():
    """
    Get security alert statistics.

    Returns:
        {
            "total_alerts": <count>,
            "by_severity": {<severity>: <count>},
            "by_type": {<type>: <count>}
        }
    """
    from router.security_alerts import get_alert_manager

    alert_mgr = get_alert_manager()
    return alert_mgr.get_alert_stats()
