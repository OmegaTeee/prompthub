"""
Stdio bridge for JSON-RPC communication with MCP servers.

This bridge:
- Sends JSON-RPC requests to server stdin
- Reads JSON-RPC responses from server stdout
- Handles concurrent requests with request ID matching
- Uses newline-delimited JSON (NDJSON) framing
"""

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class StdioBridgeError(Exception):
    """Error in stdio bridge communication."""

    pass


class StdioBridge:
    """
    Bridges HTTP JSON-RPC to stdio JSON-RPC.

    MCP servers communicate via stdio using newline-delimited JSON.
    This bridge manages the async read/write and request/response matching.
    """

    def __init__(self, process: asyncio.subprocess.Process, name: str = "unknown"):
        """
        Initialize the bridge.

        Args:
            process: The subprocess to communicate with
            name: Server name for logging
        """
        self.process = process
        self.name = name
        self._request_id = 0
        self._pending: dict[int | str, asyncio.Future[dict]] = {}
        self._lock = asyncio.Lock()
        self._reader_task: asyncio.Task | None = None
        self._closed = False

    async def start(self) -> None:
        """Start the background reader task."""
        if self._reader_task is not None:
            return

        self._reader_task = asyncio.create_task(self._read_loop())
        logger.debug(f"Started stdio bridge reader for {self.name}")

    async def close(self) -> None:
        """Close the bridge and cancel pending requests."""
        self._closed = True

        # Cancel reader task
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        # Cancel pending requests
        for future in self._pending.values():
            if not future.done():
                future.cancel()
        self._pending.clear()

        logger.debug(f"Closed stdio bridge for {self.name}")

    async def send(
        self,
        method: str,
        params: dict | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """
        Send a JSON-RPC request and wait for response.

        Args:
            method: JSON-RPC method name
            params: Method parameters
            timeout: Timeout in seconds

        Returns:
            JSON-RPC response dict

        Raises:
            StdioBridgeError: On communication failure
            asyncio.TimeoutError: If response not received in time
        """
        if self._closed:
            raise StdioBridgeError("Bridge is closed")

        if self.process.stdin is None:
            raise StdioBridgeError("Process stdin not available")

        # Ensure reader is running
        await self.start()

        # Generate request ID
        async with self._lock:
            self._request_id += 1
            request_id = self._request_id

        # Build JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            request["params"] = params

        # Create future for response
        future: asyncio.Future[dict] = asyncio.Future()
        self._pending[request_id] = future

        try:
            # Send request (newline-delimited JSON)
            request_bytes = json.dumps(request).encode("utf-8") + b"\n"
            self.process.stdin.write(request_bytes)
            await self.process.stdin.drain()

            logger.debug(f"[{self.name}] Sent: {method} (id={request_id})")

            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            return response

        except TimeoutError:
            logger.warning(f"[{self.name}] Timeout waiting for response to {method}")
            raise
        except Exception as e:
            logger.error(f"[{self.name}] Error sending request: {e}")
            raise StdioBridgeError(f"Failed to send request: {e}") from e
        finally:
            # Clean up pending request
            self._pending.pop(request_id, None)

    async def send_notification(self, method: str, params: dict | None = None) -> None:
        """
        Send a JSON-RPC notification (no response expected).

        Args:
            method: JSON-RPC method name
            params: Method parameters
        """
        if self._closed:
            raise StdioBridgeError("Bridge is closed")

        if self.process.stdin is None:
            raise StdioBridgeError("Process stdin not available")

        # Build notification (no id field)
        notification = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params is not None:
            notification["params"] = params

        # Send notification
        notification_bytes = json.dumps(notification).encode("utf-8") + b"\n"
        self.process.stdin.write(notification_bytes)
        await self.process.stdin.drain()

        logger.debug(f"[{self.name}] Sent notification: {method}")

    async def _read_loop(self) -> None:
        """Background task to read responses from stdout."""
        if self.process.stdout is None:
            logger.error(f"[{self.name}] Process stdout not available")
            return

        try:
            while not self._closed:
                # Read line from stdout
                line = await self.process.stdout.readline()

                if not line:
                    # EOF - process probably died
                    if not self._closed:
                        logger.warning(f"[{self.name}] EOF on stdout, process may have died")
                    break

                # Parse JSON
                try:
                    line_str = line.decode("utf-8").strip()
                    if not line_str:
                        continue

                    response = json.loads(line_str)
                    logger.debug(f"[{self.name}] Received: {response}")

                    # Match response to request
                    response_id = response.get("id")
                    if response_id is not None and response_id in self._pending:
                        future = self._pending[response_id]
                        if not future.done():
                            future.set_result(response)
                    else:
                        # Notification or unknown response
                        logger.debug(
                            f"[{self.name}] Received notification or unmatched response"
                        )

                except json.JSONDecodeError as e:
                    logger.warning(f"[{self.name}] Invalid JSON from server: {e}")
                except Exception as e:
                    logger.error(f"[{self.name}] Error processing response: {e}")

        except asyncio.CancelledError:
            logger.debug(f"[{self.name}] Reader task cancelled")
            raise
        except Exception as e:
            logger.error(f"[{self.name}] Reader loop error: {e}")

    async def initialize(self) -> dict:
        """
        Send MCP initialize request.

        This should be called after starting the bridge to initialize
        the MCP protocol handshake.

        Returns:
            Server capabilities
        """
        response = await self.send(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "agenthub-router",
                    "version": "0.1.0",
                },
            },
        )

        if "error" in response:
            raise StdioBridgeError(f"Initialize failed: {response['error']}")

        # Send initialized notification
        await self.send_notification("notifications/initialized")

        return response.get("result", {})

    async def list_tools(self) -> list[dict]:
        """List available tools from the MCP server."""
        response = await self.send("tools/list", {})
        if "error" in response:
            raise StdioBridgeError(f"tools/list failed: {response['error']}")
        return response.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """
        Call a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        response = await self.send(
            "tools/call",
            {"name": name, "arguments": arguments},
        )
        if "error" in response:
            raise StdioBridgeError(f"tools/call failed: {response['error']}")
        return response.get("result", {})
