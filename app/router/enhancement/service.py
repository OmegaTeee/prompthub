"""
Prompt Enhancement Service.

This service orchestrates prompt enhancement by:
1. Checking cache for previously enhanced prompts
2. Checking circuit breaker state for LLM server
3. Calling LLM server for enhancement
4. Caching results
5. Gracefully degrading when LLM server is unavailable

The service provides resilient prompt enhancement with automatic
failover to returning the original prompt if enhancement fails.
"""

import asyncio
import json
import logging
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from router.cache import EnhancementCache
from router.config.settings import get_settings
from router.enhancement.llm_client import (
    LLMClient,
    LLMConfig,
    LLMConnectionError,
    LLMError,
)
from router.enhancement.context_window import TokenBudget
from router.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
)

logger = logging.getLogger(__name__)


class PrivacyLevel(StrEnum):
    """Privacy boundary for prompt enhancement routing.

    Determines whether a client's prompts may be sent to
    external (cloud) enhancement services.
    """

    LOCAL_ONLY = "local_only"
    FREE_OK = "free_ok"
    ANY = "any"


_PRIVACY_STRICTNESS: dict[PrivacyLevel, int] = {
    PrivacyLevel.LOCAL_ONLY: 0,
    PrivacyLevel.FREE_OK: 1,
    PrivacyLevel.ANY: 2,
}


def resolve_privacy_level(
    config_level: PrivacyLevel,
    header_level: PrivacyLevel | None,
) -> PrivacyLevel:
    """Resolve effective privacy level.

    The header can only downgrade (more restrictive), never upgrade.
    """
    if header_level is None:
        return config_level
    if _PRIVACY_STRICTNESS[header_level] < _PRIVACY_STRICTNESS[config_level]:
        return header_level
    return config_level


class EnhancementRule(BaseModel):
    """Configuration for how to enhance prompts for a specific client."""

    enabled: bool = True
    model: str = "llama3.2:3b"
    system_prompt: str = "Improve clarity and structure. Preserve intent. Return only the enhanced prompt."
    temperature: float = 0.3
    max_tokens: int | None = 500
    privacy_level: PrivacyLevel = PrivacyLevel.LOCAL_ONLY


class EnhancementResult(BaseModel):
    """Result of a prompt enhancement operation."""

    original: str
    enhanced: str
    model: str | None = None
    cached: bool = False
    enhanced_by_llm: bool = False
    error: str | None = None
    privacy_level: PrivacyLevel = PrivacyLevel.LOCAL_ONLY
    provider: str | None = None  # "llm" or "openrouter"

    @property
    def was_enhanced(self) -> bool:
        """Check if the prompt was actually enhanced."""
        return self.original != self.enhanced


