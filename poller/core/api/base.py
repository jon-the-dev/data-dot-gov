"""
Base API client for government data collection.

Provides common functionality for making API requests with
rate limiting, error handling, and response validation.
"""

import logging
import time
from typing import Any, Dict, Optional

import requests

from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class BaseAPI:
    """Base class for API clients with common functionality"""

    def __init__(self, base_url: str, rate_limiter: RateLimiter, name: str = "BaseAPI"):
        """
        Initialize base API client

        Args:
            base_url: Base URL for the API
            rate_limiter: Rate limiter instance
            name: Name for logging purposes
        """
        self.base_url = base_url.rstrip("/")
        self.rate_limiter = rate_limiter
        self.name = name
        self.session = requests.Session()

        # Set a reasonable timeout and user agent
        self.session.headers.update(
            {"User-Agent": "Senate-Gov-Data-Collector/1.0 (Educational Research)"}
        )

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        retries: int = 3,
        timeout: int = 30,
    ) -> Optional[Dict]:
        """
        Make a rate-limited request to the API

        Args:
            endpoint: API endpoint (relative to base URL)
            params: Query parameters
            headers: Additional headers
            retries: Number of retry attempts
            timeout: Request timeout in seconds

        Returns:
            Response data or None if failed
        """
        self.rate_limiter.wait_if_needed()

        # Build URL
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        url = f"{self.base_url}/{endpoint}"

        # Merge headers
        request_headers = {}
        if headers:
            request_headers.update(headers)

        last_exception = None

        for attempt in range(retries + 1):
            try:
                logger.debug(f"{self.name}: Making request to {url}")

                response = self.session.get(
                    url, params=params, headers=request_headers, timeout=timeout
                )
                response.raise_for_status()

                # Try to parse JSON
                try:
                    return response.json()
                except ValueError as e:
                    logger.error(f"{self.name}: Invalid JSON response from {url}: {e}")
                    return None

            except requests.exceptions.HTTPError as e:
                last_exception = e
                status_code = e.response.status_code if e.response else None

                if status_code is None:
                    logger.error(f"{self.name}: HTTP error with no response: {e}")
                    continue
                elif status_code == 429:  # Rate limit exceeded
                    backoff_time = 60 * (attempt + 1)  # Exponential backoff
                    logger.warning(
                        f"{self.name}: Rate limit exceeded (429), backing off for {backoff_time}s..."
                    )
                    time.sleep(backoff_time)
                    continue
                elif status_code == 403:
                    logger.error(
                        f"{self.name}: Forbidden (403) - Check authentication/API key"
                    )
                    return None
                elif status_code == 404:
                    logger.warning(f"{self.name}: Not found (404): {url}")
                    return None
                elif status_code >= 500:  # Server errors - retry
                    backoff_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"{self.name}: Server error {status_code}, retrying in {backoff_time}s..."
                    )
                    time.sleep(backoff_time)
                    continue
                else:
                    logger.error(f"{self.name}: HTTP error {status_code}: {e}")
                    return None

            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(
                    f"{self.name}: Timeout on attempt {attempt + 1}/{retries + 1}"
                )
                if attempt < retries:
                    time.sleep(2**attempt)  # Exponential backoff
                continue

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(
                    f"{self.name}: Connection error on attempt {attempt + 1}/{retries + 1}"
                )
                if attempt < retries:
                    time.sleep(2**attempt)  # Exponential backoff
                continue

            except Exception as e:
                last_exception = e
                logger.error(f"{self.name}: Unexpected error: {e}")
                return None

        # All retries exhausted
        logger.error(
            f"{self.name}: All retry attempts failed. Last error: {last_exception}"
        )
        return None

    def _validate_response(
        self, data: Dict, required_fields: Optional[list] = None
    ) -> bool:
        """
        Validate API response structure

        Args:
            data: Response data to validate
            required_fields: List of required fields

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, dict):
            logger.error(f"{self.name}: Response is not a dictionary")
            return False

        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.error(f"{self.name}: Missing required fields: {missing_fields}")
                return False

        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get API client statistics

        Returns:
            Dictionary with client stats
        """
        return {
            "name": self.name,
            "base_url": self.base_url,
            "rate_limiter_stats": self.rate_limiter.get_stats(),
        }
