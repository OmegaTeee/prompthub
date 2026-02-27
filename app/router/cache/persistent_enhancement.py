"""
Persistent enhancement cache.

Drop-in replacement for EnhancementCache that adds SQLite
persistence via PersistentCache while keeping the same
get_enhanced/set_enhanced convenience API.
"""

from pathlib import Path

from router.cache.memory import make_cache_key
from router.cache.persistent import PersistentCache


class PersistentEnhancementCache(PersistentCache):
    """
    Persistent cache specialized for prompt enhancement results.

    Mirrors the EnhancementCache API (get_enhanced, set_enhanced)
    with write-through L1+L2 persistence underneath.
    """

    def __init__(
        self,
        max_size: int = 500,
        default_ttl: float = 7200.0,  # 2 hours
        db_path: Path = Path("/tmp/prompthub/cache.db"),
    ):
        super().__init__(
            max_size=max_size,
            default_ttl=default_ttl,
            db_path=db_path,
        )

    async def get_enhanced(
        self,
        prompt: str,
        client_name: str | None = None,
        model: str | None = None,
    ) -> str | None:
        """
        Get a cached enhanced prompt.

        Args:
            prompt: Original prompt
            client_name: Client identifier
            model: Model used for enhancement

        Returns:
            Cached enhanced prompt or None
        """
        key = make_cache_key({
            "prompt": prompt,
            "client": client_name or "default",
            "model": model or "default",
        })
        return await self.get(key)

    async def set_enhanced(
        self,
        prompt: str,
        enhanced: str,
        client_name: str | None = None,
        model: str | None = None,
        ttl: float | None = None,
    ) -> None:
        """
        Cache an enhanced prompt.

        Args:
            prompt: Original prompt
            enhanced: Enhanced prompt result
            client_name: Client identifier
            model: Model used
            ttl: Custom TTL (None uses default)
        """
        key = make_cache_key({
            "prompt": prompt,
            "client": client_name or "default",
            "model": model or "default",
        })
        await self.set(key, enhanced, ttl)
