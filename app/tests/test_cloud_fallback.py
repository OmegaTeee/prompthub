"""
Tests for cloud enhancement fallback (Path D).

Covers:
- OpenAICompatConfig extra_headers
- Cloud model mapping from cloud-models.json
- _try_cloud_fallback privacy gating
- Full enhance() flow with Ollama→OpenRouter fallback
- EnhancementResult provider field
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from router.enhancement.llm_client import LLMConfig as OpenAICompatConfig
from router.enhancement.service import (
    EnhancementResult,
    EnhancementRule,
    EnhancementService,
    PrivacyLevel,
)
from router.resilience import CircuitBreakerError, CircuitState


# --- Fixtures ---


@pytest.fixture
def cloud_models_file(tmp_path):
    """Create a cloud-models.json fixture."""
    data = {
        "local_models": {
            "llama3.2:latest": {
                "category": "general",
                "cloud_upgrade": "meta-llama/llama-3.3-70b-instruct",
            },
            "deepseek-r1:latest": {
                "category": "reasoning",
                "cloud_upgrade": "deepseek/deepseek-r1-0528",
            },
        },
        "free_models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-r1-0528:free",
        ],
    }
    path = tmp_path / "cloud-models.json"
    path.write_text(json.dumps(data))
    return path


@pytest.fixture
def enhancement_rules_file(tmp_path):
    """Create a minimal enhancement-rules.json fixture."""
    data = {
        "default": {
            "enabled": True,
            "model": "llama3.2:latest",
            "system_prompt": "Test prompt.",
        },
        "clients": {
            "perplexity": {
                "model": "llama3.2:latest",
                "system_prompt": "Perplexity prompt.",
                "privacy_level": "free_ok",
            },
            "vscode": {
                "model": "llama3.2:latest",
                "system_prompt": "VS Code prompt.",
            },
        },
    }
    path = tmp_path / "enhancement-rules.json"
    path.write_text(json.dumps(data))
    return path


def _make_service(
    tmp_path,
    cloud_models_file=None,
    enhancement_rules_file=None,
    openrouter_enabled=True,
    openrouter_api_key="test-key",
):
    """Create an EnhancementService with cloud fallback configured."""
    with patch("router.enhancement.service.get_settings") as mock_settings:
        settings = MagicMock()
        settings.ollama_api_mode = "native"
        mock_settings.return_value = settings

        return EnhancementService(
            rules_path=enhancement_rules_file,
            cache_max_size=100,
            cache_ttl=60.0,
            cache_persistent=False,
            openrouter_enabled=openrouter_enabled,
            openrouter_api_key=openrouter_api_key,
            openrouter_base_url="https://openrouter.ai/api/v1",
            openrouter_timeout=10.0,
            openrouter_default_model="deepseek/deepseek-r1-0528:free",
            cloud_models_path=cloud_models_file,
        )


# --- Tests ---


class TestOpenAICompatConfigHeaders:
    """Test extra_headers on OpenAICompatConfig."""

    def test_default_extra_headers_empty(self):
        config = OpenAICompatConfig()
        assert config.extra_headers == {}

    def test_extra_headers_set(self):
        config = OpenAICompatConfig(
            extra_headers={"Authorization": "Bearer sk-test"},
        )
        assert config.extra_headers["Authorization"] == "Bearer sk-test"

    def test_openrouter_config_has_auth(self):
        config = OpenAICompatConfig(
            base_url="https://openrouter.ai/api/v1",
            extra_headers={"Authorization": "Bearer sk-or-test"},
        )
        assert "Authorization" in config.extra_headers
        assert config.base_url == "https://openrouter.ai/api/v1"


class TestCloudModelMapping:
    """Test local→cloud model mapping loading."""

    def test_loads_mapping_from_file(self, cloud_models_file):
        mapping = EnhancementService._load_cloud_model_map(cloud_models_file)
        assert "llama3.2:latest" in mapping
        assert "deepseek-r1:latest" in mapping

    def test_maps_to_free_variant(self, cloud_models_file):
        mapping = EnhancementService._load_cloud_model_map(cloud_models_file)
        assert mapping["llama3.2:latest"] == "meta-llama/llama-3.3-70b-instruct:free"
        assert mapping["deepseek-r1:latest"] == "deepseek/deepseek-r1-0528:free"

    def test_missing_file_returns_empty(self, tmp_path):
        mapping = EnhancementService._load_cloud_model_map(
            tmp_path / "nonexistent.json",
        )
        assert mapping == {}

    def test_falls_back_to_cloud_upgrade_without_free(self, tmp_path):
        """If no :free variant in free_models, use cloud_upgrade directly."""
        data = {
            "local_models": {
                "custom:latest": {
                    "cloud_upgrade": "vendor/custom-model",
                },
            },
            "free_models": [],
        }
        path = tmp_path / "cloud-models.json"
        path.write_text(json.dumps(data))
        mapping = EnhancementService._load_cloud_model_map(path)
        assert mapping["custom:latest"] == "vendor/custom-model"


class TestTryCloudFallback:
    """Test _try_cloud_fallback method directly."""

    @pytest.fixture
    def service(self, tmp_path, cloud_models_file):
        return _make_service(tmp_path, cloud_models_file=cloud_models_file)

    @pytest.mark.asyncio
    async def test_local_only_blocks_cloud(self, service):
        """LOCAL_ONLY privacy prevents any cloud attempt."""
        rule = EnhancementRule(model="llama3.2:latest")
        result = await service._try_cloud_fallback(
            "test prompt", rule, PrivacyLevel.LOCAL_ONLY, "vscode", "Ollama down",
        )
        assert result.original == result.enhanced
        assert result.error == "Ollama down"
        assert result.provider is None

    @pytest.mark.asyncio
    async def test_free_ok_allows_cloud(self, service):
        """FREE_OK privacy allows cloud fallback."""
        service._cloud_client = AsyncMock()
        service._cloud_client.generate_from_prompt = AsyncMock(
            return_value="enhanced by cloud",
        )

        rule = EnhancementRule(model="llama3.2:latest")
        result = await service._try_cloud_fallback(
            "test prompt", rule, PrivacyLevel.FREE_OK, "perplexity", "Ollama down",
        )
        assert result.enhanced == "enhanced by cloud"
        assert result.provider == "openrouter"
        assert result.model == "meta-llama/llama-3.3-70b-instruct:free"

    @pytest.mark.asyncio
    async def test_any_allows_cloud(self, service):
        """ANY privacy allows cloud fallback."""
        service._cloud_client = AsyncMock()
        service._cloud_client.generate_from_prompt = AsyncMock(
            return_value="enhanced by cloud",
        )

        rule = EnhancementRule(model="llama3.2:latest")
        result = await service._try_cloud_fallback(
            "test prompt", rule, PrivacyLevel.ANY, "test", "Ollama down",
        )
        assert result.enhanced == "enhanced by cloud"
        assert result.provider == "openrouter"

    @pytest.mark.asyncio
    async def test_no_cloud_client_returns_original(self, service):
        """No cloud client configured → return original."""
        service._cloud_client = None

        rule = EnhancementRule(model="llama3.2:latest")
        result = await service._try_cloud_fallback(
            "test prompt", rule, PrivacyLevel.FREE_OK, "perplexity", "Ollama down",
        )
        assert result.original == result.enhanced
        assert result.error == "Ollama down"

    @pytest.mark.asyncio
    async def test_cloud_breaker_open_returns_original(self, service):
        """Cloud circuit breaker open → return original with combined error."""
        service._cloud_client = AsyncMock()
        service._cloud_circuit_breaker.check = MagicMock(
            side_effect=CircuitBreakerError("openrouter", CircuitState.OPEN, retry_after=45.0),
        )

        rule = EnhancementRule(model="llama3.2:latest")
        result = await service._try_cloud_fallback(
            "test prompt", rule, PrivacyLevel.FREE_OK, "perplexity", "Ollama down",
        )
        assert result.original == result.enhanced
        assert "cloud breaker open" in result.error
        assert "45" in result.error

    @pytest.mark.asyncio
    async def test_cloud_success_caches_result(self, service):
        """Cloud success should cache the enhanced prompt."""
        service._cloud_client = AsyncMock()
        service._cloud_client.generate_from_prompt = AsyncMock(
            return_value="cloud enhanced",
        )
        service._cache = AsyncMock()
        service._cache.set_enhanced = AsyncMock()

        rule = EnhancementRule(model="llama3.2:latest")
        await service._try_cloud_fallback(
            "test prompt", rule, PrivacyLevel.FREE_OK, "perplexity", "Ollama down",
        )
        service._cache.set_enhanced.assert_called_once()

    @pytest.mark.asyncio
    async def test_cloud_failure_records_breaker(self, service):
        """Cloud failure records to circuit breaker."""
        service._cloud_client = AsyncMock()
        service._cloud_client.generate_from_prompt = AsyncMock(
            side_effect=Exception("API error"),
        )

        rule = EnhancementRule(model="llama3.2:latest")
        result = await service._try_cloud_fallback(
            "test prompt", rule, PrivacyLevel.FREE_OK, "perplexity", "Ollama down",
        )
        assert "cloud fallback failed" in result.error
        assert "API error" in result.error

    @pytest.mark.asyncio
    async def test_unknown_model_uses_default(self, service):
        """Unknown local model maps to default cloud model."""
        service._cloud_client = AsyncMock()
        service._cloud_client.generate_from_prompt = AsyncMock(
            return_value="enhanced",
        )

        rule = EnhancementRule(model="unknown-model:latest")
        result = await service._try_cloud_fallback(
            "test prompt", rule, PrivacyLevel.FREE_OK, "perplexity", "Ollama down",
        )
        assert result.model == "deepseek/deepseek-r1-0528:free"


class TestEnhanceWithFallback:
    """Test full enhance() flow with cloud fallback."""

    @pytest.fixture
    def service(self, tmp_path, cloud_models_file, enhancement_rules_file):
        svc = _make_service(
            tmp_path,
            cloud_models_file=cloud_models_file,
            enhancement_rules_file=enhancement_rules_file,
        )
        return svc

    @pytest.mark.asyncio
    async def test_ollama_success_no_cloud_attempt(self, service):
        """When Ollama succeeds, cloud client is never called."""
        service._llm = AsyncMock()
        service._llm.generate_from_prompt = AsyncMock(
            return_value="enhanced by llm",
        )
        cloud_mock = AsyncMock()
        service._cloud_client = cloud_mock

        await service.initialize()
        result = await service.enhance("test prompt", client_name="perplexity")

        assert result.enhanced == "enhanced by llm"
        assert result.provider == "llm"
        cloud_mock.generate_from_prompt.assert_not_called()

    @pytest.mark.asyncio
    async def test_ollama_fail_free_ok_cloud_success(self, service):
        """Ollama connection error + free_ok client → cloud fallback succeeds."""
        from router.enhancement.llm_client import LLMConnectionError as OllamaConnectionError

        service._llm = AsyncMock()
        service._llm.generate_from_prompt = AsyncMock(
            side_effect=OllamaConnectionError("Connection refused"),
        )
        service._llm.is_healthy = AsyncMock(return_value=False)

        service._cloud_client = AsyncMock()
        service._cloud_client.generate_from_prompt = AsyncMock(
            return_value="cloud enhanced",
        )

        await service.initialize()
        result = await service.enhance("test prompt", client_name="perplexity")

        assert result.enhanced == "cloud enhanced"
        assert result.provider == "openrouter"

    @pytest.mark.asyncio
    async def test_ollama_fail_local_only_no_cloud(self, service):
        """Ollama fails + local_only client → returns original, no cloud."""
        from router.enhancement.llm_client import LLMConnectionError as OllamaConnectionError

        service._llm = AsyncMock()
        service._llm.generate_from_prompt = AsyncMock(
            side_effect=OllamaConnectionError("Connection refused"),
        )
        service._llm.is_healthy = AsyncMock(return_value=False)

        cloud_mock = AsyncMock()
        service._cloud_client = cloud_mock

        await service.initialize()
        result = await service.enhance("test prompt", client_name="vscode")

        assert result.original == result.enhanced
        assert result.provider is None
        cloud_mock.generate_from_prompt.assert_not_called()

    @pytest.mark.asyncio
    async def test_ollama_breaker_open_cloud_fallback(self, service):
        """Ollama circuit breaker open + free_ok → cloud fallback."""
        service._llm = AsyncMock()
        service._llm.is_healthy = AsyncMock(return_value=False)

        # Trip the Ollama circuit breaker
        for _ in range(3):
            service._circuit_breaker.record_failure(Exception("fail"))

        service._cloud_client = AsyncMock()
        service._cloud_client.generate_from_prompt = AsyncMock(
            return_value="cloud enhanced",
        )

        await service.initialize()
        result = await service.enhance("test prompt", client_name="perplexity")

        assert result.enhanced == "cloud enhanced"
        assert result.provider == "openrouter"

    @pytest.mark.asyncio
    async def test_ollama_fail_cloud_disabled(self, tmp_path, enhancement_rules_file):
        """Ollama fails + cloud disabled → returns original."""
        from router.enhancement.llm_client import LLMConnectionError as OllamaConnectionError

        service = _make_service(
            tmp_path,
            enhancement_rules_file=enhancement_rules_file,
            openrouter_enabled=False,
        )
        service._llm = AsyncMock()
        service._llm.generate_from_prompt = AsyncMock(
            side_effect=OllamaConnectionError("Connection refused"),
        )
        service._llm.is_healthy = AsyncMock(return_value=False)

        await service.initialize()
        result = await service.enhance("test prompt", client_name="perplexity")

        assert result.original == result.enhanced
        assert result.provider is None

    @pytest.mark.asyncio
    async def test_ollama_fail_cloud_fail_returns_original(self, service):
        """Both Ollama and cloud fail → returns original with combined error."""
        from router.enhancement.llm_client import LLMConnectionError as OllamaConnectionError

        service._llm = AsyncMock()
        service._llm.generate_from_prompt = AsyncMock(
            side_effect=OllamaConnectionError("Connection refused"),
        )
        service._llm.is_healthy = AsyncMock(return_value=False)

        service._cloud_client = AsyncMock()
        service._cloud_client.generate_from_prompt = AsyncMock(
            side_effect=Exception("OpenRouter 503"),
        )

        await service.initialize()
        result = await service.enhance("test prompt", client_name="perplexity")

        assert result.original == result.enhanced
        assert "Connection refused" in result.error
        assert "cloud fallback failed" in result.error

    @pytest.mark.asyncio
    async def test_cached_result_skips_both(self, service):
        """Cached result returns immediately — no Ollama or cloud call."""
        service._llm = AsyncMock()
        service._llm.is_healthy = AsyncMock(return_value=True)

        cloud_mock = AsyncMock()
        service._cloud_client = cloud_mock

        await service.initialize()

        # Populate cache
        service._cache = AsyncMock()
        service._cache.get_enhanced = AsyncMock(return_value="cached result")

        result = await service.enhance("test prompt", client_name="perplexity")

        assert result.enhanced == "cached result"
        assert result.cached is True
        service._llm.generate_from_prompt.assert_not_called()
        cloud_mock.generate_from_prompt.assert_not_called()

    @pytest.mark.asyncio
    async def test_disabled_enhancement_skips_both(self, service):
        """Disabled enhancement returns original — no cloud attempt."""
        service._llm = AsyncMock()
        service._llm.is_healthy = AsyncMock(return_value=True)

        cloud_mock = AsyncMock()
        service._cloud_client = cloud_mock

        await service.initialize()

        # Override the rule to be disabled
        service._rules["perplexity"] = EnhancementRule(enabled=False)

        result = await service.enhance("test prompt", client_name="perplexity")

        assert result.original == result.enhanced
        assert "disabled" in result.error
        cloud_mock.generate_from_prompt.assert_not_called()


class TestEnhancementResultProvider:
    """Test provider field on EnhancementResult."""

    def test_default_provider_is_none(self):
        result = EnhancementResult(original="test", enhanced="test")
        assert result.provider is None

    def test_llm_provider(self):
        result = EnhancementResult(
            original="test", enhanced="enhanced", provider="llm",
        )
        assert result.provider == "llm"

    def test_openrouter_provider(self):
        result = EnhancementResult(
            original="test", enhanced="enhanced", provider="openrouter",
        )
        assert result.provider == "openrouter"

    def test_serialization_includes_provider(self):
        result = EnhancementResult(
            original="test", enhanced="enhanced", provider="openrouter",
        )
        d = result.model_dump()
        assert d["provider"] == "openrouter"

    def test_serialization_none_provider(self):
        result = EnhancementResult(original="test", enhanced="test")
        d = result.model_dump()
        assert d["provider"] is None
