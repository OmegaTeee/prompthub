# Session Memory Guide

## What is Session Memory?

Session Memory is PromptHub's built-in brain. It **remembers important information** across your conversations, so AI models have more context about you and your needs.

### Without Memory
```
Day 1: "I prefer Python for coding"
(AI forgets)
Day 3: "Write me some code"
(AI suggests JavaScript, because it forgot your preference)
```

### With Memory
```
Day 1: "I prefer Python for coding"
(PromptHub stores this)
Day 3: "Write me some code"
(AI remembers Python preference, suggests Python code)
```

## How Memory Works

PromptHub stores three types of information:

### 1. **Sessions**
Think of a session as a "conversation thread" with a unique ID. Each session tracks:
- When it started
- What app you're using
- How many facts you've told it
- Your last interaction

### 2. **Facts**
These are individual pieces of information you want PromptHub to remember:
- Your preferences ("I prefer dark mode")
- Your background ("I'm a software engineer")
- Your goals ("I'm learning Rust")
- Your constraints ("No external APIs")

Each fact can be tagged (e.g., `#preferences`, `#background`) for easy retrieval.

### 3. **Memory Blocks**
Named storage for specific information:
- User settings (`user_settings`: theme, font size, etc.)
- Project context (`project_info`: current project details)
- Custom data (anything you want to store)

## Using Session Memory

### Via the Dashboard

1. Open http://localhost:9090
2. Look for the **Memory** section
3. You'll see:
   - Active sessions count
   - Total facts stored
   - Recent conversations

### Via API (Advanced Users)

Create a session:
```bash
curl -X POST http://localhost:9090/sessions \
  -H "Content-Type: application/json" \
  -d '{"client_id": "my-app"}'
```

The response includes a session ID. Use this ID for all your future requests to that session.

## Adding Facts

Facts are the main way to teach PromptHub about yourself.

### Simple Example

Tell PromptHub about your preferences:
```bash
curl -X POST http://localhost:9090/sessions/{session-id}/facts \
  -H "Content-Type: application/json" \
  -d '{
    "fact": "I prefer Python over JavaScript",
    "tags": ["preferences", "programming"],
    "source": "manual"
  }'
```

### Real-World Example

Store project context:
```bash
curl -X POST http://localhost:9090/sessions/{session-id}/facts \
  -H "Content-Type: application/json" \
  -d '{
    "fact": "Working on a Flask API for data analysis. Need async support.",
    "tags": ["project", "flask", "async"],
    "source": "manual"
  }'
```

## Storing Custom Data

For more structured information, use Memory Blocks:

```bash
curl -X PUT http://localhost:9090/sessions/{session-id}/memory/user_settings \
  -H "Content-Type: application/json" \
  -d '{
    "value": {
      "theme": "dark",
      "font_size": 14,
      "language": "python",
      "timezone": "PST"
    }
  }'
```

Later, retrieve it:
```bash
curl http://localhost:9090/sessions/{session-id}/memory/user_settings
```

## Dashboard Memory Panel

The dashboard shows real-time memory statistics:

| Metric | What it means |
|--------|--------------|
| **Active Sessions** | Number of ongoing conversation threads |
| **Total Facts** | All pieces of information you've stored |
| **Memory Blocks** | Structured data storage items |
| **Closed Sessions** | Old conversations (can be archived) |

Click on a recent session to see all its facts.

## Memory Best Practices

### ✅ DO
- Store preferences (coding style, tone, format)
- Store background info (your role, expertise, constraints)
- Use clear, concise facts
- Tag facts for easy searching
- Update facts when things change

### ❌ DON'T
- Store sensitive personal info (passwords, SSNs)
- Store huge files (use files feature instead)
- Keep old facts you no longer need
- Use memory for temporary info

## Managing Sessions

### View All Sessions
```bash
curl http://localhost:9090/sessions?limit=10
```

### Get Session Details
```bash
curl http://localhost:9090/sessions/{session-id}
```

### Close a Session
```bash
curl -X DELETE http://localhost:9090/sessions/{session-id}
```

This keeps the data (for archival) but marks the session as closed.

## Memory Expiration

You can set facts to expire automatically:

```bash
curl -X PUT http://localhost:9090/sessions/{session-id}/memory/temporary_data \
  -H "Content-Type: application/json" \
  -d '{
    "value": "This is temporary",
    "expires_at": "2026-03-09T12:00:00Z"
  }'
```

After the date passes, this data is automatically deleted.

## Privacy and Data

### Where is my data stored?
- Everything is stored locally on your Mac
- File: `~/.prompthub/memory.db` (SQLite database)
- No data is sent to external servers

### Who can access it?
- Only PromptHub can access it
- Only apps connected to PromptHub can use it

### How do I delete data?
Delete individual facts:
```bash
curl -X DELETE http://localhost:9090/sessions/{session-id}/facts/{fact-id}
```

Or close an entire session (keeps data) or delete manually.

## Common Questions

**Q: Does PromptHub automatically add facts?**
A: No, you control what gets stored. You must explicitly add facts.

**Q: Can I share memory between apps?**
A: Yes, if they use the same session ID. Different apps can have separate sessions.

**Q: How much can I store?**
A: Practically unlimited (up to your disk space).

**Q: Do facts expire automatically?**
A: Only if you set an expiration date. Otherwise, they stay until you delete them.

## Troubleshooting

### "Session not found"
- You might have the wrong session ID
- The session might be closed
- Try listing all sessions to find the right ID

### "Can't add facts"
- Make sure the session exists
- Check your request format (should be JSON)
- Verify the session ID is correct

### "Memory panel shows no data"
- No sessions have been created yet
- Try creating a session first
- Refresh the dashboard

## What's Next?

- **Session Memory with MCP** — Advanced guide for using memory with Memory MCP servers
- **API Configuration** — How to connect your apps to PromptHub sessions
- **Troubleshooting** — Common issues and solutions

---

**Remember:** Session Memory is optional. You can use PromptHub without it, but it's a powerful way to get better AI results by providing context.
