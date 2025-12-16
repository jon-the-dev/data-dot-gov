"""
Unified rate limiter for API compliance.

Provides thread-safe rate limiting to respect API terms of service
for both Congress.gov and Senate.gov APIs.
"""

import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe rate limiter to respect API terms of service"""

    def __init__(self, max_requests: int, time_window: int, name: Optional[str] = None):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
            name: Optional name for logging purposes
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.name = name or "RateLimiter"
        self.requests = []
        self.lock = threading.Lock()

    def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded"""
        with self.lock:
            now = time.time()

            # Remove old requests outside the time window
            self.requests = [
                req_time
                for req_time in self.requests
                if now - req_time < self.time_window
            ]

            if len(self.requests) >= self.max_requests:
                # Calculate wait time based on oldest request
                oldest_request = min(self.requests)
                wait_time = self.time_window - (now - oldest_request) + 1

                if wait_time > 0:
                    logger.info(
                        f"{self.name}: Rate limit reached, waiting {wait_time:.1f} seconds..."
                    )
                    time.sleep(wait_time)

                    # Clean up after waiting
                    now = time.time()
                    self.requests = [
                        req_time
                        for req_time in self.requests
                        if now - req_time < self.time_window
                    ]

            # Record this request
            self.requests.append(now)

    def get_stats(self) -> dict:
        """
        Get current rate limiter statistics

        Returns:
            Dictionary with current stats
        """
        with self.lock:
            now = time.time()
            # Clean up old requests
            self.requests = [
                req_time
                for req_time in self.requests
                if now - req_time < self.time_window
            ]

            return {
                "name": self.name,
                "max_requests": self.max_requests,
                "time_window": self.time_window,
                "current_requests": len(self.requests),
                "requests_remaining": max(0, self.max_requests - len(self.requests)),
                "time_until_reset": (
                    self.time_window - (now - min(self.requests))
                    if self.requests
                    else 0
                ),
            }

    def reset(self) -> None:
        """Reset the rate limiter by clearing all recorded requests"""
        with self.lock:
            self.requests.clear()
            logger.info(f"{self.name}: Rate limiter reset")
