"""
API module for government data collection.

Provides unified API clients for Congress.gov and Senate.gov
with consistent rate limiting and error handling.
"""

from .base import BaseAPI
from .congress import CongressGovAPI
from .rate_limiter import RateLimiter
from .senate import SenateGovAPI

__all__ = [
    "RateLimiter",
    "CongressGovAPI",
    "SenateGovAPI",
    "BaseAPI",
]
