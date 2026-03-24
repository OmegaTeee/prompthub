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
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    ollama_model: str = "qwen3.5:2b"
    ollama_timeout: int = 120
    ollama_api_mode: str = "native"  # "native" or "openai" - API format to use

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
