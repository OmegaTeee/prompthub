# Session Memory Guide

## What Is Session Memory?

Session Memory lets PromptHub remember important information across your conversations. Think of it like a notebook that PromptHub keeps beside the keyboard: every preference, fact, or detail you share gets written down so AI models can refer back to it later.

### Before and After

**Without memory:**

```
Day 1: "I prefer Python for coding"
(AI forgets)
Day 3: "Write me some code"
(AI suggests JavaScript because it has no record of your preference)
```

**With memory:**

```
Day 1: "I prefer Python for coding"
(PromptHub stores this as a fact)
Day 3: "Write me some code"
(AI checks the notebook, sees your Python preference, writes Python code)
```

**Key points:**

- Session Memory stores what you tell it so AI models have context.
- You control what gets saved. Nothing is stored automatically.
- All data stays on your Mac.

## How Memory Is Organized

PromptHub stores three types of information. Each serves a different purpose.

### 1. Sessions

A session is a conversation thread with a unique ID. It is like opening a new page in the notebook. Each session tracks:

- When it started.
- Which app you are using.
- How many facts it contains.
- Your last interaction.

### 2. Facts

Facts are individual pieces of information you want PromptHub to remember. Examples:

- Preferences: "I prefer dark mode."
- Background: "I am a software engineer."
- Goals: "I am learning Rust."
- Constraints: "No external APIs."

You can tag each fact (for example, `#preferences` or `#background`) to make it easy to find later.

### 3. Memory Blocks

Memory blocks hold structured data under a named key. They work like labeled folders in a filing cabinet.

- `user_settings`: theme, font size, language preference.
- `project_info`: current project details.
- Any custom key you choose.

**Key points:**

- Sessions group related facts into conversation threads.
- Facts store single pieces of information with optional tags.
- Memory blocks store structured data under a named key.

## Using Session Memory

### Through the Dashboard

1. Open your browser and go to `http://localhost:9090`.
2. Find the **Memory** section on the dashboard.
3. You will see active session count, total facts stored, and recent conversations.

### Through the API

To create a new session, run this command in Terminal:

```bash
curl -X POST http://localhost:9090/sessions \
  -H "Content-Type: application/json" \
  -d '{"client_id": "my-app"}'
```

The response includes a session ID. Save this ID -- you will use it for all future requests to that session.

## Adding Facts

Facts are the main way to teach PromptHub about you and your work.

### A Simple Example

Store a preference:

```bash
curl -X POST http://localhost:9090/sessions/{session-id}/facts \
  -H "Content-Type: application/json" \
  -d '{
    "fact": "I prefer Python over JavaScript",
    "tags": ["preferences", "programming"],
    "source": "manual"
  }'
```

Replace `{session-id}` with the ID you received when you created the session.

### A Real-World Example

Store project context so the AI knows what you are working on:

```bash
curl -X POST http://localhost:9090/sessions/{session-id}/facts \
  -H "Content-Type: application/json" \
  -d '{
    "fact": "Working on a Flask API for data analysis. Need async support.",
    "tags": ["project", "flask", "async"],
    "source": "manual"
  }'
```

**Key points:**

- Use tags to categorize facts for easier retrieval.
- The `source` field records where the fact came from.
- Replace `{session-id}` with your actual session ID in every command.

## Storing Structured Data with Memory Blocks

When you need to store a group of related settings, use a memory block. This is like creating a labeled folder instead of writing loose notes.

Save a block:

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

Retrieve the block later:

```bash
curl http://localhost:9090/sessions/{session-id}/memory/user_settings
```

## Dashboard Memory Panel

The dashboard shows real-time memory statistics at a glance.

| Metric              | What It Means                                 |
| ------------------- | --------------------------------------------- |
| **Active Sessions** | Ongoing conversation threads.                 |
| **Total Facts**     | All individual pieces of stored information.  |
| **Memory Blocks**   | Structured data items.                        |
| **Closed Sessions** | Old conversations that can be archived.       |

Click on a recent session to see all its facts.

## Best Practices

### What to Store

- Preferences: coding style, tone, output format.
- Background: your role, expertise, constraints.
- Project context: current goals and requirements.
- Use clear, concise wording for each fact.
- Add tags so you can search later.
- Update facts when your situation changes.

### What to Avoid

- Sensitive data like passwords or personal ID numbers. Memory is local, but good habits matter.
- Large files. Use the files feature for those instead.
- Outdated facts you no longer need. Delete them to keep context clean.
- Temporary information that will be irrelevant tomorrow.

## Managing Sessions

### View All Sessions

```bash
curl http://localhost:9090/sessions?limit=10
```

### Get Details for One Session

```bash
curl http://localhost:9090/sessions/{session-id}
```

### Close a Session

```bash
curl -X DELETE http://localhost:9090/sessions/{session-id}
```

Closing a session marks it as done but keeps the data for archival. The facts are not deleted.

## Setting Expiration Dates

You can make memory blocks expire automatically. This is useful for temporary project details that you know will become irrelevant after a deadline.

```bash
curl -X PUT http://localhost:9090/sessions/{session-id}/memory/temporary_data \
  -H "Content-Type: application/json" \
  -d '{
    "value": "This is temporary",
    "expires_at": "2026-03-09T12:00:00Z"
  }'
```

After the specified date, PromptHub automatically deletes this data.

**Key points:**

- Use expiration for short-lived context like sprint goals or event details.
- Data without an expiration date stays until you delete it manually.

## Privacy and Data Storage

### Where is your data stored?

Everything lives locally on your Mac in a SQLite database:

```
~/.prompthub/memory.db
```

No data is sent to external servers.

### Who can access it?

Only PromptHub and the apps connected to it can read the data.

### How do you delete data?

Delete a single fact:

```bash
curl -X DELETE http://localhost:9090/sessions/{session-id}/facts/{fact-id}
```

Or close an entire session to archive it. You can also delete the database file directly if you want a clean slate.

## Common Questions

**Q: Does PromptHub add facts on its own?**
A: No. You control what gets stored. You must add facts yourself.

**Q: Can different apps share the same memory?**
A: Yes, if they use the same session ID. You can also give each app its own session.

**Q: How much can I store?**
A: There is no built-in limit. Storage depends on your available disk space.

**Q: Do facts expire automatically?**
A: Only if you set an expiration date. Otherwise, they stay until you delete them.

## Troubleshooting

### "Session not found"

- Double-check the session ID. A single wrong character will cause this error.
- The session may be closed. List all sessions to find the right one:

  ```bash
  curl http://localhost:9090/sessions?limit=20
  ```

### "Can't add facts"

- Confirm the session exists before adding facts to it.
- Make sure your request body is valid JSON.
- Verify the session ID in the URL matches an active session.

### "Memory panel shows no data"

- No sessions have been created yet. Create one first.
- Try refreshing the dashboard page.

## What to Do Next

- **Session Memory with MCP** -- Advanced guide for using memory with Memory MCP servers.
- **API Configuration** -- How to connect your apps to PromptHub sessions.
- **Troubleshooting** -- Common issues and solutions.

---

Session Memory is optional. You can use PromptHub without it. But if you want AI models that understand your preferences and context over time, memory is a powerful way to get there.
