# PromptHub Troubleshooting Guide

When something goes wrong, this guide helps you find the cause and fix it. Work through the Quick Diagnosis steps first. If those do not solve the problem, find your specific error in the sections below.

---

## Quick Diagnosis

Think of this like a pre-flight checklist. Run these three checks before digging deeper.

### Step 1: Run the Health Check

Open Terminal and run:

```bash
python -m cli diagnose
```

You should see output like this:

```
Router is healthy
LM Studio is running
Database is accessible
API keys are loaded
All systems operational
```

If any check fails, find the matching section below for a fix.

### Step 2: Check the Logs

The log file records errors as they happen. View the most recent entries:

```bash
tail -n 50 ~/prompthub/logs/router-stderr.log
```

To show only error lines:

```bash
tail -n 100 ~/prompthub/logs/router-stderr.log | grep ERROR
```

### Step 3: Check the Dashboard

Open http://localhost:9090 in your browser. Look at the **Status** section. Green means healthy. Red means something needs attention.

**Key takeaways:**
- Run `python -m cli diagnose` first -- it checks everything at once.
- Logs tell you exactly what went wrong and when.
- The dashboard gives you a visual health overview.

---

## Common Issues

### "Cannot connect to localhost:9090"

**Problem:** PromptHub is not running or not responding. This is like trying to call a phone that is turned off.

**Fix -- work through these steps in order:**

1. Check if PromptHub is running:
   ```bash
   lsof -i :9090
   ```
   If nothing appears, PromptHub is not running. Move to step 2.

2. Start it manually:
   ```bash
   cd ~/prompthub
   source .venv/bin/activate
   uvicorn router.main:app --host 127.0.0.1 --port 9090
   ```

3. Watch the Terminal output for error messages as it starts.

4. If another app is using port 9090, find and stop it:
   ```bash
   # See what is using port 9090
   lsof -i :9090

   # Stop it (replace XXXX with the PID from above)
   kill XXXX
   ```

5. If all else fails, restart completely:
   ```bash
   killall uvicorn 2>/dev/null
   sleep 2
   cd ~/prompthub
   source .venv/bin/activate
   uvicorn router.main:app --host 127.0.0.1 --port 9090 --reload
   ```

---

### "LM Studio connection failed"

**Problem:** PromptHub cannot reach LM Studio. LM Studio is the engine that runs your AI models. If it is not running, no model requests will work.

**Fix -- work through these steps in order:**

1. Check if LM Studio is running:
   ```bash
   lsof -i :11434
   ```
   If nothing appears, LM Studio is not running.

2. Start LM Studio:
   ```bash
   lms server start
   ```

3. Test LM Studio directly:
   ```bash
   curl http://localhost:11434/api/tags
   ```
   This should return a list of models.

4. Confirm installed models:
   ```bash
   lms ls
   ```

5. If LM Studio is stuck or crashing, restart it:
   ```bash
   lms server stop || true
   sleep 2
   lms server start
   ```

---

### "401 Unauthorized" or "Missing bearer token"

**Problem:** Your API key is missing, misspelled, or not loaded. A bearer token is a security code in the format `Authorization: Bearer sk-YOUR-KEY`. Think of it like entering the wrong password at a door.

**Fix -- work through these steps in order:**

1. Check that your request header uses this exact format:
   ```
   Authorization: Bearer sk-your-key
   ```

2. Confirm the key exists in the config file:
   ```bash
   cat ~/prompthub/configs/api-keys.json | grep sk-
   ```

3. If you recently edited the file, reload the keys:
   ```bash
   curl -X POST http://localhost:9090/v1/api-keys/reload
   ```

4. If no key exists, add one. Edit `api-keys.json` and insert:
   ```json
   "sk-my-test-key": {
     "client_name": "test",
     "enhance": false,
     "description": "Test key"
   }
   ```
   Then reload with the command from step 3.

---

### "404 Model not found"

