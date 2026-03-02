# PromptHub Troubleshooting Guide

This guide covers the most common issues and how to fix them.

## Quick Diagnosis

### Step 1: Check System Health

Open Terminal and run:
```bash
python -m cli diagnose
```

You should see:
```
✅ Router is healthy
✅ Ollama is running
✅ Database is accessible
✅ API keys are loaded
✅ All systems operational
```

If any checks fail, scroll down to find your specific issue.

### Step 2: Check the Logs

View the latest errors:
```bash
tail -n 50 ~/.local/share/prompthub/logs/router-stderr.log
```

This shows the last 50 lines. Add `| grep ERROR` to see only errors:
```bash
tail -n 100 ~/.local/share/prompthub/logs/router-stderr.log | grep ERROR
```

### Step 3: Check the Dashboard

Open http://localhost:9090 and look at the **Status** section. Green means healthy, red means there's an issue.

---

## Common Issues

### ❌ "Cannot connect to localhost:9090"

**Problem:** PromptHub isn't running or isn't responding.

**What to try:**

1. **Is PromptHub running?**
   ```bash
   lsof -i :9090
   ```
   If nothing shows up, PromptHub isn't running.

2. **Start it manually:**
   ```bash
   cd ~/.local/share/prompthub
   source .venv/bin/activate
   uvicorn router.main:app --host 127.0.0.1 --port 9090
   ```

3. **Check for error messages:**
   Look at the Terminal output while it starts. Any error messages?

4. **Is another app using port 9090?**
   ```bash
   # Find what's using port 9090
   lsof -i :9090

   # Kill it if needed (replace XXXX with the PID from above)
   kill XXXX
   ```

5. **Restart completely:**
   ```bash
   killall uvicorn 2>/dev/null
   sleep 2
   cd ~/.local/share/prompthub
   source .venv/bin/activate
   uvicorn router.main:app --host 127.0.0.1 --port 9090 --reload
   ```

---

### ❌ "Ollama connection failed"

**Problem:** PromptHub can't reach Ollama.

**What to try:**

1. **Is Ollama running?**
   ```bash
   lsof -i :11434
   ```
   If nothing, Ollama isn't running.

2. **Start Ollama:**
   ```bash
   ollama serve
   ```

3. **Test Ollama directly:**
   ```bash
   curl http://localhost:11434/api/tags
   ```
   Should return a list of models.

4. **Check Ollama is healthy:**
   ```bash
   ollama list
   ```
   Should show installed models.

5. **If Ollama crashes:**
   ```bash
   # Kill any stuck Ollama processes
   killall ollama
   sleep 2

   # Restart
   ollama serve
   ```

---

### ❌ "401 Unauthorized" or "Missing bearer token"

**Problem:** API key is missing or invalid.

**What to try:**

1. **Check your header:**
   Make sure you're sending: `Authorization: Bearer sk-your-key`

2. **Verify the key exists:**
   ```bash
   cat ~/.local/share/prompthub/configs/api-keys.json | grep sk-
   ```

3. **Reload API keys (if you just changed the file):**
   ```bash
   curl -X POST http://localhost:9090/v1/api-keys/reload
   ```

4. **Add a key if missing:**
   Edit `api-keys.json` and add:
   ```json
   "sk-my-test-key": {
     "client_name": "test",
     "enhance": false,
     "description": "Test key"
   }
   ```
   Then reload.

---

### ❌ "404 Model not found"

**Problem:** The model you requested doesn't exist in Ollama.

**What to try:**

1. **List available models:**
   ```bash
   ollama list
   ```

2. **Pull the model:**
   ```bash
   ollama pull gemma3:27b
   ```
   (Replace with the model you want)

3. **Verify it's available via API:**
   ```bash
   curl http://localhost:9090/v1/models \
     -H "Authorization: Bearer sk-your-key"
   ```

4. **Wait for it to finish pulling:**
   Large models take time. Check progress in Ollama's output.

---

### ⏱️ "Request timed out" or "Enhancement taking too long"

**Problem:** An operation is taking longer than expected.

**What to try:**

1. **Disable enhancement temporarily:**
   Edit `api-keys.json`, set `"enhance": false`
   ```bash
   curl -X POST http://localhost:9090/v1/api-keys/reload
   ```

2. **Use a faster model:**
   Change to `gemma3:4b` instead of larger models.

3. **Check system resources:**
   ```bash
   # See what's using CPU/RAM
   top -o %CPU
   ```
   If Ollama is using >80% CPU, your system is overloaded.

4. **Reduce concurrent operations:**
   Don't run multiple large models at the same time.

5. **Increase timeout (advanced):**
   Edit `router/config/settings.py` and increase `ENHANCEMENT_TIMEOUT`.

---

### 💾 "Database is locked" or SQLite errors

**Problem:** Memory database is being accessed by multiple processes.

**What to try:**

1. **Ensure only one PromptHub is running:**
   ```bash
   lsof | grep memory.db
   ```
   Should show only one process.

2. **Kill any stuck processes:**
   ```bash
   # Find all uvicorn processes
   ps aux | grep uvicorn

   # Kill the stuck one
   kill -9 XXXX  # Replace XXXX with PID
   ```

3. **Restart fresh:**
   ```bash
   killall uvicorn 2>/dev/null
   sleep 2
   cd ~/.local/share/prompthub
   uvicorn router.main:app --host 127.0.0.1 --port 9090
   ```

