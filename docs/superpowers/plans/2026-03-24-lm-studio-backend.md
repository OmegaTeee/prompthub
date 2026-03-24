# LM Studio Backend Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Ollama with LM Studio as the local LLM server and rename all internal "Ollama" references to backend-agnostic "LLM" naming.

**Architecture:** Consolidate from two code paths (native Ollama API + OpenAI-compat) to one (OpenAI-compat only). Delete the native client and thinking-token shim. Rename classes, settings, routes, and templates from "Ollama" to "LLM". Install LM Studio and verify all integration points work.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, httpx, LM Studio (Homebrew cask), HTMX templates

**Spec:** `docs/superpowers/specs/2026-03-24-lm-studio-backend-design.md`

---

## File Structure

### Files to Delete
- `app/router/enhancement/ollama.py` — native Ollama client (230 lines)
- `app/router/openai_compat/streaming.py` — thinking-token NDJSON→SSE shim (137 lines)

### Files to Rename
- `app/router/enhancement/ollama_openai.py` → `app/router/enhancement/llm_client.py`
- `app/templates/partials/ollama.html` → `app/templates/partials/llm-models.html`

### Files to Modify (by task)
- **Task 1 (Settings):** `app/router/config/settings.py`, `app/.env.example`
- **Task 2 (Client):** `app/router/enhancement/llm_client.py` (renamed), `app/router/enhancement/__init__.py`
- **Task 3 (Service):** `app/router/enhancement/service.py`
- **Task 4 (Orchestrator):** `app/router/orchestrator/agent.py`
- **Task 5 (Proxy):** `app/router/openai_compat/router.py`, `app/router/openai_compat/models.py`
- **Task 6 (Routes):** `app/router/routes/enhancement.py`, `app/router/routes/health.py`, `app/router/middleware/timeout.py`
- **Task 7 (Main):** `app/router/main.py`
- **Task 8 (Dashboard):** `app/router/dashboard/router.py`, `app/templates/dashboard.html`, `app/templates/partials/llm-models.html` (renamed), `app/templates/partials/stats.html`
- **Task 9 (Docstrings):** `app/router/enhancement/service.py` (module docstring), `app/router/pipelines/documentation.py`, `app/router/routes/pipelines.py`, `app/router/memory/router.py`, `app/router/enhancement/context_window.py`
- **Task 10 (Tests):** All test files listed below
- **Task 11 (Docs):** `CLAUDE.md`, `.claude/steering/product.md`, `.claude/steering/tech.md`, `.claude/steering/structure.md`, `docs/api/openapi.yaml`, `app/pyproject.toml`
- **Task 12 (Install):** LM Studio installation, model downloads, Ollama removal
- **Task 13 (Scripts):** `scripts/prompthub-start.zsh`, `scripts/prompthub-kill.zsh`, `scripts/open-webui/start.sh`
- **Task 14 (Smoke test):** End-to-end verification with LM Studio

---

### Task 1: Settings — Rename Fields and Add Backward-Compat Aliases

**Files:**
- Modify: `app/router/config/settings.py:22-27,102-109`
- Modify: `app/.env.example:8-16`

- [ ] **Step 1: Update settings fields with AliasChoices**

In `app/router/config/settings.py`, replace lines 22-26:

```python
# Before (lines 22-26):
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    ollama_model: str = "qwen3.5:2b"
    ollama_timeout: int = 120
    ollama_api_mode: str = "native"

# After:
    llm_host: str = Field(
        default="localhost",
        validation_alias=AliasChoices("LLM_HOST", "OLLAMA_HOST"),
    )
    llm_port: int = Field(
        default=1234,
        validation_alias=AliasChoices("LLM_PORT", "OLLAMA_PORT"),
    )
    llm_model: str = Field(
        default="qwen3.5:2b",
        validation_alias=AliasChoices("LLM_MODEL", "OLLAMA_MODEL"),
    )
    llm_timeout: int = Field(
        default=120,
        validation_alias=AliasChoices("LLM_TIMEOUT", "OLLAMA_TIMEOUT"),
    )
    # ollama_api_mode: DELETED — only one mode now (OpenAI-compat)
```

Add import at top of file:

```python
from pydantic import AliasChoices, Field
```

- [ ] **Step 2: Update model_post_init normalization**

Replace lines 102-109:

```python
# Before:
        host = self.ollama_host
        if "://" in host:
            host = host.split("://", 1)[1]
        if ":" in host:
            host = host.split(":", 1)[0]
        self.ollama_host = host

# After:
        host = self.llm_host
        if "://" in host:
            host = host.split("://", 1)[1]
        if ":" in host:
            host = host.split(":", 1)[0]
        self.llm_host = host
```

Update the comment on lines 102-103:

```python
# Before:
        # Normalize ollama_host: strip scheme and port if present
        # (handles OLLAMA_HOST=http://localhost:11434 from system env)

# After:
        # Normalize llm_host: strip scheme and port if present
        # (handles LLM_HOST=http://localhost:1234 from system env)
```

- [ ] **Step 3: Update .env.example**

Replace lines 8-16 in `app/.env.example`:

