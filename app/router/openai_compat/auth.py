"""Bearer token authentication for OpenAI-compatible API proxy."""

import json
import logging
from pathlib import Path

from router.openai_compat.models import ApiKeyConfig, ApiKeysRegistry

logger = logging.getLogger(__name__)


class ApiKeyManager:
    """Manages API key validation and client resolution.

    Loads token-to-client mappings from a JSON config file.
    Each token maps to a client_name (used for enhancement rule lookup)
    and an enhance flag (controls whether the enhancement pipeline runs).
    """

    def __init__(self, config_path: Path | str | None = None):
        self._registry = ApiKeysRegistry()
        self._config_path = Path(config_path) if config_path else None

    def load(self) -> None:
        """Load API keys from JSON config file."""
        if not self._config_path or not self._config_path.exists():
            logger.warning(
                "No API keys config found at %s — "
                "OpenAI-compatible proxy will reject all requests",
                self._config_path,
            )
            return

        try:
            with open(self._config_path) as f:
                data = json.load(f)
            self._registry = ApiKeysRegistry(**data)
            logger.info(
                "Loaded %d API keys for OpenAI-compatible proxy",
                len(self._registry.keys),
            )
        except Exception as e:
            logger.error("Failed to load API keys config: %s", e)

    def reload(self) -> None:
        """Reload API keys from config file (hot-reload)."""
        self.load()

    def validate_token(self, token: str) -> ApiKeyConfig | None:
        """Validate a bearer token and return its config, or None if invalid."""
        return self._registry.keys.get(token)

    @property
    def key_count(self) -> int:
        """Number of registered API keys."""
        return len(self._registry.keys)
