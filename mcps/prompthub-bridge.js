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
import { formatToolCallResult } from './bridge-result.js';

// Explicit IPv4 to avoid DNS resolution, IPv6 issues, and ensure consistency
// across different platforms (especially Windows and containerized environments)
const PROMPTHUB_URL = process.env.PROMPTHUB_URL || 'http://127.0.0.1:9090';
const CLIENT_NAME = process.env.CLIENT_NAME || 'claude-desktop';

// Progressive tool disclosure.
//   TOOL_DISCLOSURE=full        (default): return tools for every running server
//   TOOL_DISCLOSURE=progressive          : return only tier-1 + explicitly loaded
//                                          servers + meta-tools
//   TIER1_SERVERS=a,b,c                  : comma-separated server names seeded
//                                          into the active set on startup
//
// Precedence: explicit env vars > router /clients/{name}/tool-profile > default
// "full". When BOTH env vars are unset, the bridge fetches the per-client
// profile from the router at startup (Phase 2). Setting either env var pins
// the bridge to env-driven config and skips the router fetch — useful for
// debugging or running the bridge against a profile-less router.
const TOOL_DISCLOSURE_ENV = process.env.TOOL_DISCLOSURE;
const TIER1_SERVERS_ENV = process.env.TIER1_SERVERS;

// `let` (not `const`) so misconfiguration can be re-normalized to '' below,
// AND so the startup router-profile fetch (below in main()) can override
// these when the operator hasn't pinned them via env.
const VALID_DISCLOSURE_MODES = new Set(['full', 'progressive']);
let toolDisclosure = (TOOL_DISCLOSURE_ENV || '').toLowerCase().trim();
if (toolDisclosure && !VALID_DISCLOSURE_MODES.has(toolDisclosure)) {
  console.error(
    `[bridge] Invalid TOOL_DISCLOSURE='${TOOL_DISCLOSURE_ENV}'. ` +
    `Expected 'full' or 'progressive'. Falling back to 'full'.`
  );
  toolDisclosure = '';
}
let tier1Servers = TIER1_SERVERS_ENV
  ? TIER1_SERVERS_ENV.split(',').map(s => s.trim()).filter(Boolean)
  : [];

// Per-session tool disclosure state — reset on bridge restart / client reconnect.
// Holds server names whose tools are currently included in tools/list.
const activeServers = new Set(tier1Servers);

