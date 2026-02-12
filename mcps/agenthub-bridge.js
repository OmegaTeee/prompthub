#!/usr/bin/env node

/**
 * AgentHub Unified MCP Bridge
 *
 * This MCP server acts as a bridge between Claude Desktop (stdio transport)
 * and AgentHub's HTTP endpoints, aggregating all 7 MCP servers into one
 * unified interface.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

const AGENTHUB_URL = process.env.AGENTHUB_URL || 'http://localhost:9090';
const CLIENT_NAME = process.env.CLIENT_NAME || 'claude-desktop';

// All 8 MCP servers available through AgentHub
const SERVERS = [
  'context7',
  'desktop-commander',
  'sequential-thinking',
  'memory',
  'deepseek-reasoner',
  'fetch',
  'obsidian',
  'duckduckgo'
];

/**
 * Make HTTP request to AgentHub
 */
async function callAgentHub(serverName, jsonRpcRequest) {
  const url = `${AGENTHUB_URL}/mcp/${serverName}/tools/call`;

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
  const allTools = [];

  for (const serverName of SERVERS) {
    try {
      const response = await callAgentHub(serverName, {
        jsonrpc: '2.0',
        method: 'tools/list',
        id: 1
      });

      if (response.result && response.result.tools) {
        // Prefix tool names with server name to avoid conflicts
        // Use underscore separator (MCP names can only contain: a-zA-Z0-9_-)
        const prefixedTools = response.result.tools.map(tool => ({
          ...tool,
          name: `${serverName}_${tool.name}`,
          description: `[${serverName}] ${tool.description}`
        }));

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
  const [serverName, actualToolName] = toolName.split('_', 2);

  if (!SERVERS.includes(serverName)) {
    throw new Error(`Unknown server: ${serverName}`);
  }

  const response = await callAgentHub(serverName, {
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
      name: 'agenthub',
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

  console.error('AgentHub MCP Bridge started');
  console.error(`Connected to: ${AGENTHUB_URL}`);
  console.error(`Client name: ${CLIENT_NAME}`);
  console.error(`Servers: ${SERVERS.join(', ')}`);
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
