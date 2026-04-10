# I want to feed Claude history into PromptHub

> Research snapshot: this note captures an exploratory integration idea, not an
> approved feature plan. Model examples and suggested tooling below should be
> treated as provisional.

Here's a solid integration plan for feeding Claude Code history into PromptHub, based on how the data is structured.

## Claude Code History Format

The JSONL files at `~/.claude/projects/` are the richest source — each contains a complete conversation transcript as one JSON object per line. Each line records a specific event type: user messages, Claude's responses (including tool calls), tool results, and file modification tracking.[^1]

The project folder name is the working directory path with every non-alphanumeric character replaced by `-` (e.g., `/Users/omega/Code/PromptHub` → `-Users-omega-Code-PromptHub`).[^2]

## PromptHub Integration Strategy

**1. MCP Tool: `read_session_history`**

- Input: optional `project_dir` (default: cwd) and `session_id` or `latest`
- Logic: resolve encoded cwd → scan `~/.claude/projects/<encoded-cwd>/*.jsonl` → parse and return
- Useful for: surfacing previous decisions, code patterns, or solutions back into active context

**2. MCP Tool: `search_history`**

- Full-text or semantic search across all `.jsonl` files in `~/.claude/projects/`
- Index on startup or lazily; filter by `role: "user"` lines for prompt patterns
- Useful for: "what did I tell Claude about X last week?" queries

**3. MCP Tool: `history_to_prompt`**

- Distills a session into a summarized context block using a local model (e.g., DeepSeek-R1 for reasoning)
- Strips tool_use/tool_result noise, keeps only `user`/`assistant` message content
- Output: a condensed `CLAUDE.md`-style context snippet ready to inject into a new session

## Key Parsing Notes

- `~/.claude/history.jsonl` is **not** the full conversation — it only tracks slash command usage (meta-log). The real session transcripts are in `~/.claude/projects/<encoded-dir>/<session-id>.jsonl`.[^1][^2]
- Sessions are **auto-deleted** over time by default. You'll want your MCP server to archive copies to a PromptHub store (SQLite or flat file) on a schedule or on session close.[^3]
- To disable auto-deletion, set `cleanupPeriodDays: -1` in `~/.claude/settings.json`.[^4]

## Quick Shell Test

```bash
# Find your PromptHub sessions
ls ~/.claude/projects/-Users-$(whoami)-Code-PromptHub/

# Peek at the latest session
ls -t ~/.claude/projects/-Users-$(whoami)-Code-PromptHub/*.jsonl | head -1 | xargs tail -n 20 | python3 -m json.tool
```

The `history_to_prompt` tool is probably the highest-leverage piece for PromptHub — it would let any MCP client auto-inject "what happened last session" without manual `/resume`. Want me to scaffold that as a `fastMCP` tool?

<span style="display:none">[^10][^11][^12][^13][^14][^15][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://codesignal.com/learn/courses/foundation-getting-started-with-claude-code/lessons/exploring-conversation-history

[^2]: https://platform.claude.com/docs/en/agent-sdk/sessions

[^3]: https://dev.to/kuroko1t/i-built-a-tool-to-stop-losing-my-claude-code-conversation-history-5500

[^4]: https://code.claude.com/docs/en/settings

[^5]: https://mintlify.com/1shanpanta/claude-analytics/reference/data-sources/history

[^6]: https://www.reddit.com/r/ClaudeAI/comments/1rpmur2/does_anthropic_publish_an_official_json_schema/

[^7]: https://johndamask.substack.com/p/devlog-making-a-claude-code-history

[^8]: https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use

[^9]: https://github.com/thomasrice/claude-sessions

[^10]: https://github.com/withLinda/claude-JSONL-browser

[^11]: https://stevekinney.com/courses/ai-development/claude-code-session-management

[^12]: https://www.claude-hub.com/resource/github-cli-withLinda-claude-JSONL-browser-claude-JSONL-browser/

[^13]: https://www.reddit.com/r/ClaudeAI/comments/1r66oo0/how_i_structure_claude_code_projects_claudemd/

[^14]: https://x.com/minchoi/status/2036279719386100126

[^15]: https://simonw.substack.com/p/building-a-tool-to-copy-paste-share