```bash
# Local LLM server (LM Studio, Ollama, or any OpenAI-compatible server)
LLM_HOST=localhost
LLM_PORT=1234
LLM_MODEL=qwen3.5:2b
LLM_TIMEOUT=120
# Legacy aliases (still work): OLLAMA_HOST, OLLAMA_PORT, OLLAMA_MODEL, OLLAMA_TIMEOUT
```

- [ ] **Step 4: Run tests to check nothing breaks at import level**

Run: `cd app && python -c "from router.config import get_settings; s = get_settings(); print(s.llm_host, s.llm_port)"`

Expected: `localhost 1234` (or `localhost 11434` if your `.env` still has `OLLAMA_PORT=11434` — that's correct backward-compat behavior; it will update when you change `.env` in Task 12)

- [ ] **Step 5: Commit**

```bash
git add app/router/config/settings.py app/.env.example
git commit -m "feat: rename ollama_* settings to llm_* with backward-compat aliases"
```

---

### Task 2: Rename the OpenAI-Compat Client

**Files:**
- Rename: `app/router/enhancement/ollama_openai.py` → `app/router/enhancement/llm_client.py`
- Modify: `app/router/enhancement/llm_client.py` (class renames)
- Modify: `app/router/enhancement/__init__.py`
- Delete: `app/router/enhancement/ollama.py`

- [ ] **Step 1: Rename the file**

```bash
cd app && git mv router/enhancement/ollama_openai.py router/enhancement/llm_client.py
```

- [ ] **Step 2: Rename classes in llm_client.py**

In `app/router/enhancement/llm_client.py`:

| Line | Before | After |
|---|---|---|
| 2 | `"""OpenAI-compatible client for Ollama."""` | `"""OpenAI-compatible client for local LLM servers."""` |
| 20 | `class OpenAICompatConfig` | `class LLMConfig` |
| 56 | `class OllamaOpenAIError` | `class LLMError` |
| 62 | `class OllamaOpenAIConnectionError(OllamaOpenAIError)` | `class LLMConnectionError(LLMError)` |
| 68 | `class OllamaOpenAIModelError(OllamaOpenAIError)` | `class LLMModelError(LLMError)` |
| 74 | `class OllamaOpenAIClient` | `class LLMClient` |

Also update all log messages that say "Ollama" to "LLM server" (lines 251, 252, 257, 258, 261, 262) and all docstrings that mention "Ollama" (lines 5-8, 78-93, 130, 133, 147).

- [ ] **Step 3: Delete the native client**

```bash
cd app && git rm router/enhancement/ollama.py
```

- [ ] **Step 4: Update __init__.py exports**

Replace the imports and `__all__` in `app/router/enhancement/__init__.py`:

```python
# Before (lines 9-16):
from router.enhancement.ollama import (
    OllamaClient,
    OllamaConfig,
    OllamaConnectionError,
    OllamaError,
    OllamaModelError,
    OllamaResponse,
)

# After:
from router.enhancement.llm_client import (
    LLMClient,
    LLMConfig,
    LLMConnectionError,
    LLMError,
    LLMModelError,
)
```

Update `__all__` (lines 33-38):

```python
# Before:
    "OllamaClient",
    "OllamaConfig",
    "OllamaConnectionError",
    "OllamaError",
    "OllamaModelError",
    "OllamaResponse",

# After:
    "LLMClient",
    "LLMConfig",
    "LLMConnectionError",
    "LLMError",
    "LLMModelError",
```

Also update the `ollama_openai` imports if present (check for `from router.enhancement.ollama_openai import`).

- [ ] **Step 5: Verify imports resolve**

Run: `cd app && python -c "from router.enhancement import LLMClient, LLMConfig, LLMError; print('OK')"`

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add -A app/router/enhancement/
git commit -m "feat: rename Ollama client to LLMClient, delete native client"
```

---

### Task 3: Simplify Enhancement Service

This is the most complex single-file change — the dual-mode switching and two error hierarchies collapse into one.

**Files:**
- Modify: `app/router/enhancement/service.py:26-37,133,177-193,210,524,556-577,597,609`

- [ ] **Step 1: Replace imports**

```python
# Before (lines 26-37):
from router.enhancement.ollama import (
    OllamaClient,
    OllamaConfig,
    OllamaConnectionError,
    OllamaError,
)
from router.enhancement.ollama_openai import (
    OllamaOpenAIClient,
    OllamaOpenAIConnectionError,
    OllamaOpenAIError,
    OpenAICompatConfig,
)

# After:
from router.enhancement.llm_client import (
    LLMClient,
    LLMConfig,
    LLMConnectionError,
    LLMError,
)
```

- [ ] **Step 2: Update type annotation and constructor parameter**

```python
# Before (line 133):
    _ollama: OllamaClient | OllamaOpenAIClient

# After:
    _llm: LLMClient

# Before (line 138):
    def __init__(self, ..., ollama_config: OllamaConfig | None = None, ...):

# After:
    def __init__(self, ..., llm_config: LLMConfig | None = None, ...):
```

Update all references to `ollama_config` parameter within the constructor body to `llm_config`.

- [ ] **Step 3: Simplify __init__ — remove mode switching**

Replace the mode-switching block (lines 177-193). Remove `self._api_mode = settings.ollama_api_mode` (line 177). Replace the `if/else` block with:

```python
        llm_config = LLMConfig(
            base_url=f"http://{settings.llm_host}:{settings.llm_port}/v1",
            timeout=float(settings.llm_timeout),
        )
        self._llm = LLMClient(llm_config)
        logger.info("Using OpenAI-compatible LLM API at %s", llm_config.base_url)
```

- [ ] **Step 4: Update circuit breaker name**

```python
# Before (line 210):
        self._circuit_breaker = CircuitBreaker("ollama", ...)

# After:
        self._circuit_breaker = CircuitBreaker("llm", ...)
```

- [ ] **Step 5: Remove isinstance check**

```python
# Before (line 524):
            if isinstance(self._ollama, OllamaOpenAIClient):

# After — remove the isinstance check entirely, keep only the OpenAI-compat branch
```

- [ ] **Step 6: Simplify error handling**

```python
# Before (lines 565-577):
        except (OllamaConnectionError, OllamaOpenAIConnectionError) as e:
            logger.warning("Ollama connection failed: %s", e)
            ...
        except (OllamaError, OllamaOpenAIError) as e:
            logger.error("Ollama error: %s", e)

# After:
        except LLMConnectionError as e:
            logger.warning("LLM connection failed: %s", e)
            ...
        except LLMError as e:
            logger.error("LLM error: %s", e)
```

- [ ] **Step 7: Update provider and stats strings**

```python
# Before (line 562):
                provider="ollama",
# After:
                provider="llm",

# Before (line 597):
            "ollama_healthy": await self._ollama.is_healthy(),
# After:
            "llm_healthy": await self._llm.is_healthy(),

# Before (line 609):
            logger.info("Ollama circuit breaker reset")
# After:
            logger.info("LLM circuit breaker reset")
```

- [ ] **Step 8: Replace all remaining `self._ollama` references with `self._llm`**

Search and replace `self._ollama` → `self._llm` throughout the file.

- [ ] **Step 9: Verify import chain**

Run: `cd app && python -c "from router.enhancement.service import EnhancementService; print('OK')"`

Expected: `OK`

- [ ] **Step 10: Commit**

```bash
git add app/router/enhancement/service.py
git commit -m "feat: simplify enhancement service to single LLM client code path"
```

---

### Task 4: Port Orchestrator to OpenAI-Compat Client

**Files:**
- Modify: `app/router/orchestrator/agent.py:26,88-90,113-118,147,151,275`

- [ ] **Step 1: Replace import**

```python
# Before (line 26):
from router.enhancement.ollama import OllamaClient, OllamaConfig

# After:
from router.enhancement.llm_client import LLMClient, LLMConfig
```

- [ ] **Step 2: Update __init__ and type annotations**

```python
# Before (lines 88-90):
    def __init__(self, ollama_config: OllamaConfig | None = None):
        self._config = ollama_config or OllamaConfig()
        self._client = OllamaClient(self._config)

# After:
    def __init__(self, llm_config: LLMConfig | None = None):
        self._config = llm_config or LLMConfig()
        self._client = LLMClient(self._config)
```

- [ ] **Step 3: Update initialize() method (lines 105-118)**

The `initialize()` method uses `self._client.is_healthy()` and `self._client.has_model(MODEL)`. Both methods exist on `LLMClient` and use `/v1/models` (not the native `/api/tags`), so they work as-is. Only update the log messages:

```python
# Before (lines 111-115):
                f"Orchestrator model '{MODEL}' not found in Ollama. "
                f"Pull with: ollama pull {MODEL}. "
                f"Orchestrator will pass-through until model is available."

# After:
                f"Orchestrator model '{MODEL}' not found on LLM server. "
                f"Load it in LM Studio or your model server. "
                f"Orchestrator will pass-through until model is available."

# Before (line 118):
            logger.warning("Ollama unavailable — orchestrator disabled until Ollama starts.")

# After:
            logger.warning("LLM server unavailable — orchestrator disabled until server starts.")
```

- [ ] **Step 4: Update _call_model() method (lines 204-223)**

The native client's `generate()` returns `OllamaResponse` with `.response` (plain string). The `LLMClient.chat_completion()` returns `ChatCompletionResponse` with `.choices[0].message.content`. Replace the full call block:

```python
# Before (lines 212-223):
            response = await self._client.generate(
                model=MODEL,
                prompt=user_msg,
                system=SYSTEM_PROMPT,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            self._breaker.record_success()
        except Exception as e:
            self._breaker.record_failure(e)
            raise
        raw = _strip_think_blocks(response.response)

# After:
            response = await self._client.chat_completion(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            self._breaker.record_success()
        except Exception as e:
            self._breaker.record_failure(e)
            raise
        content = response.choices[0].message.content
        raw = _strip_think_blocks(content)
```

- [ ] **Step 5: Update remaining log messages and string literals**

```python
# Lines 147, 151: "Ollama unavailable" → "LLM server unavailable"
```

- [ ] **Step 6: Update factory function**

```python
# Before (line 275):
def get_orchestrator_agent(ollama_config: OllamaConfig | None = None) -> OrchestratorAgent:

# After:
def get_orchestrator_agent(llm_config: LLMConfig | None = None) -> OrchestratorAgent:
```

Update the body to pass `llm_config` instead of `ollama_config`.

- [ ] **Step 7: Verify**

Run: `cd app && python -c "from router.orchestrator.agent import OrchestratorAgent; print('OK')"`

Expected: `OK`

- [ ] **Step 8: Commit**

```bash
git add app/router/orchestrator/agent.py
git commit -m "feat: port orchestrator from native Ollama to OpenAI-compat LLMClient"
```

---

### Task 5: Simplify OpenAI-Compat Proxy Layer

**Files:**
- Modify: `app/router/openai_compat/router.py:19-24,29,40-41,61-63,140,157,285,327-337,367+`
- Modify: `app/router/openai_compat/models.py:10`
- Delete: `app/router/openai_compat/streaming.py`

- [ ] **Step 1: Delete the streaming shim**

```bash
cd app && git rm router/openai_compat/streaming.py
```

- [ ] **Step 2: Update imports in router.py**

```python
# Before (lines 19-24):
from router.enhancement.ollama_openai import (
    OllamaOpenAIClient,
    OllamaOpenAIConnectionError,
    OllamaOpenAIError,
    OpenAICompatConfig,
)

# After:
from router.enhancement.llm_client import (
    LLMClient,
    LLMConfig,
    LLMConnectionError,
    LLMError,
)

# Delete line 29:
from router.openai_compat.streaming import stream_ollama_response
```

- [ ] **Step 3: Rename function params and variables**

```python
# Before (lines 40-41):
    ollama_base_url: str = "http://localhost:11434/v1",
    ollama_timeout: float = 120.0,

# After:
    llm_base_url: str = "http://localhost:1234/v1",
    llm_timeout: float = 120.0,

# Before (lines 61-63):
    _ollama_client = OllamaOpenAIClient(
        OpenAICompatConfig(base_url=ollama_base_url, timeout=ollama_timeout)
    )

# After:
    _llm_client = LLMClient(
        LLMConfig(base_url=llm_base_url, timeout=llm_timeout)
    )
```

Replace all `_ollama_client` → `_llm_client` throughout the file.

- [ ] **Step 4: Update circuit breaker key**

```python
# Before (line 140):
        breaker = cb_registry.get("ollama-proxy") if cb_registry else None

# After:
        breaker = cb_registry.get("llm-proxy") if cb_registry else None
```

- [ ] **Step 5: Update error messages and audit strings**

Replace all `resource_type="ollama"` → `resource_type="llm"` throughout.

```python
# Line 157:
"Service temporarily unavailable — LLM circuit breaker open"

# Line 285:
f"Cannot reach LLM server: {e}"
```

- [ ] **Step 6: Replace streaming with direct httpx SSE passthrough**

The streaming path (around line 327) currently calls `stream_ollama_response()` which routes through native `/api/chat`. Replace with direct passthrough to `/v1/chat/completions`:

```python
async def _stream_with_breaker(payload, breaker, llm_client):
    """Stream chat completion via OpenAI-compat /v1/chat/completions."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(llm_client._config.timeout)) as client:
        async with client.stream(
            "POST",
            f"{llm_client._config.base_url}/chat/completions",
            json=payload,
            headers=llm_client._config.extra_headers or {},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    yield f"{line}\n\n"
    yield "data: [DONE]\n\n"
```

- [ ] **Step 7: Delete `_chat_via_native_api` and `_ollama_base_from_v1`**

Remove the `_chat_via_native_api()` function (line 367+) and any `_ollama_base_from_v1` helper. Non-streaming requests now use `_llm_client.chat_completion()` directly.

- [ ] **Step 8: Update error exception types**

```python
# Before:
    except OllamaOpenAIConnectionError as e:
    except OllamaOpenAIError as e:

# After:
    except LLMConnectionError as e:
    except LLMError as e:
```

- [ ] **Step 9: Update models.py comment**

In `app/router/openai_compat/models.py` line 10:

```python
# Before:
    Response models are reused from router.enhancement.ollama_openai.

# After:
    Response models are reused from router.enhancement.llm_client.
```

- [ ] **Step 10: Verify**

Run: `cd app && python -c "from router.openai_compat import create_openai_compat_router; print('OK')"`

Expected: `OK`

- [ ] **Step 11: Commit**

```bash
git add -A app/router/openai_compat/
git commit -m "feat: simplify /v1/ proxy — delete thinking shim, use direct SSE passthrough"
```

---

### Task 6: Rename Route Paths

**Files:**
- Modify: `app/router/routes/enhancement.py:1,49,95,103,142`
- Modify: `app/router/routes/health.py:27-38`
- Modify: `app/router/middleware/timeout.py:28`

- [ ] **Step 1: Update enhancement route paths**

In `app/router/routes/enhancement.py`:

```python
# Line 1:
"""Prompt enhancement (LLM) endpoints."""

# Line 49:
    @router.post("/llm/enhance")

# Line 95:
    @router.get("/llm/stats")

# Line 103:
    @router.post("/llm/orchestrate", response_model=OrchestrateResponse)

# Line 142:
    @router.post("/llm/reset")
```

- [ ] **Step 2: Update health route**

In `app/router/routes/health.py`:

```python
# Before (lines 27-38):
        ollama_status = "unknown"
        ...
        ollama_status = "up" if stats.get("ollama_healthy") else "down"
        ...
        "ollama": ollama_status,

# After:
        llm_status = "unknown"
        ...
        llm_status = "up" if stats.get("llm_healthy") else "down"
        ...
        "llm": llm_status,
```

- [ ] **Step 3: Update timeout path**

In `app/router/middleware/timeout.py` line 28:

```python
# Before:
    "/ollama/enhance": 180.0,

# After:
    "/llm/enhance": 180.0,
```

- [ ] **Step 4: Commit**

```bash
git add app/router/routes/enhancement.py app/router/routes/health.py app/router/middleware/timeout.py
git commit -m "feat: rename /ollama/* routes to /llm/*"
```

---

### Task 7: Update main.py

**Files:**
- Modify: `app/router/main.py:26,183-186,211,402-411,523,536-538`

- [ ] **Step 1: Update import**

```python
# Before (line 26):
from router.enhancement import EnhancementService, OllamaConfig

# After:
from router.enhancement import EnhancementService, LLMConfig
```

- [ ] **Step 2: Update config construction**

```python
# Before (lines 183-186):
    ollama_config = OllamaConfig(
        base_url=f"http://{settings.ollama_host}:{settings.ollama_port}",
        timeout=float(settings.ollama_timeout),
    )

# After:
    llm_config = LLMConfig(
        base_url=f"http://{settings.llm_host}:{settings.llm_port}/v1",
        timeout=float(settings.llm_timeout),
    )
```

Note: the `/v1` suffix is added here because `LLMConfig` expects an OpenAI-compat base URL.

- [ ] **Step 3: Update orchestrator call**

```python
# Before (line 211):
    orchestrator_agent = get_orchestrator_agent(ollama_config)

# After:
    orchestrator_agent = get_orchestrator_agent(llm_config)
```

- [ ] **Step 4: Rename _get_ollama_info → _get_llm_info**

```python
# Before (line 402):
async def _get_ollama_info():

# After:
async def _get_llm_info():
```

Update the URL inside to use `settings.llm_host` and `settings.llm_port` (lines 410-411).

- [ ] **Step 5: Update dashboard router call**

```python
# Before (line 523):
    create_dashboard_router(..., get_ollama_info=_get_ollama_info, ...)

# After:
    create_dashboard_router(..., get_llm_info=_get_llm_info, ...)
```

- [ ] **Step 6: Update openai_compat router call**

```python
# Before (lines 536-538):
    ollama_base_url=f"http://{_openai_settings.ollama_host}:{_openai_settings.ollama_port}/v1",
    ollama_timeout=float(_openai_settings.ollama_timeout),

# After:
    llm_base_url=f"http://{_openai_settings.llm_host}:{_openai_settings.llm_port}/v1",
    llm_timeout=float(_openai_settings.llm_timeout),
```

- [ ] **Step 7: Verify app starts**

Run: `cd app && python -c "from router.main import app; print('FastAPI app created')"`

Expected: `FastAPI app created`

- [ ] **Step 8: Commit**

```bash
git add app/router/main.py
git commit -m "feat: update main.py to use LLM naming throughout"
```

---

### Task 8: Update Dashboard and Templates

**Files:**
- Modify: `app/router/dashboard/router.py:42,60,149,398-407`
- Rename: `app/templates/partials/ollama.html` → `app/templates/partials/llm-models.html`
- Modify: `app/templates/dashboard.html:66-74`
- Modify: `app/templates/partials/stats.html:22-37`
- Modify: `app/templates/partials/llm-models.html` (after rename)

- [ ] **Step 1: Rename the template file**

```bash
cd app && git mv templates/partials/ollama.html templates/partials/llm-models.html
```

- [ ] **Step 2: Update llm-models.html content**

```html
<!-- Before line 1: -->
<h3>&#x1F9E0; Ollama Models</h3>

<!-- After: -->
<h3>&#x1F9E0; Local Models</h3>

<!-- Before line 17: -->
<p class="text-muted">No models available (Ollama may be down)</p>

<!-- After: -->
<p class="text-muted">No models available (LLM server may be down)</p>
```

- [ ] **Step 3: Update dashboard.html**

```html
<!-- Before (lines 66-74): -->
        <!-- Ollama & API Clients -->
        <div
          class="card"
          hx-get="/dashboard/ollama-partial"
          hx-trigger="load, every 30s"
          hx-swap="innerHTML"
        >
          <div class="loading">Loading Ollama info</div>
        </div>

<!-- After: -->
        <!-- Local Models & API Clients -->
        <div
          class="card"
          hx-get="/dashboard/llm-partial"
          hx-trigger="load, every 30s"
          hx-swap="innerHTML"
        >
          <div class="loading">Loading LLM info</div>
        </div>
```

- [ ] **Step 4: Update stats.html**

```html
<!-- Before (line 22): -->
<h3 style="margin-top: 25px;">&#x1F916; Ollama Status</h3>

<!-- After: -->
<h3 style="margin-top: 25px;">&#x1F916; LLM Status</h3>
```

Replace all `ollama_healthy` → `llm_healthy` and `<strong>Ollama</strong>` → `<strong>LLM</strong>` in the template.

- [ ] **Step 5: Update dashboard/router.py**

```python
# Before (line 42):
    get_ollama_info: Callable[[], Any] | None = None,

# After:
    get_llm_info: Callable[[], Any] | None = None,

# Before (line 60):
    get_ollama_info: Function to get Ollama models and API keys summary

# After:
    get_llm_info: Function to get local models and API keys summary

# Before (line 149):
                "ollama_healthy": stats.get("ollama_healthy", False),

# After:
                "llm_healthy": stats.get("llm_healthy", False),

# Before (lines 398-407):
    @router.get("/ollama-partial", response_class=HTMLResponse)
    async def ollama_partial(request: Request):
        """HTMX partial: Ollama models and API clients."""
        if not get_ollama_info:
            return HTMLResponse("<p class='text-muted'>Ollama panel not configured</p>")
        info = await get_ollama_info()
        ...
            "partials/ollama.html",

# After:
    @router.get("/llm-partial", response_class=HTMLResponse)
    async def llm_partial(request: Request):
        """HTMX partial: local models and API clients."""
        if not get_llm_info:
            return HTMLResponse("<p class='text-muted'>LLM panel not configured</p>")
        info = await get_llm_info()
        ...
            "partials/llm-models.html",
```

- [ ] **Step 6: Commit**

```bash
git add app/router/dashboard/router.py app/templates/
git commit -m "feat: rename dashboard Ollama panel to LLM"
```

---

### Task 9: Update Docstrings in Other Modules

**Files:**
- Modify: `app/router/pipelines/documentation.py` (3 docstring refs)
- Modify: `app/router/routes/pipelines.py` (1 docstring ref)
- Modify: `app/router/memory/router.py` (3 docstring refs)
- Modify: `app/router/enhancement/context_window.py:36` (1 comment)

- [ ] **Step 1: Update all "Ollama" → "LLM" in docstrings**

In each file, find-and-replace "Ollama" → "local LLM" or "LLM server" in docstrings and comments only. Do not change code logic.

In `app/router/enhancement/service.py`, update the module docstring (lines 1-13) — it mentions "Ollama" six times.

In `context_window.py` line 36:

```python
# Before:
# Source: Ollama /api/show -> model_info.<arch>.context_length

# After:
# Source: model metadata (context_length from model manifest)
```

- [ ] **Step 2: Commit**

```bash
git add app/router/enhancement/service.py app/router/pipelines/ app/router/routes/pipelines.py app/router/memory/router.py app/router/enhancement/context_window.py
git commit -m "docs: update Ollama references in module docstrings to LLM"
```

---

### Task 10: Update Test Files

**Files:**
- Modify: `app/tests/test_enhancement.py` (skipped but has Ollama references)
- Modify: `app/tests/test_openai_compat.py:96-97`
- Modify: `app/tests/test_endpoints.py:36,236`
- Modify: `app/tests/test_cloud_fallback.py:18,323,346,388,409`
- Modify: `app/tests/unit/test_orchestrator.py` (mock targets)
- Modify: `app/tests/integration/test_enhancement_and_caching.py` (route paths)
- Modify: `app/tests/integration/test_client_integrations.py` (route paths)
- Modify: `app/pyproject.toml:18`

- [ ] **Step 1: Update test_openai_compat.py**

```python
# Before (lines 96-97):
    ollama_base_url="http://localhost:11434/v1",
    ollama_timeout=30.0,

# After:
    llm_base_url="http://localhost:1234/v1",
    llm_timeout=30.0,
```

- [ ] **Step 2: Update test_endpoints.py**

```python
# Before (line 36):
    data["services"]["ollama"]
# After:
    data["services"]["llm"]

# Before (line 236):
    assert "ollama" in data["services"]
# After:
    assert "llm" in data["services"]
```

- [ ] **Step 3: Update test_cloud_fallback.py**

```python
# Before (line 18):
from router.enhancement.ollama_openai import OpenAICompatConfig

# After:
from router.enhancement.llm_client import LLMConfig

# Before (lines 323, 346, 388, 409 — inline imports):
from router.enhancement.ollama import OllamaConnectionError

# After:
from router.enhancement.llm_client import LLMConnectionError
```

Update all `OllamaConnectionError` → `LLMConnectionError` and `OpenAICompatConfig` → `LLMConfig` throughout.

- [ ] **Step 4: Update test_orchestrator.py mock targets**

The mocks target `agent._client.generate` (native API). Update to target `agent._client.chat_completion` (OpenAI-compat API) and adjust mock return values to match the `ChatCompletionResponse` format.

- [ ] **Step 5: Update test_enhancement.py**

In `app/tests/test_enhancement.py`, update any `mock_ollama_client` references and Ollama import paths. The file is currently skipped (`pytest.mark.skip`) but broken imports would cause collection errors.

- [ ] **Step 6: Update integration test route paths**

In `test_enhancement_and_caching.py` and `test_client_integrations.py`, replace all `/ollama/enhance` → `/llm/enhance`.

- [ ] **Step 7: Update pyproject.toml marker**

```toml
# Before (line 18):
    "requires_ollama: Tests that require Ollama to be running",

# After:
    "requires_llm: Tests that require a local LLM server to be running",
```

- [ ] **Step 8: Run full test suite**

Run: `cd app && pytest tests/ -v --tb=short 2>&1 | tail -30`

Expected: All tests pass (with updated imports/paths). Fix any failures before proceeding.

- [ ] **Step 9: Commit**

```bash
git add app/tests/ app/pyproject.toml
git commit -m "test: update all test files for Ollama → LLM rename"
```

---

### Task 11: Update Documentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.claude/steering/product.md`
- Modify: `.claude/steering/tech.md`
- Modify: `.claude/steering/structure.md`
- Modify: `docs/api/openapi.yaml`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update CLAUDE.md**

Replace all "Ollama" references with appropriate alternatives:
- Module table: `enhancement/` description → "LLM HTTP client (OpenAI-compat), per-client prompt enhancement..."
- Architecture → "LLM server" instead of "Ollama"
- Settings table → `LLM_HOST`, `LLM_PORT`, etc.
- API endpoints → `/llm/enhance`, `/llm/stats`, `/llm/orchestrate`
- Config files description → update `.env` description
- Key patterns → update timeout and model references

- [ ] **Step 2: Update steering docs**

In each of `product.md`, `tech.md`, `structure.md`: replace "Ollama" with "local LLM server" or "LM Studio" as appropriate to the context. Keep mentions in historical context (e.g., "previously used Ollama").

- [ ] **Step 3: Update openapi.yaml**

Replace `/ollama/enhance` → `/llm/enhance` and other renamed paths. Update descriptions.

- [ ] **Step 4: Add CHANGELOG entry**

Under `## [Unreleased]` → `### Changed`:

```markdown
- **LLM backend abstraction**: Renamed all internal "Ollama" references to backend-agnostic "LLM" naming. Deleted native Ollama API client (~230 lines) and thinking-token NDJSON→SSE shim (~140 lines). One OpenAI-compatible code path works with LM Studio, Ollama, or any `/v1/` server. Settings: `LLM_HOST`, `LLM_PORT`, `LLM_MODEL`, `LLM_TIMEOUT` (old `OLLAMA_*` names still work as aliases). Routes: `/ollama/enhance` → `/llm/enhance`, `/ollama/stats` → `/llm/stats`, `/ollama/orchestrate` → `/llm/orchestrate`. Dashboard: "Ollama Models" → "Local Models".
```

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md CHANGELOG.md .claude/steering/ docs/api/openapi.yaml
git commit -m "docs: update all documentation for LLM backend rename"
```

---

### Task 12: Install LM Studio and Remove Ollama

This task handles the actual server swap on your machine.

**Prerequisites:** All code changes (Tasks 1-11) must be committed and tests passing.

- [ ] **Step 1: Stop Ollama**

```bash
# Stop the Ollama service
brew services stop ollama
# Verify it's stopped
pgrep -x ollama && echo "Still running" || echo "Stopped"
```

- [ ] **Step 2: Install LM Studio**

```bash
brew install --cask lm-studio
```

- [ ] **Step 3: Launch LM Studio and start the server**

Open LM Studio from Applications. In LM Studio:
1. Go to the **Developer** tab (left sidebar)
2. Click **Start Server** — it will listen on `localhost:1234`
3. Verify: `curl http://localhost:1234/v1/models`

- [ ] **Step 4: Download models**

Use LM Studio's CLI (`lms`) or the GUI to download models. The essential models to download first:

```bash
# From LM Studio CLI (if available):
lms get qwen/qwen3.5-2b-gguf
lms get qwen/qwen3-14b-gguf

# Or use the GUI: Search tab → search each model → download Q8_0 quantization
```

Full model list to match current Ollama inventory:

| Ollama name | LM Studio search term | Priority |
|---|---|---|
| `qwen3.5:2b` | `qwen3.5-2b` | High — default enhancement |
| `qwen3:14b` | `qwen3-14b` | High — orchestrator |
| `gemma3:27b` | `gemma3-27b` | Medium — Claude Desktop enhancement |
| `gemma3:4b` | `gemma3-4b` | Low — fallback only |
| `qwen3-coder:30b` | `qwen3-coder-30b` | Low — Claude Code enhancement |
| `bge-m3` | `bge-m3` | Low — embeddings (check LM Studio compatibility) |

- [ ] **Step 5: Verify LM Studio serves models**

```bash
curl -s http://localhost:1234/v1/models | python3 -m json.tool
```

Expected: JSON response with model IDs matching what was loaded.

- [ ] **Step 6: Update .env with new port**

In `app/.env`, update:

```bash
LLM_HOST=localhost
LLM_PORT=1234
LLM_MODEL=qwen3.5:2b
LLM_TIMEOUT=120
```

- [ ] **Step 7: Verify PromptHub connects to LM Studio**

```bash
cd app && uvicorn router.main:app --port 9090 &
sleep 3
curl -s http://localhost:9090/health | python3 -m json.tool
# Should show "llm": "up"

curl -s http://localhost:9090/v1/models | python3 -m json.tool
# Should list LM Studio models

kill %1
```

- [ ] **Step 8: Remove Ollama**

Only after verifying LM Studio works:

```bash
# Uninstall Ollama binary
brew uninstall ollama

# Remove Ollama model data (~52 GB)
rm -rf ~/.ollama

# Verify removal
which ollama && echo "Still installed" || echo "Removed"
```

- [ ] **Step 9: Commit .env changes (not .env itself — it's gitignored)**

No git commit needed for `.env`. The `.env.example` was already updated in Task 1.

---

### Task 13: Update Shell Scripts

**Files:**
- Modify: `scripts/prompthub-start.zsh`
- Modify: `scripts/prompthub-kill.zsh`
- Modify: `scripts/open-webui/start.sh`

- [ ] **Step 1: Update prompthub-start.zsh**

Replace Ollama-specific startup logic:
- "Starting Ollama" → "Starting LM Studio server" (or remove — LM Studio may already be running)
- `pgrep -x "ollama"` → check for LM Studio process or just check `curl localhost:1234/v1/models`
- `ollama serve` → LM Studio starts via the GUI app; the script should just verify the server is reachable

```bash
# Health check for LLM server (works with LM Studio or Ollama)
LLM_PORT="${LLM_PORT:-1234}"
if ! curl -sf "http://127.0.0.1:${LLM_PORT}/v1/models" > /dev/null 2>&1; then
    echo "⚠️  LLM server not responding on port ${LLM_PORT}"
    echo "   Start LM Studio and enable the server in the Developer tab"
    exit 1
fi
echo "✓ LLM server healthy on port ${LLM_PORT}"
```

- [ ] **Step 2: Update prompthub-kill.zsh**

Replace `killall ollama` with a note or remove the Ollama kill section. LM Studio is managed via its own GUI — the kill script should focus on PromptHub processes only.

- [ ] **Step 3: Update open-webui/start.sh**

Replace Ollama health check (line 43-47):

```bash
# Before:
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
curl -sf "http://127.0.0.1:${OLLAMA_PORT}/"

# After:
LLM_PORT="${LLM_PORT:-1234}"
curl -sf "http://127.0.0.1:${LLM_PORT}/v1/models"
```

- [ ] **Step 4: Commit**

```bash
git add scripts/
git commit -m "feat: update shell scripts for LM Studio (replace Ollama commands)"
```

---

### Task 14: End-to-End Smoke Test

**Prerequisites:** LM Studio running with at least `qwen3.5:2b` loaded. All code changes committed.

- [ ] **Step 1: Start PromptHub**

```bash
cd app && uvicorn router.main:app --reload --port 9090
```

- [ ] **Step 2: Health check**

```bash
curl -s http://localhost:9090/health | python3 -m json.tool
```

Expected: `"llm": "up"`, all other services healthy.

- [ ] **Step 3: Model listing**

```bash
curl -s http://localhost:9090/v1/models | python3 -m json.tool
```

Expected: JSON with LM Studio model IDs.

- [ ] **Step 4: Enhancement**

```bash
curl -s -X POST http://localhost:9090/llm/enhance \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: vscode" \
  -d '{"prompt": "explain what MCP is"}' | python3 -m json.tool
```

Expected: Enhanced prompt returned with `"provider": "llm"`.

- [ ] **Step 5: OpenAI-compat proxy (streaming)**

```bash
curl -s -X POST http://localhost:9090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-prompthub-raycast-001" \
  -d '{"model": "qwen3.5:2b", "messages": [{"role": "user", "content": "hello"}], "stream": true}'
```

Expected: SSE stream with `data: {...}` chunks, ending with `data: [DONE]`. No thinking tokens.

- [ ] **Step 6: OpenAI-compat proxy (non-streaming)**

```bash
curl -s -X POST http://localhost:9090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-prompthub-raycast-001" \
  -d '{"model": "qwen3.5:2b", "messages": [{"role": "user", "content": "hello"}], "stream": false}' | python3 -m json.tool
```

Expected: Standard ChatCompletion response.

- [ ] **Step 7: Dashboard**

Open `http://localhost:9090/dashboard` in browser. Verify:
- "Local Models" panel shows loaded models
- "LLM Status" shows healthy
- No "Ollama" text visible anywhere

- [ ] **Step 8: Raycast Chat (if Raycast installed)**

Open Raycast → AI Chat → select `local-router qwen3.5 2b` → send a message.

Expected: Streaming response, no "Failed connecting to server" errors.

- [ ] **Step 9: Run full test suite one final time**

```bash
cd app && pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 10: Final commit (if any fixups were needed)**

```bash
git add -A
git commit -m "fix: smoke test fixups for LM Studio integration"
```
