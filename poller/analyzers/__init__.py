"""
Congressional Analysis Package

This package provides specialized analysis modules for Congressional data:
- party_analytics: Party unity, bipartisanship, member consistency analysis
- geographic_analytics: State patterns, regional analysis, delegation unity
- temporal_analytics: Timeline trends, election cycles, seasonal patterns
- topic_analytics: Bill categorization, committee activity, policy focus
- orchestrator: Comprehensive analysis coordination and reporting

All modules use the core.api, core.storage, and core.models for data access.
"""

__version__ = "1.0.0"

from analyzers.geographic_analytics import GeographicAnalyzer
from analyzers.orchestrator import AnalysisOrchestrator
from analyzers.party_analytics import PartyAnalyzer
from analyzers.temporal_analytics import TemporalAnalyzer
from analyzers.topic_analytics import TopicAnalyzer

__all__ = [
    "PartyAnalyzer",
    "GeographicAnalyzer",
    "TemporalAnalyzer",
    "TopicAnalyzer",
    "AnalysisOrchestrator",
]
