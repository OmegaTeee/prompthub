"""
Application settings using Pydantic Settings.

Settings are loaded from environment variables and .env file.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = {"env_file": ".env", "env_prefix": "", "case_sensitive": False}

    # Server
    host: str = "0.0.0.0"
    port: int = 9090

    # Ollama
    ollama_host: str = "host.docker.internal"
    ollama_port: int = 11434
    ollama_model: str = "llama3.2:3b"
    ollama_timeout: int = 30
    ollama_api_mode: str = "native"  # "native" or "openai" - API format to use

    # Cache
    cache_max_size: int = 1000
    cache_similarity_threshold: float = 0.85
    cache_persistent: bool = True
    cache_db_path: str = "/tmp/prompthub/cache.db"

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

    # Logging
    log_level: str = "info"

    def model_post_init(self, __context: object) -> None:
        if not self.workspace_root:
            # Auto-detect: settings.py -> config/ -> router/ -> app/ -> workspace root
            self.workspace_root = str(
                Path(__file__).resolve().parents[3]
            )

        # Normalize ollama_host: strip scheme and port if present
        # (handles OLLAMA_HOST=http://localhost:11434 from system env)
        host = self.ollama_host
        if "://" in host:
            host = host.split("://", 1)[1]
        if ":" in host:
            host = host.split(":", 1)[0]
        self.ollama_host = host


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
