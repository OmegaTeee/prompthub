"""
Prompt Enhancement Service.

This service orchestrates prompt enhancement by:
1. Checking cache for previously enhanced prompts
2. Checking circuit breaker state for Ollama
3. Calling Ollama for enhancement
4. Caching results
5. Gracefully degrading when Ollama is unavailable

The service provides resilient prompt enhancement with automatic
failover to returning the original prompt if enhancement fails.
"""

import aiofiles
import json
import logging
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from router.cache import EnhancementCache
from router.config.settings import get_settings
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

    @property
    def was_enhanced(self) -> bool:
        """Check if the prompt was actually enhanced."""
        return self.original != self.enhanced


class EnhancementService:
    """
    Service for enhancing prompts via Ollama.

    Provides resilient prompt enhancement with:
    - L1 cache for repeated prompts
    - Circuit breaker for Ollama failures
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

    # Type annotation for client that can be either API type
    _ollama: OllamaClient | OllamaOpenAIClient

    def __init__(
        self,
        rules_path: str | Path | None = None,
        ollama_config: OllamaConfig | None = None,
        cache_max_size: int = 500,
        cache_ttl: float = 7200.0,
        cache_persistent: bool = True,
        cache_db_path: str = "/tmp/prompthub/cache.db",
    ):
        """
        Initialize the enhancement service.

        Args:
            rules_path: Path to enhancement-rules.json
            ollama_config: Ollama client configuration
            cache_max_size: Maximum cache entries
            cache_ttl: Cache entry TTL in seconds
            cache_persistent: Use SQLite-backed persistent cache
            cache_db_path: Path for persistent cache database
        """
        self.rules_path = Path(rules_path) if rules_path else None
        self._rules: dict[str, EnhancementRule] = {}
        self._default_rule = EnhancementRule()

        # Determine which Ollama API to use
        settings = get_settings()
        self._api_mode = settings.ollama_api_mode

        # Components - instantiate appropriate Ollama client
        if self._api_mode == "openai":
            # Use OpenAI-compatible API
            openai_config = OpenAICompatConfig(
                base_url=ollama_config.base_url.rstrip("/api") + "/v1" if ollama_config else "http://localhost:11434/v1",
                timeout=ollama_config.timeout if ollama_config else 30.0,
                max_retries=ollama_config.max_retries if ollama_config else 2,
                retry_delay=ollama_config.retry_delay if ollama_config else 1.0,
            )
            self._ollama = OllamaOpenAIClient(openai_config)
            logger.info("Using OpenAI-compatible Ollama API")
        else:
            # Use native Ollama API (default)
            self._ollama = OllamaClient(ollama_config)
            logger.info("Using native Ollama API")

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
            "ollama",
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30.0,
                half_open_max_calls=1,
            ),
        )

        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the service.

        Loads enhancement rules and checks Ollama health.
        """
        # Load rules (now async to avoid blocking event loop on file I/O)
        if self.rules_path and self.rules_path.exists():
            await self._load_rules_async()
        else:
            logger.warning("No enhancement rules file found, using defaults")

        # Initialize persistent cache if applicable
        if hasattr(self._cache, "initialize"):
            await self._cache.initialize()

        # Check Ollama health
        if await self._ollama.is_healthy():
            logger.info("Ollama is healthy")
        else:
            logger.warning("Ollama is not available, enhancement will be degraded")

        self._initialized = True

    async def _load_rules_async(self) -> None:
        """Load enhancement rules from JSON file asynchronously."""
        if not self.rules_path:
            return

        try:
            # Use aiofiles for non-blocking file I/O
            async with aiofiles.open(self.rules_path) as f:
                content = await f.read()
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

    async def enhance(
        self,
        prompt: str,
        client_name: str | None = None,
        bypass_cache: bool = False,
        privacy_override: PrivacyLevel | None = None,
    ) -> EnhancementResult:
        """
        Enhance a prompt using Ollama.

        This method:
        1. Checks if enhancement is enabled for the client
        2. Checks cache for previously enhanced prompt
        3. Checks circuit breaker state
        4. Calls Ollama for enhancement
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
            return EnhancementResult(
                original=prompt,
                enhanced=prompt,
                error=f"Ollama circuit breaker open, retry in {e.retry_after:.0f}s",
                privacy_level=effective_privacy,
            )

        # Call Ollama
        try:
            # Call appropriate API based on mode
            if isinstance(self._ollama, OllamaOpenAIClient):
                # OpenAI-compatible API - use chat completion format
                enhanced = await self._ollama.generate_from_prompt(
                    model=rule.model,
                    prompt=prompt,
                    system=rule.system_prompt,
                    temperature=rule.temperature,
                    max_tokens=rule.max_tokens,
                )
            else:
                # Native API - use generate endpoint
                response = await self._ollama.generate(
                    model=rule.model,
                    prompt=prompt,
                    system=rule.system_prompt,
                    temperature=rule.temperature,
                    max_tokens=rule.max_tokens,
                )
                enhanced = response.response.strip()

            # Record success
            self._circuit_breaker.record_success()

            # Cache the result
            await self._cache.set_enhanced(
                prompt=prompt,
                enhanced=enhanced,
                client_name=client_name,
                model=rule.model,
            )

            logger.debug(f"Enhanced prompt with {rule.model} (API: {self._api_mode})")
            return EnhancementResult(
                original=prompt,
                enhanced=enhanced,
                model=rule.model,
                enhanced_by_llm=True,
                privacy_level=effective_privacy,
            )

        except (OllamaConnectionError, OllamaOpenAIConnectionError) as e:
            self._circuit_breaker.record_failure(e)
            logger.warning(f"Ollama connection failed: {e}")
            return EnhancementResult(
                original=prompt,
                enhanced=prompt,
                error=str(e),
                privacy_level=effective_privacy,
            )

        except (OllamaError, OllamaOpenAIError) as e:
            self._circuit_breaker.record_failure(e)
            logger.error(f"Ollama error: {e}")
            return EnhancementResult(
                original=prompt,
                enhanced=prompt,
                error=str(e),
                privacy_level=effective_privacy,
            )

        except Exception as e:
            self._circuit_breaker.record_failure(e)
            logger.exception(f"Unexpected error during enhancement: {e}")
            return EnhancementResult(
                original=prompt,
                enhanced=prompt,
                error=str(e),
                privacy_level=effective_privacy,
            )

    async def get_stats(self) -> dict[str, Any]:
        """
        Get service statistics.

        Returns:
            Dictionary with cache and circuit breaker stats
        """
        return {
            "cache": self._cache.stats().model_dump(),
            "circuit_breaker": self._circuit_breaker.stats.model_dump(),
            "ollama_healthy": await self._ollama.is_healthy(),
        }

    async def reset_circuit_breaker(self) -> None:
        """Reset the Ollama circuit breaker."""
        self._circuit_breaker.reset()
        logger.info("Ollama circuit breaker reset")

    async def clear_cache(self) -> None:
        """Clear the enhancement cache."""
        await self._cache.clear()
        logger.info("Enhancement cache cleared")

    async def close(self) -> None:
        """Clean up resources."""
        await self._ollama.close()
        if hasattr(self._cache, "close"):
            await self._cache.close()