function resetActiveServers(nextTier1) {
  activeServers.clear();
  for (const name of nextTier1) activeServers.add(name);
}

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
// Built-in defaults fix known double-prefix issues (e.g., perplexity-comet_comet_ask → comet_ask)
// Override or extend via env var TOOL_PREFIX_ALIASES="server:displayPrefix:stripFromTool,..."
// Comet (the local browser) is the actual surface these tools control; "perplexity"
// is the parent brand. Keeping the display prefix as "comet" reflects what the tools
// do (drive a Comet browser via CDP) rather than what brand owns the back end.
const TOOL_PREFIX_ALIASES = new Map([
  ['perplexity-comet', { displayPrefix: 'comet', stripPrefix: 'comet_' }],
]);
const TOOL_REVERSE_MAP = new Map([
  ['comet', { serverName: 'perplexity-comet', stripPrefix: 'comet_' }],
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

/**
 * Fetch the per-client tool profile from the router (Phase 2 plumbing).
 * Returns `null` on any error so the caller can silently fall back to
 * `full` disclosure — a router that is down, missing the endpoint, or
 * returning garbage must never prevent the bridge from starting.
 */
async function fetchToolProfileFromRouter() {
  try {
    const response = await fetch(
      `${PROMPTHUB_URL}/clients/${encodeURIComponent(CLIENT_NAME)}/tool-profile`,
      { headers: { 'X-Client-Name': CLIENT_NAME } }
    );
    if (!response.ok) return null;
    const data = await response.json();
    if (!data || typeof data !== 'object') return null;
    return data;
  } catch (error) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Bridge meta-tools — owned by the bridge, not proxied to a backend server
// ---------------------------------------------------------------------------
// Two responsibilities:
//   1. Server discovery and on-demand start
//      (prompthub_list_available_servers, prompthub_start_server) —
//      surfaces on-demand servers like chrome-devtools-mcp
//      whose tools are invisible until the server is running.
//   2. Cross-session memory search (prompthub_memory_search) —
//      lets chat models consult prior facts/blocks before reaching for
//      browser tools; routes to the FastAPI POST /sessions/search endpoint.
// ---------------------------------------------------------------------------

const META_TOOL_NAMES = new Set([
  'prompthub_list_available_servers',
  'prompthub_start_server',
  'prompthub_memory_search',
  'discover_tools',
  'load_server_tools',
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
      'Start a configured but stopped MCP server (currently chrome-devtools-mcp). Waits until the server reaches "running" status, then signals tools/list_changed so the client refreshes its tool list. Use prompthub_list_available_servers first to see which servers exist.',
    inputSchema: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          description: 'Server name as listed by prompthub_list_available_servers (for example, "chrome-devtools-mcp").',
        },
      },
      required: ['name'],
      additionalProperties: false,
    },
  },
  {
    name: 'prompthub_memory_search',
    description:
      'Search prior conversation context (facts and memory blocks across every session for this client) before reaching for browser tools like comet_ask. Use this when the user references earlier work, past decisions, repo plans, or architecture context that may have been discussed before. Returns ranked results (BM25); higher score = more relevant. If results are empty or low-confidence, then escalate to comet_ask or other research tools.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search expression. Plain words work; advanced FTS5 syntax (prefix*, AND/OR, "phrase") is also accepted.',
        },
        limit: {
          type: 'integer',
          minimum: 1,
          maximum: 100,
          description: 'Max combined results across facts and memory blocks (1-100). Default 10.',
        },
        cross_client: {
          type: 'boolean',
          description: 'Search every session regardless of owning client. Use ONLY when the user explicitly asks to search across all clients/identities; the default (false) keeps results scoped to the current client and preserves the privacy boundary.',
        },
      },
      required: ['query'],
      additionalProperties: false,
    },
  },
  {
    name: 'discover_tools',
    description:
      'Discover available tools without loading full schemas. Returns a lightweight catalog (server, tool name, one-line description) across running servers. Use this to decide which server to load before calling load_server_tools. Especially useful when TOOL_DISCLOSURE=progressive hides most tools by default.',
    inputSchema: {
      type: 'object',
      properties: {
        server: {
          type: 'string',
          description: 'Optional server name filter (router server name, e.g. "memory", "desktop-commander").',
        },
        query: {
          type: 'string',
          description: 'Optional substring query to filter tool names/descriptions (case-insensitive).',
        },
      },
      additionalProperties: false,
    },
  },
  {
    name: 'load_server_tools',
    description:
      'Promote a server into the active tool set (progressive disclosure). After loading, the bridge emits notifications/tools/list_changed so the client refreshes tools/list and the LLM can call the new tools. No-op effect in TOOL_DISCLOSURE=full mode since all running servers are already active.',
    inputSchema: {
      type: 'object',
      properties: {
        server: {
          type: 'string',
          description: 'Server name to load (router server name, e.g. "memory", "desktop-commander").',
        },
      },
      required: ['server'],
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
 * Search session memory (facts + blocks) via the router's
 * POST /sessions/search endpoint. The router scopes results to the
 * caller's client_id automatically (via the audit context populated
 * from X-Client-ID), so cross-tenant data is invisible without an
 * explicit cross_client flag.
 *
 * NOTE: Two headers are sent because they serve different layers:
 *   - X-Client-Name: enhancement-rule lookup (which client's rule to apply)
 *   - X-Client-ID:   audit-context client_id (which sessions to search)
 * Both carry CLIENT_NAME because the bridge represents one identity to
 * the router. The audit layer reads X-Client-ID; without it the
 * default is "anonymous" and the search returns no rows for sessions
 * owned by the caller.
 */
async function searchMemoryViaRouter(args) {
  if (!args?.query || typeof args.query !== 'string') {
    throw new Error('Missing required argument: query (string)');
  }

  // Coerce + clamp limit to match the API model bounds (1..100). The
  // router would 422 on an out-of-range value; doing it here gives the
  // chat model a clean experience regardless of input shape (negative,
  // fractional, oversized, missing).
  let limit = 10;
  if (args.limit !== undefined && args.limit !== null) {
    const parsed = Math.floor(Number(args.limit));
    if (Number.isFinite(parsed)) {
      limit = Math.max(1, Math.min(parsed, 100));
    }
  }

  const body = { query: args.query, limit };
  if (args.cross_client === true) {
    body.cross_client = true;
  }

  const response = await fetch(`${PROMPTHUB_URL}/sessions/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Client-Name': CLIENT_NAME,
      'X-Client-ID': CLIENT_NAME,
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(`POST /sessions/search failed: HTTP ${response.status}${text ? ` — ${text}` : ''}`);
  }
  return await response.json();
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
  if (name === 'prompthub_memory_search') {
    return await searchMemoryViaRouter(args);
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
  if (name === 'discover_tools') {
    return await discoverTools(args || {});
  }
  if (name === 'load_server_tools') {
    const serverName = args?.server;
    if (!serverName || typeof serverName !== 'string') {
      throw new Error('Missing required argument: server (string)');
    }

    // Short-circuit in full mode: every running server's tools are already
    // visible, so loading anything is a no-op. Returning here avoids a
    // misleading `loaded: true` response *and* a wasteful
    // tools/list_changed refresh in clients that act on it.
    if ((toolDisclosure || 'full') !== 'progressive') {
      return {
        server: serverName,
        loaded: false,
        disclosure: 'full',
        note: 'load_server_tools is a no-op in full disclosure mode; ' +
              'all running servers are already active.',
      };
    }

    // Validate the server is actually running so the caller gets a clear
    // error instead of a silent no-op tools/list_changed. The check is
    // deliberately fresh (not cached) so a server that stopped between
    // discover_tools and load_server_tools is caught.
    const running = await fetchRunningServers();
    if (!running.includes(serverName)) {
      throw new Error(`Unknown or stopped server: ${serverName}`);
    }

    // Ordering: mutate active set before sending the notification so the
    // client's next tools/list reflects the new server. A tools/list that
    // races *between* the activeServers.add and the notification still sees
    // the new server; the notification just prompts an extra refresh.
    activeServers.add(serverName);
    const result = {
      server: serverName,
      loaded: true,
      disclosure: toolDisclosure || 'full',
      active_servers: [...activeServers].sort(),
    };

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
 * Fetch tools from the specified servers (already filtered to running ones).
 * Returns a list with the bridge-owned META_TOOLS appended.
 */
async function getToolsForServers(servers) {
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
 * Lightweight catalog of tools (server, tool name, description) across
 * running servers. Does NOT return schemas — agents use this to decide
 * which server to load via load_server_tools.
 *
 * Goes through callPromptHub, which POSTs to /mcp/{server}/tools/call
 * with JSON-RPC `method: "tools/list"` (the router multiplexes all
 * JSON-RPC methods through the `/tools/call` endpoint). Same path used
 * by getToolsForServers, so the router's tool_registry cache-through
 * (24h TTL) absorbs repeated calls.
 */
async function discoverTools(args) {
  const running = await fetchRunningServers();
  const serverFilter = args?.server && typeof args.server === 'string' ? args.server.trim() : '';
  const query = args?.query && typeof args.query === 'string' ? args.query.toLowerCase().trim() : '';

  const servers = serverFilter
    ? running.filter(s => s === serverFilter)
    : running;

  if (serverFilter && servers.length === 0) {
    throw new Error(`Unknown or stopped server: ${serverFilter}`);
  }

  /** @type {{server: string, tool: string, description: string}[]} */
  const catalog = [];

  for (const serverName of servers) {
    try {
      const response = await callPromptHub(serverName, {
        jsonrpc: '2.0',
        method: 'tools/list',
        id: 1,
      });

      if (response.result && response.result.tools) {
        const rawTools = response.result.tools;
        const alias = TOOL_PREFIX_ALIASES.get(serverName);
        const displayPrefix = alias ? alias.displayPrefix : serverName;
        const stripPrefix = alias ? alias.stripPrefix : '';

        for (const tool of rawTools) {
          const toolName = stripPrefix && tool.name.startsWith(stripPrefix)
            ? tool.name.substring(stripPrefix.length)
            : tool.name;
          const fullName = `${displayPrefix}_${toolName}`;
          if (EXCLUDE_TOOLS.has(fullName)) continue;

          const description = truncateDescription(
            `[${displayPrefix}] ${tool.description || ''}`.trim()
          ) || `[${displayPrefix}]`;

          const row = { server: serverName, tool: fullName, description };
          if (query) {
            const haystack = `${row.tool} ${row.description}`.toLowerCase();
            if (!haystack.includes(query)) continue;
          }
          catalog.push(row);
        }
      }
    } catch (error) {
      console.error(`Failed to fetch tools from ${serverName}:`, error.message);
    }
  }

  return { servers, tool_count: catalog.length, tools: catalog };
}

/**
 * Effective tools/list payload, gated by TOOL_DISCLOSURE.
 *   full         : every running server's tools + META_TOOLS
 *   progressive  : only tier-1 + explicitly loaded servers + META_TOOLS
 */
async function getEffectiveToolsList() {
  const running = await fetchRunningServers();

  if ((toolDisclosure || 'full') !== 'progressive') {
    return await getToolsForServers(running);
  }

  // Progressive: only tier-1 + explicitly loaded servers (intersected with
  // running so a stopped tier-1 entry doesn't surface stale tools).
  const allowed = [...activeServers].filter(name => running.includes(name));
  return await getToolsForServers(allowed);
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
    const tools = await getEffectiveToolsList();
    return { tools };
  });

  // Handle tools/call requests
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      const result = META_TOOL_NAMES.has(name)
        ? await handleMetaTool(name, args || {}, server)
        : await callTool(name, args || {});

      return formatToolCallResult(result);
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

  // ---------------------------------------------------------------------
  // Resolve startup config BEFORE binding stdio. If we connected the
  // transport first, an MCP client that sends `tools/list` immediately
  // after `initialize` could race the router-profile fetch and receive
  // the env-default tool list (typically `full` mode) instead of the
  // resolved progressive profile. By blocking on config resolution
  // here, the first request handler invocation is guaranteed to see
  // the final state.
  // ---------------------------------------------------------------------

  // Fetch initial server list (populates cachedServers used by load_server_tools).
  const servers = await fetchRunningServers();

  // Router-profile fallback. Skipped when the operator has pinned either
  // env var, so explicit env wins over router config (predictable, easy
  // to debug). Failure here is silent — the bridge falls back to env-driven
  // "full" mode, which is the safe default.
  let profileSource = 'env';
  if (!TOOL_DISCLOSURE_ENV && !TIER1_SERVERS_ENV) {
    const profile = await fetchToolProfileFromRouter();
    if (profile && typeof profile.disclosure === 'string') {
      toolDisclosure = profile.disclosure.toLowerCase().trim();
      profileSource = 'router';
    }
    if (profile && Array.isArray(profile.tier1_servers)) {
      // .trim() matches env-var parsing — stray whitespace from hand-edited
      // config would otherwise break running-server matching downstream.
      tier1Servers = profile.tier1_servers
        .map(s => String(s).trim())
        .filter(Boolean);
      resetActiveServers(tier1Servers);
      profileSource = 'router';
    }
  }

  // Validate the resolved TIER1_SERVERS against the configured roster.
  // Runs *after* the router-profile fallback so it validates the final
  // tier1 list (either env-provided or router-supplied), not just env.
  // We check against *configured* (not just *running*) so a tier-1 entry
  // for an on-demand server like `obsidian` doesn't get flagged — it's
  // legitimate to seed it now and start it later. The actual run-time
  // intersection happens in getEffectiveToolsList().
  if (tier1Servers.length > 0) {
    try {
      const allConfigured = await listAvailableServers();
      const knownNames = new Set(
        Array.isArray(allConfigured?.servers)
          ? allConfigured.servers.map(s => s.name).filter(Boolean)
          : []
      );
      const unknownTier1 = tier1Servers.filter(s => !knownNames.has(s));
      if (unknownTier1.length > 0) {
        console.error(
          `[bridge] TIER1_SERVERS contains server(s) not configured in the ` +
          `router: ${unknownTier1.join(', ')}. These will be ignored.`
        );
      }
    } catch (err) {
      console.error(
        `[bridge] Could not validate TIER1_SERVERS against router: ${err.message}`
      );
    }
  }

  // Bind stdio transport only after config is finalized.
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('PromptHub MCP Bridge started');
  console.error(`Connected to: ${PROMPTHUB_URL}`);
  console.error(`Client name: ${CLIENT_NAME}`);
  console.error(
    `Tool disclosure: ${toolDisclosure || 'full'} ` +
    `(tier1: ${tier1Servers.join(', ') || '(none)'}, source: ${profileSource})`
  );
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
