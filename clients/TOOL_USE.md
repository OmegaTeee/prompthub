# Tool-Use Rules for PromptHub Clients

Shared tool-routing guidance for any client whose local model calls tools
through PromptHub (claude.ai/code, LM Studio, Cherry Studio, Zed, Claude
Desktop, etc.). Aimed at smaller models — **particularly `qwen3-4b-thinking`** —
that need explicit rules to pick the right tool.

Copy the **Rules block** at the bottom into your client's system prompt.
Keep this file as the single source of truth; per-client copies drift.

---

## Tool roster (what PromptHub exposes)

Tool names below match what the bridge presents *after* the
`TOOL_PREFIX_ALIASES` pass in `mcps/prompthub-bridge.js` (e.g. `comet_ask`
becomes `perplexity_ask`). A few clients add their own MCPs on top (e.g.
`fetch` via `mcp-server-fetch` in [clients/lm-studio/mcp.json](lm-studio/mcp.json));
those are noted where relevant.

| Prefix                  | Purpose                                                           | Source server (`mcp-servers.json`) |
| ----------------------- | ----------------------------------------------------------------- | ---------------------------------- |
| `desktop_commander_*`   | Local files, shell, processes, search                             | `desktop-commander` (26 tools)     |
| `perplexity_*`          | Real-browser navigation via Comet (JS-rendered, logins, research) | `perplexity-comet` (8 tools)       |
| `duckduckgo_*`          | Lightweight web search + plain-text page fetch                    | `duckduckgo` (2 tools)             |
| `context7_*`            | Library/framework docs (React, FastAPI, etc.)                     | `context7` (2 tools)               |
| `sequential_thinking`   | Stepwise reasoning scratchpad                                     | `sequential-thinking` (1 tool)     |
| `memory_*`              | Cross-session knowledge graph                                     | `memory` (9 tools)                 |
| `obsidian-mcp-tools_*`  | Vault ops (requires Obsidian running)                             | `obsidian-mcp-tools` (18 tools)    |
| `fetch` *(client-side)* | Plain HTTP GET — no JS, no rendering                              | `mcp-server-fetch` in client mcp.json |

On-demand (not auto-started): `chrome-devtools-mcp`, `browsermcp`, `mcp-obsidian`.
Start with `curl -X POST http://localhost:9090/servers/{name}/start` first.

---

## Routing decisions

Pick by the **shape of the input**, not by the task label.

| Input                                                     | Use                         | Why                                   |
| --------------------------------------------------------- | --------------------------- | ------------------------------------- |
| JS-rendered page (lmstudio.ai, GitHub file viewer, app UI) | `perplexity_ask` with URL   | Plain fetch gets `<script>` shell only |
| Login-gated page, form fill, multi-step browsing          | `perplexity_ask`            | Real browser session, agentic        |
| Raw URL → plain text/JSON (APIs, GitHub raw, RSS, robots.txt) | `fetch` *(or `duckduckgo_fetch_content`)* | No browser overhead    |
| "What is X?" / quick web lookup                           | `duckduckgo_search`         | Cheap, no browser spin-up             |
| Deep research, summarization, cross-site synthesis        | `perplexity_ask`            | Perplexity's research mode            |
| Local file read/write/edit                                | `desktop_commander_*`       | Filesystem, not URL                   |
| Shell command, process management, diagnostics            | `desktop_commander_start_process` / `_list_processes` | Host OS, not browser |
| Library/API docs ("how do I use FastAPI lifespan?")       | `context7_query-docs`       | Versioned, structured                 |
| Multi-step reasoning ("plan this refactor")               | `sequential_thinking`       | Externalizes chain-of-thought         |
| Vault note ops (Obsidian)                                 | `obsidian-mcp-tools_*`      | Obsidian must be open                 |

---

## Anti-patterns

- **Never** call `desktop_commander_read_file` with `isUrl: true` on a
  JS-rendered page. It returns empty HTML shells. Use `perplexity_ask`.
- **Never** call `perplexity_ask` for a plain text/JSON URL — it spins up
  a real browser for something `fetch` does in 50 ms.
- **Don't** call `sequential_thinking` on short prompts. Reserve it for
  tasks the model would otherwise bounce off of.
- **Don't** chain browser tools and file tools in the same turn without a
  clear need — emit one tool call, read the response, then decide.

---

## Fallback

If a URL returns only raw HTML with no readable content (only `<script>`
tags, no body text), **retry immediately with `perplexity_ask`** using
the same URL as the prompt. Don't loop on the failing fetcher.

## Timeout recovery (Perplexity/Comet)

If `perplexity_ask` returns a timeout error, the task is probably **still
running** inside Comet — the proxy gave up, the browser didn't. Do this:

1. Call `perplexity_poll` to check task status.
2. If status shows progress, poll again in 5–10 s.
3. Only re-issue `perplexity_ask` if `perplexity_poll` reports the task
   is no longer active.

Never retry `perplexity_ask` directly on timeout — it starts a fresh
research flow and abandons the one that was nearly done.

---

## Rules block (copy into your system prompt)

Paste this into your client's system prompt below your base persona. It's
intentionally terse — smaller thinking models respect short rules better
than long ones.

```markdown
## Tool Use Rules
- JS-rendered sites (lmstudio.ai, GitHub files, SPA UIs) → `perplexity_ask`
- Raw URLs (APIs, GitHub raw, plain HTML) → `fetch` or `duckduckgo_fetch_content`
- Local files, terminal, processes → `desktop_commander_*`
- Quick web lookups ("what is X") → `duckduckgo_search`
- Deep research, login-gated pages → `perplexity_ask`
- Library/API docs → `context7_query-docs`
- Stepwise reasoning on hard problems → `sequential_thinking`

Fallback: if a URL returns only script tags with no readable content,
retry once with `perplexity_ask`.

If `perplexity_ask` times out, call `perplexity_poll` to check status
before retrying. The task is usually still running inside Comet.

Never use `desktop_commander_read_file` with `isUrl: true` for web pages.
```
