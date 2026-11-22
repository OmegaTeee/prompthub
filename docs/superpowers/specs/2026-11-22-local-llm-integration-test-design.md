# Local LLM Integration Test Design

## Intent

Replace stale Ollama-specific enhancement test assumptions with coverage for PromptHub's configured local OpenAI-compatible provider. The live test should catch broken `.env` host, port, model, or router wiring.

## Goals

- Exercise `POST /llm/enhance` through the isolated test router and its `.env`-configured provider.
- Assert that the response uses the configured default model and succeeds through the local LLM provider.
- Verify that the configured orchestrator model is available at the same provider endpoint without making a timeout-sensitive generation request.
- Include this smoke test in local full-suite runs so provider misconfiguration fails visibly.
- Keep unit/cloud-fallback tests deterministic and provider-mocked; describe those tests generically as local LLM behavior.

## Non-goals

- Change `.env`, provider endpoints, production routing, or model configuration.
- Make CI depend on a local LM Studio/Headroom service. Current CI explicitly selects tests and does not include integration tests.
- Assert generated prose quality, which is nondeterministic across model/runtime versions.

## Approaches

- Replace the old skipped semantic/model-specific Ollama tests with assertions for the current model: rejected because the named client profiles are disabled and their prose checks are brittle.
- Add one live `/llm/enhance` smoke test using the settings loaded from `.env`: selected because it validates the actual router-to-provider path and model without coupling to model-generated wording.
- Only rename Ollama references: rejected because it would leave system configuration untested.

## Constraints

- `.env` configures `LLM_HOST=localhost`, `LLM_PORT=8788`, `LLM_MODEL=phi-4-mini-instruct`, and `LLM_ORCHESTRATOR_MODEL=phi-4-mini-reasoning`.
- Port 8788 is the configured Headroom endpoint; Headroom fronts LM Studio on port 1234.
- Use the existing `live_router` fixture and registered `requires_llm` marker.
- The test runs in local `pytest tests`; current CI uses an explicit unit-test file list and does not collect integration tests.

## Implementation

Add the live provider smoke test, verify both configured model IDs are available, remove obsolete skipped Ollama-specific assertions, and replace stale provider terminology in test-only mocked cases. Do not change application code.
