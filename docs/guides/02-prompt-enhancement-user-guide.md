# Prompt Enhancement Guide

## What Is Prompt Enhancement?

Prompt Enhancement automatically rewrites your prompts before they reach the AI model. Think of it like a copy editor who reads your rough draft and polishes it before it goes to print.

The result: clearer requests, more relevant context, and higher-quality AI responses -- all happening in the background.

### Before and After

**Without enhancement:**

```
You: "Summarize this"
AI: (unsure what "this" refers to, gives a generic answer)
```

**With enhancement:**

```
You: "Summarize this"
PromptHub rewrites it to: "Please summarize the main ideas and key takeaways from the provided document"
AI: (understands the request, gives a focused answer)
```

**Key points:**

- Enhancement rewrites vague prompts into clear ones.
- It runs automatically -- you do not need to change how you write.
- The AI model receives the improved version, not your original.

## How to Enable Enhancement

You have three options. Pick the one that fits your workflow.

### Option 1: Enable for a Specific App (Recommended)

This approach lets you turn enhancement on for one app without affecting the others. It is like setting a thermostat room by room instead of for the whole house.

1. Open `~/prompthub/configs/api-keys.json`.
2. Find the entry for your app (for example, `sk-prompthub-code-001`).
3. Change `"enhance": false` to `"enhance": true`.
4. Save the file.

The change takes effect right away. No restart needed.

```json
{
  "keys": {
    "sk-prompthub-code-001": {
      "client_name": "vscode",
      "enhance": true,
      "description": "VS Code (with enhancement)"
    }
  }
}
```

### Option 2: Enable Globally

If you want every app enhanced by default:

1. Open `~/prompthub/.env`.
2. Add or change this line:

   ```
   AUTO_ENHANCE_MCP=true
   ```

3. Restart PromptHub.

From that point on, all prompts are improved automatically.

### Option 3: Enable per Request (Advanced)

Some apps let you set custom HTTP headers. Add this header to a single request:

```
X-Enhance: true
```

This overrides the global and per-app settings for that one request only.

**Key points:**

- Per-app is the recommended approach. It gives you fine-grained control.
- Global enhancement is a single toggle in `.env`.
- Per-request headers work for one-off testing.

## Enhancement Models

An enhancement model is the local AI that rewrites your prompt. It is a small, specialized model that runs on your Mac through LM Studio. Think of it as a dedicated writing assistant that lives on your computer.

Enhancement models:

- Run locally. They do not need the internet.
- Are small and fast. Most finish in 1-2 seconds.
- Are separate from the main AI model that answers your question.

### Changing the Enhancement Model

Different apps can use different models. For example, you might want a lightweight model for VS Code and a more capable one for Claude Desktop.

1. Open `~/prompthub/configs/enhancement-rules.json`.
2. Find your app under `"clients"`.
3. Change the `"model"` value to any model available in LM Studio.

```json
{
  "clients": {
    "vscode": { "model": "qwen3-4b-instruct-2507" },
    "claude-desktop": { "model": "qwen3-4b-instruct-2507" }
  }
}
```

**Key points:**

- Enhancement models run locally via LM Studio.
- All clients use the same enhancement model (`qwen3-4b-instruct-2507`) by default.
- You can override the model per client if needed.

## When to Use Enhancement

### Good Fit

- Your prompts tend to be short or vague.
- You want consistently better AI responses.
- You are asking complex, multi-part questions.

### Not Ideal

- Your prompts are already detailed and specific.
- You need the fastest possible response time.
- You are running quick test queries.
- Latency matters more than quality for your use case.

## Performance Impact

Enhancement adds a small delay because PromptHub rewrites your prompt before sending it to the main model.

- **The enhancement model** (`qwen3-4b-instruct-2507`): 1-2 seconds.

For most workflows, the improvement in response quality is worth the wait.

## Troubleshooting

### Enhancement feels slow

- Check if LM Studio is busy with other tasks. Run `lms ps` to see active models.
- Disable enhancement for that app if speed is critical.

### No visible improvement

- Some prompts are already clear. Enhancement helps most with vague or short inputs.
- Try a more complex question to see the difference.
- Check the logs to confirm enhancement is running:

  ```bash
  tail -f ~/prompthub/logs/router-stderr.log
  ```

### Enhancement keeps failing

- Make sure the enhancement model is downloaded:

  ```bash
  lms get qwen3-4b-instruct-2507
  ```

- Verify LM Studio is running:

  ```bash
  lms server start
  ```

-- If you use cloud-based enhancement, check your internet connection.

## Advanced: Custom Enhancement Rules

You can tailor enhancement behavior for each app by editing `~/prompthub/configs/enhancement-rules.json`. Options include:

- Assigning different models to different apps.
- Writing custom system prompts that guide how enhancement rewrites your input.
- Enabling or disabling enhancement per app.

See the **Advanced Power User Manual** for full details.

## How to Disable Enhancement

### Disable for one app

1. Open `~/prompthub/configs/api-keys.json`.
2. Set `"enhance": false` for that app's entry.
3. Save the file. The change takes effect immediately.

### Disable globally

1. Open `~/prompthub/.env`.
2. Change the line to:

   ```
   AUTO_ENHANCE_MCP=false
   ```

3. Restart PromptHub.

## Summary

| Question                       | Answer                                                         |
| ------------------------------ | -------------------------------------------------------------- |
| What does it do?               | Rewrites your prompts automatically for better AI responses.   |
| How do I enable it?            | Set `enhance: true` in your app's entry in `api-keys.json`.   |
| Does it slow things down?      | Adds 1-2 seconds with lightweight models.                      |
| Can I disable it?              | Yes, per-app or globally.                                      |
| How do I know it is working?   | Check the logs or notice better AI responses.                  |

---

Next: Read the **Session Memory Guide** to learn how PromptHub remembers important context across conversations.
