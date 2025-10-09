"""
Data Source Orchestration
=========================

Orchestration logic for managing multiple data sources.

Author: Document Intelligence Platform Team
Date: October 2025
"""

from .data_source_registry import DataSourceRegistry, get_registry, register_source
from .multi_source_orchestrator import MultiSourceOrchestrator, SearchResult, IngestionJob

__all__ = [
    "DataSourceRegistry",
    "get_registry",
    "register_source",
    "MultiSourceOrchestrator",
    "SearchResult",
    "IngestionJob"
]
