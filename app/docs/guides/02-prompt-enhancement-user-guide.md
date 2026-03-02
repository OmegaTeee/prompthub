# Prompt Enhancement Guide

## What is Prompt Enhancement?

Prompt Enhancement is a feature that **automatically improves your prompts** before sending them to AI models. Think of it as a smart editor that:
- Makes your requests clearer
- Adds helpful context
- Improves the quality of AI responses
- Works transparently in the background

### Without Enhancement
```
You: "Summarize this"
AI: (confused about what "this" is, gives generic response)
```

### With Enhancement
```
You: "Summarize this"
PromptHub: (improves it to) "Please summarize the main ideas and key takeaways from the provided document"
AI: (understands better, gives focused response)
```

## Enabling Enhancement

Enhancement can be enabled in two ways:

### Method 1: Always Enhance (Global Setting)

If you want all your requests enhanced by default:

1. Open the file `~/.local/share/prompthub/.env`
2. Add or change this line:
   ```
   AUTO_ENHANCE_MCP=true
   ```
3. Restart PromptHub
4. From now on, all prompts are automatically improved

### Method 2: Enhance per App (Recommended)

You can enable enhancement for specific apps only:

1. Open `~/.local/share/prompthub/configs/api-keys.json`
2. Find your app's entry (e.g., `sk-prompthub-code-001`)
3. Change `"enhance": false` to `"enhance": true`
4. Save the file
5. The change takes effect immediately — no restart needed

Example:
```json
{
  "keys": {
    "sk-prompthub-code-001": {
      "client_name": "vscode",
      "enhance": true,  // ← Changed to true
      "description": "VS Code (with enhancement)"
    }
  }
}
```

### Method 3: Per-Request (Advanced)

For apps that support custom headers, add this to individual requests:
```
X-Enhance: true
```

This overrides the global setting for just that one request.

## Enhancement Models

Each app can use a different "enhancement model" — this is the AI that improves your prompt. The default is a lightweight model that's fast and efficient.

**What are enhancement models?**
- Small, specialized AI models
- Run locally on your computer
- Improve prompts in 1-2 seconds
- Don't require internet

**Changing the Enhancement Model**

1. Open `~/.local/share/prompthub/configs/enhancement-rules.json`
2. Find your app under `"clients"`
3. Change the `"model"` value to one available in Ollama

Example:
```json
{
  "clients": {
    "vscode": { "model": "gemma3:4b" },
    "claude-desktop": { "model": "gemma3:27b" }
  }
}
```

## When to Use Enhancement

✅ **Use enhancement when:**
- Your prompts are vague or unclear
- You want better quality responses
- You're asking complex questions
- You want AI to suggest improvements

❌ **Skip enhancement when:**
- Your prompts are already very specific
- You need the absolute fastest response
- You're testing with simple queries
- Your app's latency is critical

## Performance Impact

Enabling enhancement adds a small delay:
- **With lightweight models** — 1-2 seconds added
- **With larger models** — 3-5 seconds added

This is usually worth it for better results!

## Troubleshooting Enhancement

### "Enhancement is slow"
- Switch to a faster model: `gemma3:4b` instead of `gemma3:27b`
- Disable enhancement for that app if speed is critical
- Check if Ollama is busy (run other models in the background?)

### "I don't see any improvement"
- Some prompts are already clear and don't need enhancement
- Try asking more complex questions to see the benefit
- Check the logs to verify enhancement is actually running

### "Enhancement keeps failing"
- Make sure the enhancement model is downloaded: `ollama pull gemma3:4b`
- Verify Ollama is running: `ollama serve`
- Check your internet connection (for cloud enhancements)

## Advanced: Custom Enhancement Rules

For power users, you can create custom rules based on your app. Edit `enhancement-rules.json` to:
- Use different models for different clients
- Enable/disable enhancement per client
- Add custom system prompts for enhancement

See **Advanced Power User Manual** for details.

## Disabling Enhancement

If you want to turn off enhancement entirely:

1. Open `~/.local/share/prompthub/.env`
2. Change `AUTO_ENHANCE_MCP=true` to `AUTO_ENHANCE_MCP=false`
3. OR set `"enhance": false` for specific apps in `api-keys.json`
4. Restart PromptHub (if using global setting)

## Summary

| Question | Answer |
|----------|--------|
| What does it do? | Automatically improves your prompts before sending to AI |
| How do I enable it? | Set `enhance: true` in your app's settings |
| Does it slow things down? | Only 1-2 seconds (usually worth it!) |
| Can I disable it? | Yes, per-app or globally |
| How do I know if it's working? | Check the logs or notice better AI responses |

---

Next: Read **Session Memory Guide** to learn how PromptHub remembers important information.
