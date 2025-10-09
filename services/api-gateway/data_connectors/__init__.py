"""
Data Connectors Package
=======================

This package contains all data source connectors and orchestration logic
for the multi-source data integration system.

Author: Document Intelligence Platform Team
Date: October 2025
"""

from .orchestrator.data_source_registry import get_registry, register_source
from .orchestrator.multi_source_orchestrator import MultiSourceOrchestrator
from .base.abstract_data_source import (
    AbstractDataSource, StandardDocument, SourceType, DocumentType,
    Author, Entity, Relationship
)

__all__ = [
    "get_registry",
    "register_source", 
    "MultiSourceOrchestrator",
    "AbstractDataSource",
    "StandardDocument",
    "SourceType",
    "DocumentType",
    "Author",
    "Entity",
    "Relationship"
]
