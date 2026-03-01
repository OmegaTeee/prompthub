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

// Schema minification: strip verbose fields from tool inputSchemas to reduce context usage
// Set MINIFY_SCHEMAS=false to disable (enabled by default)
const MINIFY_SCHEMAS = process.env.MINIFY_SCHEMAS !== 'false';

// Max characters for tool descriptions (0 = no limit)
const DESC_MAX_LENGTH = parseInt(process.env.DESC_MAX_LENGTH || '200', 10);

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
    /** @type {any} */
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

  /** @type {any} */
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

// ---------------------------------------------------------------------------
// Schema minification — strip verbose fields to reduce LLM context usage
// Keeps: type, properties, required, enum, items, oneOf/anyOf/allOf, format,
//        additionalProperties, minimum/maximum, minLength/maxLength, pattern
// Strips: description, title, examples, default, $comment, $defs/definitions
// ---------------------------------------------------------------------------

/** Fields to preserve on every schema node */
const KEEP_FIELDS = new Set([
  'type', 'properties', 'required', 'enum', 'const',
  'items', 'oneOf', 'anyOf', 'allOf',
  'additionalProperties', 'format', 'pattern',
  'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
  'minLength', 'maxLength', 'minItems', 'maxItems',
]);

/**
 * Recursively strip noise from a JSON Schema object.
 * Returns a new object — does not mutate the original.
 */
function minifySchema(schema) {
  if (!schema || typeof schema !== 'object') return schema;
  if (Array.isArray(schema)) return schema.map(minifySchema);

  const out = {};
  for (const [key, value] of Object.entries(schema)) {
    if (!KEEP_FIELDS.has(key)) continue;

    if (key === 'properties' && typeof value === 'object') {
      out.properties = {};
      for (const [prop, propSchema] of Object.entries(value)) {
        out.properties[prop] = minifySchema(propSchema);
      }
    } else if (key === 'items') {
      out.items = minifySchema(value);
    } else if (key === 'additionalProperties' && typeof value === 'object') {
      out.additionalProperties = minifySchema(value);
    } else if (['oneOf', 'anyOf', 'allOf'].includes(key) && Array.isArray(value)) {
      out[key] = value.map(minifySchema);
    } else {
      out[key] = value;
    }
  }
  return out;
}

/**
 * Truncate a description string to DESC_MAX_LENGTH at a word boundary.
 */
function truncateDescription(desc) {
  if (!desc || !DESC_MAX_LENGTH || desc.length <= DESC_MAX_LENGTH) return desc;
  const cut = desc.lastIndexOf(' ', DESC_MAX_LENGTH);
  return desc.substring(0, cut > 0 ? cut : DESC_MAX_LENGTH) + '...';
}

/**
 * Rough byte size of a JSON-serialized object (for logging savings).
 */
function jsonSize(obj) {
  return JSON.stringify(obj).length;
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
        const rawTools = response.result.tools;

        // Prefix tool names with server name to avoid conflicts
        // Use underscore separator (MCP names can only contain: a-zA-Z0-9_-)
        const prefixedTools = rawTools
          .map(tool => {
            const mapped = {
              ...tool,
              name: `${serverName}_${tool.name}`,
              description: truncateDescription(`[${serverName}] ${tool.description}`),
            };
            if (MINIFY_SCHEMAS && mapped.inputSchema) {
              mapped.inputSchema = minifySchema(mapped.inputSchema);
            }
            return mapped;
          })
          .filter(tool => !EXCLUDE_TOOLS.has(tool.name));

        // Log per-server savings when minification is active
        if (MINIFY_SCHEMAS && prefixedTools.length > 0) {
          const rawSize = jsonSize(rawTools);
          const minSize = jsonSize(prefixedTools);
          const pct = rawSize > 0 ? Math.round((1 - minSize / rawSize) * 100) : 0;
          console.error(
            `[minify] ${serverName}: ${rawTools.length} tools, ${rawSize} → ${minSize} bytes (−${pct}%)`
          );
        }

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

// Graceful shutdown on pipe closure (Claude Desktop exit/reload)
// Without this, writing to a closed stdout crashes with EPIPE
process.stdout.on('error', () => process.exit(0));
process.stdin.on('end', () => process.exit(0));

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
  console.error(`Schema minification: ${MINIFY_SCHEMAS ? 'ON' : 'OFF'} (desc limit: ${DESC_MAX_LENGTH || 'none'})`);
  console.error(`Running servers: ${servers.join(', ') || '(none — router may not be running)'}`);
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
