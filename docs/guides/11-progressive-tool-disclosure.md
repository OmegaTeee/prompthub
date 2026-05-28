# Progressive Tool Disclosure Guide

## What Is Progressive Tool Disclosure?

When you connect an AI client (Claude Desktop, VS Code, Cherry Studio) to PromptHub, the AI can see every tool from every running MCP server — file operations, web search, Obsidian notes, browser control, and more. That's powerful, but it has a cost: the AI has to read the full list of ~70 tools *before every single message*, even when it only needs one or two.

Progressive Tool Disclosure fixes this. Instead of dumping every tool on the AI up front, PromptHub shows it a small starter set and lets it **ask for more when it actually needs them**.

Think of it like a kitchen. The full toolset is every utensil in every drawer. Progressive disclosure keeps the everyday tools on the counter (the ones you reach for constantly) and leaves the specialty gadgets in labelled drawers. When a recipe calls for a melon baller, the AI opens the drawer — but it isn't staring at the melon baller while making toast.

### Before and After

**Without progressive disclosure (full mode):**

```
You: "List the files in my project folder."
[AI receives ~70 tool definitions, ~25,000 tokens of context, then calls one tool]
```

**With progressive disclosure:**

```
You: "List the files in my project folder."
[AI receives ~14 tool definitions, ~6,000 tokens, then calls one tool]
```

**Key points:**

- The AI starts each conversation with only your **tier-1** tools plus a couple of "discovery" helpers.
- When a task needs a tool that isn't loaded, the AI **discovers and loads it on demand** — automatically, without you doing anything.
- Typical savings: about **80% less tool context** at the start of a conversation. That means faster first responses and lower token usage on cloud fallback.

## The Two Modes

PromptHub's bridge runs in one of two modes per client:

| Mode | What the AI sees | When to use |
|---|---|---|
| **`full`** (default) | Every tool from every running server | Small toolsets, or clients that don't support live tool refresh |
| **`progressive`** | Tier-1 servers + 2 discovery helpers, then more on demand | Large toolsets, context-sensitive clients |

`full` is the default, so **nothing changes until you opt a client in**. Existing setups behave exactly as before.

## How the AI Loads Tools (the magic, explained)

In progressive mode, the bridge adds two small "meta-tools" the AI can call:

1. **`discover_tools`** — Returns a lightweight catalog: server name, tool name, and a one-line description for every available tool. No bulky parameter schemas. This is how the AI *finds out what's possible* without paying the full context cost.
2. **`load_server_tools`** — Promotes a whole server's tools into the active set. After loading, the bridge tells your client "the tool list changed," and your client refreshes so the AI can call the new tools.

A typical progressive-mode flow looks like this:

```
You: "Search the web for the latest Python release."
AI:  (calls discover_tools, sees "duckduckgo_search")
AI:  (calls load_server_tools with server="duckduckgo")
     → bridge promotes duckduckgo, signals tools/list_changed
AI:  (calls duckduckgo_search with your query)
AI:  "Here are the latest Python release notes..."
```

You don't see or trigger any of this — it happens inside the AI's turn. You just see the final answer (and, in most clients, the tool-call trace if you expand it).

## How to Turn It On

You have two ways to enable progressive mode for a client. The first is recommended because it keeps all your configuration in one place.

### Option 1: Per-Client Tool Profile (Recommended)

Add a `tool_profile` block to the client's entry in `~/prompthub/app/configs/enhancement-rules.json`:

```jsonc
"clients": {
  "claude-desktop": {
    "model": "qwen3-4b-instruct-2507",
    "tool_profile": {
      "disclosure": "progressive",
      "tier1_servers": ["memory", "sequential-thinking", "desktop-commander"]
    },
    "system_prompt": "..."
  }
}
```

- `disclosure`: `"progressive"` or `"full"`.
- `tier1_servers`: the servers whose tools are always visible (your "everyday tools on the counter").

The PromptHub bridge fetches this profile automatically at startup. No per-client launch-script edits needed — the router is the single source of truth.

Four clients ship with progressive profiles already configured: `claude-desktop`, `claude-code`, `vscode`, and `open-webui`.

### Option 2: Environment Variables (override / debugging)

If you want to pin a specific behavior for one client launch — or test before committing to a config — set env vars on the bridge process in your client's MCP config:

```jsonc
"prompthub": {
  "command": "node",
  "args": ["/Users/youruser/prompthub/mcps/prompthub-bridge.js"],
  "env": {
    "CLIENT_NAME": "claude-desktop",
    "TOOL_DISCLOSURE": "progressive",
    "TIER1_SERVERS": "memory,sequential-thinking,desktop-commander"
  }
}
```

**Precedence**: explicit env vars **win over** the router profile. If you set `TOOL_DISCLOSURE` or `TIER1_SERVERS`, the bridge uses those and skips the router fetch. Leave both unset to let the router profile (Option 1) drive.

### Choosing Your Tier-1 Servers

Tier-1 should hold the servers a given client reaches for *most often*, so common tasks need zero discovery round-trips. Good defaults by client type:

| Client type | Suggested tier-1 |
|---|---|
| General assistant (Claude Desktop) | `memory`, `sequential-thinking`, `desktop-commander` |
| Code editor (VS Code, Claude Code) | `desktop-commander`, `context7`, `memory` |
| Chat UI (Open WebUI) | `memory`, `sequential-thinking` |

