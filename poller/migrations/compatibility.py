#!/usr/bin/env python3
"""
Backward compatibility layer for the core package migration.

This module provides thin wrappers that maintain original class/function signatures
while internally using the new core modules. This ensures existing code continues
to work during the migration period.
"""

import warnings
from typing import Dict, List, Optional

from core.api.congress import CongressGovAPI as CoreCongressGovAPI

# Import from core modules
from core.api.rate_limiter import RateLimiter as CoreRateLimiter
from core.api.senate import SenateGovAPI as CoreSenateGovAPI
from core.storage import save_index as core_save_index
from core.storage import save_individual_record as core_save_individual_record


class RateLimiter:
    """
    Compatibility wrapper for RateLimiter.

    DEPRECATED: Use core.api.rate_limiter.RateLimiter directly.
    """

    def __init__(self, max_requests: int, time_window: int):
        warnings.warn(
            "Using compatibility RateLimiter. Import from core.api.rate_limiter instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._core_limiter = CoreRateLimiter(max_requests, time_window)

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        return self._core_limiter.wait_if_needed()

    @property
    def max_requests(self):
        return self._core_limiter.max_requests

    @property
    def time_window(self):
        return self._core_limiter.time_window


class CongressGovAPI:
    """
    Compatibility wrapper for CongressGovAPI.

    DEPRECATED: Use core.api.congress.CongressGovAPI directly.
    """

    def __init__(self, api_key: Optional[str] = None, max_workers: int = 10):
        warnings.warn(
            "Using compatibility CongressGovAPI. Import from core.api.congress instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._core_api = CoreCongressGovAPI(api_key=api_key, max_workers=max_workers)

    def _make_request(self, endpoint: str, params: Optional[Dict] = None):
        """Make a rate-limited request to Congress.gov API."""
        return self._core_api._make_request(endpoint, params)

    def get_bills(self, congress: Optional[int] = None, limit: int = 25,
                 max_results: int = 25, output_dir: str = "data",
                 incremental: bool = True) -> List[Dict]:
        """Get bills from Congress."""
        return self._core_api.get_bills(
            congress=congress, limit=limit, max_results=max_results,
            output_dir=output_dir, incremental=incremental
        )

    def get_house_votes(self, congress: int = 118, session: int = None,
                       limit: int = 25, max_results: int = 25) -> List[Dict]:
        """Get House roll call votes."""
        return self._core_api.get_house_votes(
            congress=congress, session=session, limit=limit, max_results=max_results
        )

    def get_bills_with_votes(self, congress: int = 118, limit: int = 25,
                           max_results: int = 25) -> List[Dict]:
        """Get bills with their voting information."""
        return self._core_api.get_bills_with_votes(
            congress=congress, limit=limit, max_results=max_results
        )

    # Expose core API properties
    @property
    def api_key(self):
        return self._core_api.api_key

    @property
    def session(self):
        return self._core_api.session

    @property
    def rate_limiter(self):
        return self._core_api.rate_limiter


class SenateGovAPI:
    """
    Compatibility wrapper for SenateGovAPI.

    DEPRECATED: Use core.api.senate.SenateGovAPI directly.
    """

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        warnings.warn(
            "Using compatibility SenateGovAPI. Import from core.api.senate instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._core_api = CoreSenateGovAPI(username=username, password=password)

    def authenticate(self):
        """Authenticate with senate.gov API."""
        return self._core_api.authenticate()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None):
        """Make a rate-limited request to the API."""
        return self._core_api._make_request(endpoint, params)

    def get_filings(self, filing_type: str = "LD-1",
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   limit: int = 25,
                   max_results: int = 25,
                   output_dir: str = "data",
                   incremental: bool = True) -> List[Dict]:
        """Get lobbying disclosure filings."""
        return self._core_api.get_filings(
            filing_type=filing_type, start_date=start_date, end_date=end_date,
            limit=limit, max_results=max_results, output_dir=output_dir,
            incremental=incremental
        )

    def get_lobbyists(self, start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     limit: int = 25,
                     max_results: int = 25,
                     output_dir: str = "data",
                     incremental: bool = True) -> List[Dict]:
        """Get lobbyist information."""
        return self._core_api.get_lobbyists(
            start_date=start_date, end_date=end_date, limit=limit,
            max_results=max_results, output_dir=output_dir, incremental=incremental
        )

    # Expose core API properties
    @property
    def username(self):
        return self._core_api.username

    @property
    def password(self):
        return self._core_api.password

    @property
    def token(self):
        return self._core_api.token

    @property
    def session(self):
        return self._core_api.session

    @property
    def rate_limiter(self):
        return self._core_api.rate_limiter


def save_individual_record(record: Dict, record_type: str, identifier: str,
                          base_dir: str = "data") -> str:
    """
    Compatibility wrapper for save_individual_record.

    DEPRECATED: Use core.storage.save_individual_record directly.
    """
    warnings.warn(
        "Using compatibility save_individual_record. Import from core.storage instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return core_save_individual_record(record, record_type, identifier, base_dir)


def save_index(records: List[Dict], record_type: str,
              base_dir: str = "data", congress: Optional[int] = None) -> str:
    """
    Compatibility wrapper for save_index.

    DEPRECATED: Use core.storage.save_index directly.
    """
    warnings.warn(
        "Using compatibility save_index. Import from core.storage instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return core_save_index(records, record_type, base_dir, congress)


# Legacy imports - these provide a smooth migration path
__all__ = [
    "RateLimiter",
    "CongressGovAPI",
    "SenateGovAPI",
    "save_individual_record",
    "save_index"
]


def get_migration_status() -> Dict:
    """
    Get the current migration status and recommendations.

    Returns:
        Dictionary with migration information and next steps.
    """
    return {
        "status": "compatibility_layer_active",
        "message": "You are using the compatibility layer. All functionality works but with deprecation warnings.",
        "next_steps": [
            "Update imports to use core.api.* and core.storage.* directly",
            "Remove any local class definitions that duplicate core functionality",
            "Test thoroughly with the new imports",
            "Remove this compatibility layer when migration is complete"
        ],
        "core_modules": {
            "rate_limiter": "core.api.rate_limiter.RateLimiter",
            "congress_api": "core.api.congress.CongressGovAPI",
            "senate_api": "core.api.senate.SenateGovAPI",
            "storage": "core.storage (save_individual_record, save_index, FileStorage)"
        }
    }


if __name__ == "__main__":
    # Print migration status when run directly
    import json
    status = get_migration_status()
    print("=== Core Package Migration Status ===")
    print(json.dumps(status, indent=2))
