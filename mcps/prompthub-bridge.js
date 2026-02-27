#!/usr/bin/env node

/**
 * PromptHub Unified MCP Bridge
 *
 * This MCP server acts as a bridge between MCP clients (stdio transport)
 * and PromptHub's HTTP endpoints, dynamically aggregating all running
 * MCP servers into one unified interface.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
// import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

// Explicit IPv4 to avoid DNS resolution, IPv6 issues, and ensure consistency
// across different platforms (especially Windows and containerized environments)
const PROMPTHUB_URL = process.env.PROMPTHUB_URL || 'http://127.0.0.1:9090';
const CLIENT_NAME = process.env.CLIENT_NAME || 'claude-desktop';

// Optional: comma-separated list of servers to expose (empty = all running)
const SERVERS_FILTER = process.env.SERVERS
  ? process.env.SERVERS.split(',').map(s => s.trim()).filter(Boolean)
  : [];

// Optional: comma-separated prefixed tool names to exclude
// e.g., "desktop-commander_get_config,desktop-commander_give_feedback_to_desktop_commander"
const EXCLUDE_TOOLS = new Set(
  process.env.EXCLUDE_TOOLS
    ? process.env.EXCLUDE_TOOLS.split(',').map(s => s.trim()).filter(Boolean)
    : []
);

// Cache of running server names (refreshed on each tools/list call)
let cachedServers = [];

/**
 * Fetch the list of running servers from the router
 */
async function fetchRunningServers() {
  try {
    const response = await fetch(`${PROMPTHUB_URL}/servers`, {
      headers: { 'X-Client-Name': CLIENT_NAME }
    });
    const data = await response.json();

    if (data.servers) {
      cachedServers = data.servers
        .filter(s => s.status === 'running')
        .map(s => s.name)
        .filter(name => SERVERS_FILTER.length === 0 || SERVERS_FILTER.includes(name));
    }
  } catch (error) {
    console.error('Failed to fetch server list from router:', error.message);
    // Keep using cached list if router is temporarily unreachable
  }

  return cachedServers;
}

/**
 * Make HTTP request to PromptHub
 */
async function callPromptHub(serverName, jsonRpcRequest) {
  const url = `${PROMPTHUB_URL}/mcp/${serverName}/tools/call`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Client-Name': CLIENT_NAME
    },
    body: JSON.stringify(jsonRpcRequest)
  });

  const data = await response.json();

  // Handle FastAPI error responses
  if (data.detail) {
    return {
      jsonrpc: '2.0',
      error: {
        code: -32001,
        message: data.detail
      },
      id: jsonRpcRequest.id
    };
  }

  return data;
}

/**
 * Fetch tools from all servers
 */
async function getAllTools() {
  const servers = await fetchRunningServers();
  const allTools = [];

  for (const serverName of servers) {
    try {
      const response = await callPromptHub(serverName, {
        jsonrpc: '2.0',
        method: 'tools/list',
        id: 1
      });

      if (response.result && response.result.tools) {
        // Prefix tool names with server name to avoid conflicts
        // Use underscore separator (MCP names can only contain: a-zA-Z0-9_-)
        const prefixedTools = response.result.tools
          .map(tool => ({
            ...tool,
            name: `${serverName}_${tool.name}`,
            description: `[${serverName}] ${tool.description}`
          }))
          .filter(tool => !EXCLUDE_TOOLS.has(tool.name));

        allTools.push(...prefixedTools);
      }
    } catch (error) {
      console.error(`Failed to fetch tools from ${serverName}:`, error.message);
    }
  }

  return allTools;
}

/**
 * Call a tool on the appropriate server
 */
async function callTool(toolName, args) {
  // Tool name format: "server-name_tool-name"
  // Split on first underscore only — tool names may contain underscores
  // (e.g., "desktop-commander_create_directory")
  const idx = toolName.indexOf('_');
  if (idx === -1) {
    throw new Error(`Invalid tool name format: ${toolName} (expected "server_tool")`);
  }
  const serverName = toolName.substring(0, idx);
  const actualToolName = toolName.substring(idx + 1);

  if (cachedServers.length > 0 && !cachedServers.includes(serverName)) {
    throw new Error(`Unknown or stopped server: ${serverName}`);
  }

  const response = await callPromptHub(serverName, {
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: actualToolName,
      arguments: args
    },
    id: 1
  });

  if (response.error) {
    throw new Error(response.error.message);
  }

  return response.result;
}

/**
 * Create and start the MCP server
 */
async function main() {
  const server = new Server(
    {
      name: 'prompthub',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Handle tools/list requests
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    const tools = await getAllTools();
    return { tools };
  });

  // Handle tools/call requests
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      const result = await callTool(name, args || {});

      return {
        content: [
          {
            type: 'text',
            text: typeof result === 'string' ? result : JSON.stringify(result, null, 2)
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error: ${error.message}`
          }
        ],
        isError: true
      };
    }
  });

  // Start stdio transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Fetch initial server list
  const servers = await fetchRunningServers();

  console.error('PromptHub MCP Bridge started');
  console.error(`Connected to: ${PROMPTHUB_URL}`);
  console.error(`Client name: ${CLIENT_NAME}`);
  console.error(`Running servers: ${servers.join(', ') || '(none — router may not be running)'}`);
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
