"""
Dashboard Router.

Provides endpoints for the HTMX-powered dashboard:
- Main dashboard page
- Health status partial
- Stats partial
- Activity partial
- Quick actions (clear cache, restart servers)
"""

import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import markdown2
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from router.config import get_settings
from router.enhancement.context_window import TokenBudget
from router.middleware import activity_log

logger = logging.getLogger(__name__)

# Templates directory
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


def create_dashboard_router(
    get_health: Callable[[], Any],
    get_stats: Callable[[], Any],
    get_servers: Callable[[], Any],
    clear_cache: Callable[[], Any],
    restart_server: Callable[[str], Any],
    start_server: Callable[[str], Any],
    stop_server: Callable[[str], Any],
    get_circuit_breakers: Callable[[], dict[str, Any]],
    get_ollama_info: Callable[[], Any] | None = None,
    reload_api_keys: Callable[[], Any] | None = None,
    get_memory_info: Callable[[], Any] | None = None,
    get_tool_registry_info: Callable[[], Any] | None = None,
    get_open_webui_info: Callable[[], Any] | None = None,
) -> APIRouter:
    """
    Create the dashboard router with injected dependencies.

    Args:
        get_health: Function to get overall health status
        get_stats: Function to get enhancement stats
        get_servers: Function to get server statuses
        clear_cache: Function to clear the enhancement cache
        restart_server: Function to restart a server by name
        start_server: Function to start a server by name
        stop_server: Function to stop a server by name
        get_circuit_breakers: Function to get circuit breaker states
        get_ollama_info: Function to get Ollama models and API keys summary
        reload_api_keys: Function to reload API keys from config
        get_memory_info: Function to get session memory stats
        get_tool_registry_info: Function to get tool registry stats
        get_open_webui_info: Function to get Open WebUI connection status

    Returns:
        Configured APIRouter for dashboard endpoints
    """
    router = APIRouter(prefix="/dashboard", tags=["dashboard"])
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    @router.get("", response_class=HTMLResponse)
    async def dashboard(request: Request):
        """Main dashboard page."""
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "title": "PromptHub Dashboard",
            },
        )

    @router.get("/health-partial", response_class=HTMLResponse)
    async def health_partial(request: Request):
        """HTMX partial: Service health status."""
        # Get server statuses
        servers_data = await get_servers()
        servers = []

        for name, info in servers_data.get("servers", {}).items():
            status = info.get("status", "unknown")
            status_class = "healthy" if status == "running" else "down"
            servers.append(
                {
                    "name": name,
                    "status": status,
                    "status_class": status_class,
                    "pid": info.get("pid"),
                }
            )

        # Get circuit breaker states
        breakers_data = get_circuit_breakers()
        circuit_breakers = []

        for name, stats in breakers_data.items():
            circuit_breakers.append(
                {
                    "name": name,
                    "state": stats.state.value if hasattr(stats.state, 'value') else str(stats.state),
                    "failures": stats.failure_count,
                    "last_failure": stats.last_failure_time,
                }
            )

        return templates.TemplateResponse(
            request,
            "partials/health.html",
            {
                "services": servers,
                "circuit_breakers": circuit_breakers,
            },
        )

    @router.get("/stats-partial", response_class=HTMLResponse)
    async def stats_partial(request: Request):
        """HTMX partial: Enhancement cache stats."""
        stats = await get_stats()
        cache_stats = stats.get("cache", {})
        circuit_breaker = stats.get("circuit_breaker", {})

        # Calculate hit rate
        hits = cache_stats.get("hits", 0)
        misses = cache_stats.get("misses", 0)
        total = hits + misses
        hit_rate = hits / total if total > 0 else 0

        return templates.TemplateResponse(
            request,
            "partials/stats.html",
            {
                "cache_stats": {
                    "hits": hits,
                    "misses": misses,
                    "hit_rate": hit_rate,
                    "total_cached": cache_stats.get("size", 0),
                    "max_size": cache_stats.get("max_size", 0),
                },
                "ollama_healthy": stats.get("ollama_healthy", False),
                "circuit_breaker": circuit_breaker,
            },
        )

    @router.get("/activity-partial", response_class=HTMLResponse)
    async def activity_partial(request: Request):
        """HTMX partial: Recent request activity."""
        activity = activity_log.get_recent(limit=50)
        return templates.TemplateResponse(
            request,
            "partials/activity.html",
            {
                "activity": activity,
            },
        )

    @router.get("/guides-partial", response_class=HTMLResponse)
    async def guides_partial(request: Request):
        """HTMX partial: User guides list."""
        # Get guides directory (at workspace root, outside app/)
        settings = get_settings()
        guides_dir = Path(settings.workspace_root) / "guides"

        if not guides_dir.exists():
            return templates.TemplateResponse(
                request,
                "partials/guides.html",
                {
                    "guides": [],
                },
            )

        # Read index.md to get descriptions (if available)
        descriptions = {}
        index_file = guides_dir / "index.md"
        if index_file.exists():
            # Parse index.md for descriptions
            # Simple parsing: look for lines like "- `filename.md` — Description"
            content = index_file.read_text()
            for line in content.split('\n'):
                if line.strip().startswith('-') and '.md' in line:
                    # Extract filename and description
                    parts = line.split('—') if '—' in line else line.split('-', 1)
                    if len(parts) >= 2:
                        # Get filename from first part (look for .md)
                        filename_match = re.search(r'([a-z0-9_-]+\.md)', parts[0], re.IGNORECASE)
                        if filename_match:
                            filename = filename_match.group(1)
                            desc = parts[1].strip()
                            descriptions[filename] = desc

        # Scan for .md files
        guides = []
        for md_file in sorted(guides_dir.glob("*.md")):
            # Get file stats
            stat = md_file.stat()
            size_kb = int(stat.st_size / 1024)

            # Extract title from first H1 or use filename
            title = md_file.stem.replace('-', ' ').replace('_', ' ').title()
            try:
                content = md_file.read_text(encoding='utf-8')
                # Look for first H1 (# Title)
                for line in content.split('\n'):
                    if line.startswith('# '):
                        title = line[2:].strip()
                        break
            except Exception:
                pass  # Use default title from filename

            guides.append({
                "filename": md_file.name,
                "title": title,
                "description": descriptions.get(md_file.name, ""),
                "size_kb": size_kb,
            })

        # Sort: index.md first, then alphabetically
        guides.sort(key=lambda g: (g["filename"] != "index.md", g["title"].lower()))

        return templates.TemplateResponse(
            request,
            "partials/guides.html",
            {
                "guides": guides,
            },
        )

    @router.get("/guides/view/{filename}", response_class=HTMLResponse)
    async def guide_view(request: Request, filename: str):
        """View a specific guide with rendered markdown."""
        # Validate filename (security: prevent path traversal)
        if not re.match(r'^[a-zA-Z0-9_-]+\.md$', filename):
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid filename format"}
            )

        # Get guides directory (at workspace root, outside app/)
        settings = get_settings()
        guides_dir = Path(settings.workspace_root) / "guides"
        guide_file = guides_dir / filename

        # Ensure file exists and is within guides directory
        try:
            guide_file = guide_file.resolve()
            guides_dir = guides_dir.resolve()

            if not str(guide_file).startswith(str(guides_dir)):
                return JSONResponse(
                    status_code=403,
                    content={"error": "Access denied"}
                )

            if not guide_file.exists() or not guide_file.is_file():
                return JSONResponse(
                    status_code=404,
                    content={"error": "Guide not found"}
                )
        except Exception:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid file path"}
            )

        # Read and render markdown
        try:
            content = guide_file.read_text(encoding='utf-8')

            # Extract title from first H1 or use filename
            title = filename.replace('-', ' ').replace('_', ' ').replace('.md', '').title()
            for line in content.split('\n'):
                if line.startswith('# '):
                    title = line[2:].strip()
                    break

            # Render markdown to HTML
            html_content = markdown2.markdown(
                content,
                extras=[
                    "fenced-code-blocks",
                    "tables",
                    "header-ids",
                    "task_list",
                ]
            )

            return templates.TemplateResponse(
                request,
                "partials/guide-view.html",
                {
                    "title": title,
                    "content": html_content,
                },
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to render guide: {str(e)}"}
            )

    async def _validate_server_name(server: str) -> tuple[bool, str | None]:
        """
        Validate server name format and existence.

        Args:
            server: Server name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check format (alphanumeric, hyphens, underscores only)
        if not re.match(r"^[a-z0-9_-]+$", server):
            return False, "Invalid server name format"

        # Check if server exists in registry
        servers_data = await get_servers()
        if server not in servers_data.get("servers", {}):
            return False, f"Server '{server}' not found"

        return True, None

    @router.post("/actions/clear-cache")
    async def clear_cache_action():
        """Clear the enhancement cache."""
        await clear_cache()
        return {"status": "success", "message": "Cache cleared"}

    @router.post("/actions/restart/{server}")
    async def restart_server_action(server: str):
        """Restart an MCP server."""
        # Validate server name
        is_valid, error_msg = await _validate_server_name(server)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": error_msg}
            )

        try:
            await restart_server(server)
            return {"status": "success", "message": f"{server} restarted"}
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

    @router.post("/actions/start/{server}")
    async def start_server_action(server: str):
        """Start an MCP server."""
        # Validate server name
        is_valid, error_msg = await _validate_server_name(server)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": error_msg}
            )

        try:
            await start_server(server)
            return {"status": "success", "message": f"{server} started"}
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

    @router.post("/actions/stop/{server}")
    async def stop_server_action(server: str):
        """Stop an MCP server."""
        # Validate server name
        is_valid, error_msg = await _validate_server_name(server)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": error_msg}
            )

        try:
            await stop_server(server)
            return {"status": "success", "message": f"{server} stopped"}
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

    @router.get("/ollama-partial", response_class=HTMLResponse)
    async def ollama_partial(request: Request):
        """HTMX partial: Ollama models and API clients."""
        if not get_ollama_info:
            return HTMLResponse("<p class='text-muted'>Ollama panel not configured</p>")

        info = await get_ollama_info()
        return templates.TemplateResponse(
            request,
            "partials/ollama.html",
            {
                "models": info.get("models", []),
                "api_keys": info.get("api_keys", []),
            },
        )

    @router.post("/actions/reload-api-keys")
    async def reload_api_keys_action():
        """Reload API keys from config file."""
        if not reload_api_keys:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "API key reload not configured"}
            )
        try:
            result = await reload_api_keys()
            return {"status": "success", "message": f"API keys reloaded ({result} keys)"}
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

    @router.get("/memory-partial", response_class=HTMLResponse)
    async def memory_partial(request: Request):
        """HTMX partial: Session memory stats."""
        if not get_memory_info:
            return templates.TemplateResponse(
                request,
                "partials/memory.html",
                {
                    "stats": {},
                    "recent_sessions": [],
                },
            )

        try:
            info = await get_memory_info()
            stats = info.get("stats", {})
            recent_sessions = info.get("recent_sessions", [])

            return templates.TemplateResponse(
                request,
                "partials/memory.html",
                {
                    "stats": stats,
                    "recent_sessions": recent_sessions,
                },
            )
        except Exception as e:
            logger.warning(f"Error loading memory info: {e}")
            return templates.TemplateResponse(
                request,
                "partials/memory.html",
                {
                    "stats": {},
                    "recent_sessions": [],
                    "error": str(e),
                },
            )

    @router.get("/tool-registry-partial", response_class=HTMLResponse)
    async def tool_registry_partial(request: Request):
        """HTMX partial: Tool registry cache stats."""
        if not get_tool_registry_info:
            return templates.TemplateResponse(
                request,
                "partials/tool-registry.html",
                {"stats": {}, "snapshots": []},
            )

        try:
            info = await get_tool_registry_info()
            return templates.TemplateResponse(
                request,
                "partials/tool-registry.html",
                {
                    "stats": info.get("stats", {}),
                    "snapshots": info.get("snapshots", []),
                },
            )
        except Exception as e:
            logger.warning("Error loading tool registry info: %s", e)
            return templates.TemplateResponse(
                request,
                "partials/tool-registry.html",
                {"stats": {}, "snapshots": [], "error": str(e)},
            )

    @router.get("/open-webui-partial", response_class=HTMLResponse)
    async def open_webui_partial(request: Request):
        """HTMX partial: Open WebUI connection status."""
        if not get_open_webui_info:
            return templates.TemplateResponse(
                request,
                "partials/open-webui.html",
                {
                    "status": "down",
                    "api_base_url": "",
                    "mcp_endpoint": "",
                    "port": 3000,
                    "recent_activity": 0,
                },
            )

        try:
            info = await get_open_webui_info()
            return templates.TemplateResponse(
                request,
                "partials/open-webui.html",
                {
                    "status": info.get("status", "down"),
                    "api_base_url": info.get("api_base_url", ""),
                    "mcp_endpoint": info.get("mcp_endpoint", ""),
                    "port": info.get("port", 3000),
                    "recent_activity": info.get("recent_activity", 0),
                },
            )
        except Exception as e:
            logger.warning("Error loading Open WebUI info: %s", e)
            return templates.TemplateResponse(
                request,
                "partials/open-webui.html",
                {
                    "status": "down",
                    "api_base_url": "",
                    "mcp_endpoint": "",
                    "port": 3000,
                    "recent_activity": 0,
                    "error": str(e),
                },
            )

    @router.get("/token-budget-partial", response_class=HTMLResponse)
    async def token_budget_partial(request: Request):
        """HTMX partial: Token budget per client model."""
        import json
        from pathlib import Path

        settings = get_settings()
        rules_path = (
            Path(settings.workspace_root) / "app" / settings.enhancement_rules_config
        )

        rows = []
        try:
            data = json.loads(rules_path.read_text())
            default_rule = data.get("default", {})
            clients = data.get("clients", {})

            # Merge default into each client rule (same logic as service.py)
            merged_clients = {"default": default_rule}
            for name, rule in clients.items():
                merged = {**default_rule, **rule}
                merged_clients[name] = merged

            for client_name, rule in merged_clients.items():
                model = rule.get("model", "unknown")
                max_tokens = rule.get("max_tokens") or 500
                system_prompt = rule.get("system_prompt", "")
                enabled = rule.get("enabled", True)

                budget = TokenBudget(
                    model=model,
                    max_response_tokens=max_tokens,
                    system_prompt=system_prompt,
                )
                s = budget.summary()
                rows.append(
                    {
                        "client": client_name,
                        "model": model,
                        "enabled": enabled,
                        "context_k": s["context_limit_tokens"] // 1024,
                        "available_tokens": s["available_for_input_tokens"],
                        "available_chars": s["available_for_input_chars"],
                        "system_tokens": s["system_prompt_tokens"],
                        "max_response_tokens": s["max_response_tokens"],
                        "cap": s["enhancement_input_cap"],
                    }
                )
        except Exception as e:
            logger.warning(f"Error computing token budgets: {e}")

        return templates.TemplateResponse(
            request,
            "partials/token-budget.html",
            {"rows": rows},
        )

    return router
