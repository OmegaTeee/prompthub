# Local LLM Integration Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace stale Ollama-specific test assumptions with a live smoke test for the `.env`-configured local provider.

**Architecture:** Add one integration test that calls the isolated router's enhancement endpoint using the default rule and asserts provider/model/error fields. Keep cloud-fallback and other unit coverage mocked; remove outdated Ollama wording and disabled-client model assertions from tests.

**Tech Stack:** Python 3.13 uv environment, pytest 9, pytest-asyncio, HTTPX AsyncClient.

**Spec:** `docs/superpowers/specs/2026-11-22-local-llm-integration-test-design.md`

## Global Constraints

- Do not change production code or `.env`.
- The integration smoke test uses existing `live_router` and `requires_llm` marker.
- The local provider endpoint and model IDs are resolved from `get_settings()` (`LLM_HOST`, `LLM_PORT`, `LLM_MODEL`, `LLM_ORCHESTRATOR_MODEL`); never hard-code Ollama or provider host/port/model.
- CI's explicit test list excludes integration tests, so no local model is required in CI.

## Review Focus

- Provider unavailable or either model misconfigured: live test must fail with endpoint/model context, not skip.
- Enhancement disabled for named client: use an unconfigured client name to exercise the enabled default rule.
- Cache masks provider call: request with `bypass_cache=True`.
- Model output varies: assert response metadata and provider success, not prose content.
- Cloud fallback semantics: keep mocked tests independent of the local provider.

---

### Task 1: Local Provider Integration Coverage

**Files:**

- Create: `app/tests/integration/test_local_llm_provider.py`
- Modify: `app/tests/integration/test_enhancement_and_caching.py`
- Modify: `app/tests/test_cloud_fallback.py`
- Modify: `app/tests/test_enhancement.py`
- Modify: `app/tests/unit/test_orchestrator.py`

**Interfaces:**

- Consumes: `live_router` fixture, `get_settings()`, the registered `requires_llm` marker, `POST /llm/enhance`.
- Produces: `test_enhancement_uses_configured_local_provider`, which verifies the orchestrator model is listed and the enhancement response has status 200, `settings.llm_model`, provider `llm`, and no error.

- [x] Add the live provider test and run it with `app/.venv/bin/python -m pytest tests/integration/test_local_llm_provider.py -q` (passed).
- [x] Remove skipped Ollama-specific semantic tests that assert disabled clients or old model names; retain existing cache/fallback behavior coverage.
- [x] Replace provider-specific wording and dead `ollama_api_mode` test setup with backend-neutral local-LLM language; keep mock-driven fallback tests offline.
- [x] Run the new live test, relevant mocked tests, and full project suite. The full suite reports 380 passed, 8 skipped, and 5 failures, all in the pre-existing modified `app/tests/test_openai_compat.py` structured-response tests (missing `response_format`/`extra_params` behavior and one request reaching hard-coded port 1234). That file was not changed for this task.
- [x] Run `ruff check` on the active modified test files and `git diff --check` (both passed). The legacy, module-skipped `app/tests/test_enhancement.py` retains existing undefined-name lint findings.
