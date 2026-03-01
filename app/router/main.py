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
from collections.abc import Callable, Coroutine
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from router.audit import audit_admin_action, setup_audit_logging
from router.orchestrator import OrchestratorAgent, get_orchestrator_agent
from router.config import get_settings
from router.dashboard import create_dashboard_router
from router.enhancement import EnhancementService, OllamaConfig
from router.memory import MemoryMCPClient, create_memory_router, get_session_storage
from router.middleware import (
    ActivityLoggingMiddleware,
    AuditContextMiddleware,
    RequestTimeoutMiddleware,
)
from router.openai_compat import create_openai_compat_router
from router.openai_compat.auth import ApiKeyManager
from router.pipelines import DocumentationPipeline
from router.resilience import CircuitBreakerRegistry
from router.servers import ServerRegistry, Supervisor
from router.servers.mcp_gateway import build_mcp_gateway

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global service instances (initialized in lifespan)
registry: ServerRegistry | None = None
supervisor: Supervisor | None = None
enhancement_service: EnhancementService | None = None
circuit_breakers: CircuitBreakerRegistry | None = None
documentation_pipeline: DocumentationPipeline | None = None
orchestrator_agent: OrchestratorAgent | None = None
persistent_activity_log = None  # Will be initialized in lifespan
session_storage = None  # Will be initialized in lifespan
memory_mcp_client = None  # Will be initialized in lifespan

# Gateway lifespan management — tracks the async cleanup for the current
# FastMCP gateway so we can tear it down and re-enter on topology changes.
_gateway_exit: Callable[[], Coroutine[Any, Any, None]] | None = None


async def _mount_gateway() -> None:
    """
    Mount (or remount) the MCP gateway with proper lifespan management.

    FastMCP's StreamableHTTPSessionManager requires its lifespan to be
    entered before it can handle requests. We manually enter the sub-app's
    lifespan and store a cleanup handle so _rebuild_gateway can tear down
    the old gateway and create a fresh one after topology changes.
    """
    global _gateway_exit

    # Cleanup previous gateway lifespan if remounting
    if _gateway_exit:
        try:
            await _gateway_exit()
        except Exception as e:
            logger.warning(f"Error closing previous gateway lifespan: {e}")
        _gateway_exit = None

    # Remove existing /mcp-direct mount
    app.router.routes = [
        r
        for r in app.router.routes
        if not (hasattr(r, "path") and r.path == "/mcp-direct")
    ]

    if not registry or not supervisor:
        logger.warning("Cannot mount gateway: services not initialized")
        return

    gateway = build_mcp_gateway(supervisor, registry)
    mcp_http_app = gateway.http_app(path="/mcp")

    # Enter the FastMCP lifespan (initializes StreamableHTTPSessionManager)
    ctx = mcp_http_app.lifespan(mcp_http_app)
    await ctx.__aenter__()

    async def _exit() -> None:
        await ctx.__aexit__(None, None, None)

    _gateway_exit = _exit

    app.mount("/mcp-direct", mcp_http_app)
    logger.info("Mounted MCP gateway at /mcp-direct/mcp (lifespan active)")


async def _rebuild_gateway() -> None:
    """
    Rebuild and remount the MCP gateway after topology changes.

    Called after install/delete operations to ensure the gateway reflects
    the current set of configured servers. Start/stop/restart do NOT need
    this because the dynamic client factory handles bridge changes.

    This tears down the old gateway's lifespan (StreamableHTTPSessionManager)
    and creates a fresh one with the updated server list.
    """
    await _mount_gateway()
    logger.info("Rebuilt MCP gateway after topology change")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    global registry, supervisor, enhancement_service, circuit_breakers, documentation_pipeline, orchestrator_agent, persistent_activity_log, session_storage, memory_mcp_client

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

    # Initialize session storage (memory system)
    session_storage = get_session_storage(db_path=log_dir / "memory.db")
    await session_storage.initialize()
    logger.info("Initialized session storage")

    # Initialize Memory MCP client (optional sync layer)
    memory_mcp_client = MemoryMCPClient(base_url="http://localhost:9090")
    logger.info("Initialized Memory MCP client")

    logger.info(f"Starting PromptHub Router on {settings.host}:{settings.port}")

    # Initialize server management
    registry = ServerRegistry(settings.mcp_servers_config)
    await registry.load_async()  # Use async file I/O

    supervisor = Supervisor(registry)

    # Start supervisor (will auto-start configured servers)
    await supervisor.start()

    # Mount FastMCP gateway for Streamable HTTP access
    # Clients can connect at /mcp-direct/mcp using standard MCP HTTP transport
    await _mount_gateway()

    # Initialize circuit breaker registry
    circuit_breakers = CircuitBreakerRegistry()

    # Initialize enhancement service with Ollama config from .env
    ollama_config = OllamaConfig(
        base_url=f"http://{settings.ollama_host}:{settings.ollama_port}",
        timeout=float(settings.ollama_timeout),
    )
    enhancement_service = EnhancementService(
        rules_path=settings.enhancement_rules_config,
        ollama_config=ollama_config,
        cache_max_size=500,
        cache_ttl=7200.0,
        cache_persistent=settings.cache_persistent,
        cache_db_path=settings.cache_db_path,
        openrouter_enabled=settings.openrouter_enabled,
        openrouter_api_key=settings.openrouter_api_key,
        openrouter_base_url=settings.openrouter_base_url,
        openrouter_timeout=float(settings.openrouter_timeout),
        openrouter_default_model=settings.openrouter_default_model,
        cloud_models_path="configs/cloud-models.json",
    )
    await enhancement_service.initialize()

    # Initialize documentation pipeline
    documentation_pipeline = DocumentationPipeline(
        enhancement_service=enhancement_service,
        supervisor=supervisor,
    )

    # Initialize orchestrator agent (qwen3:14b)
    # Uses same Ollama instance as enhancement — separate CircuitBreaker
    orchestrator_agent = get_orchestrator_agent(ollama_config)
    await orchestrator_agent.initialize()
    logger.info(f"Orchestrator agent initialized (model: qwen3:14b)")

    yield

    # Shutdown
    logger.info("Shutting down PromptHub Router")

    # Close gateway lifespan (stops StreamableHTTPSessionManager)
    if _gateway_exit:
        try:
            await _gateway_exit()
        except Exception as e:
            logger.warning(f"Error closing gateway lifespan: {e}")

    if enhancement_service:
        await enhancement_service.close()

    if orchestrator_agent:
        await orchestrator_agent.close()

    if supervisor:
        await supervisor.stop()


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


