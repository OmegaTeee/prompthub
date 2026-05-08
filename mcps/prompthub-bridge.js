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

// Tool prefix aliases: rename server prefixes in tool names to avoid redundancy
// Built-in defaults fix known double-prefix issues (e.g., perplexity-comet_comet_ask → perplexity_ask)
// Override or extend via env var TOOL_PREFIX_ALIASES="server:displayPrefix:stripFromTool,..."
const TOOL_PREFIX_ALIASES = new Map([
  ['perplexity-comet', { displayPrefix: 'perplexity', stripPrefix: 'comet_' }],
]);
const TOOL_REVERSE_MAP = new Map([
  ['perplexity', { serverName: 'perplexity-comet', stripPrefix: 'comet_' }],
]);
if (process.env.TOOL_PREFIX_ALIASES) {
  for (const entry of process.env.TOOL_PREFIX_ALIASES.split(',').map(s => s.trim()).filter(Boolean)) {
    const [serverName, displayPrefix, stripPrefix = ''] = entry.split(':');
    if (serverName && displayPrefix) {
      TOOL_PREFIX_ALIASES.set(serverName, { displayPrefix, stripPrefix });
      TOOL_REVERSE_MAP.set(displayPrefix, { serverName, stripPrefix });
    }
  }
}

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
// Bridge meta-tools — agent-initiated server start
// ---------------------------------------------------------------------------
// These two tools are owned by the bridge itself, not proxied to a backend
// server. They let agents discover and start on-demand MCP servers
// (e.g. obsidian, chrome-devtools-mcp, browsermcp) whose tools are
// otherwise invisible until the server is running.
// ---------------------------------------------------------------------------

const META_TOOL_NAMES = new Set([
  'prompthub_list_available_servers',
  'prompthub_start_server',
]);

const META_TOOLS = [
  {
    name: 'prompthub_list_available_servers',
    description:
      'List every MCP server configured in the PromptHub router, including running, stopped, and failed servers. Use this to discover on-demand servers (which do not auto-start) before calling prompthub_start_server.',
    inputSchema: {
      type: 'object',
      properties: {},
      additionalProperties: false,
    },
  },
  {
    name: 'prompthub_start_server',
    description:
      'Start a configured but stopped MCP server (auto_start=false servers like obsidian, chrome-devtools-mcp, browsermcp). Waits until the server reaches "running" status, then signals tools/list_changed so the client refreshes its tool list. Use prompthub_list_available_servers first to see which servers exist.',
    inputSchema: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          description: 'Server name as listed by prompthub_list_available_servers (e.g., "obsidian", "browsermcp").',
        },
      },
      required: ['name'],
      additionalProperties: false,
    },
  },
];

/**
 * Fetch every configured server (running, stopped, failed) from the router.
 * Unlike fetchRunningServers(), this returns the full status payload.
 */
async function listAvailableServers() {
  const response = await fetch(`${PROMPTHUB_URL}/servers`, {
    headers: { 'X-Client-Name': CLIENT_NAME },
  });
  if (!response.ok) {
    throw new Error(`GET /servers failed: HTTP ${response.status}`);
  }
  return await response.json();
}

/**
 * Start a server via the router and wait for it to reach "running" status.
 * Returns once running, or throws on failure / timeout (15 s).
 */
