"""
Application settings using Pydantic Settings.

Settings are loaded from environment variables and .env file.
Secrets that should not live on disk can be stored in macOS Keychain
via the ``keyring`` library (service="prompthub"). Settings resolved
from keyring (env wins if both present):

- ``openrouter_api_key`` <- keyring account ``openrouter_api_key``
- ``llm_api_key``        <- keyring account ``lm_api_token``
                            (LM Studio's official env-var name is
                            LM_API_TOKEN; also accepted as an alias)
"""

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Keyring service name — must match manage-keys.py and keyring_manager.py
_KEYRING_SERVICE = "prompthub"


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = {
        "env_file": ".env",
        "env_prefix": "",
        "case_sensitive": False,
        "extra": "ignore",  # tolerate legacy env vars (e.g. OLLAMA_API_MODE)
    }

    # Server
    host: str = "0.0.0.0"
    port: int = 9090

    # Local LLM server (LM Studio, Ollama, or any OpenAI-compatible server)
    llm_host: str = Field(
        default="localhost",
        validation_alias=AliasChoices("LLM_HOST", "OLLAMA_HOST"),
    )
    llm_port: int = Field(
        default=1234,
        validation_alias=AliasChoices("LLM_PORT", "OLLAMA_PORT"),
    )
    llm_model: str = Field(
        default="qwen3-4b-instruct-2507",
        validation_alias=AliasChoices("LLM_MODEL", "OLLAMA_MODEL"),
    )
    llm_timeout: int = Field(
        default=120,
        validation_alias=AliasChoices("LLM_TIMEOUT", "OLLAMA_TIMEOUT"),
    )
    llm_orchestrator_model: str = Field(
        default="qwen3-4b-thinking-2507",
        validation_alias=AliasChoices("LLM_ORCHESTRATOR_MODEL"),
    )
    llm_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_API_KEY", "LM_API_TOKEN"),
    )

    # Data directory — persistent storage for cache, activity log, memory db
    # Defaults to ~/.prompthub (XDG-style user data dir, survives reboots)
    # Override via DATA_DIR env var (e.g. DATA_DIR=/var/prompthub in production)
    data_dir: str = ""

    # Cache
    cache_max_size: int = 1000
    cache_similarity_threshold: float = 0.85
    cache_persistent: bool = True
    cache_db_path: str = ""  # resolved in model_post_init from data_dir
    activity_db_path: str = ""  # resolved in model_post_init from data_dir
    memory_db_path: str = ""  # resolved in model_post_init from data_dir
    tool_registry_db_path: str = ""  # resolved in model_post_init from data_dir
    audit_log_path: str = ""  # resolved in model_post_init from data_dir
    audit_checksum_path: str = ""  # resolved in model_post_init from data_dir

    # OpenRouter (cloud fallback)
    openrouter_enabled: bool = False
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    openrouter_timeout: int = 30
    openrouter_default_model: str = "deepseek/deepseek-r1-0528:free"

    # Circuit Breaker
    cb_failure_threshold: int = 3
    cb_recovery_timeout: int = 30

    # Enhancement middleware
    max_enhancement_body_size: int = 1_048_576  # 1 MB

    # Paths
    mcp_servers_config: str = "configs/mcp-servers.json"
    enhancement_rules_config: str = "configs/enhancement-rules.json"
    api_keys_config: str = "configs/api-keys.json"

    # Workspace root (parent of app/ directory)
    # Auto-detected if not set via WORKSPACE_ROOT env var
    workspace_root: str = ""

    # MCP Gateway — filter which servers are exposed via /mcp-direct/mcp
    # Comma-separated list of server names (empty = all servers)
    # e.g. GATEWAY_SERVERS="context7,duckduckgo,sequential-thinking"
    gateway_servers: str = ""

    # Logging
    log_level: str = "info"

    def model_post_init(self, __context: object) -> None:
        if not self.workspace_root:
            # Auto-detect: settings.py -> config/ -> router/ -> app/ -> workspace root
            self.workspace_root = str(
                Path(__file__).resolve().parents[3]
            )

        # Resolve data_dir — persistent user data (cache, logs, memory)
        if not self.data_dir:
            self.data_dir = str(Path.home() / ".prompthub")

        # Resolve DB/log paths from data_dir if not explicitly set
        data = Path(self.data_dir)
        if not self.cache_db_path:
            self.cache_db_path = str(data / "cache.db")
        if not self.activity_db_path:
            self.activity_db_path = str(data / "activity.db")
        if not self.memory_db_path:
            self.memory_db_path = str(data / "memory.db")
        if not self.tool_registry_db_path:
            self.tool_registry_db_path = str(data / "tool_registry.db")
        if not self.audit_log_path:
            self.audit_log_path = str(data / "audit.log")
        if not self.audit_checksum_path:
            self.audit_checksum_path = str(data / "audit_checksums.json")

        # Resolve secrets from keyring when not set via env / .env
        if not self.openrouter_api_key:
            self.openrouter_api_key = _get_from_keyring("openrouter_api_key")
        if not self.llm_api_key:
            # Keychain account is "lm_api_token" (matches LM Studio's official
            # env-var name LM_API_TOKEN); the Settings field stays generic.
            self.llm_api_key = _get_from_keyring("lm_api_token") or None

        # Normalize llm_host: strip scheme and port if present
        # (handles LLM_HOST=http://localhost:1234 from system env)
        host = self.llm_host
        if "://" in host:
            host = host.split("://", 1)[1]
        if ":" in host:
            host = host.split(":", 1)[0]
        self.llm_host = host


def _get_from_keyring(key: str) -> str:
    """Try to retrieve a secret from macOS Keychain. Returns '' on failure."""
    try:
        import keyring as kr

        value = kr.get_password(_KEYRING_SERVICE, key)
        if value:
            logger.debug("Resolved %s from keyring", key)
            return value
    except Exception:
        pass
    return ""


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
