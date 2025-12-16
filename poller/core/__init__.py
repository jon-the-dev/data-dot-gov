"""
Core package for Senate Gov data collection platform.

This package provides unified APIs, rate limiting, storage utilities,
and data models for congressional and lobbying data collection.
"""

__version__ = "1.0.0"

# Re-export key classes for convenience
from .api.congress import CongressGovAPI
from .api.rate_limiter import RateLimiter
from .api.senate import SenateGovAPI
from .storage.file_storage import FileStorage, save_index, save_individual_record

__all__ = [
    "RateLimiter",
    "CongressGovAPI",
    "SenateGovAPI",
    "FileStorage",
    "save_individual_record",
    "save_index",
]