async function startServerViaRouter(name) {
  if (!name || typeof name !== 'string') {
    throw new Error('Missing required argument: name (string)');
  }

  const startResp = await fetch(
    `${PROMPTHUB_URL}/servers/${encodeURIComponent(name)}/start`,
    {
      method: 'POST',
      headers: { 'X-Client-Name': CLIENT_NAME },
    }
  );
  /** @type {any} */
  const startData = await startResp.json().catch(() => ({}));
  if (!startResp.ok) {
    const detail = startData.detail || `HTTP ${startResp.status}`;
    throw new Error(`POST /servers/${name}/start failed: ${detail}`);
  }

  // Poll /servers until the target reaches "running" or "failed" (or timeout).
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    const allResp = await fetch(`${PROMPTHUB_URL}/servers`, {
      headers: { 'X-Client-Name': CLIENT_NAME },
    });
    /** @type {any} */
    const allData = await allResp.json();
    const found = allData.servers?.find(s => s.name === name);
    if (found?.status === 'running') {
      // Refresh cached list so the next tools/list call surfaces the new tools.
      await fetchRunningServers();
      return { name, status: 'running', start_response: startData };
    }
    if (found?.status === 'failed') {
      throw new Error(`Server '${name}' transitioned to 'failed' during start`);
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  throw new Error(`Timeout: '${name}' did not reach 'running' status within 15 s`);
}

/**
 * Dispatch a meta-tool call. Returns the raw result; the request handler
 * wraps it in MCP content blocks. mcpServer is the active Server instance
 * (used for sending tools/list_changed notifications post-start).
 */
async function handleMetaTool(name, args, mcpServer) {
  if (name === 'prompthub_list_available_servers') {
    return await listAvailableServers();
  }
  if (name === 'prompthub_start_server') {
    const result = await startServerViaRouter(args?.name);
    // Notify client to refresh tools/list. Some clients (Claude Desktop,
    // Cherry Studio, VS Code) may ignore this until they implement
    // tools/list_changed; failure is non-fatal.
    try {
      await mcpServer.notification({ method: 'notifications/tools/list_changed' });
      result.notification_sent = true;
    } catch (err) {
      result.notification_sent = false;
      result.notification_error = err.message;
      console.error(`tools/list_changed notification failed: ${err.message}`);
    }
    return result;
  }
  throw new Error(`Unknown meta-tool: ${name}`);
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

        // Prefix tool names with server name (or alias) to avoid conflicts
        // Use underscore separator (MCP names can only contain: a-zA-Z0-9_-)
        const alias = TOOL_PREFIX_ALIASES.get(serverName);
        const displayPrefix = alias ? alias.displayPrefix : serverName;
        const stripPrefix = alias ? alias.stripPrefix : '';

        const prefixedTools = rawTools
          .map(tool => {
            // Strip redundant prefix from tool name if alias says so
            const toolName = stripPrefix && tool.name.startsWith(stripPrefix)
              ? tool.name.substring(stripPrefix.length)
              : tool.name;
            const mapped = {
              ...tool,
              name: `${displayPrefix}_${toolName}`,
              description: truncateDescription(`[${displayPrefix}] ${tool.description}`),
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

  // Always append bridge-owned meta-tools so agents can discover and start
  // on-demand servers even when no backend servers are running.
  return [...allTools, ...META_TOOLS];
}

/**
 * Call a tool on the appropriate server
 */
async function callTool(toolName, args) {
  // Tool name format: "prefix_tool-name"
  // Split on first underscore only — tool names may contain underscores
  // (e.g., "desktop-commander_create_directory")
  const idx = toolName.indexOf('_');
  if (idx === -1) {
    throw new Error(`Invalid tool name format: ${toolName} (expected "prefix_tool")`);
  }
  const prefix = toolName.substring(0, idx);
  let actualToolName = toolName.substring(idx + 1);

  // Reverse alias lookup: if the prefix is an alias, resolve to real server name
  // and restore the stripped tool-name prefix
  const reverseAlias = TOOL_REVERSE_MAP.get(prefix);
  const serverName = reverseAlias ? reverseAlias.serverName : prefix;
  if (reverseAlias && reverseAlias.stripPrefix) {
    actualToolName = `${reverseAlias.stripPrefix}${actualToolName}`;
  }

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
      const result = META_TOOL_NAMES.has(name)
        ? await handleMetaTool(name, args || {}, server)
        : await callTool(name, args || {});

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
  if (TOOL_PREFIX_ALIASES.size > 0) {
    const aliasDesc = [...TOOL_PREFIX_ALIASES.entries()]
      .map(([srv, { displayPrefix, stripPrefix }]) =>
        `${srv} → ${displayPrefix}${stripPrefix ? ` (strip: ${stripPrefix})` : ''}`)
      .join(', ');
    console.error(`Tool aliases: ${aliasDesc}`);
  }
  console.error(`Running servers: ${servers.join(', ') || '(none — router may not be running)'}`);
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