class EnhancementService:
    """
    Service for enhancing prompts via LLM server.

    Provides resilient prompt enhancement with:
    - L1 cache for repeated prompts
    - Circuit breaker for LLM failures
    - Graceful degradation to original prompt
    - Per-client enhancement rules

    Example:
        service = EnhancementService()
        await service.initialize()

        result = await service.enhance(
            prompt="Help me write code",
            client_name="claude-desktop"
        )
        print(result.enhanced)
    """

    _llm: LLMClient

    def __init__(
        self,
        rules_path: str | Path | None = None,
        llm_config: LLMConfig | None = None,
        cache_max_size: int = 500,
        cache_ttl: float = 7200.0,
        cache_persistent: bool = True,
        cache_db_path: str = "",  # resolved to ~/.prompthub/cache.db if empty
        openrouter_enabled: bool = False,
        openrouter_api_key: str = "",
        openrouter_base_url: str = "https://openrouter.ai/api/v1",
        openrouter_timeout: float = 30.0,
        openrouter_default_model: str = "deepseek/deepseek-r1-0528:free",
        cloud_models_path: str | Path | None = None,
    ):
        """
        Initialize the enhancement service.

        Args:
            rules_path: Path to enhancement-rules.json
            llm_config: LLM client configuration
            cache_max_size: Maximum cache entries
            cache_ttl: Cache entry TTL in seconds
            cache_persistent: Use SQLite-backed persistent cache
            cache_db_path: Path for persistent cache database
            openrouter_enabled: Enable OpenRouter cloud fallback
            openrouter_api_key: OpenRouter API key
            openrouter_base_url: OpenRouter API base URL
            openrouter_timeout: Timeout for OpenRouter requests
            openrouter_default_model: Default cloud model when no mapping exists
            cloud_models_path: Path to cloud-models.json for local->cloud mapping
        """
        self.rules_path = Path(rules_path) if rules_path else None
        self._rules: dict[str, EnhancementRule] = {}
        self._default_rule = EnhancementRule()

        settings = get_settings()

        # Resolve cache_db_path from settings (single source of truth)
        if not cache_db_path:
            cache_db_path = settings.cache_db_path

        # Single LLM client — always OpenAI-compatible
        if llm_config:
            config = LLMConfig(
                base_url=llm_config.base_url,
                timeout=llm_config.timeout,
                max_retries=llm_config.max_retries if hasattr(llm_config, 'max_retries') else 2,
                retry_delay=llm_config.retry_delay if hasattr(llm_config, 'retry_delay') else 1.0,
            )
        else:
            config = LLMConfig(
                base_url=f"http://{settings.llm_host}:{settings.llm_port}/v1",
                timeout=float(settings.llm_timeout),
            )
        self._llm = LLMClient(config)
        logger.info("LLM client initialized at %s", config.base_url)

        if cache_persistent:
            from router.cache.persistent_enhancement import (
                PersistentEnhancementCache,
            )
            self._cache = PersistentEnhancementCache(
                max_size=cache_max_size,
                default_ttl=cache_ttl,
                db_path=Path(cache_db_path),
            )
        else:
            self._cache = EnhancementCache(
                max_size=cache_max_size, default_ttl=cache_ttl,
            )

        self._circuit_breaker = CircuitBreaker(
            "llm",
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30.0,
                half_open_max_calls=1,
            ),
        )

        # Cloud fallback (OpenRouter)
        self._cloud_client: LLMClient | None = None
        self._default_cloud_model = openrouter_default_model
        self._cloud_model_map: dict[str, str] = {}

        if openrouter_enabled and openrouter_api_key:
            cloud_config = LLMConfig(
                base_url=openrouter_base_url,
                timeout=openrouter_timeout,
                max_retries=1,
                retry_delay=0.5,
                extra_headers={"Authorization": f"Bearer {openrouter_api_key}"},
            )
            self._cloud_client = LLMClient(cloud_config)
            logger.info("OpenRouter cloud fallback enabled")
        elif openrouter_enabled:
            logger.warning("OpenRouter enabled but no API key provided")

        self._cloud_circuit_breaker = CircuitBreaker(
            "openrouter",
            CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=60.0,
                half_open_max_calls=1,
            ),
        )

        # Load cloud model mapping
        if cloud_models_path:
            self._cloud_model_map = self._load_cloud_model_map(
                Path(cloud_models_path),
            )

        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the service.

        Loads enhancement rules and checks LLM server health.
        """
        # Load rules (now async to avoid blocking event loop on file I/O)
        if self.rules_path and self.rules_path.exists():
            await self._load_rules_async()
        else:
            logger.warning("No enhancement rules file found, using defaults")

        # Initialize persistent cache if applicable
        if hasattr(self._cache, "initialize"):
            await self._cache.initialize()

        # Check LLM server health
        if await self._llm.is_healthy():
            logger.info("LLM server is healthy")
        else:
            logger.warning("LLM server is not available, enhancement will be degraded")

        self._initialized = True

    async def _load_rules_async(self) -> None:
        """Load enhancement rules from JSON file asynchronously."""
        if not self.rules_path:
            return

        try:
            # Non-blocking file read via thread pool
            content = await asyncio.to_thread(self.rules_path.read_text)
            data = json.loads(content)

            # Load default rule
            if "default" in data and isinstance(data["default"], dict):
                self._rules["default"] = EnhancementRule(**data["default"])
                self._default_rule = self._rules["default"]
                logger.debug("Loaded default enhancement rule")

            # Load client-specific rules
            clients = data.get("clients", {})
            if isinstance(clients, dict):
                for name, rule_data in clients.items():
                    if isinstance(rule_data, dict):
                        # Merge with default rule for missing fields
                        merged = self._default_rule.model_dump()
                        merged.update(rule_data)
                        self._rules[name] = EnhancementRule(**merged)
                        logger.debug(f"Loaded enhancement rule: {name}")

            logger.info(f"Loaded {len(self._rules)} enhancement rules")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in enhancement rules: {e}")
        except Exception as e:
            logger.error(f"Failed to load enhancement rules: {e}")

    def get_rule(self, client_name: str | None) -> EnhancementRule:
        """
        Get the enhancement rule for a client.

        Args:
            client_name: Client identifier (e.g., "claude-desktop")

        Returns:
            EnhancementRule for the client, or default rule
        """
        if client_name and client_name in self._rules:
            return self._rules[client_name]
        return self._rules.get("default", self._default_rule)

    @staticmethod
    def _load_cloud_model_map(path: Path) -> dict[str, str]:
        """Load local->cloud model mapping from cloud-models.json.

        Builds a dict like {"llama3.2:latest": "meta-llama/llama-3.3-70b-instruct:free"}
        using the cloud_upgrade field from local_models, with :free suffix.
        """
        if not path.exists():
            logger.warning(f"Cloud models config not found: {path}")
            return {}

        try:
            data = json.loads(path.read_text())
            local_models = data.get("local_models", {})
            free_models = set(data.get("free_models", []))
            mapping: dict[str, str] = {}

            for local_name, info in local_models.items():
                cloud_upgrade = info.get("cloud_upgrade")
                if not cloud_upgrade:
                    continue
                # Prefer the :free variant if it exists in free_models list
                free_variant = f"{cloud_upgrade}:free"
                if free_variant in free_models:
                    mapping[local_name] = free_variant
                else:
                    mapping[local_name] = cloud_upgrade

            logger.info(f"Loaded {len(mapping)} cloud model mappings")
            return mapping

        except Exception as e:
            logger.error(f"Failed to load cloud model map: {e}")
            return {}

    async def _try_cloud_fallback(
        self,
        prompt: str,
        rule: EnhancementRule,
        effective_privacy: PrivacyLevel,
        client_name: str | None,
        llm_error: str,
    ) -> EnhancementResult:
        """Attempt cloud enhancement when LLM server fails.

        Only proceeds if privacy level permits cloud processing
        and the cloud client is available and healthy.
        """
        # Gate: privacy must allow cloud
        if effective_privacy == PrivacyLevel.LOCAL_ONLY:
            return EnhancementResult(
                original=prompt, enhanced=prompt,
                error=llm_error, privacy_level=effective_privacy,
            )

        # Gate: cloud client must exist
        if not self._cloud_client:
            return EnhancementResult(
                original=prompt, enhanced=prompt,
                error=llm_error, privacy_level=effective_privacy,
            )

        # Gate: cloud circuit breaker
        try:
            self._cloud_circuit_breaker.check()
        except CircuitBreakerError as e:
            return EnhancementResult(
                original=prompt, enhanced=prompt,
                error=f"{llm_error}; cloud breaker open ({e.retry_after:.0f}s)",
                privacy_level=effective_privacy,
            )

        # Map local model -> cloud model
        cloud_model = self._cloud_model_map.get(
            rule.model, self._default_cloud_model,
        )

        try:
            enhanced = await self._cloud_client.generate_from_prompt(
                model=cloud_model,
                prompt=prompt,
                system=rule.system_prompt,
                temperature=rule.temperature,
                max_tokens=rule.max_tokens,
            )
            self._cloud_circuit_breaker.record_success()

            # Cache cloud result too
            await self._cache.set_enhanced(
                prompt=prompt, enhanced=enhanced,
                client_name=client_name, model=cloud_model,
            )

            logger.info(
                "Cloud fallback enhanced prompt with %s for client=%s",
                cloud_model, client_name,
            )
            return EnhancementResult(
                original=prompt, enhanced=enhanced, model=cloud_model,
                enhanced_by_llm=True, privacy_level=effective_privacy,
                provider="openrouter",
            )

        except Exception as e:
            self._cloud_circuit_breaker.record_failure(e)
            logger.warning(f"Cloud fallback failed: {e}")
            return EnhancementResult(
                original=prompt, enhanced=prompt,
                error=f"{llm_error}; cloud fallback failed: {e}",
                privacy_level=effective_privacy,
            )

    async def enhance(
        self,
        prompt: str,
        client_name: str | None = None,
        bypass_cache: bool = False,
        privacy_override: PrivacyLevel | None = None,
    ) -> EnhancementResult:
        """
        Enhance a prompt using LLM server.

        This method:
        1. Checks if enhancement is enabled for the client
        2. Checks cache for previously enhanced prompt
        3. Checks circuit breaker state
        4. Calls LLM server for enhancement
        5. Caches the result
        6. Returns original prompt if any step fails

        Args:
            prompt: The prompt to enhance
            client_name: Client identifier for rule lookup
            bypass_cache: Skip cache lookup
            privacy_override: Header-based privacy downgrade

        Returns:
            EnhancementResult with enhanced prompt
        """
        # Get rule for client
        rule = self.get_rule(client_name)

        # Resolve effective privacy level
        effective_privacy = resolve_privacy_level(
            rule.privacy_level, privacy_override,
        )

        # Check if enhancement is enabled
        if not rule.enabled:
            return EnhancementResult(
                original=prompt,
                enhanced=prompt,
                error="Enhancement disabled for client",
                privacy_level=effective_privacy,
            )

        # Check cache (unless bypassed)
        if not bypass_cache:
            cached = await self._cache.get_enhanced(
                prompt=prompt,
                client_name=client_name,
                model=rule.model,
            )
            if cached:
                logger.debug("Cache hit for enhancement")
                return EnhancementResult(
                    original=prompt,
                    enhanced=cached,
                    model=rule.model,
                    cached=True,
                    privacy_level=effective_privacy,
                )

        # Check circuit breaker
        try:
            self._circuit_breaker.check()
        except CircuitBreakerError as e:
            logger.warning(f"Circuit breaker open: {e}")
            return await self._try_cloud_fallback(
                prompt, rule, effective_privacy, client_name,
                f"LLM circuit breaker open, retry in {e.retry_after:.0f}s",
            )

        # Apply token budget — truncate if prompt exceeds what the model needs
        budget = TokenBudget(
            model=rule.model,
            max_response_tokens=rule.max_tokens or 500,
            system_prompt=rule.system_prompt,
        )
        prompt, was_truncated = budget.truncate(prompt)
        if was_truncated:
            logger.debug(
                "Prompt truncated for model=%s budget=%d tokens client=%s",
                rule.model, budget.available_for_input, client_name,
            )

        # Call LLM server
        try:
            enhanced = await self._llm.generate_from_prompt(
                model=rule.model,
                prompt=prompt,
                system=rule.system_prompt,
                temperature=rule.temperature,
                max_tokens=rule.max_tokens,
            )

            # Record success
            self._circuit_breaker.record_success()

            # Cache the result
            await self._cache.set_enhanced(
                prompt=prompt,
                enhanced=enhanced,
                client_name=client_name,
                model=rule.model,
            )

            logger.debug("Enhanced prompt with %s", rule.model)
            return EnhancementResult(
                original=prompt,
                enhanced=enhanced,
                model=rule.model,
                enhanced_by_llm=True,
                privacy_level=effective_privacy,
                provider="llm",
            )

        except LLMConnectionError as e:
            self._circuit_breaker.record_failure(e)
            logger.warning("LLM connection failed: %s", e)
            return await self._try_cloud_fallback(
                prompt, rule, effective_privacy, client_name, str(e),
            )

        except LLMError as e:
            self._circuit_breaker.record_failure(e)
            logger.error("LLM error: %s", e)
            return await self._try_cloud_fallback(
                prompt, rule, effective_privacy, client_name, str(e),
            )

        except Exception as e:
            self._circuit_breaker.record_failure(e)
            logger.exception(f"Unexpected error during enhancement: {e}")
            return await self._try_cloud_fallback(
                prompt, rule, effective_privacy, client_name, str(e),
            )

    async def get_stats(self) -> dict[str, Any]:
        """
        Get service statistics.

        Returns:
            Dictionary with cache and circuit breaker stats
        """
        stats: dict[str, Any] = {
            "cache": self._cache.stats().model_dump(),
            "circuit_breaker": self._circuit_breaker.stats.model_dump(),
            "llm_healthy": await self._llm.is_healthy(),
        }
        if self._cloud_client:
            stats["cloud_circuit_breaker"] = (
                self._cloud_circuit_breaker.stats.model_dump()
            )
            stats["cloud_healthy"] = await self._cloud_client.is_healthy()
            stats["cloud_model_map"] = self._cloud_model_map
        return stats

    async def reset_circuit_breaker(self) -> None:
        """Reset the LLM circuit breaker."""
        self._circuit_breaker.reset()
        logger.info("LLM circuit breaker reset")

    async def clear_cache(self) -> None:
        """Clear the enhancement cache."""
        await self._cache.clear()
        logger.info("Enhancement cache cleared")

    async def close(self) -> None:
        """Clean up resources."""
        await self._llm.close()
        if self._cloud_client:
            await self._cloud_client.close()
        if hasattr(self._cache, "close"):
            await self._cache.close()