4. **Check database integrity:**
   ```bash
   sqlite3 ~/.prompthub/memory.db "PRAGMA integrity_check;"
   ```
   Should return `ok`. If not, the database may be corrupted.

---

### ❌ "Session not found" or "Memory not working"

**Problem:** Can't access stored sessions or facts.

**What to try:**

1. **Check if session exists:**
   ```bash
   curl http://localhost:9090/sessions \
     -H "Authorization: Bearer sk-your-key"
   ```
   See any sessions? If not, create one:
   ```bash
   curl -X POST http://localhost:9090/sessions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-your-key" \
     -d '{"client_id": "test"}'
   ```

2. **Verify you have the right session ID:**
   Sessions are UUIDs, not short IDs. Check the exact format.

3. **Check database permissions:**
   ```bash
   ls -la ~/.prompthub/memory.db
   ```
   Should show you own the file.

4. **Clear corrupted database (last resort):**
   ```bash
   rm ~/.prompthub/memory.db
   ```
   A new one will be created. This will erase all stored sessions.

---

### 🔥 "Port 9090 already in use"

**Problem:** Another app is using the same port.

**What to try:**

1. **Find what's using port 9090:**
   ```bash
   lsof -i :9090
   ```

2. **Kill the process:**
   ```bash
   kill XXXX  # Replace with PID from above
   ```

3. **Or use a different port:**
   Start PromptHub on a different port:
   ```bash
   uvicorn router.main:app --host 127.0.0.1 --port 9091
   ```
   Then access it at `http://localhost:9091`

---

### 🌐 "Connection refused" when testing localhost

**Problem:** Apps can't connect to PromptHub even though it's running.

**What to try:**

1. **Use the correct address:**
   - ✅ Correct: `http://localhost:9090`
   - ✅ Correct: `http://127.0.0.1:9090`
   - ❌ Wrong: `http://0.0.0.0:9090` (this is the listen address, not a client address)

2. **Test locally first:**
   ```bash
   curl http://localhost:9090/health
   ```

3. **If using hostname:**
   ```bash
   curl http://$(hostname).local:9090/health
   ```

4. **Check firewall:**
   Sometimes Mac's firewall blocks local ports. Try:
   ```bash
   # Add PromptHub to firewall exceptions (if needed)
   # Usually not needed for localhost
   ```

---

### 🔧 "Something broke after an update"

**Problem:** Code changed and now things aren't working.

**What to try:**

1. **Check the error logs:**
   ```bash
   tail -f ~/.local/share/prompthub/logs/router-stderr.log
   ```
   `-f` means "follow" (watch for new errors)

2. **Restart completely:**
   ```bash
   killall uvicorn ollama
   sleep 3
   ollama serve &
   sleep 3
   cd ~/.local/share/prompthub
   uvicorn router.main:app --host 127.0.0.1 --port 9090
   ```

3. **Check for syntax errors:**
   ```bash
   cd ~/.local/share/prompthub/app
   python -m py_compile router/main.py
   ```

4. **Reinstall dependencies:**
   ```bash
   cd ~/.local/share/prompthub
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

5. **As a last resort, restart your Mac**
   Sometimes helps with lingering issues.

---

## Getting More Help

### Check the Logs Carefully

The logs usually tell you exactly what's wrong:

```bash
# See all errors in the last 200 lines
tail -n 200 ~/.local/share/prompthub/logs/router-stderr.log | grep -i error

# See the last 50 lines (most recent first)
tail -n 50 ~/.local/share/prompthub/logs/router-stderr.log

# Watch for new errors in real-time
tail -f ~/.local/share/prompthub/logs/router-stderr.log
```

### Run Diagnostics

```bash
python -m cli diagnose
```

This checks all major systems and tells you what's wrong.

### Check System Health via Dashboard

1. Open http://localhost:9090
2. Click **Health Check** button
3. It will test:
   - ✅ Router running
   - ✅ Ollama responsive
   - ✅ Database accessible
   - ✅ API keys loaded

### Restart Everything

When in doubt, restart:

```bash
# Kill everything
killall uvicorn ollama 2>/dev/null

# Wait a moment
sleep 3

# Start fresh
ollama serve &
sleep 2
cd ~/.local/share/prompthub
source .venv/bin/activate
uvicorn router.main:app --host 127.0.0.1 --port 9090 --reload
```

---

## Quick Reference

| Symptom | First Try | Second Try |
|---------|-----------|-----------|
| Can't access dashboard | Restart PromptHub | Check if Ollama is running |
| Enhancement slow | Disable it | Use smaller model |
| API returns 401 | Check API key format | Reload keys |
| API returns 404 | List models with `ollama list` | Pull missing model |
| Database locked | Restart PromptHub | Check `lsof \| grep memory.db` |
| Timeout errors | Disable enhancement | Increase timeout in settings |
| Port in use | Kill process on port | Use different port |

---

## Still Stuck?

If none of these work:

1. **Collect information:**
   ```bash
   python -m cli diagnose > diagnostics.txt
   tail -n 100 ~/.local/share/prompthub/logs/router-stderr.log >> diagnostics.txt
   ```

2. **Check the logs carefully** — The answer is usually in the error message

3. **Restart your Mac** — Fixes surprising number of issues

4. **Review the other guides** — Maybe you're missing a configuration step

Good luck! 🍀
