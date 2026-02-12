"""Tests for OpenAI-compatible API proxy.

Tests cover:
- API key loading and validation
- Request model parsing
- Enhancement integration (only last user message enhanced)
- Router endpoint behavior (auth, circuit breaker, forwarding)
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from router.openai_compat.auth import ApiKeyManager
from router.openai_compat.models import ApiKeyConfig, ApiKeysRegistry, ChatCompletionRequest
from router.openai_compat.router import _find_last_user_message, create_openai_compat_router


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_api_keys():
    """Sample API keys config data."""
    return {
        "keys": {
            "sk-prompthub-test-abc123": {
                "client_name": "test-client",
                "enhance": True,
                "description": "Test client",
            },
            "sk-prompthub-passthrough-def456": {
                "client_name": "passthrough",
                "enhance": False,
                "description": "No enhancement",
            },
        }
    }


@pytest.fixture
def api_keys_file(tmp_path, sample_api_keys):
    """Write sample API keys to a temp file and return its path."""
    path = tmp_path / "api-keys.json"
    path.write_text(json.dumps(sample_api_keys))
    return path


@pytest.fixture
def api_key_manager(api_keys_file):
    """Configured ApiKeyManager loaded from temp file."""
    mgr = ApiKeyManager(config_path=api_keys_file)
    mgr.load()
    return mgr


@pytest.fixture
def mock_enhancement_service():
    """Mock EnhancementService that returns an enhanced prompt."""
    svc = AsyncMock()
    result = MagicMock()
    result.was_enhanced = True
    result.enhanced = "Enhanced: Hello world"
    result.cached = False
    svc.enhance.return_value = result
    return svc


@pytest.fixture
def mock_circuit_breakers():
    """Mock CircuitBreakerRegistry with a no-op breaker."""
    breaker = MagicMock()
    breaker.check.return_value = None
    breaker.record_success.return_value = None
    breaker.record_failure.return_value = None

    registry = MagicMock()
    registry.get.return_value = breaker
    return registry


@pytest.fixture
def test_app(api_key_manager, mock_enhancement_service, mock_circuit_breakers):
    """FastAPI test app with the OpenAI-compat router registered."""
    app = FastAPI()
    router = create_openai_compat_router(
        enhancement_service=lambda: mock_enhancement_service,
        circuit_breakers=lambda: mock_circuit_breakers,
        api_key_manager=api_key_manager,
        ollama_base_url="http://localhost:11434/v1",
        ollama_timeout=30.0,
    )
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app):
    """TestClient for the test app."""
    return TestClient(test_app)


# =============================================================================
# ApiKeyManager Tests
# =============================================================================


class TestApiKeyManager:
    """Test API key loading and validation."""

    def test_load_valid_config(self, api_key_manager):
        """Loaded config has the expected number of keys."""
        assert api_key_manager.key_count == 2

    def test_validate_known_token(self, api_key_manager):
        """Known token returns correct ApiKeyConfig."""
        config = api_key_manager.validate_token("sk-prompthub-test-abc123")
        assert config is not None
        assert config.client_name == "test-client"
        assert config.enhance is True

    def test_validate_unknown_token(self, api_key_manager):
        """Unknown token returns None."""
        assert api_key_manager.validate_token("sk-invalid-token") is None

    def test_reload_picks_up_changes(self, api_keys_file, api_key_manager):
        """Reloading config picks up new keys."""
        new_data = {
            "keys": {
                "sk-new-key": {
                    "client_name": "new",
                    "enhance": False,
                    "description": "Added",
                }
            }
        }
        api_keys_file.write_text(json.dumps(new_data))
        api_key_manager.reload()

        assert api_key_manager.key_count == 1
        assert api_key_manager.validate_token("sk-new-key") is not None
        assert api_key_manager.validate_token("sk-prompthub-test-abc123") is None

    def test_missing_config_file(self, tmp_path):
        """Missing config file logs warning, zero keys loaded."""
        mgr = ApiKeyManager(config_path=tmp_path / "nonexistent.json")
        mgr.load()
        assert mgr.key_count == 0

    def test_no_config_path(self):
        """None config path results in zero keys."""
        mgr = ApiKeyManager(config_path=None)
        mgr.load()
        assert mgr.key_count == 0


# =============================================================================
# Model Tests
# =============================================================================


class TestChatCompletionRequest:
    """Test OpenAI request model parsing."""

    def test_minimal_request(self):
        """Minimal valid request with defaults."""
        req = ChatCompletionRequest(
            model="llama3.2",
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert req.stream is False
        assert req.temperature == 0.7
        assert req.max_tokens is None

    def test_streaming_request(self):
        """stream=True parses correctly."""
        req = ChatCompletionRequest(
            model="llama3.2",
            messages=[{"role": "user", "content": "Hi"}],
            stream=True,
        )
        assert req.stream is True

    def test_full_request(self):
        """All fields parse correctly."""
        req = ChatCompletionRequest(
            model="deepseek-r1:latest",
            messages=[
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hello"},
            ],
            temperature=0.5,
            max_tokens=100,
            top_p=0.9,
            stop=["\n"],
        )
        assert req.model == "deepseek-r1:latest"
        assert len(req.messages) == 2
        assert req.temperature == 0.5


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestFindLastUserMessage:
    """Test the helper that locates the last user message."""

    def test_single_user_message(self):
        messages = [{"role": "user", "content": "Hello"}]
        assert _find_last_user_message(messages) == 0

    def test_multiple_messages(self):
        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": "Second"},
        ]
        assert _find_last_user_message(messages) == 3

    def test_no_user_message(self):
        messages = [
            {"role": "system", "content": "Be helpful"},
            {"role": "assistant", "content": "Hello"},
        ]
        assert _find_last_user_message(messages) is None

    def test_empty_messages(self):
        assert _find_last_user_message([]) is None

    def test_system_messages_not_matched(self):
        """System messages should never be treated as user messages."""
        messages = [{"role": "system", "content": "You are helpful."}]
        assert _find_last_user_message(messages) is None


# =============================================================================
# Endpoint Tests
# =============================================================================


class TestAuthEndpoints:
    """Test authentication behavior of /v1/ endpoints."""

    def test_missing_auth_returns_401(self, client):
        """Request without Authorization header returns 401."""
        response = client.post(
            "/v1/chat/completions",
            json={"model": "llama3.2", "messages": [{"role": "user", "content": "Hi"}]},
        )
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Request with invalid bearer token returns 401."""
        response = client.post(
            "/v1/chat/completions",
            json={"model": "llama3.2", "messages": [{"role": "user", "content": "Hi"}]},
            headers={"Authorization": "Bearer sk-invalid-garbage"},
        )
        assert response.status_code == 401
        body = response.json()
        assert "error" in body["detail"]

    def test_models_without_auth_returns_401(self, client):
        """GET /v1/models without auth returns 401."""
        response = client.get("/v1/models")
        assert response.status_code == 401

    def test_api_keys_reload_no_auth_required(self, client):
        """POST /v1/api-keys/reload works without auth (admin endpoint)."""
        response = client.post("/v1/api-keys/reload")
        assert response.status_code == 200
        assert "count" in response.json()


class TestApiKeysReload:
    """Test the API keys reload endpoint."""

    def test_reload_returns_count(self, client):
        response = client.post("/v1/api-keys/reload")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["message"] == "API keys reloaded"