**Problem:** You asked for a model that LM Studio does not have. It is like requesting a book the library has not stocked yet.

**Fix -- work through these steps in order:**

1. List the models you have:
   ```bash
   lms ls
   ```

2. Download the model you need:
   ```bash
   lms get qwen3-4b-instruct-2507
   ```
   Replace `qwen3-4b-instruct-2507` with whatever model you want.

3. Confirm it shows up through the API:
   ```bash
   curl http://localhost:9090/v1/models \
     -H "Authorization: Bearer sk-your-key"
   ```

4. Large models take time to download. Check progress in the LM Studio output.

---

### "Request timed out" or "Enhancement taking too long"

**Problem:** An operation is running longer than the allowed time. This often happens when a large model is doing enhancement on a busy machine. Think of it like a queue at a busy counter -- too many tasks, not enough power.

**Fix -- work through these steps in order:**

1. Turn off enhancement temporarily. Edit `api-keys.json` and set `"enhance": false`, then reload:
   ```bash
   curl -X POST http://localhost:9090/v1/api-keys/reload
   ```

2. Check if LM Studio is busy with other tasks: run `lms ps`.

3. Check your system resources:
   ```bash
   top -o %CPU
   ```
   If LM Studio is using more than 80% CPU, your system is overloaded.

4. Avoid running multiple large models at the same time.

5. For advanced users: increase the timeout value in `router/config/settings.py` by raising `ENHANCEMENT_TIMEOUT`.

---

### "Database is locked" or SQLite Errors

**Problem:** The database file is being accessed by more than one process at once. Think of it like two people trying to write in the same notebook at the same time.

**Fix -- work through these steps in order:**

1. Check that only one copy of PromptHub is running:
   ```bash
   lsof | grep memory.db
   ```
   You should see only one process listed.

2. Stop any extra processes:
   ```bash
   # Find all uvicorn processes
   ps aux | grep uvicorn

   # Stop the extra one (replace XXXX with the PID)
   kill -9 XXXX
   ```

3. Restart cleanly:
   ```bash
   killall uvicorn 2>/dev/null
   sleep 2
   cd ~/prompthub
   uvicorn router.main:app --host 127.0.0.1 --port 9090
   ```

4. Check database health:
   ```bash
   sqlite3 ~/.prompthub/memory.db "PRAGMA integrity_check;"
   ```
   This should print `ok`. If it does not, the database may be corrupted.

---

### "Session not found" or "Memory not working"

**Problem:** You are trying to access a session that does not exist or the memory database is unavailable.

**Fix -- work through these steps in order:**

1. List your existing sessions:
   ```bash
   curl http://localhost:9090/sessions \
     -H "Authorization: Bearer sk-your-key"
   ```
   If no sessions appear, create one:
   ```bash
   curl -X POST http://localhost:9090/sessions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-your-key" \
     -d '{"client_id": "test"}'
   ```

2. Double-check your session ID. Sessions use full UUIDs (long strings like `a1b2c3d4-e5f6-...`), not short IDs.

3. Verify file permissions:
   ```bash
   ls -la ~/.prompthub/memory.db
   ```
   You should own the file.

4. As a last resort, delete the database. A new one will be created on the next request. **Warning:** this erases all stored sessions.
   ```bash
   rm ~/.prompthub/memory.db
   ```

---

### "Port 9090 already in use"

**Problem:** Another program is already using port 9090. Only one program can listen on a port at a time.

**Fix -- work through these steps in order:**

1. Find what is using the port:
   ```bash
   lsof -i :9090
   ```

2. Stop that process:
   ```bash
   kill XXXX
   ```
   Replace `XXXX` with the PID shown in step 1.

3. Or start PromptHub on a different port instead:
   ```bash
   uvicorn router.main:app --host 127.0.0.1 --port 9091
   ```
   Then access it at `http://localhost:9091`.

---

### "Connection refused" When Testing Localhost