# Load API keys early so dashboard can display them
_openai_settings = get_settings()
_openai_api_key_manager = ApiKeyManager(config_path=_openai_settings.api_keys_config)
_openai_api_key_manager.load()


async def _get_ollama_info():
    """Get Ollama models and API client summary for dashboard."""
    import httpx

    models = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"http://{_openai_settings.ollama_host}:{_openai_settings.ollama_port}/v1/models"
            )
            if resp.status_code == 200:
                models = resp.json().get("data", [])
    except Exception:
        pass  # Ollama unreachable — models will be empty

    api_keys = [
        {"client_name": cfg.client_name, "enhance": cfg.enhance, "description": cfg.description}
        for cfg in _openai_api_key_manager._registry.keys.values()
    ]

    return {"models": models, "api_keys": api_keys}


async def _reload_api_keys():
    """Reload API keys from config for dashboard."""
    _openai_api_key_manager.reload()
    return _openai_api_key_manager.key_count


async def _get_memory_info():
    """Get session memory stats for dashboard."""
    if session_storage:
        stats = await session_storage.get_stats()
        recent_sessions, _ = await session_storage.list_sessions(limit=5)
        return {"stats": stats, "recent_sessions": recent_sessions}
    return {"stats": {}, "recent_sessions": []}


# =============================================================================
# Router Registration
# =============================================================================

# Dashboard router
dashboard_router = create_dashboard_router(
    get_health=_get_health,
    get_stats=_get_stats,
    get_servers=_get_servers,
    clear_cache=_clear_cache,
    restart_server=_restart_server,
    start_server=_start_server,
    stop_server=_stop_server,
    get_circuit_breakers=_get_circuit_breakers,
    get_ollama_info=_get_ollama_info,
    reload_api_keys=_reload_api_keys,
    get_memory_info=_get_memory_info,
)
app.include_router(dashboard_router)

# OpenAI-compatible proxy router (reuses api_key_manager loaded above)
openai_compat_router = create_openai_compat_router(
    enhancement_service=lambda: enhancement_service,
    circuit_breakers=lambda: circuit_breakers,
    api_key_manager=_openai_api_key_manager,
    ollama_base_url=f"http://{_openai_settings.ollama_host}:{_openai_settings.ollama_port}/v1",
    ollama_timeout=float(_openai_settings.ollama_timeout),
)
app.include_router(openai_compat_router)

# Memory router (session management)
memory_router = create_memory_router(
    get_storage=lambda: session_storage,
    get_mcp_client=lambda: memory_mcp_client,
    get_enhancement_service=lambda: enhancement_service,
)
app.include_router(memory_router)

# Extracted route modules
from router.routes.audit import create_audit_router
from router.routes.client_configs import create_client_configs_router
from router.routes.enhancement import create_enhancement_router
from router.routes.health import create_health_router
from router.routes.mcp_proxy import create_mcp_proxy_router
from router.routes.pipelines import create_pipelines_router
from router.routes.servers import create_servers_router

app.include_router(create_health_router(
    get_supervisor=lambda: supervisor,
    get_registry=lambda: registry,
    get_enhancement_service=lambda: enhancement_service,
    get_circuit_breakers=lambda: circuit_breakers,
))

app.include_router(create_servers_router(
    get_registry=lambda: registry,
    get_supervisor=lambda: supervisor,
    get_circuit_breakers=lambda: circuit_breakers,
    rebuild_gateway=_rebuild_gateway,
))

app.include_router(create_mcp_proxy_router(
    get_registry=lambda: registry,
    get_supervisor=lambda: supervisor,
    get_circuit_breakers=lambda: circuit_breakers,
))

app.include_router(create_enhancement_router(
    get_enhancement_service=lambda: enhancement_service,
    get_orchestrator_agent=lambda: orchestrator_agent,
))

app.include_router(create_audit_router(
    get_activity_log=lambda: persistent_activity_log,
))

app.include_router(create_pipelines_router(
    get_documentation_pipeline=lambda: documentation_pipeline,
))

app.include_router(create_client_configs_router())


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
