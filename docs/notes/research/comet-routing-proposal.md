Yes, absolutely — the PromptHub enhancement layer is actually the **ideal** place to put this, since it lets you inject instructions without touching the base system prompt or Jinja template, and you can version-control it via the PR.

## What the JSON tells us first

Before the PR suggestions — the latest session shows real progress :

- Model correctly called `perplexityconnect` first, then `perplexityask` with `timeout: 120` ✓
- Thought for only **5.46 seconds** this time (vs 42s before) — the clearer system prompt dramatically reduced reasoning overhead ✓
- Tool call was correctly formed: `perplexityask` with `prompt: "Go to https://lmstudio.ai/models/neil/qwen3-thinking and return the parameters..."` and `timeout: 120` ✓
- But then timed out again at 120s and the model correctly noted: "task is still processing on a local development server" and gave up gracefully

The pipeline is working — Comet is just slow on lmstudio.ai. The MCP-level fix is still needed alongside the PromptHub layer.

***

## PromptHub Enhancement Layer Suggestions

### What to inject at the enhancement layer

The enhancement layer sits between the base system prompt and the user message, so it's perfect for:

1. **Tool routing context** — so it doesn't bloat the base system prompt
2. **Session-aware instructions** — e.g. "you are in a web research session"
3. **MCP capability declarations** — telling the model what tools are available and their quirks

```md
## Active MCP Capabilities

### Perplexity / Comet Browser
- `perplexityconnect` — start/verify Comet is running (always call first)
- `perplexityask` — send task to Comet, ALWAYS pass `timeout: 120` for URLs
- `perplexitypoll` — check async task progress (call every 5s until complete)
- `perplexityscreenshot` — capture current page state
- `perplexitytabs` — list/switch/close browser tabs
- `perplexitymode` — switch search mode (search/research/labs/learn)

### Fetch MCP
- `fetch` — direct HTTP fetch, returns markdown. Use for static/API URLs only.
- Max return: 5000 chars by default. Use `startindex` to paginate long pages.

### Desktop Commander
- File/directory ops, terminal processes, shell commands
- `readfile` with `isUrl: true` returns raw HTML only — never use for web pages

## Tool Sequencing Rules
- JS-rendered pages: `perplexityconnect` → `perplexityask` (timeout: 120) → `perplexitypoll` → `perplexityscreenshot`
- Static content: `fetch` directly
- If `perplexityask` times out: use `perplexitypoll` to check if still running before retrying
```

***

## For the PR specifically

Since this is `OmegaTeee/prompthub/pull/14`, the enhancement could be structured as a **named preset** in PromptHub that gets injected when a "web research" session type is active:

```json
{
  "id": "web-research-mcp",
  "name": "Web Research via Comet MCP",
  "description": "Injects tool routing rules and MCP capability context for browser-based research sessions",
  "enhancement": "...(markdown above)...",
  "tags": ["mcp", "comet", "perplexity", "web", "browser"],
  "tools": ["perplexity", "fetch", "desktopcommander"]
}
```

Key things to include in the PR:

1. **Separate the tool routing rules out of the base system prompt** — they belong in the enhancement layer so they're only injected when those tools are active
2. **Add `timeout` as a required parameter hint** in the Comet tool descriptions at the enhancement level — so the model sees it even if the MCP tool description doesn't surface it clearly
3. **Add the poll loop pattern** explicitly — the model doesn't know to poll after a timeout unless told

Would you like me to look at the PR directly to see what the current enhancement structure looks like so I can give you a concrete diff?
