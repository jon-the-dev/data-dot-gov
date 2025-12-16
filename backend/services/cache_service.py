"""
Cache Service for Congressional Data API

Implements multi-layer caching with Redis (if available) and in-memory fallback.
Designed to significantly reduce API response times for frequently accessed data.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Optional, Union

import redis
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class CacheService:
    """Multi-layer cache service with Redis and in-memory fallback"""

    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 300):
        """
        Initialize cache service

        Args:
            redis_url: Redis connection URL (optional)
            default_ttl: Default TTL in seconds (5 minutes)
        """
        self.redis_client = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

        # Try to connect to Redis if URL provided
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Redis connection failed, using memory cache only: {e}")
                self.redis_client = None

    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate a cache key from prefix and parameters"""
        params = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
        return f"{prefix}:{params}" if params else prefix

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (tries Redis first, then memory)

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get failed for {key}: {e}")

        # Fall back to memory cache
        if key in self.memory_cache:
            cached = self.memory_cache[key]
            if cached["expires_at"] > time.time():
                return cached["value"]
            else:
                # Remove expired entry
                del self.memory_cache[key]

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if not specified)

        Returns:
            True if successful
        """
        ttl = ttl or self.default_ttl

        # Store in Redis if available
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value))
            except Exception as e:
                logger.warning(f"Redis set failed for {key}: {e}")

        # Always store in memory cache as backup
        self.memory_cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }

        return True

    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        deleted = False

        # Delete from Redis
        if self.redis_client:
            try:
                deleted = self.redis_client.delete(key) > 0
            except Exception as e:
                logger.warning(f"Redis delete failed for {key}: {e}")

        # Delete from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
            deleted = True

        return deleted

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern

        Args:
            pattern: Key pattern (e.g., "committees:*")

        Returns:
            Number of keys deleted
        """
        count = 0

        # Clear from Redis
        if self.redis_client:
            try:
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(
                        cursor, match=pattern, count=100
                    )
                    if keys:
                        count += self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
            except Exception as e:
                logger.warning(f"Redis pattern delete failed for {pattern}: {e}")

        # Clear from memory cache
        keys_to_delete = [
            k for k in self.memory_cache.keys()
            if self._matches_pattern(k, pattern)
        ]
        for key in keys_to_delete:
            del self.memory_cache[key]
            count += 1

        return count

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern (simple wildcard support)"""
        if pattern.endswith("*"):
            return key.startswith(pattern[:-1])
        return key == pattern

    def cleanup_expired(self):
        """Remove expired entries from memory cache"""
        current_time = time.time()
        expired_keys = [
            k for k, v in self.memory_cache.items()
            if v["expires_at"] <= current_time
        ]
        for key in expired_keys:
            del self.memory_cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache instance
_cache: Optional[CacheService] = None

def init_cache(redis_url: Optional[str] = None, default_ttl: int = 300):
    """Initialize the global cache service"""
    global _cache
    _cache = CacheService(redis_url, default_ttl)
    return _cache

def get_cache() -> CacheService:
    """Get the global cache service instance"""
    global _cache
    if _cache is None:
        _cache = CacheService()
    return _cache


def cache_response(
    prefix: str,
    ttl: Optional[int] = None,
    key_params: Optional[list] = None
):
    """
    Decorator to cache API responses

    Args:
        prefix: Cache key prefix (e.g., "committees", "bills")
        ttl: Time to live in seconds
        key_params: List of parameter names to include in cache key

    Example:
        @cache_response("committees", ttl=600, key_params=["congress", "chamber"])
        async def get_committees(congress: int, chamber: str = None):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # Build cache key from specified parameters
            cache_params = {}
            if key_params:
                for param in key_params:
                    if param in kwargs:
                        cache_params[param] = kwargs[param]

            cache_key = cache._get_cache_key(prefix, **cache_params)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value

            # Call the actual function
            logger.debug(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


class CachingStrategy:
    """Caching strategy configurations for different data types"""

    # Short-lived cache for frequently changing data
    SHORT_TTL = 60  # 1 minute

    # Medium cache for semi-static data
    MEDIUM_TTL = 300  # 5 minutes

    # Long cache for mostly static data
    LONG_TTL = 3600  # 1 hour

    # Very long cache for historical/archived data
    VERY_LONG_TTL = 86400  # 24 hours

    @staticmethod
    def get_ttl_for_endpoint(endpoint: str) -> int:
        """
        Get appropriate TTL for an endpoint based on data characteristics

        Args:
            endpoint: API endpoint path

        Returns:
            TTL in seconds
        """
        # Historical data - very long cache
        if any(x in endpoint for x in ["analysis", "historical", "archived"]):
            return CachingStrategy.VERY_LONG_TTL

        # Committee data - long cache (committees don't change often)
        elif "committees" in endpoint:
            if any(x in endpoint for x in ["members", "bills"]):
                return CachingStrategy.MEDIUM_TTL  # These can change more frequently
            return CachingStrategy.LONG_TTL

        # Bills and votes - medium cache
        elif any(x in endpoint for x in ["bills", "votes"]):
            return CachingStrategy.MEDIUM_TTL

        # Member data - medium cache
        elif "members" in endpoint:
            return CachingStrategy.MEDIUM_TTL

        # Default to short cache
        else:
            return CachingStrategy.SHORT_TTL