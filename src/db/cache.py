import os
import json
import time
from typing import Any, Optional, Dict
try:
    from constants import REDIS_URL_KEY, DEFAULT_REDIS_URL, CACHE_DEFAULT_TTL
except ImportError:
    from src.constants import REDIS_URL_KEY, DEFAULT_REDIS_URL, CACHE_DEFAULT_TTL


try:
    import redis
    REDIS_INSTALLED = True
except ImportError:
    REDIS_INSTALLED = False

class CacheManager:
    """
    Production-grade Caching Manager.
    Uses Redis if available; falls back seamlessly to an in-memory TTL cache.
    """
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv(REDIS_URL_KEY, DEFAULT_REDIS_URL)
        self.redis_client = None
        self.use_redis = False
        self.in_memory_cache: Dict[str, Dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0

        self._connect_redis()

    def _connect_redis(self):
        if REDIS_INSTALLED:
            try:
                client = redis.Redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=1.5
                )
                client.ping()
                self.redis_client = client
                self.use_redis = True
            except Exception:
                self.redis_client = None
                self.use_redis = False
        else:
            self.use_redis = False

    def get(self, key: str) -> Optional[Any]:
        """Get item from Redis or in-memory cache."""
        if self.use_redis and self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val is not None:
                    self.hits += 1
                    return json.loads(val)
                self.misses += 1
                return None
            except Exception:
                # Redis error, attempt fallback
                pass

        # In-memory lookup
        entry = self.in_memory_cache.get(key)
        if entry:
            if entry["expire_at"] is None or entry["expire_at"] > time.time():
                self.hits += 1
                return entry["value"]
            else:
                # Expired
                del self.in_memory_cache[key]
        
        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = CACHE_DEFAULT_TTL) -> bool:
        """Set item in Redis or in-memory cache with expiration TTL."""
        val_str = json.dumps(value)
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.setex(key, ttl_seconds, val_str)
                return True
            except Exception:
                pass

        # In-memory storage fallback
        expire_at = time.time() + ttl_seconds if ttl_seconds > 0 else None
        self.in_memory_cache[key] = {
            "value": value,
            "expire_at": expire_at
        }
        return True

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        deleted = False
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
                deleted = True
            except Exception:
                pass

        if key in self.in_memory_cache:
            del self.in_memory_cache[key]
            deleted = True

        return deleted

    def clear(self) -> bool:
        """Clear all cached keys."""
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception:
                pass

        self.in_memory_cache.clear()
        return True

    def stats(self) -> Dict[str, Any]:
        """Returns stats about the caching layer."""
        active_keys = 0
        if self.use_redis and self.redis_client:
            try:
                active_keys = len(self.redis_client.keys("*"))
            except Exception:
                active_keys = 0
        else:
            # Clean expired before counting
            now = time.time()
            expired = [k for k, v in self.in_memory_cache.items() if v["expire_at"] and v["expire_at"] <= now]
            for k in expired:
                del self.in_memory_cache[k]
            active_keys = len(self.in_memory_cache)

        return {
            "backend": "redis" if self.use_redis else "in_memory_ttl",
            "redis_available": self.use_redis,
            "active_cached_keys": active_keys,
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": round(self.hits / (self.hits + self.misses), 3) if (self.hits + self.misses) > 0 else 0.0
        }

# Global singleton cache instance
cache = CacheManager()