**Problem:** Your app cannot reach PromptHub even though it is running. This is usually an address mismatch.

**Fix -- work through these steps in order:**

1. Use the correct address. These work:
   - `http://localhost:9090`
   - `http://127.0.0.1:9090`

   This does **not** work as a client address:
   - `http://0.0.0.0:9090` (this is a listen/bind address, not a connection address)

2. Test with a quick health check:
   ```bash
   curl http://localhost:9090/health
   ```

3. If you are connecting by hostname:
   ```bash
   curl http://$(hostname).local:9090/health
   ```

4. The macOS firewall rarely blocks localhost traffic. If you suspect it, check System Settings > Network > Firewall.

---

### "Something broke after an update"

**Problem:** Code changed and now things are not working. This is like updating an app and finding a new bug.

**Fix -- work through these steps in order:**

1. Watch the error log in real time (`-f` means "follow new lines"):
   ```bash
   tail -f ~/prompthub/logs/router-stderr.log
   ```

2. Restart everything from scratch:
   ```bash
   killall uvicorn || true
   lms server stop || true
   sleep 3
   lms server start &
   sleep 3
   cd ~/prompthub
   uvicorn router.main:app --host 127.0.0.1 --port 9090
   ```

3. Check for Python syntax errors:
   ```bash
   cd ~/prompthub/app
   python -m py_compile router/main.py
   ```

4. Reinstall dependencies in case something is missing:
   ```bash
   cd ~/prompthub
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

5. If nothing else works, restart your Mac. This clears lingering processes and stale file locks.

---

## Getting More Help

### Read the Logs Carefully

The logs almost always contain the answer. Here are three useful commands:

```bash
# Show errors from the last 200 lines
tail -n 200 ~/prompthub/logs/router-stderr.log | grep -i error

# Show the 50 most recent lines
tail -n 50 ~/prompthub/logs/router-stderr.log

# Watch for new errors as they happen
tail -f ~/prompthub/logs/router-stderr.log
```

### Run Diagnostics

```bash
python -m cli diagnose
```

This checks all major systems and reports what is healthy and what is not.

### Use the Dashboard

1. Open http://localhost:9090 in your browser.
2. Click the **Health Check** button.
3. It tests:
   - Router running
   - LM Studio responsive
   - Database accessible
   - API keys loaded

### Restart Everything

When in doubt, a clean restart often fixes the problem:

sleep 2
```bash
# Stop uvicorn and the LM Studio server (if running)
killall uvicorn 2>/dev/null || true
lms server stop || true

# Wait for them to shut down
sleep 3

# Start LM Studio and PromptHub
lms server start &
sleep 2
cd ~/prompthub
source .venv/bin/activate
uvicorn router.main:app --host 127.0.0.1 --port 9090 --reload
```

**Key takeaways:**
- Logs are your best friend -- read them first.
- `python -m cli diagnose` gives a one-command health report.
- A full restart fixes most mysterious issues.

---

## Quick Reference

| Symptom | First Try | Second Try |
|---------|-----------|-----------|
| Cannot access dashboard | Restart PromptHub | Check if LM Studio is running |
| Enhancement slow | Disable it | Use smaller model |
| API returns 401 | Check API key format | Reload keys |
| API returns 404 | List models with `lms ls` | Pull missing model |
| Database locked | Restart PromptHub | Check `lsof \| grep memory.db` |
| Timeout errors | Disable enhancement | Increase timeout in settings |
| Port in use | Kill process on port | Use different port |

---

## Still Stuck?

If none of the above works, gather information for further debugging:

1. Collect diagnostics into a file:
   ```bash
   python -m cli diagnose > diagnostics.txt
   tail -n 100 ~/prompthub/logs/router-stderr.log >> diagnostics.txt
   ```

2. Read the error messages in that file carefully. The answer is usually there.

3. Restart your Mac. This fixes a surprising number of issues.

4. Review the other guides. You may be missing a configuration step.

Good luck with the fix.
