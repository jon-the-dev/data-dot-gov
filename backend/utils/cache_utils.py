"""
Cache Utilities

Simple in-memory and file-based caching for API responses and expensive operations.
"""

import json
import logging
import os
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# In-memory cache
_memory_cache: Dict[str, Dict[str, Any]] = {}

# Cache configuration
CACHE_DIR = Path(os.getenv("CACHE_DIR", "/tmp/congress_api_cache"))
DEFAULT_TTL = 3600  # 1 hour default TTL
LONG_TTL = 86400  # 24 hours for stable data
SHORT_TTL = 300   # 5 minutes for frequently changing data


def _ensure_cache_dir():
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments."""
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    return str(hash(str(key_data)))


def cache_response(ttl: int = DEFAULT_TTL, use_file: bool = False):
    """
    Decorator for caching function responses.

    Args:
        ttl: Time to live in seconds
        use_file: Whether to use file-based cache instead of memory
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{_generate_cache_key(*args, **kwargs)}"

            # Try to get from cache first
            cached_result = get_cached_response(cache_key, use_file)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            set_cached_response(cache_key, result, ttl, use_file)
            logger.debug(f"Cached result for {cache_key}")
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{_generate_cache_key(*args, **kwargs)}"

            # Try to get from cache first
            cached_result = get_cached_response(cache_key, use_file)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            set_cached_response(cache_key, result, ttl, use_file)
            logger.debug(f"Cached result for {cache_key}")
            return result

        # Return appropriate wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_cached_response(cache_key: str, use_file: bool = False) -> Optional[Any]:
    """
    Get cached response by key.

    Args:
        cache_key: Cache key
        use_file: Whether to check file cache

    Returns:
        Cached value or None if not found/expired
    """
    current_time = time.time()

    if use_file:
        return _get_file_cached_response(cache_key, current_time)
    else:
        return _get_memory_cached_response(cache_key, current_time)


def set_cached_response(cache_key: str, value: Any, ttl: int, use_file: bool = False):
    """
    Set cached response.

    Args:
        cache_key: Cache key
        value: Value to cache
        ttl: Time to live in seconds
        use_file: Whether to use file cache
    """
    current_time = time.time()
    expire_time = current_time + ttl

    if use_file:
        _set_file_cached_response(cache_key, value, expire_time)
    else:
        _set_memory_cached_response(cache_key, value, expire_time)


def _get_memory_cached_response(cache_key: str, current_time: float) -> Optional[Any]:
    """Get response from memory cache."""
    if cache_key in _memory_cache:
        cache_entry = _memory_cache[cache_key]
        if cache_entry["expire_time"] > current_time:
            return cache_entry["value"]
        else:
            # Expired, remove from cache
            del _memory_cache[cache_key]
    return None


def _set_memory_cached_response(cache_key: str, value: Any, expire_time: float):
    """Set response in memory cache."""
    _memory_cache[cache_key] = {
        "value": value,
        "expire_time": expire_time,
        "created_time": time.time()
    }


def _get_file_cached_response(cache_key: str, current_time: float) -> Optional[Any]:
    """Get response from file cache."""
    try:
        _ensure_cache_dir()
        cache_file = CACHE_DIR / f"{cache_key}.json"

        if cache_file.exists():
            with open(cache_file) as f:
                cache_data = json.load(f)

            if cache_data["expire_time"] > current_time:
                return cache_data["value"]
            else:
                # Expired, remove file
                cache_file.unlink(missing_ok=True)

    except Exception as e:
        logger.warning(f"Error reading cache file {cache_key}: {e}")

    return None


def _set_file_cached_response(cache_key: str, value: Any, expire_time: float):
    """Set response in file cache."""
    try:
        _ensure_cache_dir()
        cache_file = CACHE_DIR / f"{cache_key}.json"

        # Convert datetime objects to strings for JSON serialization
        serializable_value = _make_json_serializable(value)

        cache_data = {
            "value": serializable_value,
            "expire_time": expire_time,
            "created_time": time.time()
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

    except Exception as e:
        logger.warning(f"Error writing cache file {cache_key}: {e}")


def _make_json_serializable(obj: Any) -> Any:
    """Convert object to JSON-serializable format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_serializable(item) for item in obj]
    elif hasattr(obj, "dict"):  # Pydantic models
        return _make_json_serializable(obj.dict())
    else:
        return obj


def clear_cache(pattern: Optional[str] = None, use_file: bool = False):
    """
    Clear cache entries matching pattern.

    Args:
        pattern: Pattern to match cache keys (None clears all)
        use_file: Whether to clear file cache
    """
    if use_file:
        _clear_file_cache(pattern)
    else:
        _clear_memory_cache(pattern)


def _clear_memory_cache(pattern: Optional[str] = None):
    """Clear memory cache."""
    if pattern is None:
        _memory_cache.clear()
        logger.info("Cleared all memory cache")
    else:
        keys_to_remove = [key for key in _memory_cache if pattern in key]
        for key in keys_to_remove:
            del _memory_cache[key]
        logger.info(f"Cleared {len(keys_to_remove)} memory cache entries matching '{pattern}'")


def _clear_file_cache(pattern: Optional[str] = None):
    """Clear file cache."""
    try:
        _ensure_cache_dir()
        if pattern is None:
            # Clear all cache files
            for cache_file in CACHE_DIR.glob("*.json"):
                cache_file.unlink()
            logger.info("Cleared all file cache")
        else:
            # Clear files matching pattern
            removed_count = 0
            for cache_file in CACHE_DIR.glob("*.json"):
                if pattern in cache_file.stem:
                    cache_file.unlink()
                    removed_count += 1
            logger.info(f"Cleared {removed_count} file cache entries matching '{pattern}'")

    except Exception as e:
        logger.warning(f"Error clearing file cache: {e}")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    current_time = time.time()

    # Memory cache stats
    memory_total = len(_memory_cache)
    memory_expired = sum(1 for entry in _memory_cache.values() if entry["expire_time"] <= current_time)
    memory_valid = memory_total - memory_expired

    # File cache stats
    file_total = 0
    file_expired = 0
    file_valid = 0

    try:
        _ensure_cache_dir()
        for cache_file in CACHE_DIR.glob("*.json"):
            file_total += 1
            try:
                with open(cache_file) as f:
                    cache_data = json.load(f)
                if cache_data["expire_time"] <= current_time:
                    file_expired += 1
                else:
                    file_valid += 1
            except Exception:
                file_expired += 1  # Treat corrupted files as expired

    except Exception as e:
        logger.warning(f"Error getting file cache stats: {e}")

    return {
        "memory_cache": {
            "total": memory_total,
            "valid": memory_valid,
            "expired": memory_expired
        },
        "file_cache": {
            "total": file_total,
            "valid": file_valid,
            "expired": file_expired
        },
        "cache_dir": str(CACHE_DIR)
    }