Everything *not* in tier-1 stays one `discover_tools` + `load_server_tools` away — still fully reachable, just not pre-loaded.

## Testing & Verification

Use these five chat prompts to confirm disclosure behaves correctly. Run them in a client you've set to `progressive` with tier-1 = `memory, sequential-thinking, desktop-commander`.

> **Watch the tool-call trace, not just the answer.** Modern AI models can *fake* a "web search" answer from memory. The proof that disclosure worked is seeing the actual `discover_tools` → `load_server_tools` → real-tool sequence in the trace, plus verifiable results (real URLs, a note that actually appears in your vault).

### Test 1 — A tier-1 task should need no discovery (negative control)

> **Type:** "List the files in my home directory."

**Expected:** The AI calls `desktop-commander_list_directory` directly. It should **not** call `discover_tools` first, because `desktop-commander` is already in tier-1.

**If it fails** (the AI calls `discover_tools` for a tier-1 tool): your tier-1 servers aren't surfacing. Check the bridge startup log line (below).

### Test 2 — A hidden tool should be discovered and loaded

> **Type:** "Use DuckDuckGo to search for 'Anthropic Claude release notes' and summarize the top three results."

**Expected:** `discover_tools` → `load_server_tools` (server `duckduckgo`) → `duckduckgo_search`. You get real result links.

**If it fails:** if the AI answers with no tool calls at all, it answered from memory — re-run and check the trace. Naming "DuckDuckGo" explicitly makes a real call more likely.

### Test 3 — A different hidden server (Obsidian)

> **Type:** "Save a note titled 'Disclosure Test' to my Obsidian vault with the body 'It works.'"

**Expected:** discovery → load of `obsidian-mcp-tools` → a `create_vault_file` call. The note appears in your vault.

**If it fails:** if the AI tries to write the file with `desktop-commander` to a random path, it didn't discover the Obsidian server.

### Test 4 — Mixing a hidden server with an already-loaded one

> **Type:** "Search the web for 'best open-source MCP servers', then save the top three to my memory."

**Expected:** exactly **one** `load_server_tools` call (for `duckduckgo`). The memory writes happen directly because `memory` is already in tier-1 — no second load.

**If it fails:** if you see `load_server_tools` called for `memory`, the AI isn't recognizing what's already active.

### Test 5 — Full-mode sanity check (regression)

Switch the client back to `full` (set `"disclosure": "full"` or `TOOL_DISCLOSURE=full`) and restart it.

> **Type:** "What MCP tools do you have available?"

**Expected:** the AI sees the full ~70-tool catalog with no discovery step. Your client's tool count jumps from ~14 to ~70.

**If it fails** (count stays low): the mode change didn't take effect — fully quit and relaunch the client, don't just close the window.

### Where to Look

| Signal | Where | Tells you |
|---|---|---|
| Startup mode line | Bridge stderr: `Tool disclosure: progressive (tier1: …)` | Which mode and tier-1 the bridge booted with |
| `tools/list_changed` + active set | Bridge stderr after a `load_server_tools` call | Confirms a server was promoted |
| Disclosure column | Dashboard → Token Budget panel | Per-client mode and tier-1 list at a glance |
| Live profile | `curl http://127.0.0.1:9090/clients/claude-desktop/tool-profile` | What the router thinks this client's profile is |

For Claude Desktop, the bridge log is at `~/Library/Logs/Claude/mcp-server-prompthub.log`. For other clients, check where they route MCP server stderr.

## Troubleshooting

**The AI never loads a hidden tool, even when asked.**
Some clients don't act on the `tools/list_changed` signal. As a fallback, the AI can still discover via `discover_tools` and the tool becomes callable after `load_server_tools` — but if your client ignores the refresh entirely, switch that client to `disclosure: full`. Tool disclosure is a per-client opt-in for exactly this reason.

**Tool count looks wrong after I changed the config.**
Config is read at bridge startup. Fully restart the client (quit, not just close the window) so the bridge re-reads its profile.

**I set env vars but the router profile is still being used.**
Both `TOOL_DISCLOSURE` and `TIER1_SERVERS` must be present for the env path to fully take over tier-1. If only one is set, check the startup log to see what the bridge actually resolved.

**A server in my tier-1 isn't showing up.**
Tier-1 only surfaces servers that are *running*. A stopped or on-demand server in your tier-1 list is silently skipped until it starts. Check the dashboard's Servers panel.

## How It Compares

| | Full mode | Progressive mode |
|---|---|---|
| Initial tool context | ~25,000 tokens (~70 tools) | ~6,000 tokens (~14 tools) |
| First-response speed | Slower (more to read) | Faster |
| Hidden tools reachable? | N/A — all visible | Yes, via discover + load |
| Best for | Few servers, simple setups | Many servers, context-sensitive clients |

---

## Related Guides

- [Client Configuration Guide](06-client-configuration-guide.md) — where `enhancement-rules.json` lives and how clients connect
- [Advanced Power User Manual](08-advanced-power-user-manual.md) — environment variables and deeper customization
- [Troubleshooting Guide](05-troubleshooting-guide.md) — general connection and bridge issues

For the bridge component reference (env vars, meta-tool details, precedence rules), see [`mcps/README.md`](../../mcps/README.md#progressive-tool-disclosure).

**Estimated reading time:** 12 minutes
