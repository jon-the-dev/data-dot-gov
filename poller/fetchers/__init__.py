"""
Congressional Transparency Platform - Unified Fetchers Module

This module provides consolidated fetching capabilities for government data,
consolidating functionality from multiple previous scripts into a unified interface.

Key Components:
- UnifiedFetcher: Common fetching operations for bills, votes, members, and filings
- SpecializedFetcher: Advanced operations for detailed analysis and cross-referencing

Usage:
    from fetchers import UnifiedFetcher, SpecializedFetcher

    # Basic fetching operations
    unified = UnifiedFetcher(data_dir="data", max_workers=5)
    results = unified.fetch_all(congress=118, max_results=100)

    # Advanced operations
    specialized = SpecializedFetcher(data_dir="data", verbose=True)
    count, files = specialized.fetch_detailed_voting_records(congress=118)
    analysis = specialized.analyze_party_voting_patterns(congress=118)

Features:
- Consolidated API usage through core.api package
- Both bulk and individual record fetching
- Incremental/resumable fetching capabilities
- Compressed storage support
- Progress tracking and logging
- Parallel processing with ThreadPoolExecutor
- Cross-referencing and data enrichment
- Party voting pattern analysis
- Committee and membership tracking
"""

from .specialized_fetcher import SpecializedFetcher
from .unified_fetcher import UnifiedFetcher

# Version information
__version__ = "1.0.0"
__author__ = "Congressional Transparency Platform"

# Public API
__all__ = [
    "UnifiedFetcher",
    "SpecializedFetcher",
]


# Convenience imports for backward compatibility
def create_unified_fetcher(**kwargs):
    """
    Create a UnifiedFetcher instance with sensible defaults.

    Args:
        **kwargs: Arguments passed to UnifiedFetcher constructor

    Returns:
        UnifiedFetcher instance
    """
    return UnifiedFetcher(**kwargs)


def create_specialized_fetcher(**kwargs):
    """
    Create a SpecializedFetcher instance with sensible defaults.

    Args:
        **kwargs: Arguments passed to SpecializedFetcher constructor

    Returns:
        SpecializedFetcher instance
    """
    return SpecializedFetcher(**kwargs)


# Add convenience functions to __all__
__all__.extend(
    [
        "create_unified_fetcher",
        "create_specialized_fetcher",
    ]
)
