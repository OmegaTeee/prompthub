"""MCP JSON-RPC proxy endpoint."""

import logging
import time
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from router.resilience import CircuitBreakerError
from router.servers import ServerStatus

logger = logging.getLogger(__name__)


def normalize_tool_schema(schema: dict) -> dict:
    """
    Normalize tool input schemas to ensure they're valid JSON Schema.

    Some MCP servers return malformed schemas (e.g., missing 'properties' field).
    This function fixes common issues to prevent client validation warnings.
    """
    if not isinstance(schema, dict):
        return schema

    if schema.get("type") == "object" and "properties" not in schema:
        schema = schema.copy()
        schema["properties"] = {}

    return schema


def normalize_mcp_response(response: dict, method: str) -> dict:
    """
    Normalize MCP JSON-RPC responses to fix common schema issues.
    """
    if method != "tools/list" and method != "tools.list":
        return response

    if not isinstance(response, dict):
        return response

    result = response.get("result")
    if not result or not isinstance(result, dict):
        return response

    tools = result.get("tools")
    if not tools or not isinstance(tools, list):
        return response

    normalized_tools = []
    for tool in tools:
        if isinstance(tool, dict) and "inputSchema" in tool:
            tool = tool.copy()
            tool["inputSchema"] = normalize_tool_schema(tool["inputSchema"])
        normalized_tools.append(tool)

    response = response.copy()
    result = result.copy()
    result["tools"] = normalized_tools
    response["result"] = result

    return response


def create_mcp_proxy_router(
    get_registry: Callable[[], Any],
    get_supervisor: Callable[[], Any],
    get_circuit_breakers: Callable[[], Any],
    get_tool_registry: Callable[[], Any] | None = None,
) -> APIRouter:
    router = APIRouter(tags=["mcp"])

    @router.post("/mcp/{server}/{path:path}")
    async def mcp_proxy(server: str, path: str, request: Request):
        """
        Proxy JSON-RPC requests to MCP servers.

        Forwards JSON-RPC calls to MCP servers via stdio bridges,
        with configurable timeouts and circuit breaker protection.
        """
        sup = get_supervisor()
        reg = get_registry()
        cbs = get_circuit_breakers()
        if not sup or not reg or not cbs:
            raise HTTPException(503, "Services not initialized")

        bridge_timeout = 30.0
        start_time = time.time()

        config = reg.get(server)
        if not config:
            raise HTTPException(404, f"Server {server} not found")

        breaker = cbs.get(server)
        try:
            breaker.check()
        except CircuitBreakerError as e:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Server {server} circuit breaker open",
                    "data": {"retry_after": e.retry_after},
                },
                "id": None,
            }

        info = reg.get_process_info(server)
        if not info or info.status != ServerStatus.RUNNING:
            if config.auto_start:
                try:
                    await sup.start_server(server)
                except Exception as e:
                    breaker.record_failure(e)
                    raise HTTPException(503, f"Failed to auto-start server: {e}")
            else:
                raise HTTPException(503, f"Server {server} is not running")

        bridge = sup.get_bridge(server)
        if not bridge:
            raise HTTPException(503, f"No bridge available for server {server}")

        try:
            body = await request.json()
        except Exception:
            body = {}

        try:
            method = body.get("method", path.replace("/", "."))
            params = body.get("params", {})

            # Cache-through for tools/list: serve from registry if cached
            is_tools_list = method in ("tools/list", "tools.list")
            tool_reg = get_tool_registry() if get_tool_registry else None

            if is_tools_list and tool_reg:
                cached_tools = await tool_reg.get_cached_tools(server)
                if cached_tools is not None:
                    elapsed_ms = (time.time() - start_time) * 1000
                    logger.debug("Tool cache hit for %s (%d tools)", server, len(cached_tools))
                    return {
                        "jsonrpc": "2.0",
                        "result": {"tools": cached_tools},
                        "id": body.get("id"),
                        "metadata": {
                            "cache": "hit",
                            "timeout_used": bridge_timeout,
                            "elapsed_ms": round(elapsed_ms, 2),
                        },
                    }

            response = await bridge.send(method, params, timeout=bridge_timeout)
            response = normalize_mcp_response(response, method)

            breaker.record_success()

            # Cache tools/list responses after successful fetch
            if is_tools_list and tool_reg and isinstance(response, dict):
                result = response.get("result")
                if isinstance(result, dict):
                    tools = result.get("tools")
                    if isinstance(tools, list):
                        try:
                            await tool_reg.cache_tools(server, tools)
                        except Exception as cache_err:
                            logger.warning("Failed to cache tools for %s: %s", server, cache_err)

            if isinstance(response, dict):
                if "metadata" not in response:
                    response["metadata"] = {}
                elapsed_ms = (time.time() - start_time) * 1000
                response["metadata"]["cache"] = "miss"
                response["metadata"]["timeout_used"] = bridge_timeout
                response["metadata"]["elapsed_ms"] = round(elapsed_ms, 2)

            return response

        except Exception as e:
            breaker.record_failure(e)
            logger.error(f"MCP proxy error for {server}/{path}: {e}")

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

    return router
